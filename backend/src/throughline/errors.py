"""Safe, actionable error mapping."""

from .models import Failure

ERRORS = {
    "NO_PLAYTEXT_STRUCTURE": "We could not identify scenes or speakers in this source.",
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
