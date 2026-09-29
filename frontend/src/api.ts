export type SubmissionState = 'queued' | 'retrieving' | 'extracting' | 'parsing' | 'ready' | 'rejected';
export type Presence = 'speaking' | 'non_speaking';
export type CharacterKind = 'named' | 'unnamed' | 'collective' | 'indeterminate' | 'silent';

export interface Progress { stage: string; percent: number; }
export interface Failure { code: string; message: string; next_action: string; }
export interface Submission { submission_id: string; source_kind: 'url' | 'pdf'; source_name: string; page_count?: number; byte_count: number; state: SubmissionState; failure?: Failure; }
export interface Scene { id: string; ordinal: number; act_id: string; label: string; source_span?: [number, number]; }
export interface Act { id: string; ordinal: number; label: string; scenes: Scene[]; }
export interface Character { id: string; display_name: string; kind: CharacterKind; first_appearance_scene_id: string; ambiguity?: { evidence: string; alternatives: string[] }; }
export interface Appearance { scene_id: string; character_id: string; presence: Presence; line_count: number; confidence: 'supported' | 'ambiguous'; explanation?: string; }
export interface Visualization { scene_ids: string[]; character_ids: string[]; colors: Record<string, string>; paths: Record<string, [number, number][]>; }
export interface AnalysisResult { schema_version: string; parser_version: string; submission: Submission; acts: Act[]; scenes: Scene[]; characters: Character[]; appearances: Appearance[]; ordering: { scene_ids: string[]; character_ids: string[]; scene_line_count_desc: Record<string, string[]> }; visualization: Visualization; }
export interface AnalysisStatus { analysis_id: string; state: SubmissionState; progress?: Progress; error?: Failure; result?: AnalysisResult; }
export interface CreateResponse { analysis_id: string; state: SubmissionState; progress: Progress; }

const API_ROOT = '/api';

export async function createUrlAnalysis(url: string): Promise<CreateResponse> {
  const response = await fetch(`${API_ROOT}/analyses`, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ url }) });
  if (!response.ok) throw new Error((await response.json()).detail?.message ?? 'The source could not be submitted.');
  return response.json() as Promise<CreateResponse>;
}

export async function createPdfAnalysis(file: File): Promise<CreateResponse> {
  const body = new FormData(); body.append('file', file);
  const response = await fetch(`${API_ROOT}/analyses`, { method: 'POST', body });
  if (!response.ok) throw new Error((await response.json()).detail?.message ?? 'The PDF could not be submitted.');
  return response.json() as Promise<CreateResponse>;
}

export async function getAnalysis(id: string, signal?: AbortSignal): Promise<AnalysisStatus> {
  const response = await fetch(`${API_ROOT}/analyses/${encodeURIComponent(id)}`, { signal });
  if (!response.ok) throw new Error('The analysis could not be retrieved.');
  return response.json() as Promise<AnalysisStatus>;
}

export async function pollAnalysis(id: string, onUpdate: (status: AnalysisStatus) => void, signal: AbortSignal): Promise<AnalysisResult> {
  for (;;) {
    const status = await getAnalysis(id, signal); onUpdate(status);
    if (status.state === 'ready' && status.result) return status.result;
    if (status.state === 'rejected') throw new Error(status.error?.message ?? 'The source was rejected.');
    await new Promise<void>((resolve, reject) => { const timer = window.setTimeout(resolve, 300); signal.addEventListener('abort', () => { window.clearTimeout(timer); reject(new DOMException('Cancelled', 'AbortError')); }, { once: true }); });
  }
}
