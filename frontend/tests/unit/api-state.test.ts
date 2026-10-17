import { describe, expect, it } from 'vitest';
import { errorState, loadingState, progressState } from '../../src/state';

describe('API state outcomes', () => {
  it('announces staged progress without a misleading percentage', () => {
    const state = loadingState('Retrieving source…');
    expect(progressState(state, 'Analyzing playtext…').statusMessage).toBe('Analyzing playtext…');
  });
  it('keeps retryable failures actionable', () => {
    expect(errorState(loadingState('Analyzing playtext…'), 'Try another source.').error).toContain('Try');
  });
});
