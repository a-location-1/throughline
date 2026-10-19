import type { AnalysisResult } from './api';
import { orderedCharacters, type CharacterOrder } from './character-order';

const NS = 'http://www.w3.org/2000/svg';
function blendColor(color: string, amount: number): string {
  const value = color.replace('#', '');
  const channels = [0, 2, 4].map((offset) => Number.parseInt(value.slice(offset, offset + 2), 16));
  const blended = channels.map((channel) => Math.round(channel + (245 - channel) * amount));
  return `#${blended.map((channel) => channel.toString(16).padStart(2, '0')).join('')}`;
}

export interface VisualizationRenderOptions {
  showNonSpeaking: boolean;
  orderBy?: CharacterOrder;
  selectedCharacterIds?: ReadonlySet<string>;
}

export function renderVisualization(
  container: HTMLElement,
  result: AnalysisResult,
  options: VisualizationRenderOptions = { showNonSpeaking: false },
  onOptionChange?: (options: VisualizationRenderOptions) => void,
  onSelectionChange?: (characterId: string, selected: boolean) => void,
): void {
  container.replaceChildren();
  const characters = orderedCharacters(result, options.showNonSpeaking, options.orderBy);
  const header = document.createElement('div'); header.className = 'plot-header'; const controls = document.createElement('div'); controls.className = 'analysis-options';
  const control = document.createElement('label'); control.className = 'option-toggle'; const input = document.createElement('input'); input.type = 'checkbox'; input.checked = options.showNonSpeaking; input.setAttribute('aria-label', 'Non-Speaking Characters'); input.addEventListener('change', () => onOptionChange?.({ showNonSpeaking: input.checked })); control.append(input, document.createTextNode('Non-Speaking Characters')); controls.append(control); header.append(controls); container.append(header);
  const orderSelect = document.createElement('label'); orderSelect.className = 'option-select'; orderSelect.append(document.createTextNode('Order By'));
  const orderInput = document.createElement('select'); orderInput.setAttribute('aria-label', 'Order By');
  for (const [value, label] of [['firstAppearance', 'First Appearance'], ['lineCount', 'Line Count']] as const) {
    const option = document.createElement('option'); option.value = value; option.textContent = label; option.selected = (options.orderBy ?? 'firstAppearance') === value; orderInput.append(option);
  }
  orderInput.addEventListener('change', () => onOptionChange?.({ ...options, orderBy: orderInput.value as CharacterOrder }));
  orderSelect.append(orderInput); controls.insertBefore(orderSelect, control);
  const body = document.createElement('div'); body.className = 'plot-canvas';
  const scroll = document.createElement('div'); scroll.className = 'plot-scroll';
  const maxLabelWidth = Math.max(64, ...characters.map((character) => character.display_name.length * 7 + 20));
  const sceneWidth = Math.max(130, maxLabelWidth + 16);
  const margin = sceneWidth / 2;
  const plotWidth = result.scenes.length * sceneWidth + margin * 2;
  const rowHeight = 56;
  const plotHeight = Math.max(96, characters.length * rowHeight);
  const plotHeader = document.createElement('div'); plotHeader.className = 'plot-header-grid'; plotHeader.style.width = `${plotWidth}px`;
  const actRow = document.createElement('div'); actRow.className = 'plot-header-row act-header';
  actRow.style.gridTemplateColumns = `${margin}px repeat(${result.scenes.length}, ${sceneWidth}px) ${margin}px`;
  const actStartMargin = document.createElement('div'); actStartMargin.className = 'plot-margin'; actRow.append(actStartMargin);
  const acts = new Map((result.acts ?? []).map((act) => [act.id, act]));
  let actIndex = 0;
  while (actIndex < result.scenes.length) {
    const actId = result.scenes[actIndex].act_id;
    let actEnd = actIndex + 1;
    while (actEnd < result.scenes.length && result.scenes[actEnd].act_id === actId) actEnd += 1;
    const actCell = document.createElement('div');
    actCell.className = `plot-act-cell ${acts.get(actId)?.kind ?? 'act'}`;
    actCell.style.gridColumn = `span ${actEnd - actIndex}`;
    if (actIndex === 0) actCell.classList.add('scene-start');
    if (actEnd === result.scenes.length) actCell.classList.add('scene-end');
    if (actEnd < result.scenes.length) actCell.classList.add('act-end');
    actCell.textContent = acts.get(actId)?.label ?? actId;
    actRow.append(actCell);
    actIndex = actEnd;
  }
  const actEndMargin = document.createElement('div'); actEndMargin.className = 'plot-margin'; actRow.append(actEndMargin);
  const sceneRow = document.createElement('div'); sceneRow.className = 'plot-header-row scene-header';
  sceneRow.style.gridTemplateColumns = `${margin}px repeat(${result.scenes.length}, ${sceneWidth}px) ${margin}px`;
  const sceneStartMargin = document.createElement('div'); sceneStartMargin.className = 'plot-margin'; sceneRow.append(sceneStartMargin);
  for (const [index, scene] of result.scenes.entries()) {
    const sceneCell = document.createElement('div'); sceneCell.className = 'plot-scene-cell'; if (index === 0) sceneCell.classList.add('scene-start'); if (index === result.scenes.length - 1) sceneCell.classList.add('scene-end'); if (index === result.scenes.length - 1 || result.scenes[index + 1].act_id !== scene.act_id) sceneCell.classList.add('act-end'); sceneCell.textContent = scene.label; sceneCell.title = `Scene ${scene.ordinal}`; sceneRow.append(sceneCell);
  }
  const sceneEndMargin = document.createElement('div'); sceneEndMargin.className = 'plot-margin'; sceneRow.append(sceneEndMargin);
  plotHeader.append(actRow, sceneRow);
  const svg = document.createElementNS(NS, 'svg'); svg.setAttribute('viewBox', `0 0 ${plotWidth} ${plotHeight}`); svg.setAttribute('width', String(plotWidth)); svg.setAttribute('height', String(plotHeight)); svg.setAttribute('role', 'img'); svg.setAttribute('aria-label', 'Character appearances across scenes'); svg.classList.add('plot-animation');
  for (let index = 0; index <= result.scenes.length; index += 1) {
    const line = document.createElementNS(NS, 'line');
    const x = margin + index * sceneWidth;
    line.setAttribute('x1', String(x)); line.setAttribute('x2', String(x)); line.setAttribute('y1', '0'); line.setAttribute('y2', String(plotHeight)); line.setAttribute('class', 'plot-grid');
    if (index === 0) line.classList.add('scene-start');
    if (index === result.scenes.length) line.classList.add('scene-end');
    if (index > 0 && index < result.scenes.length && result.scenes[index].act_id !== result.scenes[index - 1].act_id) line.classList.add('act-end');
    svg.append(line);
  }
  const appearanceByKey = new Map(result.appearances.map((appearance) => [`${appearance.character_id}:${appearance.scene_id}`, appearance]));
  for (const [row, character] of characters.entries()) {
    const points = result.visualization.paths[character.id] ?? [];
    if (!points.length) continue;
    const firstScene = points[0][0];
    const lastScene = points[points.length - 1][0];
    const y = row * rowHeight + rowHeight / 2;
    const color = result.visualization.colors[character.id] ?? '#177254';
    const labelWidth = Math.max(64, character.display_name.length * 7 + 20);
    const sceneIndexes = Array.from({ length: lastScene - firstScene + 1 }, (_, index) => firstScene + index);
    const presenceAt = (sceneIndex: number) => appearanceByKey.get(`${character.id}:${result.scenes[sceneIndex].id}`)?.presence;
    const characterGroup = document.createElementNS(NS, 'g');
    characterGroup.classList.add('character-line');
    characterGroup.dataset.characterId = character.id;
    characterGroup.setAttribute('role', 'button');
    characterGroup.setAttribute('tabindex', '0');
    characterGroup.setAttribute('aria-label', `Highlight ${character.display_name}'s journey`);
    const selected = options.selectedCharacterIds?.has(character.id) ?? false;
    characterGroup.setAttribute('aria-pressed', String(selected));
    const setSelected = (nextSelected: boolean): void => {
      characterGroup.classList.toggle('is-selected', nextSelected);
      characterGroup.setAttribute('aria-pressed', String(nextSelected));
      onSelectionChange?.(character.id, nextSelected);
    };
    characterGroup.classList.toggle('is-selected', selected);
    characterGroup.addEventListener('click', () => setSelected(!characterGroup.classList.contains('is-selected')));
    characterGroup.addEventListener('keydown', (event) => {
      if (event.key !== 'Enter' && event.key !== ' ') return;
      event.preventDefault();
      setSelected(!characterGroup.classList.contains('is-selected'));
    });
    svg.append(characterGroup);
    const drawLine = (sceneIndex: number, presence: 'absent' | 'non_speaking' | 'speaking'): void => {
      const line = document.createElementNS(NS, 'line');
      line.setAttribute('x1', String(margin + sceneIndex * sceneWidth));
      line.setAttribute('x2', String(margin + (sceneIndex + 1) * sceneWidth));
      line.setAttribute('y1', String(y)); line.setAttribute('y2', String(y));
      line.setAttribute('stroke', presence === 'speaking' ? color : blendColor(color, presence === 'non_speaking' ? 0.5 : 0.85));
      line.setAttribute('class', 'flow');
      line.style.setProperty('--flow-length', `${sceneWidth}px`);
      line.style.setProperty('--flow-delay', `${sceneIndex * 60}ms`);
      characterGroup.append(line);
    };
    const hitTarget = document.createElementNS(NS, 'line');
    hitTarget.setAttribute('x1', String(margin + firstScene * sceneWidth));
    hitTarget.setAttribute('x2', String(margin + (lastScene + 1) * sceneWidth));
    hitTarget.setAttribute('y1', String(y)); hitTarget.setAttribute('y2', String(y));
    hitTarget.setAttribute('class', 'character-line-hit-target');
    characterGroup.append(hitTarget);
    const drawSelectionRing = (sceneIndex: number): void => {
      const ring = document.createElementNS(NS, 'line');
      ring.setAttribute('x1', String(margin + sceneIndex * sceneWidth));
      ring.setAttribute('x2', String(margin + (sceneIndex + 1) * sceneWidth));
      ring.setAttribute('y1', String(y)); ring.setAttribute('y2', String(y));
      ring.setAttribute('class', 'selection-ring');
      ring.style.setProperty('--flow-delay', `${sceneIndex * 60}ms`);
      characterGroup.insertBefore(ring, characterGroup.firstChild);
    };
    for (const sceneIndex of sceneIndexes) drawSelectionRing(sceneIndex);
    const drawLabel = (sceneIndex: number, speaking: boolean): void => {
      const appearance = appearanceByKey.get(`${character.id}:${result.scenes[sceneIndex].id}`);
      if (appearance?.presence !== (speaking ? 'speaking' : 'non_speaking')) return;
      const mark = document.createElementNS(NS, 'rect');
      mark.setAttribute('x', String(margin + sceneIndex * sceneWidth + (sceneWidth - labelWidth) / 2));
      mark.setAttribute('y', String(y - 11)); mark.setAttribute('width', String(labelWidth)); mark.setAttribute('height', '22'); mark.setAttribute('rx', '8'); mark.setAttribute('fill', 'white');
      mark.setAttribute('opacity', speaking ? '0.82' : '0.41'); mark.setAttribute('class', 'plot-mark');
      characterGroup.append(mark);
      const label = document.createElementNS(NS, 'text');
      label.setAttribute('x', String(margin + sceneIndex * sceneWidth + sceneWidth / 2)); label.setAttribute('y', String(y + 4)); label.setAttribute('text-anchor', 'middle'); label.setAttribute('class', 'plot-character-label'); label.setAttribute('opacity', speaking ? '1' : '0.5'); label.textContent = character.display_name;
      characterGroup.append(label);
    };
    for (const sceneIndex of sceneIndexes) if (!presenceAt(sceneIndex)) drawLine(sceneIndex, 'absent');
    for (const sceneIndex of sceneIndexes) if (presenceAt(sceneIndex) === 'non_speaking') drawLine(sceneIndex, 'non_speaking');
    for (const sceneIndex of sceneIndexes) if (presenceAt(sceneIndex) === 'non_speaking') drawLabel(sceneIndex, false);
    for (const sceneIndex of sceneIndexes) if (presenceAt(sceneIndex) === 'speaking') drawLine(sceneIndex, 'speaking');
    for (const sceneIndex of sceneIndexes) if (presenceAt(sceneIndex) === 'speaking') drawLabel(sceneIndex, true);
  }
  scroll.append(plotHeader, svg); body.append(scroll); container.append(body);
}
