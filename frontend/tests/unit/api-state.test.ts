import { describe, expect, it } from 'vitest';
import { errorState, loadingState, progressState } from '../../src/state';

describe('API state outcomes', () => {
  it('announces progress without stealing focus', () => {
    const state = loadingState('opaque', { stage: 'queued', percent: 0 });
    expect(progressState(state, { analysis_id: 'opaque', state: 'parsing', progress: { stage: 'Parsing', percent: 70 } }).statusMessage).toBe('Parsing');
  });
  it('keeps retryable failures actionable', () => {
    expect(errorState(loadingState('opaque', { stage: 'queued', percent: 0 }), 'Try another source.').error).toContain('Try');
  });
});
