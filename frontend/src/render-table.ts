import type { AnalysisResult } from './api';

export function renderTable(container: HTMLElement, result: AnalysisResult): void {
  container.replaceChildren();
  const title = document.createElement('div'); title.className = 'table-toolbar';
  const heading = document.createElement('span'); heading.className = 'plot-title'; heading.textContent = 'Scene presence';
  const subtitle = document.createElement('span'); subtitle.className = 'plot-subtitle'; subtitle.textContent = 'Text labels distinguish speaking, non-speaking, and absence.';
  title.append(heading, subtitle); container.append(title);
  const scroll = document.createElement('div'); scroll.className = 'table-scroll';
  const table = document.createElement('table'); table.setAttribute('aria-label', 'Character by scene presence');
  const caption = document.createElement('caption'); caption.className = 'sr-only'; caption.textContent = 'Character presence by ordered scene'; table.append(caption);
  const header = document.createElement('tr');
  const characterHeader = document.createElement('th'); characterHeader.scope = 'col'; characterHeader.textContent = 'Character'; header.append(characterHeader);
  for (const scene of result.scenes) { const cell = document.createElement('th'); cell.scope = 'col'; cell.textContent = `S${String(scene.ordinal).padStart(2, '0')}`; cell.title = scene.label; header.append(cell); }
  const thead = document.createElement('thead'); thead.append(header); table.append(thead);
  const body = document.createElement('tbody');
  const byKey = new Map(result.appearances.map((appearance) => [`${appearance.character_id}:${appearance.scene_id}`, appearance]));
  for (const character of result.characters) { const row = document.createElement('tr'); const name = document.createElement('th'); name.scope = 'row'; name.textContent = character.display_name; row.append(name); for (const scene of result.scenes) { const cell = document.createElement('td'); const appearance = byKey.get(`${character.id}:${scene.id}`); cell.textContent = appearance ? appearance.presence === 'speaking' ? `Speaking (${appearance.line_count})` : 'Present, silent' : 'Absent'; cell.className = appearance?.presence ?? 'absent'; row.append(cell); } body.append(row); }
  table.append(body); scroll.append(table); container.append(scroll);
}
