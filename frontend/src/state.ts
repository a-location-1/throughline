import type { AnalysisResult, AnalysisStatus, Progress } from './api';

export interface AppState { analysisId?: string; result?: AnalysisResult; progress?: Progress; statusMessage: string; error?: string; busy: boolean; }
export const initialState: AppState = { statusMessage: '', busy: false };

export function loadingState(id: string, progress: Progress): AppState { return { analysisId: id, progress, statusMessage: progress.stage, busy: true }; }
export function progressState(current: AppState, status: AnalysisStatus): AppState { return { ...current, progress: status.progress, statusMessage: status.progress?.stage ?? current.statusMessage }; }
export function readyState(current: AppState, result: AnalysisResult): AppState { return { ...current, result, busy: false, statusMessage: 'Analysis ready.' }; }
export function errorState(current: AppState, message: string): AppState { return { ...current, busy: false, error: message, statusMessage: message }; }
export function resetState(): AppState { return { ...initialState }; }
