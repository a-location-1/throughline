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

ACT_RE = re.compile(
    r"^\s*(ACT|ACTO|AKT)\s*[:.]?\s+([IVXLCDM]+|\d+|"
    r"ONE|TWO|THREE|FOUR|FIVE|SIX|SEVEN|EIGHT|NINE|TEN)"
    r"\s*:?[ \t]*$",
    re.I,
)
ORDINAL_ACT_RE = re.compile(
    r"^\s*(FIRST|SECOND|THIRD|FOURTH|FIFTH|SIXTH|SEVENTH|EIGHTH|NINTH|TENTH)\s+ACT\s*:?[ \t]*$",
    re.I,
)
SCENE_RE = re.compile(
    r"^\s*(SCENE|SCÈNE|SZENE|CHAPTER)\s*(?::\s+|\s+)(.+?)\s*:?[ \t]*$",
    re.I,
)
BARE_SCENE_RE = re.compile(r"^\s*(SCENE|SCÈNE|SZENE)\s*:?[ \t]*$", re.I)
ACT_DROP_RE = re.compile(r"^\s*ACT\s+DROP\s*:?[ \t]*$", re.I)
SCENE_DASH_RE = re.compile(r"^\s*(?:SCENE|SCÈNE|SZENE)\s*[—–-]\s*", re.I)
SCENE_STAGE_RE = re.compile(r"^\s*(?:SCENE|SCÈNE|SZENE)\s*:\s*", re.I)
PRODUCTION_NOTES_RE = re.compile(r"^\s*PRODUCTION NOTES\s*:?[ \t]*$", re.I)
FIRST_SCENE_RE = re.compile(
    r"^\s*(?:SCENE|SCÈNE|SZENE)\s+(?:I|1)\b", re.I
)
NUMBERED_SCENE_RE = re.compile(r"^\s*(\d+)\s*[-–—]\s*(.+?)\s*$")
ROMAN_SCENE_RE = re.compile(r"^\s*([IVX]{1,8})\.?\s*$")
SECTION_RE = re.compile(r"^\s*([IVXLCDM]{1,8})\.\s+(.{2,80}?)\s*$", re.I)
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
PERIOD_SPEAKER_PREFIX_RE = re.compile(
    r"^\s*([A-ZÀ-Ý][A-ZÀ-Ý0-9 .,'’\-]{1,48})\.\s+(.+)$"
)
BRACKET_SPEAKER_PREFIX_RE = re.compile(
    r"^\s*([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ0-9 .,'’\-]{1,48})" r"\s*\[[^\[\]]*\]\s*\.\s*(.*)$"
)
DASH_SPEAKER_PREFIX_RE = re.compile(
    r"^\s*([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ0-9 .,'’\-]{1,48})\s*[—–]\s*(.*)$"
)
PLAY_END_RE = re.compile(
    r"^\s*\[?(?:END|THE END|END OF PLAY|THE END OF PLAY|END OF THE PLAY|END OF THE PROJECT GUTENBERG EBOOK.*|THE CURTAIN|BLACK\s+OUT.*END|BLACKOUT.*END)\.?\]?\.?\s*$|"
    r"^\s*\*+\s*END OF THE PROJECT GUTENBERG EBOOK.*\*+\s*$|"
    r"^\s*(?:FINIS|CURTAIN|"
    r"PROJECT GUTENBERG(?: LICENSE)?|GUTENBERG LICENSE|"
    r"NOTES TO .+|"
    r"ADVERTISEMENTS?|OTHER PLAYS|ABOUT THE AUTHOR|"
    r"(?:EDITOR'?S?|AUTHOR'?S?) (?:NOTE|PREFACE|INTRODUCTION)|"
    r"NOTES?|ESSAY|COMMENTARY|APPENDIX|APPENDICES|LICENSE|LICENCE)\s*:?[ \t]*$",
    re.I,
)
PLAY_TITLE_RE = re.compile(
    r"(?m)^\s*[A-Z][A-Z0-9 &'’\-]{2,}\s*\n\s*(?i:by)\s*(?:[A-Z].*)?$"
)
ENTER_RE = re.compile(
    r"^\s*\(?\s*(?:re-)?entr(?:y|ance)\s+of\s+(.+?)(?:[.;:]|\)?$)|"
    r"^\s*\(?\s*(?:re-)?enter(?:s)?\s+(.+?)(?:[.;:]|\)?$)",
    re.I,
)
STAGE_LABEL_RE = re.compile(r"^\s*MUSIC\s*:", re.I)
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
VOICE_OF_RE = re.compile(r"^\s*VOICE\s+OF\s+(.+?)\s*$", re.I)


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
    production_notes = list(
        re.finditer(r"(?im)^\s*PRODUCTION NOTES\s*:?[ \t]*$", text)
    )
    if production_notes:
        first_scene = re.search(
            r"(?im)^\s*(?:SCENE|SCÈNE|SZENE)\s+(?:I|1)\b.*$",
            text[production_notes[-1].end() :],
        )
        if first_scene:
            return production_notes[-1].end() + first_scene.start()
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
        if re.search(
            r"(?im)^\s*[A-Z][A-ZÀ-ÿ0-9 .,'’\-]{1,48}:\s*$", following
        ):
            return candidate.start()
    return 0


def _heading(line: str, pattern: re.Pattern[str]) -> tuple[str, str] | None:
    match = pattern.match(line)
    return (match.group(1), match.group(2).strip()) if match else None


def _act_heading(line: str) -> tuple[str, str] | None:
    heading = _heading(line, ACT_RE)
    if heading:
        return heading
    ordinal = ORDINAL_ACT_RE.match(line)
    if not ordinal:
        return None
    values = {
        "FIRST": "I",
        "SECOND": "II",
        "THIRD": "III",
        "FOURTH": "IV",
        "FIFTH": "V",
        "SIXTH": "VI",
        "SEVENTH": "VII",
        "EIGHTH": "VIII",
        "NINTH": "IX",
        "TENTH": "X",
    }
    return "ACT", values[ordinal.group(1).upper()]


def _scene_heading(line: str) -> tuple[str, str] | None:
    heading = _heading(line, SCENE_RE)
    if heading:
        return heading
    return ("SCENE", "I") if BARE_SCENE_RE.match(line) else None


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
    lines = text.splitlines(keepends=True)
    for index, line in enumerate(lines):
        if offset > minimum and PLAY_END_RE.match(line.strip()):
            if (
                line.strip().casefold() == "curtain"
                and any(
                    _scene_heading(candidate.strip())
                    or _act_heading(candidate.strip())
                    for candidate in lines[index + 1 :]
                )
            ):
                offset += len(line)
                continue
            return offset
        offset += len(line)
    return len(text)


def _rejects_noninitial_excerpt(text: str) -> bool:
    first_act = re.search(r"(?im)^\s*(?:ACT|ACTO|AKT)\s+([IVXLCDM]+|\d+)\b", text)
    if first_act and first_act.group(1).upper() not in {"I", "1"}:
        return True
    first_scene = re.search(
        r"(?im)^\s*(?:SCENE|SCÈNE|SZENE)\s*[:.]?\s+([IVXLCDM]+|\d+)\b",
        text,
    )
    if first_scene and first_scene.group(1).upper() not in {"I", "1"}:
        return True
    return False


def _chunks(text: str) -> list[SceneChunk]:
    lines = text.splitlines(keepends=True)
    markers: list[tuple[int, str, ActKind, str]] = []
    offset = 0
    current_act = "Act I"
    current_act_kind = ActKind.ACT
    first_act_start: int | None = None
    act_markers: list[tuple[int, str, ActKind]] = []
    has_scene_marker = False
    for line_index, line in enumerate(lines):
        clean = line.strip()
        act_heading = _act_heading(clean)
        if act_heading and act_heading[1][:1].islower():
            act_heading = None
        previous_clean = lines[line_index - 1].strip() if line_index else ""
        next_clean = (
            lines[line_index + 1].strip() if line_index + 1 < len(lines) else ""
        )
        if (
            act_heading
            and markers
            and previous_clean
            and not re.match(r"^(?:CURTAIN|THE END)\.?\s*$", previous_clean, re.I)
            and not _scene_heading(next_clean)
        ):
            act_heading = None
        scene_heading = _scene_heading(clean)
        numbered_scene = NUMBERED_SCENE_RE.match(clean)
        section_heading = SECTION_RE.match(clean)
        roman_scene = ROMAN_SCENE_RE.match(clean)
        if roman_scene and markers and not re.match(
            r"^(?:[A-ZÀ-Ý][A-ZÀ-Ý0-9 .,'’\-]{1,48})\.?(?:\s|$)",
            next_clean,
        ):
            roman_scene = None
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
        elif section_heading:
            has_scene_marker = True
            markers.append(
                (
                    offset,
                    current_act,
                    current_act_kind,
                    f"Section {section_heading.group(1).upper()}",
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
    if first_act_start is not None and any(
        marker[0] < first_act_start and marker[3].startswith("Scene ")
        for marker in markers
    ):
        markers = [marker for marker in markers if marker[0] >= first_act_start]
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
    while len(chunks) > 1 and not chunks[0].text.strip():
        chunks.pop(0)
    return chunks


def _roman(number: int) -> str:
    values = ((10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"))
    result = ""
    for value, symbol in values:
        count, number = divmod(number, value)
        result += symbol * count
    return result


def _has_play_evidence(text: str) -> bool:
    known_speakers = _known_speakers(text)
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if (
            _act_heading(line)
            or _scene_heading(line)
            or SPECIAL_ACT_RE.match(line)
            or NUMBERED_SCENE_RE.match(line)
            or ROMAN_SCENE_RE.match(line)
            or SEPARATOR_SCENE_RE.match(line)
            or ENTER_RE.search(line)
        ):
            return True
        speaker = SPEAKER_PREFIX_RE.match(line) or SPEAKER_RE.match(line)
        if (
            speaker
            and (
                ":" in line
                or line.rstrip().endswith((".", "!", "?"))
                or speaker.group(1).strip() == speaker.group(1).strip().upper()
            )
            and _looks_like_speaker(line, speaker.group(1), True, known_speakers)
        ):
            return True
    return False


def _tail_contains_play(text: str) -> bool:
    return any(
        _act_heading(line.strip())
        or _scene_heading(line.strip())
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
    dramatis_header = re.search(
        r"(?im)^\s*DRAMATIS PERSON[ÆA]E?\s*$", text
    )
    scene_start = re.search(r"(?im)^\s*(?:SCENE|SCÈNE|SZENE)\s*(?::|\s)", text)
    scene_start_offset = scene_start.start() if scene_start else len(text)
    if dramatis_header:
        scene_after_cast = re.search(
            r"(?im)^\s*(?:SCENE|SCÈNE|SZENE)\s*(?::|\s)",
            text[dramatis_header.end() :],
        )
        if scene_after_cast:
            scene_start_offset = dramatis_header.end() + scene_after_cast.start()
    preamble = text[:scene_start_offset]
    cast_start = re.search(r"(?im)^\s*CAST OF CHARACTERS\s*$", preamble)
    if cast_start:
        preamble = preamble[cast_start.end() :]
        play_start = re.search(r"(?im)^\s*(?:ACT|ACTO|AKT)\s+", preamble)
        if play_start:
            preamble = preamble[: play_start.start()]
    aliases: dict[str, str] = {}
    characters_start = re.search(r"(?im)^\s*CHARACTERS\s*$", preamble)
    if characters_start:
        characters_section = preamble[characters_start.end() :]
        act_start = re.search(r"(?im)^\s*(?:ACT|ACTO|AKT)\s+", characters_section)
        if act_start:
            characters_section = characters_section[: act_start.start()]
        character_line = re.compile(
            r"^([A-ZÀ-ÖØ-Þ][A-ZÀ-ÖØ-Þ0-9 .,'’\-]*?)"
            r"(?:\s*\(([^()]*)\))?\.?\s*$"
        )
        for raw_line in characters_section.splitlines():
            match = character_line.match(raw_line.strip())
            if not match:
                continue
            canonical = match.group(1).strip()
            aliases[_identity_key(canonical)] = canonical
            words = canonical.split()
            if len(words) > 1:
                aliases.setdefault(_identity_key(words[0]), canonical)
                aliases.setdefault(_identity_key(" ".join(words[:2])), canonical)
                aliases.setdefault(_identity_key(words[-1]), canonical)
                aliases.setdefault(_identity_key(" ".join(words[-2:])), canonical)
                aliases.setdefault(
                    _identity_key(f"{words[0]} {words[-1]}"), canonical
                )
            if match.group(2):
                aliases[_identity_key(match.group(2))] = canonical
    dramatis_start = re.search(r"(?im)^\s*DRAMATIS PERSON[ÆA]E?\s*$", preamble)
    if dramatis_start:
        dramatis_section = preamble[dramatis_start.end() :]
        act_start = re.search(r"(?im)^\s*(?:ACT|ACTO|AKT)\s+", dramatis_section)
        if act_start:
            dramatis_section = dramatis_section[: act_start.start()]
        for raw_line in dramatis_section.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if re.match(r"(?i)players(?:\s|$)", line):
                canonical = "PLAYERS"
            elif re.match(r"(?i)two\s+clowns(?:\s|,|$)", line):
                canonical = "TWO CLOWNS"
            else:
                match = re.match(
                    r"(?i)(?:the\s+)?([A-ZÀ-ÖØ-Þ][A-ZÀ-ÖØ-Þ'’\-]*)\s*(?:,|$)",
                    line,
                )
                if not match:
                    match = re.match(
                        r"\s*([A-ZÀ-ÿ][A-Za-zÀ-ÿ'’\-]+)\s{2,}", raw_line
                    )
                if not match:
                    continue
                canonical = match.group(1).strip()
            aliases[_identity_key(canonical)] = canonical
            if len(canonical) > 3:
                aliases.setdefault(_identity_key(canonical[:3]), canonical)
    cast_line = re.compile(
        r"^([A-ZÀ-ÖØ-Þ][A-ZÀ-ÖØ-Þ0-9 .,'’\-]{1,48}?)(?:\s*\(([^()]*)\)|,\s*.+)?$"
    )
    for raw_line in preamble.splitlines():
        stripped_line = raw_line.strip()
        if _act_heading(stripped_line) or _scene_heading(stripped_line):
            continue
        match = cast_line.match(stripped_line)
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


def _known_speakers(text: str) -> set[str]:
    return set(_inferred_speaker_aliases(text))


def _canonical_entrance_display(display: str, aliases: dict[str, str]) -> str:
    normalized = display.strip(" _.,;:")
    normalized_key = _identity_key(normalized)
    for alias_key, canonical in sorted(aliases.items(), key=lambda item: -len(item[0])):
        if normalized_key == alias_key or (
            re.search(r"\bking\s+of\s+denmark$", normalized, re.I)
            and normalized_key.startswith(alias_key)
        ):
            return canonical
        if re.match(
            rf"^{re.escape(canonical)}\s+from\b",
            normalized,
            re.I,
        ) or re.match(
            rf"^{re.escape(canonical)}\s+(?:at|in|on|off)\b",
            normalized,
            re.I,
        ) or re.match(
            rf"^{re.escape(alias_key)}\s+(?:from|at|in|on|off)\b",
            normalized,
            re.I,
        ):
            return canonical
    for alias_key, canonical in sorted(aliases.items(), key=lambda item: -len(item[0])):
        if (
            len(alias_key) >= 4
            and not re.match(r"(?:his|her)\s+", normalized, re.I)
            and re.search(
            rf"(?<![A-Za-zÀ-ÿ]){re.escape(canonical)}(?![A-Za-zÀ-ÿ])",
            normalized,
            re.I,
            )
        ):
            return canonical
    return normalized


def _entrance_displays(display: str, aliases: dict[str, str]) -> list[str]:
    normalized = display.strip(" _.,;:")
    if re.fullmatch(r"forces\s+marching", normalized, re.I):
        return []
    if re.fullmatch(
        r"(?:a|an|the|some|others|another|three\s+or\s+four)(?:\s+of\s+the)?",
        normalized,
        re.I,
    ):
        return []
    if _identity_key(normalized) in {"withdrum", "colours", "colors"}:
        return []

    def resolve_part(part: str) -> list[str]:
        part = part.strip(" _.,;:")
        if not part or re.fullmatch(r"&c", part, re.I):
            return []
        if re.fullmatch(r"(?:a|an|the|some|others|another)", part, re.I):
            return []
        if re.fullmatch(r"prince\s+escalus", part, re.I):
            return [aliases.get("prince", "PRINCE")]
        exact_alias = aliases.get(_identity_key(part))
        if exact_alias:
            return [exact_alias]
        expanded = _expanded_role_displays(part, strip_descriptors=True)
        if expanded and not part.casefold().endswith("monument"):
            return expanded
        canonical = _canonical_entrance_display(part, aliases)
        return [] if canonical.casefold().endswith("monument") else [canonical]

    if _identity_key(normalized) not in {"twoclowns", "players"}:
        normalized_key = _identity_key(normalized)
        for alias_key, canonical in sorted(
            aliases.items(), key=lambda item: -len(item[0])
        ):
            if _identity_key(canonical) == "twoclowns":
                continue
            if normalized_key == alias_key or (
                re.search(r"\bking\s+of\s+denmark$", normalized, re.I)
                and normalized_key.startswith(alias_key)
            ):
                return [canonical]
    if "," in normalized:
        parts = [
            re.sub(r"^(?:with|and)\s+", "", part.strip(" _.,;:"), flags=re.I)
            for part in re.split(r"\s*(?:,|and)\s*", normalized, flags=re.I)
            if part.strip(" _.,;:") and not re.fullmatch(r"&c", part.strip(), re.I)
            and not re.fullmatch(
                r"(?:a|an|the|some|others|another)", part.strip(), re.I
            )
        ]
        resolved_parts = [
            resolved
            for part in parts
            for resolved in resolve_part(part)
        ]
        if parts and all(
            resolve_part(part)
            or re.match(r"^[A-ZÀ-Ý]", part)
            for part in parts
        ):
            return list(dict.fromkeys(resolved_parts))
    parts = re.split(r"\s+and\s+", normalized, maxsplit=1, flags=re.I)
    if len(parts) == 2:
        result: list[str] = []
        for part in parts:
            part_expanded = _expanded_role_displays(part, strip_descriptors=True)
            if part_expanded:
                result.extend(part_expanded)
                continue
            if _identity_key(part) in {"withdrum", "colours", "colors"}:
                continue
            if re.fullmatch(r"forces\s+marching", part, re.I):
                continue
            exact_alias = aliases.get(_identity_key(part.strip(" .")))
            if exact_alias:
                result.append(exact_alias)
                continue
            canonical = _canonical_entrance_display(part, aliases)
            if canonical != part:
                result.append(canonical)
            elif (
                part[:1].isupper()
                or part.casefold() in {"attendants"}
                or re.match(r"(?:his|her)\s+", part, re.I)
            ):
                result.append(part)
        if result:
            return list(dict.fromkeys(result))
    expanded = _expanded_role_displays(normalized, strip_descriptors=True)
    if expanded:
        if normalized.casefold().endswith("monument"):
            return []
        return expanded
    matches = list(
        dict.fromkeys(
            canonical
            for alias_key, canonical in aliases.items()
            if _identity_key(normalized) == alias_key
        )
    )
    if matches:
        return matches
    canonical = _canonical_entrance_display(normalized, aliases)
    return _shared_speaker_parts(canonical, require_uppercase=False) or [canonical]


def _normalize_speaker_display(display: str) -> str:
    normalized = DELIVERY_NOTE_RE.sub("", display).strip()
    voice_of = VOICE_OF_RE.match(normalized)
    return voice_of.group(1).strip() if voice_of else normalized


def _expanded_role_displays(
    display: str, strip_descriptors: bool = False
) -> list[str]:
    normalized = _normalize_speaker_display(display).strip(" _.,;:")
    key = _identity_key(normalized)
    if key in {"withdrum", "colours", "colors"} or normalized.casefold().startswith(
        "with drum"
    ):
        return []
    if re.fullmatch(r"(?:forces\s+)?marching", normalized, re.I):
        return []
    if re.fullmatch(r"(?:two|2)\s+clowns?(?:\s+with\b.*)?", normalized, re.I):
        return ["FIRST CLOWN", "SECOND CLOWN"]
    if re.fullmatch(
        r"(?:four\s+or\s+five|certain|some|the)\s+players?", normalized, re.I
    ):
        return ["PLAYERS"]
    if key in {"bothmurderers", "murderers"}:
        return ["FIRST MURDERER", "SECOND MURDERER", "THIRD MURDERER"]
    if key == "murderer":
        return ["FIRST MURDERER"]
    if re.fullmatch(r"(?:three|3)\s+murderers?", normalized, re.I):
        return ["FIRST MURDERER", "SECOND MURDERER", "THIRD MURDERER"]
    if re.fullmatch(r"(?:servant\s+with\s+)?(?:two|2)\s+murderers?", normalized, re.I):
        return ["SERVANT", "FIRST MURDERER", "SECOND MURDERER"]
    if re.fullmatch(r"first\s+murderer(?:\s+to\s+the\s+door)?", normalized, re.I):
        return ["FIRST MURDERER"]
    if re.fullmatch(r"(?:a\s+)?doctor(?:\s+of\s+physic)?", normalized, re.I):
        return ["DOCTOR"]
    if re.fullmatch(r"(?:a\s+)?waiting[- ]gentlewoman", normalized, re.I):
        return ["GENTLEWOMAN"]
    if re.fullmatch(r"(?:an?\s+)?old\s+man", normalized, re.I):
        return ["OLD MAN"]
    if re.fullmatch(r"(?:a\s+)?porter", normalized, re.I):
        return ["PORTER"]
    if re.fullmatch(r"lady\s+macduff\s+her\s+son", normalized, re.I):
        return ["LADY MACDUFF", "SON"]
    if not strip_descriptors:
        return []
    base = re.sub(
        r"^(?:(?:an?|the|some|others?|another|certain|several|many)\s+)+"
        r"(?:of\s+the\s+)?",
        "",
        normalized,
        flags=re.I,
    )
    base = re.split(
        r"\s+(?:with|attending|to|of)\s+", base, maxsplit=1, flags=re.I
    )[0].strip()
    if base != normalized and re.fullmatch(
        r"[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ .,'’\-]*", base
    ):
        return [base.upper()]
    return []


def _speaker_displays(
    display: str, aliases: dict[str, str] | None = None
) -> list[str]:
    normalized = _normalize_speaker_display(display).strip(" .,")
    expanded = _expanded_role_displays(normalized)
    if expanded:
        return expanded
    shared_parts = _shared_speaker_parts(normalized)
    if shared_parts:
        return shared_parts
    if "," in normalized:
        parts = [part.strip(" .,") for part in normalized.split(",")]
        known_parts = aliases and all(
            _identity_key(part) in aliases for part in parts if part
        )
        if len(parts) > 1 and all(parts) and (
            normalized == normalized.upper() or known_parts
        ):
            return parts
    return [normalized]


def _character_display(display: str) -> str:
    normalized = display.strip(" .,:;")
    return normalized.upper()


def _looks_like_speaker(
    line: str,
    display: str,
    allow_terminal_period: bool = False,
    known_speakers: set[str] | None = None,
) -> bool:
    normalized = _normalize_speaker_display(display)
    if known_speakers and _identity_key(normalized) in known_speakers:
        return True
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


def _inferred_speaker_aliases(text: str) -> dict[str, str]:
    labels: list[str] = []
    for line in text.splitlines():
        match = SPEAKER_PREFIX_RE.match(line.strip())
        if not match or not match.group(2).strip():
            continue
        display = _normalize_speaker_display(match.group(1))
        words = re.findall(r"[A-Za-zÀ-ÿ]+", display)
        if 1 <= len(words) <= 3:
            labels.append(display)

    counts: dict[str, int] = {}
    for label in labels:
        key = _identity_key(label)
        counts[key] = counts.get(key, 0) + 1

    aliases: dict[str, str] = {}
    full_names = {
        _identity_key(label): label.title()
        for label in labels
        if len(re.findall(r"[A-Za-zÀ-ÿ]+", label)) >= 2
    }
    for key, label in full_names.items():
        initials = "".join(word[0] for word in re.findall(r"[A-Za-zÀ-ÿ]+", label))
        short_keys = {
            candidate
            for candidate, count in counts.items()
            if count > 1 and candidate == initials.casefold()
        }
        for short_key in short_keys:
            aliases[key] = label
            aliases[short_key] = label
    return aliases


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


def _is_inline_colon_label(
    line: str,
    display: str,
    current: list[CharacterOrSpeaker],
    by_key: dict[str, CharacterOrSpeaker],
    cast_aliases: dict[str, str],
) -> bool:
    if ":" not in line or STAGE_LABEL_RE.match(line):
        return False
    inline_text = line.split(":", 1)[1].strip()
    if not current and not inline_text:
        return False
    key = _identity_key(_normalize_speaker_display(display))
    if key in by_key or key in cast_aliases:
        return False
    words = re.findall(r"[A-Za-zÀ-ÿ]+", display)
    return bool(words) and any(word != word.upper() for word in words)


def _is_inline_abbreviation(
    line: str, display: str, current: list[CharacterOrSpeaker]
) -> bool:
    normalized = line.strip()
    return bool(
        current
        and         re.fullmatch(r"[A-Z]{2,4}\.", normalized)
        and not re.search(r"[EIOU]", normalized)
    )


def _is_unrecognized_midline_label(
    line: str,
    display: str,
    current: list[CharacterOrSpeaker],
    aliases: dict[str, str],
) -> bool:
    if not current or ":" in line or display == display.upper():
        return False
    if "," in display:
        parts = [part.strip(" .,") for part in display.split(",")]
        if all(_identity_key(part) in aliases for part in parts if part):
            return False
    key = _identity_key(_normalize_speaker_display(display))
    if key in aliases:
        return False
    if display.casefold().startswith(("to ", "towards ")):
        return True
    words = re.findall(r"[A-Za-zÀ-ÿ]+", display)
    if len(words) >= 3:
        return False
    return not words or words[0].casefold() not in {
        "captain",
        "doctor",
        "father",
        "king",
        "lady",
        "lord",
        "miss",
        "mr",
        "mrs",
        "prince",
        "queen",
        "sir",
    }


def parse_playtext(text: str, submission: PlaytextSubmission) -> AnalysisResult:
    play_start = _play_start(text)
    playtext = text[play_start:]
    if _rejects_noninitial_excerpt(playtext):
        raise ValueError("non-initial excerpt")
    if not _has_play_evidence(playtext):
        raise ValueError("not playtext")
    chunks = _chunks(playtext)
    inferred_speaker_aliases = _inferred_speaker_aliases(playtext)
    cast_source = (
        text
        if re.search(
            r"(?im)^\s*(?:CHARACTERS|DRAMATIS PERSON[ÆA]E?)\s*$", text
        )
        and re.match(r"(?im)^\s*ACT\s+(?:I|1)\b", playtext)
        else playtext
    )
    cast_aliases = _cast_aliases(cast_source)
    if re.search(
        r"(?im)^\s*[A-Z][A-Za-zÀ-ÿ'’\-]+\s{2,}",
        text[:play_start],
    ) and not re.search(r"(?im)^\s*THE PROLOGUE\.?\s*$", text[:play_start]):
        cast_aliases.update(_cast_aliases(text))
    speaker_aliases = {**inferred_speaker_aliases, **cast_aliases}
    unheaded_play = not any(
        _act_heading(line.strip())
        or _scene_heading(line.strip())
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
        last_multi_speaker_displays: list[str] = []
        saw_speaker = False
        in_stage_direction = False
        for raw_line in chunk.text.splitlines():
            line = raw_line.strip()
            if not line or PAGE_NUMBER_RE.fullmatch(line):
                continue
            if ACT_DROP_RE.match(line):
                continue
            if line.startswith("["):
                in_stage_direction = True
            if in_stage_direction:
                if line.endswith("]"):
                    in_stage_direction = False
                continue
            entrance = ENTER_RE.search(line)
            if entrance:
                entrance_display = entrance.group(1) or entrance.group(2) or ""
                entrance_displays = _entrance_displays(entrance_display, cast_aliases)
                for entrance_display in entrance_displays:
                    key = _identity_key(entrance_display)
                    if key and key not in by_key:
                        character = CharacterOrSpeaker(
                            id=f"character-{len(characters) + 1:02d}",
                            display_name=_character_display(entrance_display),
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
                or DASH_SPEAKER_PREFIX_RE.match(line)
            )
            if speaker_prefix is None and not monologue_mode:
                period_prefix = PERIOD_SPEAKER_PREFIX_RE.match(line)
                if period_prefix:
                    period_key = _identity_key(period_prefix.group(1))
                    remainder = period_prefix.group(2).lstrip()
                    if (
                        period_key in cast_aliases
                        and not remainder.startswith(("_", "("))
                    ):
                        speaker_prefix = period_prefix
            speaker = (
                None if monologue_mode else speaker_prefix or SPEAKER_RE.match(line)
            )
            if STAGE_LABEL_RE.match(line) or SCENE_DASH_RE.match(line):
                speaker = None
                speaker_prefix = None
            if _is_inline_colon_label(
                line,
                speaker.group(1) if speaker else "",
                current,
                by_key,
                speaker_aliases,
            ) or _is_inline_abbreviation(
                line, speaker.group(1) if speaker else "", current
            ) or _is_unrecognized_midline_label(
                line,
                speaker.group(1) if speaker else "",
                current,
                speaker_aliases,
            ):
                speaker = None
                speaker_prefix = None
            if (
                speaker
                and not (
                    _act_heading(line)
                    or _scene_heading(line)
                    or SPECIAL_ACT_RE.match(line)
                )
                and (
                    _looks_like_speaker(
                    line,
                    speaker.group(1),
                    allow_terminal_period=unheaded_play,
                    known_speakers=set(inferred_speaker_aliases),
                    )
                    or _shared_speaker_parts(speaker.group(1))
                )
            ):
                display = _normalize_speaker_display(speaker.group(1))
                if (
                    _identity_key(display) == "both"
                    and last_multi_speaker_displays
                ):
                    speaker_displays = last_multi_speaker_displays
                else:
                    speaker_displays = _speaker_displays(display, speaker_aliases)
                current = []
                resolved_speaker_displays: list[str] = []
                for speaker_display in speaker_displays:
                    qualified_base = _qualified_base(speaker_display)
                    source_key = _identity_key(qualified_base or speaker_display)
                    canonical_display = cast_aliases.get(
                        source_key,
                        inferred_speaker_aliases.get(
                            source_key, qualified_base or speaker_display
                        ),
                    )
                    kind = _classify(canonical_display)
                    key = _identity_key(canonical_display) or f"unnamed-{scene.id}"
                    character = by_key.get(key)
                    if character is None:
                        character = CharacterOrSpeaker(
                            id=f"character-{len(characters) + 1:02d}",
                            display_name=(
                                _character_display(canonical_display)
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
                    resolved_speaker_displays.append(canonical_display)
                if len(resolved_speaker_displays) > 1:
                    last_multi_speaker_displays = resolved_speaker_displays
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
                    if not _act_heading(name) and not _scene_heading(name)
                )
            )
            if len(cast_names) == 1:
                character = CharacterOrSpeaker(
                    id="character-01",
                    display_name=_character_display(cast_names[0]),
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
