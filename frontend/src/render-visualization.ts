import type { AnalysisResult } from './api';

const NS = 'http://www.w3.org/2000/svg';
function blendColor(color: string, amount: number): string {
  const value = color.replace('#', '');
  const channels = [0, 2, 4].map((offset) => Number.parseInt(value.slice(offset, offset + 2), 16));
  const blended = channels.map((channel) => Math.round(channel + (245 - channel) * amount));
  return `#${blended.map((channel) => channel.toString(16).padStart(2, '0')).join('')}`;
}

export interface VisualizationRenderOptions { showNonSpeaking: boolean; }

export function renderVisualization(
  container: HTMLElement,
  result: AnalysisResult,
  options: VisualizationRenderOptions = { showNonSpeaking: false },
  onOptionChange?: (options: VisualizationRenderOptions) => void,
): void {
  container.replaceChildren();
  const speakingCharacterIds = new Set(result.appearances.filter((appearance) => appearance.presence === 'speaking').map((appearance) => appearance.character_id));
  const characters = options.showNonSpeaking ? result.characters : result.characters.filter((character) => speakingCharacterIds.has(character.id));
  const header = document.createElement('div'); header.className = 'plot-header'; const controls = document.createElement('div'); controls.className = 'analysis-options';
  const control = document.createElement('label'); control.className = 'option-toggle'; const input = document.createElement('input'); input.type = 'checkbox'; input.checked = options.showNonSpeaking; input.setAttribute('aria-label', 'Non-Speaking Characters'); input.addEventListener('change', () => onOptionChange?.({ showNonSpeaking: input.checked })); control.append(input, document.createTextNode('Non-Speaking Characters')); controls.append(control); header.append(controls); container.append(header);
  const body = document.createElement('div'); body.className = 'plot-canvas';
  const scroll = document.createElement('div'); scroll.className = 'plot-scroll';
  const sceneWidth = 130;
  const plotWidth = (result.scenes.length + 1) * sceneWidth;
  const rowHeight = 56;
  const plotHeight = Math.max(96, characters.length * rowHeight);
  const plotHeader = document.createElement('div'); plotHeader.className = 'plot-header-grid'; plotHeader.style.width = `${plotWidth}px`;
  const actRow = document.createElement('div'); actRow.className = 'plot-header-row act-header';
  const acts = new Map((result.acts ?? []).map((act) => [act.id, act]));
  let actIndex = 0;
  while (actIndex < result.scenes.length) {
    const actId = result.scenes[actIndex].act_id;
    let actEnd = actIndex + 1;
    while (actEnd < result.scenes.length && result.scenes[actEnd].act_id === actId) actEnd += 1;
    const actCell = document.createElement('div');
    actCell.className = `plot-act-cell ${acts.get(actId)?.kind ?? 'act'}`;
    actCell.style.flexBasis = `${(actEnd - actIndex) * sceneWidth}px`;
    actCell.textContent = acts.get(actId)?.label ?? actId;
    actRow.append(actCell);
    actIndex = actEnd;
  }
  const sceneRow = document.createElement('div'); sceneRow.className = 'plot-header-row scene-header';
  for (const [index, scene] of result.scenes.entries()) {
    const sceneCell = document.createElement('div'); sceneCell.className = 'plot-scene-cell'; if (index === result.scenes.length - 1 || result.scenes[index + 1].act_id !== scene.act_id) sceneCell.classList.add('act-end'); sceneCell.textContent = scene.label; sceneCell.title = `Scene ${scene.ordinal}`; sceneRow.append(sceneCell);
  }
  const bufferActCell = document.createElement('div'); bufferActCell.className = 'plot-buffer-cell'; actRow.append(bufferActCell);
  const bufferSceneCell = document.createElement('div'); bufferSceneCell.className = 'plot-buffer-cell'; sceneRow.append(bufferSceneCell);
  plotHeader.append(actRow, sceneRow);
  const svg = document.createElementNS(NS, 'svg'); svg.setAttribute('viewBox', `0 0 ${plotWidth} ${plotHeight}`); svg.setAttribute('width', String(plotWidth)); svg.setAttribute('height', String(plotHeight)); svg.setAttribute('role', 'img'); svg.setAttribute('aria-label', 'Character appearances across scenes');
  for (let index = 0; index < result.scenes.length; index += 1) {
    const line = document.createElementNS(NS, 'line');
    const x = index * sceneWidth;
    line.setAttribute('x1', String(x)); line.setAttribute('x2', String(x)); line.setAttribute('y1', '0'); line.setAttribute('y2', String(plotHeight)); line.setAttribute('class', 'plot-grid');
    if (index === result.scenes.length - 1 || result.scenes[index + 1].act_id !== result.scenes[index].act_id) line.classList.add('act-end');
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
    const labelWidth = Math.min(sceneWidth - 16, Math.max(64, character.display_name.length * 7 + 20));
    for (let sceneIndex = firstScene; sceneIndex <= lastScene; sceneIndex += 1) {
      const appearance = appearanceByKey.get(`${character.id}:${result.scenes[sceneIndex].id}`);
      const line = document.createElementNS(NS, 'line');
      line.setAttribute('x1', String(sceneIndex * sceneWidth));
      line.setAttribute('x2', String((sceneIndex + 1) * sceneWidth));
      line.setAttribute('y1', String(y)); line.setAttribute('y2', String(y)); line.setAttribute('stroke', appearance?.presence === 'speaking' ? color : blendColor(color, appearance?.presence === 'non_speaking' ? 0.5 : 0.85)); line.setAttribute('class', 'flow');
      svg.append(line);
      if (appearance) {
        const mark = document.createElementNS(NS, 'rect');
        mark.setAttribute('x', String(sceneIndex * sceneWidth + (sceneWidth - labelWidth) / 2));
        mark.setAttribute('y', String(y - 11)); mark.setAttribute('width', String(labelWidth)); mark.setAttribute('height', '22'); mark.setAttribute('rx', '8'); mark.setAttribute('fill', 'white');
        mark.setAttribute('opacity', appearance.presence === 'speaking' ? '0.82' : '0.41'); mark.setAttribute('class', 'plot-mark');
        svg.append(mark);
        const label = document.createElementNS(NS, 'text');
        label.setAttribute('x', String(sceneIndex * sceneWidth + sceneWidth / 2)); label.setAttribute('y', String(y + 4)); label.setAttribute('text-anchor', 'middle'); label.setAttribute('class', 'plot-character-label'); label.setAttribute('opacity', appearance.presence === 'speaking' ? '1' : '0.5'); label.textContent = character.display_name;
        svg.append(label);
      }
    }
  }
  scroll.append(plotHeader, svg); body.append(scroll); container.append(body);
}
