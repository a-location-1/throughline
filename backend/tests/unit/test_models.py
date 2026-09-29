import pytest
from pydantic import ValidationError

from throughline.models import SceneAppearance, Presence


def test_non_speaking_appearance_requires_zero_lines():
    with pytest.raises(ValidationError):
        SceneAppearance(
            scene_id="scene-01",
            character_id="character-01",
            presence=Presence.NON_SPEAKING,
            line_count=1,
        )


def test_canonical_json_is_stable(submission):
    from throughline.models import (
        AnalysisResult,
        Act,
        Ordering,
        Scene,
        VisualizationInputs,
    )

    scene = Scene(id="scene-01", ordinal=1, act_id="act-01", label="Scene I")
    result = AnalysisResult(
        submission=submission,
        acts=[Act(id="act-01", ordinal=1, label="Act I", scenes=[scene])],
        scenes=[scene],
        characters=[],
        appearances=[],
        ordering=Ordering(scene_ids=[scene.id], character_ids=[]),
        visualization=VisualizationInputs(
            scene_ids=[scene.id], character_ids=[], colors={}, paths={}
        ),
    )
    assert result.canonical_json() == result.canonical_json()
