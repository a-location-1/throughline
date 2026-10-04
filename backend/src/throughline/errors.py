"""Safe, actionable error mapping."""

from .models import Failure

ERRORS = {
    "NOT_PLAYTEXT": "We could not establish that this source contains a playtext.",
    "NO_PLAYTEXT_STRUCTURE": "We could not identify scenes or speakers in this source.",
    "PDF_NO_TEXT": "This PDF contains no selectable text. Upload a text-based PDF instead.",
    "PDF_INVALID": "This file is not a readable PDF.",
    "PDF_TOO_LARGE": "This PDF is larger than the 10 MB upload limit.",
    "PDF_TOO_MANY_PAGES": "This PDF has more than the supported 200 pages.",
    "PDF_TEXT_TOO_LARGE": "The text extracted from this PDF is too large to analyze.",
    "SOURCE_EMPTY": "This source contains no readable text.",
    "SOURCE_UNREADABLE": "We could not read this source.",
    "SOURCE_INACCESSIBLE": "We could not retrieve this source.",
    "UNSUPPORTED_SCOPE": "This source is outside the supported playtext scope.",
    "LIMIT_EXCEEDED": "This source exceeds the supported size limit.",
    "RATE_LIMITED": "Too many analyses were submitted recently.",
    "CAPACITY_REACHED": "The analysis service is busy.",
}


def failure(
    code: str, next_action: str = "Try another text-based play PDF or public URL."
) -> Failure:
    return Failure(
        code=code,
        message=ERRORS.get(code, "This source could not be processed."),
        next_action=next_action,
    )
