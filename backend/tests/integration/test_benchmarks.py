import time

from throughline.parser import parse_playtext


def test_representative_parser_stays_responsive(submission):
    source = "SCENE I\nALICE\nHello\n" * 200
    started = time.perf_counter()
    result = parse_playtext(source, submission)
    elapsed = time.perf_counter() - started
    assert result.scenes
    assert elapsed < 2
