import type { AnalysisResult } from './api';
import { orderedCharacters, type CharacterOrder } from './character-order';

export interface TableRenderOptions {
  showNonSpeaking: boolean;
  showPresenceLabels: boolean;
  showLineCounts: boolean;
  orderBy?: CharacterOrder;
}

export function renderTable(
  container: HTMLElement,
  result: AnalysisResult,
  options: TableRenderOptions = {
    showNonSpeaking: false,
    showPresenceLabels: false,
    showLineCounts: false,
  },
  onOptionChange?: (options: TableRenderOptions) => void,
): void {
  container.replaceChildren();
  const title = document.createElement('div'); title.className = 'table-toolbar';
  const controls = document.createElement('div'); controls.className = 'analysis-options';
  const addToggle = (label: string, checked: boolean, key: keyof TableRenderOptions) => {
    const control = document.createElement('label'); control.className = 'option-toggle';
    const input = document.createElement('input'); input.type = 'checkbox'; input.checked = checked; input.setAttribute('aria-label', label);
    input.addEventListener('change', () => onOptionChange?.({ ...options, [key]: input.checked }));
    control.append(input, document.createTextNode(label)); controls.append(control);
  };
  const orderSelect = document.createElement('label'); orderSelect.className = 'option-select';
  orderSelect.append(document.createTextNode('Order By'));
  const orderInput = document.createElement('select'); orderInput.setAttribute('aria-label', 'Order By');
  for (const [value, label] of [['firstAppearance', 'First Appearance'], ['lineCount', 'Line Count']] as const) {
    const option = document.createElement('option'); option.value = value; option.textContent = label; option.selected = (options.orderBy ?? 'firstAppearance') === value; orderInput.append(option);
  }
  orderInput.addEventListener('change', () => onOptionChange?.({ ...options, orderBy: orderInput.value as CharacterOrder }));
  orderSelect.append(orderInput); controls.append(orderSelect);
  addToggle('Non-Speaking Characters', options.showNonSpeaking, 'showNonSpeaking');
  addToggle('Scene Presence Labels', options.showPresenceLabels, 'showPresenceLabels');
  addToggle('Line Counts', options.showLineCounts, 'showLineCounts');
  title.append(controls); container.append(title);
  const viewport = document.createElement('div'); viewport.className = 'table-viewport';
  const scroll = document.createElement('div'); scroll.className = 'table-scroll';
  const scrollIndicator = document.createElement('div'); scrollIndicator.className = 'table-scroll-indicator'; scrollIndicator.setAttribute('aria-hidden', 'true');
  const table = document.createElement('table'); table.setAttribute('aria-label', 'Character by scene presence');
  const caption = document.createElement('caption'); caption.className = 'sr-only'; caption.textContent = 'Character presence by ordered scene'; table.append(caption);
  const actHeader = document.createElement('tr'); actHeader.className = 'act-header';
  const characterHeader = document.createElement('th'); characterHeader.className = 'character-column'; characterHeader.scope = 'col'; characterHeader.rowSpan = 2; characterHeader.textContent = 'Character'; actHeader.append(characterHeader);
  const acts = new Map((result.acts ?? []).map((act) => [act.id, act]));
  let index = 0;
  while (index < result.scenes.length) {
    const actId = result.scenes[index].act_id;
    let end = index + 1;
    while (end < result.scenes.length && result.scenes[end].act_id === actId) end += 1;
    const cell = document.createElement('th'); cell.scope = 'colgroup'; cell.colSpan = end - index; cell.textContent = acts.get(actId)?.label ?? actId; cell.className = `${acts.get(actId)?.kind ?? 'act'} act-end`; actHeader.append(cell);
    index = end;
  }
  const sceneHeader = document.createElement('tr'); sceneHeader.className = 'scene-header';
  for (const [index, scene] of result.scenes.entries()) { const cell = document.createElement('th'); cell.scope = 'col'; cell.textContent = scene.label; cell.title = `Scene ${scene.ordinal}`; if (index === result.scenes.length - 1 || result.scenes[index + 1].act_id !== scene.act_id) cell.className = 'act-end'; sceneHeader.append(cell); }
  const thead = document.createElement('thead'); thead.append(actHeader, sceneHeader); table.append(thead);
  const body = document.createElement('tbody');
  const byKey = new Map(result.appearances.map((appearance) => [`${appearance.character_id}:${appearance.scene_id}`, appearance]));
  const characters = orderedCharacters(result, options.showNonSpeaking, options.orderBy);
  for (const character of characters) {
    const row = document.createElement('tr'); const name = document.createElement('th'); name.className = 'character-column'; name.scope = 'row'; name.textContent = character.display_name; row.append(name);
    for (const [index, scene] of result.scenes.entries()) {
      const cell = document.createElement('td'); const appearance = byKey.get(`${character.id}:${scene.id}`);
      const label = appearance?.presence === 'speaking' ? 'Speaking' : appearance?.presence === 'non_speaking' ? 'Present, silent' : 'Absent';
      const count = appearance?.presence === 'speaking' && options.showLineCounts ? String(appearance.line_count) : '';
      cell.textContent = options.showPresenceLabels ? `${label}${count ? ` (${count})` : ''}` : count;
      cell.className = `${appearance?.presence ?? 'absent'}${index === result.scenes.length - 1 || result.scenes[index + 1].act_id !== scene.act_id ? ' act-end' : ''}`; row.append(cell);
    }
    body.append(row);
  }
  table.append(body); scroll.append(table);
  const updateScrollIndicator = () => {
    const firstColumn = table.querySelector<HTMLElement>('.character-column');
    if (!firstColumn) {
      scrollIndicator.hidden = true;
      return;
    }
    scrollIndicator.hidden = scroll.scrollLeft === 0;
    scrollIndicator.style.left = `${firstColumn.offsetWidth - 3}px`;
    scrollIndicator.style.height = `${scroll.clientHeight}px`;
  };
  scroll.addEventListener('scroll', updateScrollIndicator, { passive: true });
  requestAnimationFrame(updateScrollIndicator);
  viewport.append(scroll, scrollIndicator); container.append(viewport);
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
