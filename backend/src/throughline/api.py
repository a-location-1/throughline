"""FastAPI HTTP boundary for session-only analyses."""

from __future__ import annotations

import asyncio
import csv
import io
from fastapi import BackgroundTasks, FastAPI, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl, ValidationError

from .acquisition import fetch_url
from .errors import failure
from .extraction import extract_html, extract_pdf, extract_plain
from .logging import log_event
from .models import (
    AnalysisStatus,
    CreateAnalysisResponse,
    PlaytextSubmission,
    Progress,
    SourceKind,
    SubmissionState,
)
from .parser import parse_playtext
from .state import AnalysisStore

app = FastAPI(title="Throughline API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
store = AnalysisStore()


class UrlRequest(BaseModel):
    url: HttpUrl


def _status(item) -> AnalysisStatus:
    return AnalysisStatus(
        analysis_id=item.analysis_id,
        state=item.state,
        progress=item.progress,
        error=item.error,
        result=item.result,
    )


async def _process_url(analysis_id: str, url: str) -> None:
    try:
        store.update(
            analysis_id,
            state=SubmissionState.RETRIEVING,
            progress=Progress(stage="Retrieving source", percent=20),
        )
        source = await fetch_url(url)
        store.update(
            analysis_id,
            state=SubmissionState.EXTRACTING,
            progress=Progress(stage="Extracting text", percent=45),
        )
        if source.content_type == "application/pdf":
            extracted = extract_pdf(source.content, source.source_name)
            kind = SourceKind.PDF
        elif source.content_type == "text/plain":
            extracted = extract_plain(source.content, source.source_name)
            kind = SourceKind.URL
        else:
            extracted = extract_html(source.content, source.source_name)
            kind = SourceKind.URL
        await _finish_parse(analysis_id, extracted, kind)
    except Exception as exc:  # generic response; no source details leave the process
        log_event("analysis_rejected", analysis_id=analysis_id)
        store.update(
            analysis_id,
            state=SubmissionState.REJECTED,
            progress=Progress(stage="Unable to process source", percent=100),
            error=failure(
                "SOURCE_INACCESSIBLE"
                if "retrieve" in str(exc).lower()
                else "SOURCE_UNREADABLE"
            ),
        )


async def _process_pdf(analysis_id: str, data: bytes, filename: str) -> None:
    try:
        store.update(
            analysis_id,
            state=SubmissionState.EXTRACTING,
            progress=Progress(stage="Extracting text", percent=45),
        )
        extracted = extract_pdf(data, filename)
        await _finish_parse(analysis_id, extracted, SourceKind.PDF)
    except ValueError as exc:
        code = (
            "LIMIT_EXCEEDED"
            if "large" in str(exc) or "pages" in str(exc)
            else "SOURCE_UNREADABLE"
        )
        store.update(
            analysis_id,
            state=SubmissionState.REJECTED,
            progress=Progress(stage="Unable to process source", percent=100),
            error=failure(code),
        )


async def _finish_parse(analysis_id: str, extracted, kind: SourceKind) -> None:
    store.update(
        analysis_id,
        state=SubmissionState.PARSING,
        progress=Progress(stage="Identifying scenes and speakers", percent=70),
    )
    item = store.get(analysis_id)
    if item is None:
        return
    submission = PlaytextSubmission(
        submission_id=analysis_id,
        source_kind=kind,
        source_name=extracted.source_name,
        page_count=extracted.page_count,
        byte_count=extracted.byte_count,
        state=SubmissionState.PARSING,
    )
    try:
        result = parse_playtext(extracted.text, submission)
    except ValueError:
        store.update(
            analysis_id,
            state=SubmissionState.REJECTED,
            progress=Progress(stage="No usable playtext found", percent=100),
            error=failure("NO_PLAYTEXT_STRUCTURE"),
        )
        return
    result.submission.state = SubmissionState.READY
    store.update(
        analysis_id,
        state=SubmissionState.READY,
        progress=Progress(stage="Analysis ready", percent=100),
        result=result,
    )


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/analyses", status_code=202, response_model=CreateAnalysisResponse)
async def create_analysis(
    background_tasks: BackgroundTasks, request: Request
) -> CreateAnalysisResponse:
    content_type = request.headers.get("content-type", "")
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
        item = store.create()
    except RuntimeError as exc:
        code = "RATE_LIMITED" if "rate" in str(exc) else "CAPACITY_REACHED"
        raise HTTPException(
            status_code=429 if code == "RATE_LIMITED" else 503,
            detail=failure(code).model_dump(),
        ) from exc
    if url_request is not None:
        background_tasks.add_task(_process_url, item.analysis_id, str(url_request.url))
    else:
        data = await file.read()
        if len(data) > 10 * 1024 * 1024:
            store.reset(item.analysis_id)
            raise HTTPException(
                status_code=413, detail=failure("LIMIT_EXCEEDED").model_dump()
            )
        background_tasks.add_task(
            _process_pdf, item.analysis_id, data, file.filename or "upload.pdf"
        )
    return CreateAnalysisResponse(
        analysis_id=item.analysis_id, state=item.state, progress=item.progress
    )


@app.get("/api/analyses/{analysis_id}", response_model=AnalysisStatus)
async def get_analysis(analysis_id: str) -> AnalysisStatus:
    item = store.get(analysis_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return _status(item)


@app.get("/api/analyses/{analysis_id}/csv")
async def get_csv(analysis_id: str):
    item = store.get(analysis_id)
    if item is None or item.result is None:
        raise HTTPException(status_code=404, detail="Analysis not found")
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(["character", "scene_id", "presence", "line_count"])
    names = {
        character.id: character.display_name for character in item.result.characters
    }
    for appearance in item.result.appearances:
        values = [
            names[appearance.character_id],
            appearance.scene_id,
            appearance.presence.value,
            appearance.line_count,
        ]
        writer.writerow(
            [
                (
                    f"'={value}"
                    if isinstance(value, str) and value[:1] in "=+-@"
                    else value
                )
                for value in values
            ]
        )
    from fastapi.responses import Response

    return Response(
        output.getvalue(),
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=throughline-analysis.csv"
        },
    )
