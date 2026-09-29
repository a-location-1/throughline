from throughline.models import Presence, SceneAppearance
from throughline.visualization import build_visualization


def test_visualization_order_and_colors_are_deterministic():
    appearances = [
        SceneAppearance(
            scene_id="scene-02",
            character_id="character-01",
            presence=Presence.SPEAKING,
            line_count=1,
        ),
        SceneAppearance(
            scene_id="scene-01",
            character_id="character-01",
            presence=Presence.NON_SPEAKING,
            line_count=0,
        ),
    ]
    first = build_visualization(["scene-01", "scene-02"], ["character-01"], appearances)
    second = build_visualization(
        ["scene-01", "scene-02"], ["character-01"], appearances
    )
    assert first.model_dump() == second.model_dump()
    assert first.paths["character-01"] == [(0, 0), (1, 0)]
