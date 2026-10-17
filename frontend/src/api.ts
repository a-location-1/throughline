export type SubmissionState = 'ready';
export type Presence = 'speaking' | 'non_speaking';
export type CharacterKind = 'named' | 'unnamed' | 'collective' | 'indeterminate' | 'silent';
export type ActKind = 'act' | 'prologue' | 'epilogue' | "entr'acte" | 'interlude';

export interface Failure { code: string; message: string; next_action: string; }
export interface Submission { submission_id: string; source_kind: 'url' | 'pdf'; source_name: string; page_count?: number; byte_count: number; state: SubmissionState; failure?: Failure; }
export interface Scene { id: string; ordinal: number; act_id: string; label: string; source_span?: [number, number]; }
export interface Act { id: string; ordinal: number; label: string; kind: ActKind; scenes: Scene[]; }
export interface Character { id: string; display_name: string; kind: CharacterKind; first_appearance_scene_id: string; ambiguity?: { evidence: string; alternatives: string[] }; }
export interface Appearance { scene_id: string; character_id: string; presence: Presence; line_count: number; confidence: 'supported' | 'ambiguous'; explanation?: string; }
export interface Visualization { scene_ids: string[]; character_ids: string[]; colors: Record<string, string>; paths: Record<string, [number, number][]>; }
export interface ParserNotice { code: string; message: string; }
export interface AnalysisResult { schema_version: string; parser_version: string; submission: Submission; acts: Act[]; scenes: Scene[]; characters: Character[]; appearances: Appearance[]; notices: ParserNotice[]; ordering: { scene_ids: string[]; character_ids: string[]; scene_line_count_desc: Record<string, string[]> }; visualization: Visualization; }

const API_ROOT = (import.meta as ImportMeta & {
  env?: { VITE_API_ROOT?: string };
}).env?.VITE_API_ROOT ?? '/api';
export type Stage = 'Uploading source…' | 'Retrieving source…' | 'Analyzing playtext…';
export type StageUpdate = (stage: Stage) => void;

async function responseError(response: Response, fallback: string): Promise<never> {
  const body = await response.json().catch(() => undefined);
  throw new Error(body?.detail?.message ?? body?.detail ?? fallback);
}

export async function createUrlAnalysis(
  url: string,
  signal?: AbortSignal,
  onStage?: StageUpdate,
): Promise<AnalysisResult> {
  onStage?.('Retrieving source…');
  const response = await fetch(`${API_ROOT}/analyses`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ url }),
    signal,
  });
  if (!response.ok) return responseError(response, 'The source could not be analyzed.');
  onStage?.('Analyzing playtext…');
  return response.json() as Promise<AnalysisResult>;
}

export async function createPdfAnalysis(
  file: File,
  signal?: AbortSignal,
  onStage?: StageUpdate,
): Promise<AnalysisResult> {
  onStage?.('Uploading source…');
  const body = new FormData();
  body.append('file', file);
  const response = await fetch(`${API_ROOT}/analyses`, { method: 'POST', body, signal });
  if (!response.ok) return responseError(response, 'The PDF could not be analyzed.');
  onStage?.('Analyzing playtext…');
  return response.json() as Promise<AnalysisResult>;
}
