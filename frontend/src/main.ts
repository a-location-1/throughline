import './styles.css';
import { createPdfAnalysis, createUrlAnalysis, pollAnalysis, type AnalysisResult } from './api';
import { errorState, initialState, loadingState, progressState, readyState, type AppState } from './state';
import { resultToCsv } from './csv';
import { renderTable } from './render-table';
import { renderVisualization } from './render-visualization';

let appState: AppState = initialState;
let controller: AbortController | undefined;
const form = document.querySelector<HTMLFormElement>('#source-form')!;
const urlInput = document.querySelector<HTMLInputElement>('#play-url')!;
const uploadInput = document.querySelector<HTMLInputElement>('#pdf-upload')!;
const feedback = document.querySelector<HTMLElement>('#source-feedback')!;
const analysis = document.querySelector<HTMLElement>('#analysis')!;
const resultStatus = document.querySelector<HTMLElement>('#result-status')!;
const resultHeading = document.querySelector<HTMLElement>('#results-heading')!;
const resultMeta = document.querySelector<HTMLElement>('#result-meta')!;
const plot = document.querySelector<HTMLElement>('#plot-view')!;
const table = document.querySelector<HTMLElement>('#table-view')!;

function announce(message: string, isError = false): void { appState = isError ? errorState(appState, message) : { ...appState, statusMessage: message }; feedback.textContent = message; feedback.style.color = isError ? 'var(--red)' : 'var(--green)'; resultStatus.textContent = message; }
function showResult(result: AnalysisResult): void { analysis.hidden = false; resultHeading.textContent = result.submission.source_name || 'Playtext analysis'; resultMeta.textContent = `${result.acts.length} acts · ${result.scenes.length} scenes · ${result.characters.length} characters`; renderVisualization(plot, result); renderTable(table, result); analysis.scrollIntoView({ behavior: 'smooth', block: 'start' }); }
async function submit(source: Promise<{ analysis_id: string; progress: { stage: string; percent: number } }>): Promise<void> { controller?.abort(); controller = new AbortController(); try { const created = await source; appState = loadingState(created.analysis_id, created.progress); announce(created.progress.stage); const result = await pollAnalysis(created.analysis_id, (status) => { appState = progressState(appState, status); announce(status.progress?.stage ?? 'Processing'); }, controller.signal); appState = readyState(appState, result); showResult(result); announce('Analysis ready.'); } catch (error) { if ((error as Error).name !== 'AbortError') announce((error as Error).message, true); } }
form.addEventListener('submit', (event) => { event.preventDefault(); const url = urlInput.value.trim(); if (!url) { announce('Add a public URL or choose a PDF.', true); urlInput.focus(); return; } void submit(createUrlAnalysis(url)); });
uploadInput.addEventListener('change', () => { const file = uploadInput.files?.[0]; if (!file) return; if (file.size > 10 * 1024 * 1024) { announce('The PDF exceeds the 10 MB limit.', true); return; } void submit(createPdfAnalysis(file)); });
document.querySelector<HTMLButtonElement>('.clear-button')!.addEventListener('click', () => { controller?.abort(); urlInput.value = ''; uploadInput.value = ''; appState = initialState; announce('Source cleared.'); urlInput.focus(); });
document.querySelectorAll<HTMLButtonElement>('.view-option').forEach((button) => button.addEventListener('click', () => { const showTable = button.dataset.view === 'table'; plot.hidden = showTable; table.hidden = !showTable; document.querySelectorAll('.view-option').forEach((option) => option.setAttribute('aria-pressed', String(option === button))); }));
document.querySelector<HTMLButtonElement>('#copy-data')!.addEventListener('click', async () => { if (!appState.result) return; const text = appState.result.characters.map((character) => `${character.display_name}: ${appState.result!.appearances.filter((appearance) => appearance.character_id === character.id).map((appearance) => `${appearance.scene_id} (${appearance.presence})`).join(', ')}`).join('\n'); try { await navigator.clipboard.writeText(text); announce('Analysis copied to the clipboard.'); } catch { announce('Copy failed. Select the table and copy it manually.', true); } });
document.querySelector<HTMLButtonElement>('#download-data')!.addEventListener('click', () => { if (!appState.result) return; const blob = new Blob([resultToCsv(appState.result)], { type: 'text/csv;charset=utf-8' }); const link = document.createElement('a'); link.href = URL.createObjectURL(blob); link.download = 'throughline-analysis.csv'; link.click(); URL.revokeObjectURL(link.href); announce('CSV download started.'); });
