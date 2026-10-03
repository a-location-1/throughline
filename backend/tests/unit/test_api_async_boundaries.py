import asyncio
import threading

import pytest

from throughline import api
from throughline.models import SourceKind, SubmissionState
from throughline.extraction import ExtractedText
from throughline.state import AnalysisStore


@pytest.mark.asyncio
async def test_parse_runs_off_event_loop(monkeypatch):
    store = AnalysisStore()
    item = store.create("test-client")
    started = threading.Event()
    caller_thread = threading.get_ident()
    worker_threads = []

    original_parse = api.parse_playtext

    def blocking_parse(text, submission):
        worker_threads.append(threading.get_ident())
        started.set()
        return original_parse(text, submission)

    monkeypatch.setattr(api, "store", store)
    monkeypatch.setattr(api, "parse_playtext", blocking_parse)
    extracted = ExtractedText("ALICE\nHello", "play.txt")

    task = asyncio.create_task(
        api._finish_parse(item.analysis_id, extracted, SourceKind.URL)
    )
    await asyncio.to_thread(started.wait)
    assert worker_threads[0] != caller_thread
    await task


@pytest.mark.asyncio
async def test_compressed_responses_are_rejected_before_body_iteration(monkeypatch):
    from throughline.acquisition import fetch_url

    class Response:
        is_redirect = False
        headers = {
            "content-type": "text/plain",
            "content-encoding": "gzip",
        }

        def raise_for_status(self):
            pass

        def aiter_raw(self, size):
            raise AssertionError("compressed body must not be read")

    class Client:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        class Stream:
            async def __aenter__(self):
                return Response()

            async def __aexit__(self, *args):
                pass

        def stream(self, method, url):
            return self.Stream()

    monkeypatch.setattr(
        "throughline.acquisition.httpx.AsyncClient", lambda **kwargs: Client()
    )
    monkeypatch.setattr(
        "throughline.acquisition._public_host", lambda host: ("93.184.216.34",)
    )
    with pytest.raises(ValueError, match="compressed"):
        await fetch_url("https://example.org/play")