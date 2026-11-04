export type Agent = 'prediction' | 'knowledge' | 'rl' | 'education' | 'verifier' | 'safety';
export type Evidence = { evidence_id: string; source_title: string; source_url: string; publisher: string; section: string; excerpt: string; retrieved_at: string };
export type Output = { score?: number; predicted_class?: number; model_version?: string; model_id?: string; limitations?: string[]; action?: string; policy_version?: string; decision_source?: string; evidence_ids?: string[]; evidence?: Evidence[]; proposed_action?: string; effective_action?: string; override_reason?: string; generation_mode?: string; llm_status?: string; llm_model?: string; provider_error?: string; verified?: boolean; mode?: string; reason_codes?: string[]; claims?: {claim_id: string; text: string; supports: {evidence_id: string; quote: string}[]}[] };
export type Safety = { stage: string; decision: string; reason: string; rule_ids: string[]; checked_content: string; allowed: boolean };
export type Event = { sequence: number; run_id: string; agent_id: Agent | null; status: string; reason: string; timestamp: string; rule_ids: string[]; safety_decision?: string; safety_stage?: string; action?: string; policy_version?: string; decision_source?: string; proposed_action?: string; effective_action?: string; action_override_reason?: string; attempt?: number; duration_ms?: number | null; input_summary?: Record<string,unknown>; output_summary?: Record<string,unknown> };
export type Run = { run_id: string; status: string; response: string; evidence: Evidence[]; agent_results: Record<Agent, { status: string; implementation: string; errors: string[]; output: Output | null }>; agent_trace: Event[]; safety_decisions: Safety[]; warnings: string[]; limitations: string[]; generation_mode?: string; grounding?: {verified: boolean; mode: string; reason_codes:string[]}; retrieval_rounds?: number; corpus_version?: string };
export type Readiness = { checked_at: string; components: Record<string, { status: string; version?: string; code?: string; sources?: number; chunks?: number; model?: string }> };
export type Source = {id: string; url: string; retrieved_at: string; chunk_count: number; sha256: string};
export type Experiment = { name: string; status?: string; report: { scope: string; summary: Record<string, string | number | null>[] } | null; manifest?: { timestamp: string; code_version: string; dataset_version: unknown; seed: unknown; outputs: Record<string, string> } };
export const API = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');
export async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(API + path, { ...init, signal: init?.signal ?? AbortSignal.timeout(120000) });
  if (!response.ok) throw new Error(`API ${response.status}: ${response.status === 422 ? 'Dữ liệu không hợp lệ. Kiểm tra 8 trường và xác nhận synthetic.' : response.status === 503 ? 'Dependency chưa sẵn sàng. Kiểm tra PostgreSQL / backend.' : 'Không thể hoàn thành yêu cầu.'}`);
  return response.json();
}
export const fields = [
  ['pregnancies', 'Số lần mang thai', 'lần', 0, 1], ['glucose', 'Glucose', 'mg/dL', 0, 'any'],
  ['blood_pressure', 'Huyết áp tâm trương', 'mmHg', 0, 'any'], ['skin_thickness', 'Độ dày nếp gấp da', 'mm', 0, 'any'],
  ['insulin', 'Insulin', 'µU/mL', 0, 'any'], ['bmi', 'BMI', 'kg/m²', 0, 'any'],
  ['diabetes_pedigree', 'Chỉ số phả hệ tiểu đường', 'index', 0, 'any'], ['age', 'Tuổi', 'năm', 1, 1],
] as const;
export const synthetic = { pregnancies: 0, glucose: 100, blood_pressure: 70, skin_thickness: 20, insulin: 50, bmi: 22, diabetes_pedigree: 0.3, age: 30 };
export function validateAssessment(values: Record<string, string>) {
  for (const [key, label, , min, step] of fields) {
    const value = Number(values[key]);
    if (!values[key]?.trim() || !Number.isFinite(value) || value < min || (step === 1 && !Number.isInteger(value))) return `${label}: nhập số ${step === 1 ? 'nguyên ' : ''}≥ ${min}.`;
  }
  return '';
}
export function citationUrl(value: string) {
  try { const url = new URL(value); return url.protocol === 'https:' && url.hostname === 'www.niddk.nih.gov' && !url.username && !url.password && !url.port && !url.search && !url.hash ? url.href : null; } catch { return null; }
}
