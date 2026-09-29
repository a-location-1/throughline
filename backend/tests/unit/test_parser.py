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
