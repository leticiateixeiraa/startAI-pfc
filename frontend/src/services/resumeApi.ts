// feat(resume): análise de currículo por IA (página "Meu perfil").
import api from "./api";

export type ResumeCriterion = { key: string; label: string; score: number };
export type ResumeImprovement = { title: string; suggestion: string };

export type ResumeAnalysis = {
  file_name: string;
  file_type: "pdf" | "docx";
  target_role: string | null;
  overall_score: number;
  summary: string;
  criteria: ResumeCriterion[];
  strengths: string[];
  improvements: ResumeImprovement[];
  skills_found: string[];
  skills_missing: string[];
  suggested_job_title: string | null;
  analyzed_at: string;
};

export const RESUME_MAX_BYTES = 5 * 1024 * 1024;

export async function getResumeAnalysis(): Promise<ResumeAnalysis | null> {
  const { data } = await api.get<ResumeAnalysis | null>("/resume/me");
  return data;
}

export async function analyzeResume(file: File, targetRole: string): Promise<ResumeAnalysis> {
  const form = new FormData();
  form.append("file", file);
  if (targetRole.trim()) form.append("target_role", targetRole.trim());
  // Sem Content-Type: o navegador define o multipart com o boundary certo.
  // A análise pela IA pode levar alguns segundos, então o prazo é maior.
  const { data } = await api.post<ResumeAnalysis>("/resume/analyze", form, { timeout: 90_000 });
  return data;
}

export async function deleteResumeAnalysis(): Promise<void> {
  await api.delete("/resume/me");
}
