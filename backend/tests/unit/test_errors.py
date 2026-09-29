from throughline.errors import failure


def test_failure_is_actionable_and_generic():
    item = failure("NO_PLAYTEXT_STRUCTURE")
    assert item.message
    assert item.next_action
    assert "example.org" not in item.message
