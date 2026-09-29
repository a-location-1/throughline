"""Deterministic visualization inputs shared by table and plot views."""

from __future__ import annotations

from .models import SceneAppearance, VisualizationInputs

PALETTE = [
    "#177254",
    "#b44336",
    "#b8860b",
    "#375a7f",
    "#7b4b94",
    "#8b5e3c",
    "#236b8e",
    "#4c7a34",
]


def build_visualization(
    scene_ids: list[str], character_ids: list[str], appearances: list[SceneAppearance]
) -> VisualizationInputs:
    colors = {
        character_id: PALETTE[index % len(PALETTE)]
        for index, character_id in enumerate(character_ids)
    }
    scene_index = {scene_id: index for index, scene_id in enumerate(scene_ids)}
    char_index = {
        character_id: index for index, character_id in enumerate(character_ids)
    }
    paths: dict[str, list[tuple[int, int]]] = {
        character_id: [] for character_id in character_ids
    }
    for appearance in appearances:
        paths[appearance.character_id].append(
            (scene_index[appearance.scene_id], char_index[appearance.character_id])
        )
    for path in paths.values():
        path.sort()
    return VisualizationInputs(
        scene_ids=scene_ids, character_ids=character_ids, colors=colors, paths=paths
    )
