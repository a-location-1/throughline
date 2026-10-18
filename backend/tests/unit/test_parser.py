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
        "CAPULET",
        "LADY CAPULET",
    ]
    assert [appearance.line_count for appearance in result.appearances] == [
        1,
        1,
    ]


def test_parser_handles_numbered_interview_sections_and_aliases(submission):
    text = """i. First topic
    christian hawkey: The opening question.
    DaviD Levine: The opening answer.
    ii. Second topic
    ch: The next question.
    DL: The next answer.
    iii. Final topic
    ch: One last question.
    DL: One last answer.
    """

    result = parse_playtext(text, submission)

    assert [scene.label for scene in result.scenes] == [
        "Section I",
        "Section II",
        "Section III",
    ]
    assert [character.display_name for character in result.characters] == [
        "CHRISTIAN HAWKEY",
        "DAVID LEVINE",
    ]
    assert [notice.code for notice in result.notices] == ["UNCONVENTIONAL_STRUCTURE"]
    assert all(
        appearance.presence == Presence.SPEAKING
        for appearance in result.appearances
    )


def test_parser_strips_parenthetical_delivery_notes_from_speaker_names(submission):
    text = """SCENE I
    CAPULET (Angrily):
    What noise is this?
    """

    result = parse_playtext(text, submission)

    assert [character.display_name for character in result.characters] == ["CAPULET"]
    assert result.appearances[0].line_count == 1


def test_parser_normalizes_html_style_entrances(submission):
    text = """Dramatis Personae
Prince
Attendants
Capulet
Paris
Servant
Romeo
Mercutio
Benvolio
Watch
Balthasar
Friar Lawrence

ACT I
SCENE I
Enter Prince Escalus, with Attendants.
Enter Capulet, Paris and Servant.
Enter Romeo, Mercutio, Benvolio, with Maskers.
Enters the monument.
Re-enter some of the Watch with Balthasar.
Re-enter others of the Watch with Friar Lawrence.
"""

    result = parse_playtext(text, submission)

    names = {character.display_name for character in result.characters}
    assert {
        "PRINCE",
        "ATTENDANTS",
        "CAPULET",
        "PARIS",
        "SERVANT",
        "ROMEO",
        "MERCUTIO",
        "BENVOLIO",
        "WATCH",
    } <= names
    assert not names & {"MONUMENT", "A", "SOME", "OTHERS", "THE"}


def test_parser_normalizes_location_qualified_entrances(submission):
    text = """CHARACTERS
CONSTANTINE TREPLIEFF, her son

ACT I
SCENE I
Enter TREPLIEFF from behind the stage.
"""

    result = parse_playtext(text, submission)

    assert [character.display_name for character in result.characters] == [
        "CONSTANTINE TREPLIEFF"
    ]


def test_parser_recognizes_ordinal_act_headings(submission):
    text = """FIRST ACT
SCENE
ALICE.
Opening.
ACT DROP
SECOND ACT
SCENE
BOB.
Reply.
ACT DROP
THIRD ACT
SCENE
ALICE.
Closing.
"""

    result = parse_playtext(text, submission)

    assert [(act.label, act.kind) for act in result.acts] == [
        ("Act I", ActKind.ACT),
        ("Act II", ActKind.ACT),
        ("Act III", ActKind.ACT),
    ]
    assert "SECOND ACT" not in {character.display_name for character in result.characters}
    assert "THIRD ACT" not in {character.display_name for character in result.characters}


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


def test_parser_strips_scene_location_descriptions_from_labels(submission):
    text = """ACT I
    SCENE I. A public place.
    ALICE
    Welcome.
    2 — A street.
    BOB
    Reply.
    """

    result = parse_playtext(text, submission)

    assert [scene.label for scene in result.scenes] == ["Scene I", "Scene 2"]


def test_parser_ignores_scene_references_in_production_notes(submission):
    text = """CHARACTERS
    ANNA
    CARL
    PRODUCTION NOTES
    The rabbit appears after Scene VI.

    Scene 1
    ANNA
    We begin.
    Scene 2
    CARL
    We continue.
    """

    result = parse_playtext(text, submission)

    assert [scene.label for scene in result.scenes] == ["Scene 1", "Scene 2"]


def test_parser_keeps_inline_labels_in_the_current_speaker_line(submission):
    text = """Scene 1
    THE THIRD MAN
    Lesson Five:
    Basic dialogue.
    Do: Use the facilities.
    Music: Violins swell.
    Exercise: La carte.
    Sixieme Leçon: Pronoms directs.
    (Music: Violins swell.)
    ATD.
    VOICE OF ANNA
    I am here.
    """

    result = parse_playtext(text, submission)

    assert [character.display_name for character in result.characters] == [
        "THE THIRD MAN",
        "ANNA",
    ]
    assert [appearance.line_count for appearance in result.appearances] == [7, 1]


def test_parser_uses_dramatis_personae_to_normalize_shortened_names(submission):
    text = """DRAMATIS PERSONAE
    Rosaura           a lady
    Segismund         the prince
    Clotaldo          a general

    ACT I
    SCENE I
    (Enter Rosaura and Segismund.)
    ROS.
    We have arrived.
    SEG.
    So we have.
    Music: A brief flourish.
    Never Ape
    This continues the speech.
    """

    result = parse_playtext(text, submission)

    assert [character.display_name for character in result.characters] == [
        "ROSAURA",
        "SEGISMUND",
    ]


def test_parser_normalizes_grouped_roles_and_gutenberg_end_marker(submission):
    text = """Dramatis Personæ
An English Doctor.
A Porter.
An Old Man.
ACT I
SCENE I
a Porter
Hello.
an Old man
Good day.
PORTER.
Again.
OLD MAN.
Again.
MACBETH, LENNOX.
Together.
Enter Servant with two Murderers.
Servant.
Wait.
BOTH MURDERERS.
Speak.
Enter three Murderers.
FIRST MURDERER.
One.
SECOND MURDERER.
Two.
THIRD MURDERER.
Three.
Enter first Murderer to the door.
FIRST MURDERER.
Again.
Enter a Doctor of Physic and a Waiting-Gentlewoman.
DOCTOR.
Report.
GENTLEWOMAN.
Report.
*** END OF THE PROJECT GUTENBERG EBOOK MACBETH ***
START: FULL LICENSE
DAMAGE.
This is not play text.
"""

    result = parse_playtext(text, submission)

    assert [character.display_name for character in result.characters] == [
        "PORTER",
        "OLD MAN",
        "MACBETH",
        "LENNOX",
        "SERVANT",
        "FIRST MURDERER",
        "SECOND MURDERER",
        "THIRD MURDERER",
        "DOCTOR",
        "GENTLEWOMAN",
    ]


def test_parser_handles_hamlet_cast_and_grouping_conventions(submission):
    text = """Dramatis Personæ
HAMLET, Prince of Denmark
CLAUDIUS, King of Denmark
LAERTES, Son to Polonius
VOLTEMAND, Courtier
MARCELLUS, Officer
BARNARDO, Officer
Players
Two Clowns, Grave-diggers

ACT I
SCENE I
Enter Claudius King of Denmark.
CLAUDIUS.
Welcome.
Laertes, Voltemand,
We have news.
MARCELLUS and BARNARDO.
We keep watch.
HAMLET.
Are you armed?
Both.
We are.
Enter four or five Players.
Enter two Clowns with spades.
Enter Forces marching.
"""

    result = parse_playtext(text, submission)
    names = [character.display_name for character in result.characters]

    assert "CLAUDIUS" in names
    assert "CLAUDIUS KING" not in names
    assert "HAMLET" in names
    assert "THE TRAGEDY OF HAMLET" not in names
    assert "LAERTES" in names
    assert "VOLTEMAND" in names
    assert "LAERTES, VOLTEMAND" not in names
    assert "BOTH" not in names
    assert "MARCELLUS" in names
    assert "BARNARDO" in names
    assert "TWO CLOWNS" not in names
    assert "FIRST CLOWN" in names
    assert "SECOND CLOWN" in names
    assert names.count("PLAYERS") == 1
    assert "FOUR OR FIVE PLAYERS" not in names
    assert "FORCES MARCHING" not in names


def test_parser_normalizes_descriptive_entrances(submission):
    text = """Dramatis Personae
Basilio
Segismund
Astolfo
Estrella
Clotaldo
Rosaura
Fife
Soldiers

ACT I
SCENE I
(Enter first from the topmost rock Rosaura, as from horseback, in man's attire; and, after her, Fife.)
ROSAURA.
I am here.
(Enter Soldiers with black vizors and torches.)
CLOTALDO.
Stand aside.
SCENE II
Enter on one side Astolfo, Duke of Muscovy, with his train.
ASTOLFO.
Welcome.
SCENE III
Enter suddenly Clotaldo.
CLOTALDO.
Again.
(Enter Rosaura suddenly.)
ROSAURA.
Again.
SCENE IV
(Enter Soldiers cautiously up the rocks.)
CAPTAIN.
Advance.
"""

    result = parse_playtext(text, submission)
    names = [character.display_name for character in result.characters]

    assert "ROSAURA" in names
    assert "SOLDIERS" in names
    assert "ASTOLFO" in names
    assert "CLOTALDO" in names
    assert "CAPTAIN" in names
    for invalid in (
        "FIRST FROM THE TOPMOST ROCK ROSAURA",
        "TORCHES",
        "ON ONE SIDE ASTOLFO",
        "SUDDENLY CLOTALDO",
        "ROSAURA SUDDENLY",
        "SOLDIERS CAUTIOUSLY UP THE ROCKS",
    ):
        assert invalid not in names


def test_parser_uses_parenthetical_character_aliases(submission):
    text = """THE LIVE CORPSE
    CHARACTERS
    THEODORE VASÍLYEVICH PROTÁSOV (FÉDYA).
    ELISABETH ANDRÉYEVNA PROTÁSOVA (LISA).
    PRINCE SERGIUS DMÍTRIEVICH ABRÉZKOV.

    ACT I
    Scene 1
    FÉDYA.
    I am here.
    LISA.
    So am I.
    PRINCE ABRÉZKOV.
    Welcome.
    """

    result = parse_playtext(text, submission)

    assert [character.display_name for character in result.characters] == [
        "THEODORE VASÍLYEVICH PROTÁSOV",
        "ELISABETH ANDRÉYEVNA PROTÁSOVA",
        "PRINCE SERGIUS DMÍTRIEVICH ABRÉZKOV",
    ]


def test_parser_accepts_period_delimited_inline_speakers(submission):
    text = """CHARACTERS
    ABRAHAM.
    EPHREM.

    SCENE I
    ABRAHAM. Brother Ephrem, may I speak to you?
    EPHREM. Speak at once.
    """

    result = parse_playtext(text, submission)

    assert [character.display_name for character in result.characters] == [
        "ABRAHAM",
        "EPHREM",
    ]
    assert [appearance.line_count for appearance in result.appearances] == [1, 1]


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


def test_parser_does_not_treat_gutenberg_license_prose_as_second_play(submission):
    text = """MACBETH
by William Shakespeare

ACT I
SCENE I
MACBETH
The play begins.

*** END OF THE PROJECT GUTENBERG EBOOK MACBETH ***

Updated editions will replace the previous one.
The Foundation may copy and distribute this work.
"""

    result = parse_playtext(text, submission)

    assert [notice.code for notice in result.notices] == []


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


def test_parser_rejects_title_case_webpage_navigation_as_playtext(submission):
    text = """Google
Gmail
Images
Sign in
Advanced search
Advertising
Business Solutions
About Google
Privacy
Terms
Google apps
"""

    try:
        parse_playtext(text, submission)
    except ValueError as exc:
        assert str(exc) == "not playtext"
    else:
        raise AssertionError("webpage navigation must not be accepted as a playtext")


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


def test_parser_accepts_an_excerpt_beginning_with_act_one(submission):
    text = """THE JEWELER'S SHOP
    I.
    TERESA
    Andrew has chosen me.

    ANDREW
    I have come to speak.

    CHORUS
    We observe them.
    """

    result = parse_playtext(text, submission)

    assert len(result.acts) == 1
    assert len(result.scenes) == 1
    assert [character.display_name for character in result.characters] == [
        "TERESA",
        "ANDREW",
        "CHORUS",
    ]


def test_parser_rejects_an_excerpt_beginning_after_act_one(submission):
    for text in (
        "ACT II\nSCENE I\nALICE\nA later-act excerpt.\n",
        "SCENE II\nALICE\nA later-scene excerpt.\n",
    ):
        try:
            parse_playtext(text, submission)
        except ValueError as exc:
            assert str(exc) == "non-initial excerpt"
        else:
            raise AssertionError("later excerpts must not be accepted")
