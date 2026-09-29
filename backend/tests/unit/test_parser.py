from throughline.models import CharacterKind, Presence
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


def test_parser_keeps_unnamed_speaker(submission):
    result = parse_playtext("SCENE I\nUNKNOWN\nA line\n", submission)
    assert result.characters[0].kind == CharacterKind.UNNAMED
    assert result.characters[0].display_name == "Unnamed speaker"
