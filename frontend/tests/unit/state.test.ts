import { describe, expect, it } from 'vitest';
import { errorState, loadingState, readyState, resetState } from '../../src/state';

describe('state transitions', () => { it('tracks loading and reset', () => { const loading = loadingState('id', { stage: 'queued', percent: 0 }); expect(loading.busy).toBe(true); expect(resetState().analysisId).toBeUndefined(); }); it('tracks failures', () => { expect(errorState(loadingState('id', { stage: 'x', percent: 1 }), 'bad').error).toBe('bad'); }); it('tracks ready results', () => { const state = readyState(loadingState('id', { stage: 'x', percent: 1 }), { } as never); expect(state.busy).toBe(false); }); });
