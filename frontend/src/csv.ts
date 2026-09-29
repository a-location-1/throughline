import type { AnalysisResult } from './api';

function escapeCell(value: string | number): string {
  const text = String(value);
  const safe = /^[=+\-@]/.test(text) ? `'${text}` : text;
  return /[",\n\r]/.test(safe) ? `"${safe.replaceAll('"', '""')}"` : safe;
}

export function resultToCsv(result: AnalysisResult): string {
  const names = new Map(result.characters.map((character) => [character.id, character.display_name]));
  const rows: Array<Array<string | number>> = [['character', 'scene_id', 'presence', 'line_count']];
  for (const appearance of result.appearances) rows.push([names.get(appearance.character_id) ?? appearance.character_id, appearance.scene_id, appearance.presence, appearance.line_count]);
  return rows.map((row) => row.map(escapeCell).join(',')).join('\r\n') + '\r\n';
}
