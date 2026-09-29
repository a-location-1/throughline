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
  const actHeader = document.createElement('tr'); actHeader.className = 'act-header';
  const characterHeader = document.createElement('th'); characterHeader.scope = 'col'; characterHeader.rowSpan = 2; characterHeader.textContent = 'Character'; actHeader.append(characterHeader);
  const acts = new Map((result.acts ?? []).map((act) => [act.id, act]));
  let index = 0;
  while (index < result.scenes.length) {
    const actId = result.scenes[index].act_id;
    let end = index + 1;
    while (end < result.scenes.length && result.scenes[end].act_id === actId) end += 1;
    const cell = document.createElement('th'); cell.scope = 'colgroup'; cell.colSpan = end - index; cell.textContent = acts.get(actId)?.label ?? actId; cell.className = acts.get(actId)?.kind ?? 'act'; actHeader.append(cell);
    index = end;
  }
  const sceneHeader = document.createElement('tr'); sceneHeader.className = 'scene-header';
  for (const scene of result.scenes) { const cell = document.createElement('th'); cell.scope = 'col'; cell.textContent = scene.label; cell.title = `Scene ${scene.ordinal}`; sceneHeader.append(cell); }
  const thead = document.createElement('thead'); thead.append(actHeader, sceneHeader); table.append(thead);
  const body = document.createElement('tbody');
  const byKey = new Map(result.appearances.map((appearance) => [`${appearance.character_id}:${appearance.scene_id}`, appearance]));
  for (const character of result.characters) { const row = document.createElement('tr'); const name = document.createElement('th'); name.scope = 'row'; name.textContent = character.display_name; row.append(name); for (const scene of result.scenes) { const cell = document.createElement('td'); const appearance = byKey.get(`${character.id}:${scene.id}`); cell.textContent = appearance ? appearance.presence === 'speaking' ? `Speaking (${appearance.line_count})` : 'Present, silent' : 'Absent'; cell.className = appearance?.presence ?? 'absent'; row.append(cell); } body.append(row); }
  table.append(body); scroll.append(table); container.append(scroll);
  const ambiguityNotes = result.characters.filter((character) => character.ambiguity?.alternatives.length);
  if (ambiguityNotes.length) {
    const notes = document.createElement('ol'); notes.className = 'table-footnotes'; notes.setAttribute('aria-label', 'Character normalization notes');
    for (const character of ambiguityNotes) {
      const note = document.createElement('li');
      note.textContent = `${character.display_name}: ${character.ambiguity!.evidence}. Source labels: ${character.ambiguity!.alternatives.join(', ')}.`;
      notes.append(note);
    }
    container.append(notes);
  }
}
