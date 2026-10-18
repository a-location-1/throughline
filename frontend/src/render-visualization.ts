import type { AnalysisResult } from './api';

const NS = 'http://www.w3.org/2000/svg';
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
  const body = document.createElement('div'); body.className = 'plot-canvas'; const svg = document.createElementNS(NS, 'svg'); svg.setAttribute('viewBox', `0 0 900 ${Math.max(180, characters.length * 48)}`); svg.setAttribute('role', 'img'); svg.setAttribute('aria-label', 'Character appearances across scenes');
  const summary = document.createElement('p'); summary.className = 'plot-summary'; summary.textContent = characters.map((character) => `${character.display_name}: ${result.appearances.filter((item) => item.character_id === character.id).map((item) => item.scene_id).join(', ') || 'absent'}`).join(' · ');
  for (let index = 0; index < result.scenes.length; index += 1) { const line = document.createElementNS(NS, 'line'); line.setAttribute('x1', String(40 + index * (820 / Math.max(1, result.scenes.length - 1)))); line.setAttribute('x2', line.getAttribute('x1')!); line.setAttribute('y1', '15'); line.setAttribute('y2', String(Math.max(160, result.characters.length * 48))); line.setAttribute('class', 'plot-grid'); svg.append(line); }
  for (const [row, character] of characters.entries()) { const points = result.visualization.paths[character.id] ?? []; if (!points.length) continue; const path = document.createElementNS(NS, 'path'); const d = points.map(([sceneIndex]) => `${40 + sceneIndex * (820 / Math.max(1, result.scenes.length - 1))},${35 + row * 48}`).join(' L '); path.setAttribute('d', `M ${d}`); path.setAttribute('stroke', result.visualization.colors[character.id]); path.setAttribute('class', 'flow flow-speaking'); path.setAttribute('fill', 'none'); svg.append(path); for (const [sceneIndex] of points) { const circle = document.createElementNS(NS, 'circle'); circle.setAttribute('cx', String(40 + sceneIndex * (820 / Math.max(1, result.scenes.length - 1)))); circle.setAttribute('cy', String(35 + row * 48)); circle.setAttribute('r', '5'); circle.setAttribute('fill', result.visualization.colors[character.id]); circle.setAttribute('class', 'plot-node'); svg.append(circle); } }
  body.append(svg); container.append(body, summary);
}
