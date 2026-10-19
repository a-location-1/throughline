import type { AnalysisResult, Character } from './api';

export type CharacterOrder = 'firstAppearance' | 'lineCount';

export function orderedCharacters(
  result: AnalysisResult,
  showNonSpeaking: boolean,
  order: CharacterOrder = 'firstAppearance',
): Character[] {
  const speakingCharacterIds = new Set(
    result.appearances
      .filter((appearance) => appearance.presence === 'speaking')
      .map((appearance) => appearance.character_id),
  );
  const characters = result.characters
    .map((character, index) => ({ character, index }))
    .filter(({ character }) => showNonSpeaking || speakingCharacterIds.has(character.id));
  const sceneOrder = new Map(result.scenes.map((scene, index) => [scene.id, index]));
  const firstAppearanceOrder = (character: Character): number =>
    sceneOrder.get(character.first_appearance_scene_id) ?? Number.MAX_SAFE_INTEGER;
  const lineCounts = new Map<string, number>();
  for (const appearance of result.appearances) {
    lineCounts.set(
      appearance.character_id,
      (lineCounts.get(appearance.character_id) ?? 0) + appearance.line_count,
    );
  }

  characters.sort((a, b) => {
    if (order === 'lineCount') {
      const lineCountDifference =
        (lineCounts.get(b.character.id) ?? 0) - (lineCounts.get(a.character.id) ?? 0);
      if (lineCountDifference) return lineCountDifference;
    }
    return (
      firstAppearanceOrder(a.character) - firstAppearanceOrder(b.character) ||
      a.index - b.index
    );
  });
  return characters.map(({ character }) => character);
}
