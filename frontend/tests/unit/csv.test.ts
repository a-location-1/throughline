import { describe, expect, it } from 'vitest';
import { resultToCsv } from '../../src/csv';
import type { AnalysisResult } from '../../src/api';

const result = { characters: [{ id: 'c1', display_name: '=Unsafe', kind: 'named', first_appearance_scene_id: 's1' }], appearances: [{ scene_id: 's1', character_id: 'c1', presence: 'speaking', line_count: 2, confidence: 'supported' }] } as AnalysisResult;

describe('resultToCsv', () => { it('escapes formula-leading names and produces deterministic rows', () => { expect(resultToCsv(result)).toContain("'=Unsafe"); expect(resultToCsv(result).split('\r\n')[1]).toBe("'=Unsafe,s1,speaking,2"); }); });
