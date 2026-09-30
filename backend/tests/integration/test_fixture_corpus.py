from pathlib import Path

from throughline.parser import parse_playtext


def _structural_projection(result: dict) -> dict:
    acts_by_id = {act["id"]: act for act in result["acts"]}
    scenes_by_id = {scene["id"]: scene for scene in result["scenes"]}
    characters_by_id = {
        character["id"]: character for character in result["characters"]
    }
    return {
        "acts": [
            {
                "label": act["label"],
                "kind": act.get("kind", "act"),
                "scenes": [scene["label"] for scene in act["scenes"]],
            }
            for act in result["acts"]
        ],
        "scenes": [
            {
                "label": scene["label"],
                "act": acts_by_id[scene["act_id"]]["label"],
            }
            for scene in result["scenes"]
        ],
        "characters": [
            {
                "display_name": character["display_name"],
                "kind": character["kind"],
                "first_appearance_scene": scenes_by_id[
                    character["first_appearance_scene_id"]
                ]["label"],
            }
            for character in result["characters"]
        ],
        "appearances": sorted(
            [
                {
                    "scene": scenes_by_id[appearance["scene_id"]]["label"],
                    "character": characters_by_id[appearance["character_id"]][
                        "display_name"
                    ],
                    "presence": appearance["presence"],
                }
                for appearance in result["appearances"]
            ],
            key=lambda item: (item["scene"], item["character"]),
        ),
    }


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


def test_ready_fixtures_match_structural_answer_keys(golden_fixture, submission):
    result = parse_playtext(golden_fixture["source_text"], submission)

    actual = _structural_projection(result.model_dump(mode="json"))
    expected = _structural_projection(golden_fixture["expected"])

    assert actual == expected
