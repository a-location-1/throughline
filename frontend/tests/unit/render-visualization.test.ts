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

it('orders plot rows by line count with first appearance tie-breaking', () => {
	const container = document.createElement('div');
	const result = {
		scenes: [{ id: 's1', ordinal: 1, label: 'Scene I' }, { id: 's2', ordinal: 2, label: 'Scene II' }],
		characters: [
			{ id: 'c1', display_name: 'First tie', first_appearance_scene_id: 's1' },
			{ id: 'c2', display_name: 'Most lines', first_appearance_scene_id: 's2' },
			{ id: 'c3', display_name: 'Second tie', first_appearance_scene_id: 's2' },
		],
		appearances: [
			{ scene_id: 's1', character_id: 'c1', presence: 'speaking', line_count: 8 },
			{ scene_id: 's2', character_id: 'c1', presence: 'speaking', line_count: 8 },
			{ scene_id: 's1', character_id: 'c2', presence: 'speaking', line_count: 20 },
			{ scene_id: 's2', character_id: 'c3', presence: 'speaking', line_count: 16 },
		],
		visualization: {
			paths: { c1: [[0, 0]], c2: [[0, 1]], c3: [[0, 2]] },
			colors: { c1: '#177254', c2: '#b44336', c3: '#555555' },
		},
	} as unknown as AnalysisResult;

	renderVisualization(container, result, { showNonSpeaking: false, orderBy: 'lineCount' });

	expect([...container.querySelectorAll<SVGGElement>('.character-line')].map((line) => line.dataset.characterId)).toEqual(['c2', 'c1', 'c3']);
	expect(container.querySelector('select')?.value).toBe('lineCount');
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
	const characterLine = container.querySelector('.character-line')!;
	expect(characterLine.contains(container.querySelector('.plot-mark'))).toBe(true);
});

it('supports pointer and keyboard selection with an SVG underlay', () => {
	const container = document.createElement('div');
	const result = {
		scenes: [{ id: 's1', ordinal: 1, label: 'Scene I' }],
		characters: [{ id: 'c1', display_name: 'Alice' }],
		appearances: [{ scene_id: 's1', character_id: 'c1', presence: 'speaking', line_count: 1 }],
		visualization: { paths: { c1: [[0, 0]] }, colors: { c1: '#177254' } },
	} as unknown as AnalysisResult;
	const changes: Array<[string, boolean]> = [];

	renderVisualization(container, result, { showNonSpeaking: false }, undefined, (characterId, selected) => changes.push([characterId, selected]));

	const characterLine = container.querySelector<SVGGElement>('.character-line')!;
	expect(characterLine.getAttribute('aria-pressed')).toBe('false');
	characterLine.dispatchEvent(new MouseEvent('click', { bubbles: true }));
	expect(characterLine.getAttribute('aria-pressed')).toBe('true');
	expect(characterLine.classList.contains('is-selected')).toBe(true);
	expect(changes).toEqual([['c1', true]]);
	expect(container.querySelector('.selection-ring')).toBeTruthy();
	expect(container.querySelector('.plot-character-label')?.getAttribute('class')).toContain('plot-character-label');

	characterLine.dispatchEvent(new KeyboardEvent('keydown', { key: ' ', bubbles: true }));
	expect(characterLine.getAttribute('aria-pressed')).toBe('false');
	expect(changes).toEqual([['c1', true], ['c1', false]]);
});

it('widens every scene column for the longest character label', () => {
	const container = document.createElement('div');
	const result = {
		scenes: [
			{ id: 's1', ordinal: 1, act_id: 'act-1', label: 'Scene I' },
			{ id: 's2', ordinal: 2, act_id: 'act-1', label: 'Scene II' },
		],
		characters: [{ id: 'c1', display_name: 'CONSTANTINE TREPLIEFF' }],
		appearances: [
			{ scene_id: 's1', character_id: 'c1', presence: 'speaking', line_count: 1 },
		],
		visualization: { paths: { c1: [[0, 0]] }, colors: { c1: '#177254' } },
	} as unknown as AnalysisResult;

	renderVisualization(container, result);

	expect(container.querySelector('.plot-mark')?.getAttribute('width')).toBe('167');
	expect(container.querySelector('.plot-header-grid')?.getAttribute('style')).toContain('width: 549px');
	expect(container.querySelector('.act-header')?.getAttribute('style')).toContain('repeat(2, 183px)');
	expect(container.querySelector('svg')?.getAttribute('width')).toBe('549');
	expect(container.querySelector<SVGLineElement>('.flow')?.style.getPropertyValue('--flow-length')).toBe('183px');
});

it('restores selected characters and starts flow animation when rerendered', () => {
	const container = document.createElement('div');
	const result = {
		scenes: [{ id: 's1', ordinal: 1, label: 'Scene I' }],
		characters: [{ id: 'c1', display_name: 'Alice' }],
		appearances: [{ scene_id: 's1', character_id: 'c1', presence: 'speaking', line_count: 1 }],
		visualization: { paths: { c1: [[0, 0]] }, colors: { c1: '#177254' } },
	} as unknown as AnalysisResult;

	renderVisualization(container, result, { showNonSpeaking: false, selectedCharacterIds: new Set(['c1']) });

	expect(container.querySelector('.plot-animation')).toBeTruthy();
	expect(container.querySelector('.character-line')?.getAttribute('aria-pressed')).toBe('true');
	expect(container.querySelector('.character-line')?.classList.contains('is-selected')).toBe(true);
	expect(container.querySelector('.flow')?.getAttribute('class')).toContain('flow');
});
