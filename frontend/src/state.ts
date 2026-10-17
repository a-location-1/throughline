import type { AnalysisResult, Stage } from './api';

export interface AppState { result?: AnalysisResult; stage?: Stage; statusMessage: string; error?: string; busy: boolean; }
export const initialState: AppState = { statusMessage: '', busy: false };

export function loadingState(stage: Stage): AppState { return { stage, statusMessage: stage, busy: true }; }
export function progressState(current: AppState, stage: Stage): AppState { return { ...current, stage, statusMessage: stage }; }
export function readyState(current: AppState, result: AnalysisResult): AppState { return { ...current, result, busy: false, statusMessage: 'Analysis ready.' }; }
export function errorState(current: AppState, message: string): AppState { return { ...current, busy: false, error: message, statusMessage: message }; }
export function resetState(): AppState { return { ...initialState }; }
