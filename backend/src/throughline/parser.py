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
    ParserNotice,
    PlaytextSubmission,
    Presence,
    Scene,
    SceneAppearance,
)
from .visualization import build_visualization

ACT_RE = re.compile(r"^\s*(ACT|ACTO|AKT)\s*[:.]?\s+(.+?)\s*:?[ \t]*$", re.I)
SCENE_RE = re.compile(
    r"^\s*(SCENE|SCÈNE|SZENE|CHAPTER)\s*[:.]?\s+(.+?)\s*:?[ \t]*$",
    re.I,
)
SCENE_STAGE_RE = re.compile(r"^\s*(?:SCENE|SCÈNE|SZENE)\s*:\s*", re.I)
NUMBERED_SCENE_RE = re.compile(r"^\s*(\d+)\s*[-–—]\s*(.+?)\s*$")
ROMAN_SCENE_RE = re.compile(r"^\s*([IVXLCDM]+)\.?\s*$")
SEPARATOR_SCENE_RE = re.compile(r"^\s*(?:-{3,}|_{3,}|={3,})\s*$")
SPECIAL_ACT_RE = re.compile(
    r"^\s*(?:THE\s+)?(PROLOGUE|EPILOGUE|ENTR['’]?ACTE|ENTRACTE|INTERLUDE)\.?\s*:?[ \t]*$",
    re.I,
)
SPEAKER_RE = re.compile(
    r"^\s*([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ0-9 .,'’\-]{1,48})"
    r"(?:\s*(?:\([^()]*\)|\[[^\[\]]*\]))?[.]?\s*:?[ \t]*$"
)
SPEAKER_PREFIX_RE = re.compile(
    r"^\s*([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ0-9 .,'’\-]{1,48})"
    r"(?:\s*(?:\([^()]*\)|\[[^\[\]]*\]))?\s*:\s*(.*)$"
)
BRACKET_SPEAKER_PREFIX_RE = re.compile(
    r"^\s*([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ0-9 .,'’\-]{1,48})" r"\s*\[[^\[\]]*\]\s*\.\s*(.*)$"
)
PLAY_END_RE = re.compile(
    r"^\s*\[?(?:END|THE END|END OF PLAY|THE END OF PLAY|END OF THE PLAY|END OF THE PROJECT GUTENBERG EBOOK.*|THE CURTAIN|BLACK\s+OUT.*END|BLACKOUT.*END)\.?\]?\.?\s*$|"
    r"^\s*(?:FINIS|CURTAIN|"
    r"PROJECT GUTENBERG(?: LICENSE)?|GUTENBERG LICENSE|"
    r"NOTES TO .+|"
    r"ADVERTISEMENTS?|OTHER PLAYS|ABOUT THE AUTHOR|"
    r"(?:EDITOR'?S?|AUTHOR'?S?) (?:NOTE|PREFACE|INTRODUCTION)|"
    r"NOTES?|ESSAY|COMMENTARY|APPENDIX|APPENDICES|LICENSE|LICENCE)\s*:?[ \t]*$",
    re.I,
)
PLAY_TITLE_RE = re.compile(
    r"(?im)^\s*[A-Z][A-Z0-9 &'’\-]{2,}\s*\n\s*by\s*(?:[A-Z].*)?$"
)
ENTER_RE = re.compile(
    r"^\s*(?:re-)?entr(?:y|ance)\s+of\s+(.+?)(?:[.,;:]|$)|"
    r"^\s*(?:re-)?enter(?:s)?\s+(.+?)(?:[.,;:]|$)",
    re.I,
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
PAGE_NUMBER_RE = re.compile(r"^\d+$")
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


def _play_start(text: str) -> int:
    matches = list(re.finditer(r"(?im)^\s*THE\s+PROLOGUE\.?\s*$", text))
    if matches:
        return matches[-1].start()
    dramatis = re.search(r"(?im)^\s*Dramatis Person[æa]e?\s*$", text)
    if dramatis:
        act_after_cast = re.search(r"(?im)^\s*ACT\s+(?:I|1)\b", text[dramatis.end() :])
        if act_after_cast:
            return dramatis.end() + act_after_cast.start()
    dramatic_start = list(re.finditer(r"(?im)^\s*\[The Scene shows\b", text))
    if dramatic_start:
        return dramatic_start[0].start()
    title_start = re.search(
        r"(?im)^\s*[A-Z][A-Z0-9 &'’\-]{2,}\s*$\n\s*(?:_|\[The Scene shows\b)",
        text,
    )
    if title_start:
        return title_start.start()
    act_candidates = list(re.finditer(r"(?im)^\s*ACT\s+I\s*$", text))
    for index, candidate in enumerate(act_candidates):
        next_act = (
            act_candidates[index + 1].start()
            if index + 1 < len(act_candidates)
            else candidate.end() + 3000
        )
        following = text[candidate.end() : next_act]
        if re.search(r"(?im)^\s*[A-Z][A-ZÀ-ÿ0-9 .,'’\-]{1,48}:\s*$", following):
            return candidate.start()
    return 0


def _heading(line: str, pattern: re.Pattern[str]) -> tuple[str, str] | None:
    match = pattern.match(line)
    return (match.group(1), match.group(2).strip()) if match else None


def _scene_label(prefix: str, value: str) -> str:
    identifier = re.match(r"(?:[IVXLCDM]+|\d+|[A-Z]+)", value, re.I)
    return f"{prefix.title()} {identifier.group(0) if identifier else value}".strip()


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
    act_markers: list[tuple[int, str, ActKind]] = []
    has_scene_marker = False
    for line in lines:
        clean = line.strip()
        act_heading = _heading(clean, ACT_RE)
        scene_heading = _heading(clean, SCENE_RE)
        numbered_scene = NUMBERED_SCENE_RE.match(clean)
        roman_scene = ROMAN_SCENE_RE.match(clean)
        if act_heading:
            if first_act_start is None:
                first_act_start = offset
            prefix, value = act_heading
            current_act = f"{prefix.title()} {value.rstrip(':').strip()}"
            current_act_kind = ActKind.ACT
            act_markers.append((offset, current_act, current_act_kind))
        special_act = _special_act(clean)
        is_late_prologue = bool(
            special_act
            and special_act[1] == ActKind.PROLOGUE
            and (first_act_start is not None or markers)
        )
        if special_act and not is_late_prologue:
            current_act, current_act_kind = special_act
            markers.append((offset, current_act, current_act_kind, current_act))
        is_stage_description = bool(
            scene_heading
            and scene_heading[0].upper() in {"SCENE", "SCÈNE", "SZENE"}
            and scene_heading[1].startswith("_")
        )
        if scene_heading and not is_stage_description:
            has_scene_marker = True
            prefix, value = scene_heading
            markers.append(
                (offset, current_act, current_act_kind, _scene_label(prefix, value))
            )
        elif numbered_scene:
            has_scene_marker = True
            markers.append(
                (
                    offset,
                    current_act,
                    current_act_kind,
                    f"Scene {numbered_scene.group(1)}",
                )
            )
        elif roman_scene:
            has_scene_marker = True
            markers.append(
                (
                    offset,
                    current_act,
                    current_act_kind,
                    f"Scene {roman_scene.group(1).upper()}",
                )
            )
        elif SEPARATOR_SCENE_RE.match(clean):
            has_scene_marker = True
            if not markers:
                markers.append(
                    (
                        first_act_start or 0,
                        current_act,
                        current_act_kind,
                        "Scene I",
                    )
                )
            markers.append(
                (
                    offset,
                    current_act,
                    current_act_kind,
                    f"Scene {_roman(len(markers) + 1)}",
                )
            )
        elif SCENE_STAGE_RE.match(clean):
            has_scene_marker = True
            markers.append((offset, current_act, current_act_kind, "Scene I"))
        offset += len(line)
    play_end = _play_end(text, 0)
    if not has_scene_marker and act_markers:
        markers = [
            (start, label, kind, "Scene I")
            for start, label, kind in act_markers
            if start < play_end
        ]
    markers = [marker for marker in markers if marker[0] < play_end]
    if not markers:
        start = first_act_start or 0
        end = play_end
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
        end = markers[index + 1][0] if index + 1 < len(markers) else play_end
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


def _roman(number: int) -> str:
    values = ((10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"))
    result = ""
    for value, symbol in values:
        count, number = divmod(number, value)
        result += symbol * count
    return result


def _has_play_evidence(text: str) -> bool:
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if (
            ACT_RE.match(line)
            or SCENE_RE.match(line)
            or SPECIAL_ACT_RE.match(line)
            or NUMBERED_SCENE_RE.match(line)
            or ROMAN_SCENE_RE.match(line)
            or SEPARATOR_SCENE_RE.match(line)
            or ENTER_RE.search(line)
        ):
            return True
        speaker = SPEAKER_PREFIX_RE.match(line) or SPEAKER_RE.match(line)
        if speaker and _looks_like_speaker(line, speaker.group(1), True):
            return True
    return False


def _tail_contains_play(text: str) -> bool:
    return any(
        ACT_RE.match(line.strip())
        or SCENE_RE.match(line.strip())
        or SPECIAL_ACT_RE.match(line.strip())
        or NUMBERED_SCENE_RE.match(line.strip())
        or ROMAN_SCENE_RE.match(line.strip())
        for line in text.splitlines()
    ) or bool(PLAY_TITLE_RE.search(text))


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
    cast_start = re.search(r"(?im)^\s*CAST OF CHARACTERS\s*$", preamble)
    if cast_start:
        preamble = preamble[cast_start.end() :]
        play_start = re.search(r"(?im)^\s*(?:ACT|ACTO|AKT)\s+", preamble)
        if play_start:
            preamble = preamble[: play_start.start()]
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
        shared_parts = _shared_speaker_parts(canonical)
        for part in shared_parts:
            aliases[_identity_key(part)] = part
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


def _looks_like_speaker(
    line: str, display: str, allow_terminal_period: bool = False
) -> bool:
    normalized = _normalize_speaker_display(display)
    if (
        normalized.endswith(".")
        and not allow_terminal_period
        and normalized != normalized.upper()
    ):
        return False
    if allow_terminal_period:
        normalized = normalized.rstrip(".")
    if not normalized or re.search(r"[!?;]$", normalized):
        return False
    if normalized == normalized.upper():
        return True
    words = re.findall(r"[A-Za-zÀ-ÿ]+", normalized)
    if ":" in line:
        stopwords = {
            "a",
            "an",
            "and",
            "as",
            "by",
            "for",
            "from",
            "in",
            "of",
            "the",
            "to",
        }
        return (
            len(words) <= 2
            and words
            and words[0].casefold() not in stopwords
            and all(word[0].isupper() for word in words)
        )
    return len(words) > 1 and all(
        word[0].isupper() and word[1:] == word[1:].lower() for word in words
    )


def _qualified_base(display: str) -> str | None:
    match = QUALIFIED_SPEAKER_RE.match(display)
    return match.group("base").strip() if match else None


def _shared_speaker_parts(display: str, require_uppercase: bool = True) -> list[str]:
    normalized = display.strip().rstrip(".").strip()
    parts = re.split(r"\s+(?:and|&)\s+", normalized, maxsplit=1, flags=re.I)
    if len(parts) != 2:
        return []
    if not all(re.match(r"^[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ .,'’\-]*$", part) for part in parts):
        return []
    if require_uppercase and not all(part == part.upper() for part in parts):
        return []
    return [part.strip() for part in parts]


def parse_playtext(text: str, submission: PlaytextSubmission) -> AnalysisResult:
    play_start = _play_start(text)
    playtext = text[play_start:]
    if not _has_play_evidence(playtext):
        raise ValueError("not playtext")
    chunks = _chunks(playtext)
    cast_aliases = _cast_aliases(playtext)
    unheaded_play = not any(
        ACT_RE.match(line.strip())
        or SCENE_RE.match(line.strip())
        or SPECIAL_ACT_RE.match(line.strip())
        or NUMBERED_SCENE_RE.match(line.strip())
        or ROMAN_SCENE_RE.match(line.strip())
        or SEPARATOR_SCENE_RE.match(line.strip())
        for line in playtext.splitlines()
    )
    play_end = _play_end(playtext, 0)
    notices: list[ParserNotice] = []
    if unheaded_play:
        notices.append(
            ParserNotice(
                code="UNCONVENTIONAL_STRUCTURE",
                message=(
                    "The source did not provide conventional act or scene markers; "
                    "the analysis uses one best-effort scene."
                ),
            )
        )
    if _tail_contains_play(playtext[play_end:]):
        notices.append(
            ParserNotice(
                code="MULTIPLE_PLAYS",
                message="Multiple plays were found; only the first play was analyzed.",
            )
        )
    monologue_mode = any(
        NUMBERED_SCENE_RE.match(line.strip()) for line in playtext.splitlines()
    )
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
            source_span=(chunk.start + play_start, chunk.end + play_start),
        )
        act.scenes.append(scene)
        scenes.append(scene)

    characters: list[CharacterOrSpeaker] = []
    by_key: dict[str, CharacterOrSpeaker] = {}
    appearance_counts: dict[tuple[str, str], int] = {}
    scene_presence: set[tuple[str, str]] = set()
    scene_confidence: dict[tuple[str, str], Confidence] = {}
    for scene, chunk in zip(scenes, chunks):
        current: list[CharacterOrSpeaker] = []
        saw_speaker = False
        for raw_line in chunk.text.splitlines():
            line = raw_line.strip()
            if not line or PAGE_NUMBER_RE.fullmatch(line):
                continue
            entrance = ENTER_RE.search(line)
            if entrance:
                entrance_display = entrance.group(1) or entrance.group(2) or ""
                display = _canonical_entrance_display(entrance_display, cast_aliases)
                entrance_displays = _shared_speaker_parts(
                    display, require_uppercase=False
                ) or [display]
                for entrance_display in entrance_displays:
                    key = _identity_key(entrance_display)
                    if key and key not in by_key:
                        character = CharacterOrSpeaker(
                            id=f"character-{len(characters) + 1:02d}",
                            display_name=entrance_display,
                            kind=CharacterKind.SILENT,
                            first_appearance_scene_id=scene.id,
                        )
                        by_key[key] = character
                        characters.append(character)
                    if key:
                        scene_presence.add((scene.id, by_key[key].id))
                continue
            speaker_prefix = (
                None
                if monologue_mode
                else SPEAKER_PREFIX_RE.match(line)
                or BRACKET_SPEAKER_PREFIX_RE.match(line)
            )
            speaker = (
                None if monologue_mode else speaker_prefix or SPEAKER_RE.match(line)
            )
            if (
                speaker
                and not (
                    ACT_RE.match(line)
                    or SCENE_RE.match(line)
                    or SPECIAL_ACT_RE.match(line)
                )
                and (
                    _looks_like_speaker(
                        line, speaker.group(1), allow_terminal_period=unheaded_play
                    )
                    or _shared_speaker_parts(speaker.group(1))
                )
            ):
                display = _normalize_speaker_display(speaker.group(1))
                if unheaded_play:
                    display = display.rstrip(".")
                shared_parts = _shared_speaker_parts(display)
                speaker_displays = shared_parts or [display]
                current = []
                for speaker_display in speaker_displays:
                    qualified_base = _qualified_base(speaker_display)
                    source_key = _identity_key(qualified_base or speaker_display)
                    canonical_display = cast_aliases.get(
                        source_key, qualified_base or speaker_display
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
                        if speaker_display not in character.ambiguity.alternatives:
                            character.ambiguity.alternatives.append(speaker_display)
                    elif canonical_display != speaker_display:
                        if character.ambiguity is None:
                            character.ambiguity = Ambiguity(
                                evidence="source role label was grouped with the cast-list character",
                                alternatives=[],
                            )
                        if speaker_display not in character.ambiguity.alternatives:
                            character.ambiguity.alternatives.append(speaker_display)
                    current.append(character)
                saw_speaker = True
                for character in current:
                    scene_presence.add((scene.id, character.id))
                if speaker_prefix and speaker_prefix.group(2).strip():
                    inline_text = speaker_prefix.group(2).strip()
                    if not (inline_text.startswith("(") and inline_text.endswith(")")):
                        for character in current:
                            appearance_counts[(scene.id, character.id)] = (
                                appearance_counts.get((scene.id, character.id), 0) + 1
                            )
                continue
            if current and not (line.startswith("(") and line.endswith(")")):
                for character in current:
                    appearance_counts[(scene.id, character.id)] = (
                        appearance_counts.get((scene.id, character.id), 0) + 1
                    )
            elif line.startswith("(") and line.endswith(")"):
                for character in current:
                    scene_confidence[(scene.id, character.id)] = Confidence.AMBIGUOUS

        if not saw_speaker and len(characters) == 1:
            character = characters[0]
            speech_lines = [
                line.strip()
                for line in chunk.text.splitlines()
                if line.strip()
                and not PAGE_NUMBER_RE.fullmatch(line.strip())
                and not line.strip().startswith(("(", "["))
            ]
            if speech_lines:
                scene_presence.add((scene.id, character.id))
                appearance_counts[(scene.id, character.id)] = len(speech_lines)

        if not characters:
            cast_names = list(
                dict.fromkeys(
                    name
                    for name in cast_aliases.values()
                    if not ACT_RE.match(name) and not SCENE_RE.match(name)
                )
            )
            if len(cast_names) == 1:
                character = CharacterOrSpeaker(
                    id="character-01",
                    display_name=cast_names[0],
                    kind=_classify(cast_names[0]),
                    first_appearance_scene_id=scenes[0].id,
                )
                characters.append(character)
                for scene in scenes:
                    scene_presence.add((scene.id, character.id))
                    speech_lines = [
                        line.strip()
                        for line in next(
                            chunk.text.splitlines() for chunk in chunks if chunk.text
                        )
                        if line.strip() and not line.strip().startswith(("(", "*"))
                    ]
                    appearance_counts[(scene.id, character.id)] = len(speech_lines)

    if not characters and scenes:
        character = CharacterOrSpeaker(
            id="character-01",
            display_name="Unnamed speaker",
            kind=CharacterKind.UNNAMED,
            first_appearance_scene_id=scenes[0].id,
        )
        characters.append(character)
        for scene, chunk in zip(scenes, chunks):
            speech_lines = [
                line.strip()
                for line in chunk.text.splitlines()
                if line.strip()
                and not PAGE_NUMBER_RE.fullmatch(line.strip())
                and not line.strip().startswith(("(", "[", "<<"))
            ]
            if speech_lines:
                scene_presence.add((scene.id, character.id))
                appearance_counts[(scene.id, character.id)] = len(speech_lines)

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
        notices=notices,
        ordering=ordering,
        visualization=build_visualization(scene_ids, character_ids, appearances),
    )
    return result
