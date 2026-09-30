from pathlib import Path

from throughline.parser import parse_playtext


def test_fixture_style_result_has_unique_ordered_ids(submission):
    result = parse_playtext("ACT I\nSCENE I\nALICE\nHello\n", submission)
    assert len({scene.id for scene in result.scenes}) == len(result.scenes)
    assert result.ordering.scene_ids == [scene.id for scene in result.scenes]


def test_formatting_test_trifles_preserves_structural_answer(submission):
    source = (
        Path(__file__).parents[1]
        / "fixtures"
        / "sources"
        / "formatting-test-trifles.txt"
    ).read_text()

    result = parse_playtext(source, submission)

    assert len(result.acts) == 1
    assert len(result.scenes) == 1
    assert {character.display_name for character in result.characters} == {
        "GEORGE HENDERSON",
        "HENRY PETERS",
        "LEWIS HALE",
        "MRS PETERS",
        "MRS HALE",
    }
    assert all(
        appearance.presence.value == "speaking" for appearance in result.appearances
    )
