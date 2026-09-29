import { describe, expect, it } from 'vitest';
import { renderTable } from '../../src/render-table';
import type { AnalysisResult } from '../../src/api';

describe('renderTable', () => { it('renders a real accessible table and text presence states', () => { const container = document.createElement('div'); const result = { scenes: [{ id: 's1', ordinal: 1, label: 'Scene I' }], characters: [{ id: 'c1', display_name: 'Alice' }], appearances: [{ scene_id: 's1', character_id: 'c1', presence: 'non_speaking', line_count: 0 }] } as AnalysisResult; renderTable(container, result); expect(container.querySelector('table')).toBeTruthy(); expect(container.textContent).toContain('Present, silent'); }); });
