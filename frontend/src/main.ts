import './styles.css';
import { createPdfAnalysis, createUrlAnalysis, type AnalysisResult, type Stage } from './api';
import { errorState, initialState, loadingState, progressState, readyState, resetState, type AppState } from './state';
import { resultToCsv } from './csv';
import { renderTable, type TableRenderOptions } from './render-table';
import { renderVisualization, type VisualizationRenderOptions } from './render-visualization';
import { logger } from './logger';

let appState: AppState = initialState;
let controller: AbortController | undefined;
const DEFAULT_PLAY_URL = 'https://www.gutenberg.org/cache/epub/1513/pg1513-images.html';
const DEFAULT_DISPLAY_OPTIONS: TableRenderOptions = { showNonSpeaking: false, showPresenceLabels: false, showLineCounts: false, orderBy: 'firstAppearance' };
let displayOptions: TableRenderOptions = { ...DEFAULT_DISPLAY_OPTIONS };
let selectedCharacterIds = new Set<string>();
let dragDepth = 0;
const form = document.querySelector<HTMLFormElement>('#source-form')!;
const urlInput = document.querySelector<HTMLInputElement>('#play-url')!;
const uploadInput = document.querySelector<HTMLInputElement>('#pdf-upload')!;
const uploadZone = document.querySelector<HTMLElement>('.upload-zone')!;
const feedback = document.querySelector<HTMLElement>('#source-feedback')!;
const analysis = document.querySelector<HTMLElement>('#analysis')!;
const resultStatus = document.querySelector<HTMLElement>('#result-status')!;
const resultHeading = document.querySelector<HTMLElement>('#results-heading')!;
const resultMeta = document.querySelector<HTMLElement>('#result-meta')!;
const plot = document.querySelector<HTMLElement>('#plot-view')!;
const table = document.querySelector<HTMLElement>('#table-view')!;
const submitButton = form.querySelector<HTMLButtonElement>('button[type="submit"]')!;

function announce(message: string, isError = false): void { appState = isError ? errorState(appState, message) : { ...appState, statusMessage: message }; feedback.textContent = message; feedback.style.color = isError ? 'var(--red)' : 'var(--green)'; resultStatus.textContent = message; }
function setBusy(busy: boolean): void { form.querySelectorAll<HTMLInputElement>('input').forEach((input) => { input.disabled = busy; }); submitButton.disabled = busy; }
function replayPlotAnimation(): void { const svg = plot.querySelector<SVGSVGElement>('svg'); if (!svg) return; svg.classList.remove('plot-animation'); void svg.getBoundingClientRect(); svg.classList.add('plot-animation'); }
function resetAnalysis(): void {
  appState = resetState();
  displayOptions = { ...DEFAULT_DISPLAY_OPTIONS };
  selectedCharacterIds = new Set<string>();
  analysis.hidden = true;
  plot.replaceChildren();
  table.replaceChildren();
  resultHeading.textContent = '';
  resultMeta.textContent = '';
  resultStatus.textContent = '';
  plot.hidden = false;
  table.hidden = true;
  document.querySelectorAll('.view-option').forEach((option) => {
    const isPlot = option.getAttribute('data-view') === 'plot';
    option.classList.toggle('active', isPlot);
    option.setAttribute('aria-pressed', String(isPlot));
  });
}
function showResult(result: AnalysisResult, scroll = true): void { analysis.hidden = false; resultHeading.textContent = result.submission.source_name || 'Playtext analysis'; const noticeSummary = result.notices.map((notice) => notice.message).join(' '); const speakingCharacters = new Set(result.appearances.filter((appearance) => appearance.presence === 'speaking').map((appearance) => appearance.character_id)); resultMeta.textContent = `${result.acts.length} acts (${result.scenes.length} total scenes) · ${speakingCharacters.size} speaking characters (${result.characters.length} total characters)${noticeSummary ? ` · ${noticeSummary}` : ''}`; renderVisualization(plot, result, { showNonSpeaking: displayOptions.showNonSpeaking, orderBy: displayOptions.orderBy, selectedCharacterIds }, (options: VisualizationRenderOptions) => { displayOptions = { ...displayOptions, ...options }; showResult(result, false); }, (characterId, selected) => { if (selected) selectedCharacterIds.add(characterId); else selectedCharacterIds.delete(characterId); }); renderTable(table, result, displayOptions, (options) => { displayOptions = options; showResult(result, false); }); if (scroll) analysis.scrollIntoView({ behavior: 'smooth', block: 'start' }); }
async function submit(source: (signal: AbortSignal, onStage: (stage: Stage) => void) => Promise<AnalysisResult>, metadata: { sourceKind: 'url' | 'pdf'; byteCount?: number }): Promise<void> { controller?.abort(); resetAnalysis(); controller = new AbortController(); const startedAt = performance.now(); setBusy(true); appState = loadingState('Analyzing playtext…'); announce(appState.statusMessage); logger.info('analysis started', metadata); try { const result = await source(controller.signal, (stage) => { appState = progressState(appState, stage); announce(stage); }); appState = readyState(appState, result); showResult(result); announce(result.notices.length ? `Analysis ready. ${result.notices.map((notice) => notice.message).join(' ')}` : 'Analysis ready.'); logger.info('analysis finished', { ...metadata, durationMs: Math.round(performance.now() - startedAt) }); } catch (error) { if ((error as Error).name !== 'AbortError') { logger.error('analysis failed', { ...metadata, durationMs: Math.round(performance.now() - startedAt), errorType: (error as Error).name }); announce((error as Error).message, true); } } finally { setBusy(false); } }
form.addEventListener('submit', (event) => { event.preventDefault(); const url = urlInput.value.trim() || DEFAULT_PLAY_URL; void submit((signal, onStage) => createUrlAnalysis(url, signal, onStage), { sourceKind: 'url' }); });
function handlePdfFile(file: File): void {
  const isPdf = file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf');
  if (!isPdf) {
    controller?.abort();
    resetAnalysis();
    announce('Please choose a PDF file.', true);
    logger.warn('analysis validation failed', { reason: 'not_a_pdf', fileName: file.name });
    return;
  }
  if (file.size > 10 * 1024 * 1024) {
    controller?.abort();
    resetAnalysis();
    announce('The PDF exceeds the 10 MB limit.', true);
    logger.warn('analysis validation failed', { reason: 'file_too_large', byteCount: file.size });
    return;
  }
  void submit((signal, onStage) => createPdfAnalysis(file, signal, onStage), { sourceKind: 'pdf', byteCount: file.size });
}
uploadInput.addEventListener('change', () => { const file = uploadInput.files?.[0]; if (file) handlePdfFile(file); });
uploadZone.addEventListener('dragenter', (event) => {
  event.preventDefault();
  dragDepth += 1;
  uploadZone.classList.add('is-dragging');
});
uploadZone.addEventListener('dragover', (event) => { event.preventDefault(); });
uploadZone.addEventListener('dragleave', (event) => {
  event.preventDefault();
  dragDepth = Math.max(0, dragDepth - 1);
  if (dragDepth === 0) uploadZone.classList.remove('is-dragging');
});
uploadZone.addEventListener('drop', (event) => {
  event.preventDefault();
  dragDepth = 0;
  uploadZone.classList.remove('is-dragging');
  const files = event.dataTransfer?.files;
  if (!files?.length) return;
  if (files.length > 1) {
    controller?.abort();
    resetAnalysis();
    announce('Please drop one PDF at a time.', true);
    logger.warn('analysis validation failed', { reason: 'multiple_files_dropped', fileCount: files.length });
    return;
  }
  handlePdfFile(files[0]);
});
document.querySelector<HTMLButtonElement>('.clear-button')!.addEventListener('click', () => { controller?.abort(); urlInput.value = ''; uploadInput.value = ''; resetAnalysis(); announce('Source cleared.'); urlInput.focus(); });
document.querySelectorAll<HTMLButtonElement>('.view-option').forEach((button) => button.addEventListener('click', () => { const showTable = button.dataset.view === 'table'; plot.hidden = showTable; table.hidden = !showTable; document.querySelectorAll('.view-option').forEach((option) => option.setAttribute('aria-pressed', String(option === button))); if (!showTable) replayPlotAnimation(); }));
document.querySelector<HTMLButtonElement>('#copy-data')!.addEventListener('click', async () => { if (!appState.result) return; const text = appState.result.characters.map((character) => `${character.display_name}: ${appState.result!.appearances.filter((appearance) => appearance.character_id === character.id).map((appearance) => `${appearance.scene_id} (${appearance.presence})`).join(', ')}`).join('\n'); try { await navigator.clipboard.writeText(text); announce('Analysis copied to the clipboard.'); } catch { announce('Copy failed. Select the table and copy it manually.', true); } });
document.querySelector<HTMLButtonElement>('#download-data')!.addEventListener('click', () => { if (!appState.result) return; const blob = new Blob([resultToCsv(appState.result)], { type: 'text/csv;charset=utf-8' }); const link = document.createElement('a'); link.href = URL.createObjectURL(blob); link.download = 'throughline-analysis.csv'; link.click(); URL.revokeObjectURL(link.href); announce('CSV download started.'); });
