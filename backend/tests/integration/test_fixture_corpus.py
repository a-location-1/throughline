from throughline.parser import parse_playtext


def test_fixture_style_result_has_unique_ordered_ids(submission):
    result = parse_playtext("ACT I\nSCENE I\nALICE\nHello\n", submission)
    assert len({scene.id for scene in result.scenes}) == len(result.scenes)
    assert result.ordering.scene_ids == [scene.id for scene in result.scenes]
