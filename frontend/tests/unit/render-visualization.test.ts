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
	expect(container.querySelector('.plot-summary')?.textContent).not.toContain('Silent group');
	renderVisualization(container, result, { showNonSpeaking: true });
	expect(container.querySelector('.plot-summary')?.textContent).toContain('Silent group');
});
