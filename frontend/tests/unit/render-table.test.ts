import { describe, expect, it } from 'vitest';
import { renderTable } from '../../src/render-table';
import type { AnalysisResult } from '../../src/api';

describe('renderTable', () => {
	it('hides non-speaking characters and labels by default', () => {
		const container = document.createElement('div');
		const result = {
			scenes: [{ id: 's1', ordinal: 1, label: 'Scene I' }],
			characters: [{ id: 'c1', display_name: 'Alice' }, { id: 'c2', display_name: 'Silent group' }],
			appearances: [
				{ scene_id: 's1', character_id: 'c1', presence: 'speaking', line_count: 2 },
				{ scene_id: 's1', character_id: 'c2', presence: 'non_speaking', line_count: 0 },
			],
		} as AnalysisResult;

		renderTable(container, result);

		expect(container.querySelector('table')).toBeTruthy();
		expect(container.textContent).toContain('Alice');
		expect(container.textContent).not.toContain('Silent group');
		expect(container.querySelector('td')?.textContent).toBe('');
	});

	it('renders all label and line-count combinations', () => {
		const container = document.createElement('div');
		const result = {
			scenes: [{ id: 's1', ordinal: 1, label: 'Scene I' }],
			characters: [{ id: 'c1', display_name: 'Alice' }],
			appearances: [{ scene_id: 's1', character_id: 'c1', presence: 'speaking', line_count: 52 }],
		} as AnalysisResult;

		renderTable(container, result, { showNonSpeaking: false, showPresenceLabels: true, showLineCounts: true });

		expect(container.querySelector('td')?.textContent).toBe('Speaking (52)');
	});

	it('orders characters by line count and breaks ties by first appearance', () => {
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
		} as AnalysisResult;

		renderTable(container, result, { showNonSpeaking: false, showPresenceLabels: false, showLineCounts: false, orderBy: 'lineCount' });

		expect([...container.querySelectorAll('tbody th')].map((cell) => cell.textContent)).toEqual(['Most lines', 'First tie', 'Second tie']);
		expect(container.querySelector('select')?.value).toBe('lineCount');
	});
});

it('groups scenes under act and special-section headers', () => {
	const container = document.createElement('div');
	const result = {
		acts: [
			{ id: 'prologue', ordinal: 1, label: 'Prologue', kind: 'prologue', scenes: [] },
			{ id: 'act-1', ordinal: 2, label: 'Act I', kind: 'act', scenes: [] },
		],
		scenes: [
			{ id: 's1', ordinal: 1, act_id: 'prologue', label: 'Prologue' },
			{ id: 's2', ordinal: 2, act_id: 'act-1', label: 'Scene I' },
		],
		characters: [],
		appearances: [],
	} as unknown as AnalysisResult;

	renderTable(container, result);

	const headerRows = container.querySelectorAll('thead tr');
	expect(headerRows).toHaveLength(2);
	expect(headerRows[0].textContent).toContain('Prologue');
	expect(headerRows[0].textContent).toContain('Act I');
	expect(headerRows[1].textContent).toContain('Scene I');
});

it('marks only the last scene in each act as an act boundary', () => {
	const container = document.createElement('div');
	const result = {
		acts: [{ id: 'act-1', ordinal: 1, label: 'Act I', kind: 'act', scenes: [] }, { id: 'act-2', ordinal: 2, label: 'Act II', kind: 'act', scenes: [] }],
		scenes: [
			{ id: 's1', ordinal: 1, act_id: 'act-1', label: 'Scene I' },
			{ id: 's2', ordinal: 2, act_id: 'act-1', label: 'Scene II' },
			{ id: 's3', ordinal: 3, act_id: 'act-2', label: 'Scene I' },
		],
		characters: [],
		appearances: [],
	} as unknown as AnalysisResult;

	renderTable(container, result);

	const sceneHeaders = container.querySelectorAll('.scene-header th');
	expect(sceneHeaders[0].classList.contains('act-end')).toBeFalsy();
	expect(sceneHeaders[1].classList.contains('act-end')).toBeTruthy();
	expect(sceneHeaders[2].classList.contains('act-end')).toBeTruthy();
});

it('renders normalization ambiguity as footnotes below the table', () => {
	const container = document.createElement('div');
	const result = {
		scenes: [{ id: 's1', ordinal: 1, label: 'Scene I' }],
		characters: [{
			id: 'c1', display_name: 'CAPULET',
			ambiguity: {
				evidence: 'descriptive speaker qualifier was grouped with the base role',
				alternatives: ['CAPULET WITH A CAPE'],
			},
		}],
		appearances: [],
	} as unknown as AnalysisResult;

	renderTable(container, result);

	const footnotes = container.querySelector('.table-footnotes');
	expect(footnotes).toBeTruthy();
	expect(footnotes?.textContent).toContain('CAPULET WITH A CAPE');
	expect(container.lastElementChild).toBe(footnotes);
});
