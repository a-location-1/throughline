"""Typed domain models for deterministic playtext analysis."""

from __future__ import annotations

import json
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SourceKind(str, Enum):
    URL = "url"
    PDF = "pdf"


class SubmissionState(str, Enum):
    QUEUED = "queued"
    RETRIEVING = "retrieving"
    EXTRACTING = "extracting"
    PARSING = "parsing"
    READY = "ready"
    REJECTED = "rejected"


class CharacterKind(str, Enum):
    NAMED = "named"
    UNNAMED = "unnamed"
    COLLECTIVE = "collective"
    INDETERMINATE = "indeterminate"
    SILENT = "silent"


class ActKind(str, Enum):
    ACT = "act"
    PROLOGUE = "prologue"
    EPILOGUE = "epilogue"
    ENTR_ACTE = "entr'acte"
    INTERLUDE = "interlude"


class Presence(str, Enum):
    SPEAKING = "speaking"
    NON_SPEAKING = "non_speaking"


class Confidence(str, Enum):
    SUPPORTED = "supported"
    AMBIGUOUS = "ambiguous"


class Failure(BaseModel):
    code: str
    message: str
    next_action: str


class Progress(BaseModel):
    stage: str
    percent: int = Field(ge=0, le=100)


class PlaytextSubmission(BaseModel):
    model_config = ConfigDict(extra="forbid")

    submission_id: str
    source_kind: SourceKind
    source_name: str = ""
    page_count: int | None = Field(default=None, ge=0, le=200)
    byte_count: int = Field(default=0, ge=0, le=10 * 1024 * 1024)
    state: SubmissionState = SubmissionState.QUEUED
    failure: Failure | None = None


class Scene(BaseModel):
    id: str
    ordinal: int = Field(ge=1)
    act_id: str
    label: str
    source_span: tuple[int, int] | None = None


class Act(BaseModel):
    id: str
    ordinal: int = Field(ge=1)
    label: str
    kind: ActKind = ActKind.ACT
    scenes: list[Scene] = Field(default_factory=list)


class Ambiguity(BaseModel):
    evidence: str
    alternatives: list[str] = Field(default_factory=list)


class CharacterOrSpeaker(BaseModel):
    id: str
    display_name: str
    kind: CharacterKind
    first_appearance_scene_id: str
    ambiguity: Ambiguity | None = None


class SceneAppearance(BaseModel):
    scene_id: str
    character_id: str
    presence: Presence
    line_count: int = Field(ge=0)
    confidence: Confidence = Confidence.SUPPORTED
    explanation: str | None = None

    @model_validator(mode="after")
    def non_speaking_has_no_lines(self) -> "SceneAppearance":
        if self.presence == Presence.NON_SPEAKING and self.line_count != 0:
            raise ValueError("non_speaking appearances must have zero lines")
        return self


class VisualizationInputs(BaseModel):
    scene_ids: list[str]
    character_ids: list[str]
    colors: dict[str, str]
    paths: dict[str, list[tuple[int, int]]]


class Ordering(BaseModel):
    scene_ids: list[str]
    character_ids: list[str]
    scene_line_count_desc: dict[str, list[str]] = Field(default_factory=dict)


class AnalysisResult(BaseModel):
    schema_version: str = "1.0"
    parser_version: str = "0.1.0"
    submission: PlaytextSubmission
    acts: list[Act]
    scenes: list[Scene]
    characters: list[CharacterOrSpeaker]
    appearances: list[SceneAppearance]
    ordering: Ordering
    visualization: VisualizationInputs

    def canonical_json(self) -> str:
        return json.dumps(
            self.model_dump(mode="json"),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )


class AnalysisStatus(BaseModel):
    analysis_id: str
    state: SubmissionState
    progress: Progress | None = None
    error: Failure | None = None
    result: AnalysisResult | None = None


class CreateAnalysisResponse(BaseModel):
    analysis_id: str
    state: SubmissionState
    progress: Progress
