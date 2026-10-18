import { describe, expect, it } from 'vitest';
import { renderVisualization } from '../../src/render-visualization';
import type { AnalysisResult } from '../../src/api';

describe('renderVisualization', () => { it('renders an accessible SVG from shared result data', () => { const container = document.createElement('div'); const result = { scenes: [{ id: 's1', ordinal: 1, label: 'Scene I' }], characters: [{ id: 'c1', display_name: 'Alice' }], appearances: [{ scene_id: 's1', character_id: 'c1', presence: 'speaking', line_count: 1 }], visualization: { paths: { c1: [[0, 0]] }, colors: { c1: '#177254' } } } as unknown as AnalysisResult; renderVisualization(container, result); expect(container.querySelector('svg')?.getAttribute('role')).toBe('img'); expect(container.textContent).toContain('Alice'); }); });

it('omits characters who never speak unless enabled', () => {
	const container = document.createElement('div');
	const result = {
		scenes: [{ id: 's1', ordinal: 1, label: 'Scene I' }],
		characters: [{ id: 'c1', display_name: 'Alice' }, { id: 'c2', display_name: 'Silent group' }],
		appearances: [
			{ scene_id: 's1', character_id: 'c1', presence: 'speaking', line_count: 1 },
			{ scene_id: 's1', character_id: 'c2', presence: 'non_speaking', line_count: 0 },
		],
		visualization: { paths: { c1: [[0, 0]], c2: [[0, 1]] }, colors: { c1: '#177254', c2: '#b44336' } },
	} as unknown as AnalysisResult;

	renderVisualization(container, result);
	expect(container.querySelector('.plot-character-label')?.textContent).toBe('Alice');
	expect(container.textContent).not.toContain('Silent group');
	renderVisualization(container, result, { showNonSpeaking: true });
	expect(container.textContent).toContain('Silent group');
});

it('renders act and scene headers with presence-aware fixed-height rows', () => {
	const container = document.createElement('div');
	const result = {
		acts: [{ id: 'act-1', label: 'Act I', kind: 'act', scenes: [] }],
		scenes: [
			{ id: 's1', ordinal: 1, act_id: 'act-1', label: 'Scene I' },
			{ id: 's2', ordinal: 2, act_id: 'act-1', label: 'Scene II' },
			{ id: 's3', ordinal: 3, act_id: 'act-1', label: 'Scene III' },
		],
		characters: [{ id: 'c1', display_name: 'Alice' }, { id: 'c2', display_name: 'Bob' }],
		appearances: [
			{ scene_id: 's1', character_id: 'c1', presence: 'speaking', line_count: 1 },
			{ scene_id: 's2', character_id: 'c1', presence: 'non_speaking', line_count: 0 },
			{ scene_id: 's1', character_id: 'c2', presence: 'speaking', line_count: 1 },
			{ scene_id: 's3', character_id: 'c2', presence: 'speaking', line_count: 1 },
		],
		visualization: { paths: { c1: [[0, 0], [1, 0]], c2: [[0, 1], [2, 1]] }, colors: { c1: '#177254', c2: '#b44336' } },
	} as unknown as AnalysisResult;

	renderVisualization(container, result);

	expect(container.querySelectorAll('.plot-header-row')).toHaveLength(2);
	expect(container.querySelector('.plot-act-cell')?.textContent).toBe('Act I');
	expect(container.querySelectorAll('.plot-scene-cell')).toHaveLength(3);
	expect(container.querySelector('.plot-scene-cell')?.classList.contains('scene-start')).toBe(true);
	expect(container.querySelectorAll('.plot-scene-cell')[2]?.classList.contains('scene-end')).toBe(true);
	expect(container.querySelectorAll('.plot-grid')).toHaveLength(4);
	expect(container.querySelector('.plot-grid.scene-start')).toBeTruthy();
	expect(container.querySelector('.plot-grid.scene-end')).toBeTruthy();
	expect(container.querySelector('svg')?.getAttribute('height')).toBe('112');
	const flowColors = [...container.querySelectorAll('.flow')].map((line) => line.getAttribute('stroke'));
	expect(flowColors).toEqual(['#86b4a5', '#177254', '#ebdad8', '#b44336', '#b44336']);
	expect(container.querySelector('.plot-character-header')).toBeNull();
	expect(container.querySelectorAll('.plot-buffer-cell')).toHaveLength(0);
	expect(container.querySelector('.act-header')?.getAttribute('style')).toContain('repeat(3, 130px)');
	expect(container.querySelector('.plot-mark')?.getAttribute('width')).toBe('64');
	expect(container.querySelector('.plot-mark')?.getAttribute('height')).toBe('22');
	expect(container.querySelector('svg')?.getAttribute('width')).toBe('520');
	const svg = container.querySelector('svg')!;
	expect([...svg.children].indexOf(container.querySelectorAll('.plot-mark')[1])).toBeGreaterThan([...svg.children].indexOf(container.querySelector('.flow')!));
});
