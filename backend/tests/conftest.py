import pytest

from throughline.models import PlaytextSubmission, SourceKind


@pytest.fixture
def submission() -> PlaytextSubmission:
    return PlaytextSubmission(
        submission_id="test", source_kind=SourceKind.URL, source_name="example.org"
    )
