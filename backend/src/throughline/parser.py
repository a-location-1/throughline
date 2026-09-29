"""Explicit, deterministic playtext parsing heuristics."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .models import (
    Act,
    Ambiguity,
    AnalysisResult,
    CharacterKind,
    CharacterOrSpeaker,
    Confidence,
    Ordering,
    PlaytextSubmission,
    Presence,
    Scene,
    SceneAppearance,
)
from .visualization import build_visualization

ACT_RE = re.compile(r"^\s*(?:ACT|ACTO|AKT)\s+(.+?)\s*$", re.I)
SCENE_RE = re.compile(r"^\s*(?:SCENE|SCÈNE|SZENE)\s+(.+?)\s*$", re.I)
SPEAKER_RE = re.compile(r"^\s*([A-Z][A-Z0-9 .,'’()\-]{1,48})(?::)?\s*$")
ENTER_RE = re.compile(
    r"\b(?:enter|enters|entrance of)\s+([A-Z][A-Za-zÀ-ÿ'’\- ]+)", re.I
)
COLLECTIVE_WORDS = {
    "ALL",
    "CHORUS",
    "CROWD",
    "COMPANY",
    "SOLDIERS",
    "PEOPLE",
    "GUARDS",
    "ENSEMBLE",
}
UNNAMED_WORDS = {"UNKNOWN", "UNNAMED", "A VOICE", "VOICE", "SOMEONE"}


@dataclass
class SceneChunk:
    act_label: str
    scene_label: str
    text: str
    start: int
    end: int


def _heading(line: str, pattern: re.Pattern[str]) -> str | None:
    match = pattern.match(line)
    return match.group(1).strip() if match else None


def _chunks(text: str) -> list[SceneChunk]:
    lines = text.splitlines(keepends=True)
    markers: list[tuple[int, str, str]] = []
    offset = 0
    current_act = "Act I"
    for line in lines:
        clean = line.strip()
        act_label = _heading(clean, ACT_RE)
        scene_label = _heading(clean, SCENE_RE)
        if act_label:
            current_act = f"Act {act_label}"
        if scene_label:
            markers.append((offset, current_act, f"Scene {scene_label}"))
        offset += len(line)
    if not markers:
        return [SceneChunk("Act I", "Scene I", text, 0, len(text))]
    chunks: list[SceneChunk] = []
    for index, (start, act_label, scene_label) in enumerate(markers):
        end = markers[index + 1][0] if index + 1 < len(markers) else len(text)
        body_start = start + len(text[start:].splitlines(keepends=True)[0])
        chunks.append(
            SceneChunk(act_label, scene_label, text[body_start:end], start, end)
        )
    return chunks


def _classify(display: str) -> CharacterKind:
    key = re.sub(r"[^A-Z0-9 ]", "", display.upper()).strip()
    if not key or key in UNNAMED_WORDS:
        return CharacterKind.UNNAMED
    if key in COLLECTIVE_WORDS or any(word in key.split() for word in COLLECTIVE_WORDS):
        return CharacterKind.COLLECTIVE
    return CharacterKind.NAMED


def _identity_key(display: str) -> str:
    return re.sub(r"[^\w]", "", display.casefold())


def parse_playtext(text: str, submission: PlaytextSubmission) -> AnalysisResult:
    chunks = _chunks(text)
    acts: list[Act] = []
    scenes: list[Scene] = []
    act_by_label: dict[str, Act] = {}
    for index, chunk in enumerate(chunks, 1):
        act = act_by_label.get(chunk.act_label)
        if act is None:
            act = Act(
                id=f"act-{len(acts) + 1:02d}",
                ordinal=len(acts) + 1,
                label=chunk.act_label,
            )
            acts.append(act)
            act_by_label[chunk.act_label] = act
        scene = Scene(
            id=f"scene-{index:02d}",
            ordinal=index,
            act_id=act.id,
            label=chunk.scene_label,
            source_span=(chunk.start, chunk.end),
        )
        act.scenes.append(scene)
        scenes.append(scene)

    characters: list[CharacterOrSpeaker] = []
    by_key: dict[str, CharacterOrSpeaker] = {}
    appearance_counts: dict[tuple[str, str], int] = {}
    scene_presence: set[tuple[str, str]] = set()
    scene_confidence: dict[tuple[str, str], Confidence] = {}
    for scene, chunk in zip(scenes, chunks):
        current: CharacterOrSpeaker | None = None
        for raw_line in chunk.text.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            entrance = ENTER_RE.search(line)
            if entrance:
                display = entrance.group(1).strip()
                key = _identity_key(display)
                if key and key not in by_key:
                    character = CharacterOrSpeaker(
                        id=f"character-{len(characters) + 1:02d}",
                        display_name=display,
                        kind=CharacterKind.SILENT,
                        first_appearance_scene_id=scene.id,
                    )
                    by_key[key] = character
                    characters.append(character)
                if key:
                    scene_presence.add((scene.id, by_key[key].id))
                continue
            speaker = SPEAKER_RE.match(line)
            if speaker and not line.startswith(("ACT ", "SCENE ")):
                display = speaker.group(1).strip()
                kind = _classify(display)
                key = _identity_key(display) or f"unnamed-{scene.id}"
                character = by_key.get(key)
                if character is None:
                    character = CharacterOrSpeaker(
                        id=f"character-{len(characters) + 1:02d}",
                        display_name=(
                            display
                            if kind != CharacterKind.UNNAMED
                            else "Unnamed speaker"
                        ),
                        kind=kind,
                        first_appearance_scene_id=scene.id,
                    )
                    by_key[key] = character
                    characters.append(character)
                elif character.display_name != display and character.ambiguity is None:
                    character.ambiguity = Ambiguity(
                        evidence="formatting or naming variation",
                        alternatives=[display],
                    )
                current = character
                scene_presence.add((scene.id, character.id))
                continue
            if current is not None and not (
                line.startswith("(") and line.endswith(")")
            ):
                appearance_counts[(scene.id, current.id)] = (
                    appearance_counts.get((scene.id, current.id), 0) + 1
                )
            elif line.startswith("(") and line.endswith(")"):
                scene_confidence[(scene.id, current.id if current else "")] = (
                    Confidence.AMBIGUOUS
                )

    appearances: list[SceneAppearance] = []
    for scene in scenes:
        for character in characters:
            key = (scene.id, character.id)
            lines = appearance_counts.get(key, 0)
            if key not in scene_presence and lines == 0:
                continue
            presence = Presence.SPEAKING if lines else Presence.NON_SPEAKING
            appearances.append(
                SceneAppearance(
                    scene_id=scene.id,
                    character_id=character.id,
                    presence=presence,
                    line_count=lines,
                    confidence=scene_confidence.get(key, Confidence.SUPPORTED),
                    explanation=(
                        "Source attribution is ambiguous."
                        if scene_confidence.get(key) == Confidence.AMBIGUOUS
                        else None
                    ),
                )
            )
    if not characters or not scenes:
        raise ValueError("no playtext structure")
    scene_ids = [scene.id for scene in scenes]
    character_ids = [character.id for character in characters]
    line_sort = {
        scene_id: sorted(
            (
                character.id
                for character in characters
                if (scene_id, character.id) in appearance_counts
            ),
            key=lambda cid: (
                -appearance_counts[(scene_id, cid)],
                character_ids.index(cid),
            ),
        )
        for scene_id in scene_ids
    }
    ordering = Ordering(
        scene_ids=scene_ids,
        character_ids=character_ids,
        scene_line_count_desc=line_sort,
    )
    result = AnalysisResult(
        submission=submission,
        acts=acts,
        scenes=scenes,
        characters=characters,
        appearances=appearances,
        ordering=ordering,
        visualization=build_visualization(scene_ids, character_ids, appearances),
    )
    return result
