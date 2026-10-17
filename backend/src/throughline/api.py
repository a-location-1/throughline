"""FastAPI HTTP boundary for session-only analyses."""

from __future__ import annotations

import asyncio
import os
from fastapi import FastAPI, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, HttpUrl, ValidationError

from .acquisition import fetch_url
from .errors import failure
from .extraction import extract_html, extract_pdf, extract_plain
from .logging import log_event, log_frontend_event
from .models import (
    AnalysisResult,
    PlaytextSubmission,
    SourceKind,
    SubmissionState,
)
from .parser import parse_playtext
from .state import RateLimiter

app = FastAPI(title="Throughline API", version="0.1.0")
configured_origins = os.getenv("FRONTEND_ORIGINS", "http://localhost:5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in configured_origins.split(",") if origin.strip()],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["content-type"],
)
rate_limiter = RateLimiter(
    {
        "analysis": (12, 60),
        "logs": (60, 60),
    }
)
CPU_TIMEOUT_SECONDS = 60
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_LOG_MESSAGE_LENGTH = 1000
MAX_LOG_CONTEXT_BYTES = 8 * 1024


def _processing_error_code(error: Exception) -> str:
    message = str(error).lower()
    if "image-only pdf" in message:
        return "PDF_NO_TEXT"
    if "too many pages" in message:
        return "PDF_TOO_MANY_PAGES"
    if "extracted text too large" in message:
        return "PDF_TEXT_TOO_LARGE"
    if "invalid pdf" in message:
        return "PDF_INVALID"
    if "empty source" in message:
        return "SOURCE_EMPTY"
    if "large" in message:
        return "PDF_TOO_LARGE"
    return "SOURCE_UNREADABLE"


class UrlRequest(BaseModel):
    url: HttpUrl


class FrontendLogRequest(BaseModel):
    level: str
    message: str = Field(min_length=1, max_length=MAX_LOG_MESSAGE_LENGTH)
    context: dict[str, object] = Field(default_factory=dict)

def _client_id(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _raise_processing_error(exc: Exception) -> None:
    code = _processing_error_code(exc) if isinstance(exc, ValueError) else (
        "SOURCE_INACCESSIBLE" if "retrieve" in str(exc).lower() else "SOURCE_UNREADABLE"
    )
    raise HTTPException(status_code=422, detail=failure(code).model_dump()) from exc


async def _finish_parse(extracted, kind: SourceKind) -> AnalysisResult:
    submission = PlaytextSubmission(
        submission_id="request",
        source_kind=kind,
        source_name=extracted.source_name,
        page_count=extracted.page_count,
        byte_count=extracted.byte_count,
        state=SubmissionState.PARSING,
    )
    try:
        result = await asyncio.wait_for(
            asyncio.to_thread(parse_playtext, extracted.text, submission),
            CPU_TIMEOUT_SECONDS,
        )
    except ValueError:
        raise HTTPException(
            status_code=422, detail=failure("NOT_PLAYTEXT").model_dump()
        ) from None
    result.submission.state = SubmissionState.READY
    return result


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/logs", status_code=204)
async def create_frontend_log(entry: FrontendLogRequest, request: Request) -> None:
    if not rate_limiter.allow(_client_id(request), "logs"):
        raise HTTPException(
            status_code=429,
            detail=failure("RATE_LIMITED").model_dump(),
            headers={"Retry-After": "60"},
        )
    if len(str(entry.context).encode("utf-8")) > MAX_LOG_CONTEXT_BYTES:
        raise HTTPException(status_code=413, detail="Log context is too large")
    level = entry.level.lower()
    if level not in {"info", "warn", "error"}:
        raise HTTPException(status_code=400, detail="Unsupported log level")
    log_frontend_event(level, entry.message, entry.context)


@app.post("/api/analyses", response_model=AnalysisResult)
async def create_analysis(
    request: Request,
) -> AnalysisResult:
    if not rate_limiter.allow(_client_id(request), "analysis"):
        raise HTTPException(
            status_code=429,
            detail=failure("RATE_LIMITED").model_dump(),
            headers={"Retry-After": "60"},
        )
    content_type = request.headers.get("content-type", "")
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            request_bytes = int(content_length)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid request size") from exc
        if request_bytes > MAX_UPLOAD_BYTES + 1024 * 1024:
            raise HTTPException(
                status_code=413, detail=failure("PDF_TOO_LARGE").model_dump()
            )
    url_request: UrlRequest | None = None
    file: UploadFile | None = None
    if content_type.startswith("application/json"):
        try:
            url_request = UrlRequest.model_validate(await request.json())
        except (ValueError, ValidationError) as exc:
            raise HTTPException(
                status_code=400, detail="Provide one valid public URL."
            ) from exc
    elif content_type.startswith("multipart/form-data"):
        form = await request.form()
        candidate = form.get("file")
        if candidate is not None and hasattr(candidate, "read"):
            file = candidate  # Starlette's multipart parser supplies this object.
    if (url_request is None) == (file is None):
        raise HTTPException(
            status_code=400, detail="Provide exactly one URL or PDF file."
        )
    try:
        if url_request is not None:
            source = await fetch_url(str(url_request.url))
            if source.content_type == "application/pdf":
                extracted = await asyncio.wait_for(
                    asyncio.to_thread(extract_pdf, source.content, source.source_name),
                    CPU_TIMEOUT_SECONDS,
                )
                kind = SourceKind.PDF
            elif source.content_type == "text/plain":
                extracted = await asyncio.wait_for(
                    asyncio.to_thread(extract_plain, source.content, source.source_name),
                    CPU_TIMEOUT_SECONDS,
                )
                kind = SourceKind.URL
            else:
                extracted = await asyncio.wait_for(
                    asyncio.to_thread(extract_html, source.content, source.source_name),
                    CPU_TIMEOUT_SECONDS,
                )
                kind = SourceKind.URL
        else:
            data = await file.read(MAX_UPLOAD_BYTES + 1)
            if len(data) > MAX_UPLOAD_BYTES:
                raise HTTPException(
                    status_code=413, detail=failure("PDF_TOO_LARGE").model_dump()
                )
            extracted = await asyncio.wait_for(
                asyncio.to_thread(extract_pdf, data, file.filename or "upload.pdf"),
                CPU_TIMEOUT_SECONDS,
            )
            kind = SourceKind.PDF
        return await _finish_parse(extracted, kind)
    except HTTPException:
        raise
    except Exception as exc:
        log_event("analysis_rejected")
        _raise_processing_error(exc)
