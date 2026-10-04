import json
from pathlib import Path

import pytest

from throughline.models import PlaytextSubmission, SourceKind

FIXTURE_ROOT = Path(__file__).parent / "fixtures"


def _ready_fixture_cases() -> list[dict[str, object]]:
    manifest = json.loads((FIXTURE_ROOT / "manifest.json").read_text())
    cases = []
    for case in manifest["cases"]:
        if case["status"] != "ready":
            continue
        expected = json.loads((FIXTURE_ROOT / case["expected"]).read_text())
        if "acts" not in expected or "characters" not in expected:
            raise AssertionError(
                f"ready fixture {case['slug']} does not contain a complete answer key"
            )
        cases.append(case)
    return cases


def _rejected_fixture_cases() -> list[dict[str, object]]:
    manifest = json.loads((FIXTURE_ROOT / "manifest.json").read_text())
    return [
        case
        for case in manifest["cases"]
        if case["status"] == "rejected" and case.get("parser_check", True)
    ]


@pytest.fixture(params=_ready_fixture_cases(), ids=lambda case: case["slug"])
def golden_fixture(request: pytest.FixtureRequest) -> dict[str, object]:
    case = request.param
    return {
        **case,
        "source_text": (FIXTURE_ROOT / case["source"]).read_text(),
        "expected": json.loads((FIXTURE_ROOT / case["expected"]).read_text()),
    }


@pytest.fixture(params=_rejected_fixture_cases(), ids=lambda case: case["slug"])
def rejected_fixture(request: pytest.FixtureRequest) -> dict[str, object]:
    case = request.param
    return {
        **case,
        "source_text": (FIXTURE_ROOT / case["source"]).read_text(),
        "expected": json.loads((FIXTURE_ROOT / case["expected"]).read_text()),
    }


@pytest.fixture
def submission() -> PlaytextSubmission:
    return PlaytextSubmission(
        submission_id="test", source_kind=SourceKind.URL, source_name="example.org"
    )
