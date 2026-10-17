import { describe, expect, it } from 'vitest';
import { errorState, loadingState, readyState, resetState } from '../../src/state';

describe('state transitions', () => {
  it('tracks loading and reset', () => {
    const loading = loadingState('Retrieving source…');
    expect(loading.busy).toBe(true);
    expect(resetState().result).toBeUndefined();
  });
  it('tracks failures', () => {
    expect(errorState(loadingState('Analyzing playtext…'), 'bad').error).toBe('bad');
  });
  it('tracks ready results', () => {
    const state = readyState(loadingState('Analyzing playtext…'), {} as never);
    expect(state.busy).toBe(false);
  });
});
