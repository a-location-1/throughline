import { describe, expect, it } from 'vitest';
import { renderTable } from '../../src/render-table';
import type { AnalysisResult } from '../../src/api';

describe('renderTable', () => { it('renders a real accessible table and text presence states', () => { const container = document.createElement('div'); const result = { scenes: [{ id: 's1', ordinal: 1, label: 'Scene I' }], characters: [{ id: 'c1', display_name: 'Alice' }], appearances: [{ scene_id: 's1', character_id: 'c1', presence: 'non_speaking', line_count: 0 }] } as AnalysisResult; renderTable(container, result); expect(container.querySelector('table')).toBeTruthy(); expect(container.textContent).toContain('Present, silent'); }); });

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
