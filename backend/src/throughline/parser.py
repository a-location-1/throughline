"""Explicit, deterministic playtext parsing heuristics."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .models import (
    Act,
    Ambiguity,
    AnalysisResult,
    ActKind,
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
SCENE_STAGE_RE = re.compile(r"^\s*(?:SCENE|SCÈNE|SZENE)\s*:\s*", re.I)
SPECIAL_ACT_RE = re.compile(
    r"^\s*(PROLOGUE|EPILOGUE|ENTR['’]?ACTE|ENTRACTE|INTERLUDE)\s*:?[ \t]*$",
    re.I,
)
SPEAKER_RE = re.compile(
    r"^\s*([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ0-9 .,'’\-]{1,48}(?:\([^()]*\))?)(?::)?\s*$"
)
SPEAKER_PREFIX_RE = re.compile(
    r"^\s*([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ0-9 .,'’\-]{1,48}(?:\([^()]*\))?)\s*:\s*(.*)$"
)
PLAY_END_RE = re.compile(
    r"^\s*(?:THE END|END OF THE PLAY|FINIS|CURTAIN|"
    r"PROJECT GUTENBERG(?: LICENSE)?|GUTENBERG LICENSE|"
    r"ADVERTISEMENTS?|OTHER PLAYS|ABOUT THE AUTHOR|"
    r"(?:EDITOR'?S?|AUTHOR'?S?) (?:NOTE|PREFACE|INTRODUCTION)|"
    r"NOTES?|ESSAY|COMMENTARY|APPENDIX|APPENDICES|LICENSE|LICENCE)\s*:?[ \t]*$",
    re.I,
)
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
DELIVERY_NOTE_RE = re.compile(r"\s+\([^()]*\)\s*$")
QUALIFIED_SPEAKER_RE = re.compile(r"^(?P<base>.+?)\s+WITH\s+(?:A|AN|THE)\s+.+$", re.I)


@dataclass
class SceneChunk:
    act_label: str
    act_kind: ActKind
    scene_label: str
    text: str
    start: int
    end: int


def _heading(line: str, pattern: re.Pattern[str]) -> str | None:
    match = pattern.match(line)
    return match.group(1).strip() if match else None


def _special_act(line: str) -> tuple[str, ActKind] | None:
    match = SPECIAL_ACT_RE.match(line)
    if not match:
        return None
    label = match.group(1).upper().replace("’", "'")
    if label in {"ENTRACTE", "ENTR'ACTE"}:
        return "Entr'acte", ActKind.ENTR_ACTE
    kind = ActKind(label.casefold())
    return label.title(), kind


def _play_end(text: str, minimum: int) -> int:
    offset = 0
    for line in text.splitlines(keepends=True):
        if offset > minimum and PLAY_END_RE.match(line.strip()):
            return offset
        offset += len(line)
    return len(text)


def _chunks(text: str) -> list[SceneChunk]:
    lines = text.splitlines(keepends=True)
    markers: list[tuple[int, str, ActKind, str]] = []
    offset = 0
    current_act = "Act I"
    current_act_kind = ActKind.ACT
    first_act_start: int | None = None
    for line in lines:
        clean = line.strip()
        act_label = _heading(clean, ACT_RE)
        scene_label = _heading(clean, SCENE_RE)
        if act_label:
            if first_act_start is None:
                first_act_start = offset
            current_act = f"Act {act_label}"
            current_act_kind = ActKind.ACT
        special_act = _special_act(clean)
        if special_act:
            current_act, current_act_kind = special_act
            markers.append((offset, current_act, current_act_kind, current_act))
        if scene_label:
            markers.append(
                (offset, current_act, current_act_kind, f"Scene {scene_label}")
            )
        elif SCENE_STAGE_RE.match(clean):
            markers.append((offset, current_act, current_act_kind, "Scene I"))
        offset += len(line)
    if not markers:
        start = first_act_start or 0
        end = _play_end(text, start)
        return [
            SceneChunk(
                "Act I" if first_act_start is None else current_act,
                ActKind.ACT,
                "Scene I",
                text[start:end],
                start,
                end,
            )
        ]
    chunks: list[SceneChunk] = []
    for index, (start, act_label, act_kind, scene_label) in enumerate(markers):
        end = (
            markers[index + 1][0]
            if index + 1 < len(markers)
            else _play_end(text, start)
        )
        body_start = start + len(text[start:].splitlines(keepends=True)[0])
        chunks.append(
            SceneChunk(
                act_label,
                act_kind,
                scene_label,
                text[body_start:end],
                start,
                end,
            )
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


def _cast_aliases(text: str) -> dict[str, str]:
    scene_start = re.search(r"(?im)^\s*(?:SCENE|SCÈNE|SZENE)\s*(?::|\s)", text)
    preamble = text[: scene_start.start()] if scene_start else ""
    aliases: dict[str, str] = {}
    cast_line = re.compile(
        r"^([A-ZÀ-ÖØ-Þ][A-ZÀ-ÖØ-Þ0-9 .,'’\-]{1,48}?)(?:\s*\(([^()]*)\)|,\s*.+)?$"
    )
    for raw_line in preamble.splitlines():
        match = cast_line.match(raw_line.strip())
        if not match:
            continue
        canonical = match.group(1).strip()
        aliases[_identity_key(canonical)] = canonical
        words = canonical.split()
        if len(words) > 1:
            aliases.setdefault(_identity_key(words[-1]), canonical)
        if match.group(2):
            aliases[_identity_key(match.group(2))] = canonical
    return aliases


def _canonical_entrance_display(display: str, aliases: dict[str, str]) -> str:
    normalized = display.strip(" _.,;:")
    normalized_key = _identity_key(normalized)
    for alias_key, canonical in sorted(aliases.items(), key=lambda item: -len(item[0])):
        if normalized_key.startswith(alias_key):
            return canonical
    return normalized


def _normalize_speaker_display(display: str) -> str:
    return DELIVERY_NOTE_RE.sub("", display).strip()


def _looks_like_speaker(line: str, display: str) -> bool:
    if line.endswith(":"):
        return True
    normalized = _normalize_speaker_display(display)
    if not normalized or re.search(r"[.!?;]$", normalized):
        return False
    if normalized == normalized.upper():
        return True
    words = re.findall(r"[A-Za-zÀ-ÿ]+", normalized)
    return len(words) > 1 and all(
        word[0].isupper() and word[1:] == word[1:].lower() for word in words
    )


def _qualified_base(display: str) -> str | None:
    match = QUALIFIED_SPEAKER_RE.match(display)
    return match.group("base").strip() if match else None


def parse_playtext(text: str, submission: PlaytextSubmission) -> AnalysisResult:
    chunks = _chunks(text)
    cast_aliases = _cast_aliases(text)
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
                kind=chunk.act_kind,
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
                display = _canonical_entrance_display(entrance.group(1), cast_aliases)
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
            speaker_prefix = SPEAKER_PREFIX_RE.match(line)
            speaker = speaker_prefix or SPEAKER_RE.match(line)
            if (
                speaker
                and not (
                    ACT_RE.match(line)
                    or SCENE_RE.match(line)
                    or SPECIAL_ACT_RE.match(line)
                )
                and _looks_like_speaker(line, speaker.group(1))
            ):
                display = _normalize_speaker_display(speaker.group(1))
                qualified_base = _qualified_base(display)
                source_key = _identity_key(qualified_base or display)
                canonical_display = cast_aliases.get(
                    source_key, qualified_base or display
                )
                kind = _classify(canonical_display)
                key = _identity_key(canonical_display) or f"unnamed-{scene.id}"
                character = by_key.get(key)
                if character is None:
                    character = CharacterOrSpeaker(
                        id=f"character-{len(characters) + 1:02d}",
                        display_name=(
                            canonical_display
                            if kind != CharacterKind.UNNAMED
                            else "Unnamed speaker"
                        ),
                        kind=kind,
                        first_appearance_scene_id=scene.id,
                    )
                    by_key[key] = character
                    characters.append(character)
                if qualified_base:
                    if character.ambiguity is None:
                        character.ambiguity = Ambiguity(
                            evidence="descriptive speaker qualifier was grouped with the base role",
                            alternatives=[],
                        )
                    if display not in character.ambiguity.alternatives:
                        character.ambiguity.alternatives.append(display)
                elif canonical_display != display:
                    if character.ambiguity is None:
                        character.ambiguity = Ambiguity(
                            evidence="source role label was grouped with the cast-list character",
                            alternatives=[],
                        )
                    if display not in character.ambiguity.alternatives:
                        character.ambiguity.alternatives.append(display)
                elif character.display_name != display and character.ambiguity is None:
                    character.ambiguity = Ambiguity(
                        evidence="formatting or naming variation",
                        alternatives=[display],
                    )
                current = character
                scene_presence.add((scene.id, character.id))
                if speaker_prefix and speaker_prefix.group(2).strip():
                    inline_text = speaker_prefix.group(2).strip()
                    if not (inline_text.startswith("(") and inline_text.endswith(")")):
                        appearance_counts[(scene.id, character.id)] = (
                            appearance_counts.get((scene.id, character.id), 0) + 1
                        )
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
