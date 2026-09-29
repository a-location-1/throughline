import { describe, expect, it } from 'vitest';
import { renderVisualization } from '../../src/render-visualization';
import type { AnalysisResult } from '../../src/api';

describe('renderVisualization', () => { it('renders an accessible SVG from shared result data', () => { const container = document.createElement('div'); const result = { scenes: [{ id: 's1', ordinal: 1, label: 'Scene I' }], characters: [{ id: 'c1', display_name: 'Alice' }], appearances: [{ scene_id: 's1', character_id: 'c1', presence: 'speaking', line_count: 1 }], visualization: { paths: { c1: [[0, 0]] }, colors: { c1: '#177254' } } } as unknown as AnalysisResult; renderVisualization(container, result); expect(container.querySelector('svg')?.getAttribute('role')).toBe('img'); expect(container.textContent).toContain('Alice'); }); });
