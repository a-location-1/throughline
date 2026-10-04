from throughline.models import ActKind, CharacterKind, Presence
from throughline.parser import parse_playtext


def test_parser_preserves_order_and_speaking_lines(submission):
    text = """ACT I\nSCENE I\nALICE\nHello.\nBOB\nReply.\nSCENE II\nALICE\nAgain.\n"""
    result = parse_playtext(text, submission)
    assert [scene.id for scene in result.scenes] == ["scene-01", "scene-02"]
    assert [character.display_name for character in result.characters] == [
        "ALICE",
        "BOB",
    ]
    assert result.appearances[0].presence == Presence.SPEAKING
    assert result.appearances[0].line_count == 1


def test_parser_splits_shared_speaker_labels(submission):
    text = """ACT I
SCENE I
ALPHA
The first character speaks.
BETA
The second character speaks.
ALPHA and BETA.
We will wait upon you.
"""

    result = parse_playtext(text, submission)

    assert [character.display_name for character in result.characters] == [
        "ALPHA",
        "BETA",
    ]
    assert all(" and " not in character.display_name for character in result.characters)
    counts = {
        character.display_name: appearance.line_count
        for character in result.characters
        for appearance in result.appearances
        if appearance.character_id == character.id
    }
    assert counts == {"ALPHA": 2, "BETA": 2}


def test_parser_accepts_mixed_case_headers_and_speaker_labels(submission):
    text = """Title page
    Act I
    Scene I
    Capulet:
    What noise is this?
    Lady Capulet
    We should go.
    """

    result = parse_playtext(text, submission)

    assert [act.label for act in result.acts] == ["Act I"]
    assert [scene.label for scene in result.scenes] == ["Scene I"]
    assert [character.display_name for character in result.characters] == [
        "Capulet",
        "Lady Capulet",
    ]
    assert [appearance.line_count for appearance in result.appearances] == [
        1,
        1,
    ]


def test_parser_strips_parenthetical_delivery_notes_from_speaker_names(submission):
    text = """SCENE I
    CAPULET (Angrily):
    What noise is this?
    """

    result = parse_playtext(text, submission)

    assert [character.display_name for character in result.characters] == ["CAPULET"]
    assert result.appearances[0].line_count == 1


def test_parser_keeps_qualified_speaker_ambiguous_and_distinct(submission):
    text = """SCENE I
    CAPULET
    The house is mine.
    LADY CAPULET
    We should go.
    CAPULET WITH A CAPE
    Make way.
    """

    result = parse_playtext(text, submission)

    assert [character.display_name for character in result.characters] == [
        "CAPULET",
        "LADY CAPULET",
    ]
    qualified = result.characters[0]
    assert qualified.ambiguity is not None
    assert qualified.ambiguity.alternatives == ["CAPULET WITH A CAPE"]


def test_parser_preserves_prologue_before_act_one(submission):
    text = """PROLOGUE
    CHORUS
    Two households, both alike in dignity.
    ACT I
    SCENE I
    ALICE
    Welcome.
    """

    result = parse_playtext(text, submission)

    assert [(act.label, act.kind) for act in result.acts] == [
        ("Prologue", ActKind.PROLOGUE),
        ("Act I", ActKind.ACT),
    ]
    assert [scene.label for scene in result.scenes] == ["Prologue", "Scene I"]
    assert result.scenes[0].act_id == result.acts[0].id
    assert [character.display_name for character in result.characters] == [
        "CHORUS",
        "ALICE",
    ]


def test_parser_treats_entr_acte_as_special_act(submission):
    text = """ACT I
    SCENE I
    ALICE
    Welcome.
    ENTR'ACTE
    MUSIC
    ACT II
    SCENE I
    BOB
    Reply.
    """

    result = parse_playtext(text, submission)

    assert [(act.label, act.kind) for act in result.acts] == [
        ("Act I", ActKind.ACT),
        ("Entr'acte", ActKind.ENTR_ACTE),
        ("Act II", ActKind.ACT),
    ]
    assert [scene.label for scene in result.scenes] == [
        "Scene I",
        "Entr'acte",
        "Scene I",
    ]


def test_parser_keeps_unnamed_speaker(submission):
    result = parse_playtext("SCENE I\nUNKNOWN\nA line\n", submission)
    assert result.characters[0].kind == CharacterKind.UNNAMED
    assert result.characters[0].display_name == "Unnamed speaker"


def test_parser_excludes_front_matter_before_first_scene(submission):
    text = """THE MERCHANT OF VENICE
    A play in five acts

    Dramatis Personae
    ALICE
    BOB

    ACT I
    SCENE I
    ALICE
    Welcome.
    """

    result = parse_playtext(text, submission)

    assert [character.display_name for character in result.characters] == ["ALICE"]
    assert result.appearances[0].line_count == 1


def test_parser_excludes_front_matter_before_one_act_play(submission):
    text = """THE MERCHANT OF VENICE
    A play in one act

    Dramatis Personae
    ALICE
    BOB

    ACT I
    ALICE
    Welcome.
    """

    result = parse_playtext(text, submission)

    assert [character.display_name for character in result.characters] == ["ALICE"]
    assert result.appearances[0].line_count == 1


def test_parser_excludes_back_matter_after_the_play(submission):
    text = """ACT I
    SCENE I
    ALICE
    Welcome.

    THE END

    Project Gutenberg License
    This ebook may be redistributed.
    ADVERTISEMENTS
    BOB
    Buy another play.
    """

    result = parse_playtext(text, submission)

    assert [character.display_name for character in result.characters] == ["ALICE"]
    assert result.appearances[0].line_count == 1


def test_parser_accepts_consistent_chapter_scene_markers(submission):
    text = """ACT I:
CHAPTER 1
ALICE
The word scene is spoken here.
CHAPTER 2
BOB
The second section begins.
"""

    result = parse_playtext(text, submission)

    assert [act.label for act in result.acts] == ["Act I"]
    assert [scene.label for scene in result.scenes] == [
        "Chapter 1",
        "Chapter 2",
    ]


def test_parser_accepts_separator_scene_markers(submission):
    text = """ACT I
ALICE
The opening section.
---
BOB
The next section.
"""

    result = parse_playtext(text, submission)

    assert [scene.label for scene in result.scenes] == ["Scene I", "Scene II"]


def test_parser_warns_and_scopes_to_first_play(submission):
    text = """ACT I
SCENE I
ALICE
First play.
END

ACT I
SCENE I
BOB
Second play.
"""

    result = parse_playtext(text, submission)

    assert [character.display_name for character in result.characters] == ["ALICE"]
    assert [notice.code for notice in result.notices] == ["MULTIPLE_PLAYS"]


def test_parser_rejects_ordinary_non_play_text(submission):
    text = """Welcome to our website.
This page describes a scene from a product launch.
Read more about our company below.
"""

    try:
        parse_playtext(text, submission)
    except ValueError as exc:
        assert str(exc) == "not playtext"
    else:
        raise AssertionError("ordinary prose must not be accepted as a playtext")


def test_parser_handles_unheaded_gutenberg_play_and_notes_boundary(submission):
    text = """Preface and publication history.

CHARACTERS OF THE PLAY
IPHIGENIA
ORESTES

THE IPHIGENIA IN TAURIS

[The Scene shows a temple on a sea-coast.]

IPHIGENIA.
The play begins without an act or scene heading.

CHORUS.
[STROPHE 1.]
The strophe is part of the scene.

NOTES TO IPHIGENIA IN TAURIS
P. 3, 1. 1. Explanatory notes begin here.
"""

    result = parse_playtext(text, submission)

    assert len(result.acts) == 1
    assert len(result.scenes) == 1
    assert result.scenes[0].label == "Scene I"
    assert "NOTES TO IPHIGENIA IN TAURIS" not in result.scenes[0].label
    assert {character.display_name for character in result.characters} >= {
        "IPHIGENIA",
        "CHORUS",
    }


def test_parser_scopes_three_play_pdf_text_and_carries_single_speaker(submission):
    text = """WINNER
by Playwright Lastname

I.
JULIET
The opening speech.

II.
The speaker label is omitted here.

III.
Another unlabeled scene.

[The End]

GATES OPEN
by Playwright Lastname
I.
ROY
The second play must not be analyzed.

[The End]

GATES CLOSE
by Playwright Lastname
I.
JULIET
The third play must not be analyzed.
"""

    result = parse_playtext(text, submission)

    assert [scene.label for scene in result.scenes] == [
        "Scene I",
        "Scene II",
        "Scene III",
    ]
    assert [character.display_name for character in result.characters] == ["JULIET"]
    assert [appearance.line_count for appearance in result.appearances] == [
        1,
        1,
        1,
    ]
    assert [notice.code for notice in result.notices] == ["MULTIPLE_PLAYS"]


def test_parser_handles_pdf_script_scene_variants_and_page_numbers(submission):
    text = """HER LUGGAGE
by Jane Doe

Cast of Characters
ABASIAMA FALL 60s. A description.
GRAHAM TWICE 36. A description.
QUI FALL 30. A description.

ACT ONE
SCENE ONE
2
INIABASI
The opening speech.

SCENE 2
QUI
The second scene.

END OF PLAY
"""

    result = parse_playtext(text, submission)

    assert [scene.label for scene in result.scenes] == ["Scene ONE", "Scene 2"]
    assert {character.display_name for character in result.characters} == {
        "INIABASI",
        "QUI",
    }
    assert all(appearance.line_count == 1 for appearance in result.appearances)


def test_parser_returns_disclaimer_for_unconventional_unheaded_script(submission):
    text = """NOPAL
Storytellers in the Country
SHOW RUNDOWN: acts, scenes, video, and music.

A) Office of the Police.
JOHNSON
Welcome to the office of the police.

B) Border crossing.
EL GUIA
The desert is the border.

BLACK OUT. END
"""

    result = parse_playtext(text, submission)

    assert len(result.scenes) == 1
    assert [notice.code for notice in result.notices] == ["UNCONVENTIONAL_STRUCTURE"]
    assert {character.display_name for character in result.characters} >= {
        "JOHNSON",
        "EL GUIA",
    }
