from throughline.parser import parse_playtext


def test_repeated_parse_is_byte_identical(submission):
    text = "SCENE I\nALICE\nHello\n"
    assert (
        parse_playtext(text, submission).canonical_json()
        == parse_playtext(text, submission).canonical_json()
    )
