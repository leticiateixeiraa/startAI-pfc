// feat(evaluation): consulta e geração da avaliação das respostas por IA.
import api from "./api";

export type EvaluationCriteria = {
  relevance: number;
  coherence: number;
  completeness: number;
  adequacy: number;
};

export type AnswerEvaluation = {
  order_index: number;
  question: string;
  answer: string;
  score: number;
  criteria: EvaluationCriteria;
  feedback: string;
  strengths: string[];
  improvements: string[];
};

export type InterviewEvaluation = {
  session_id: string;
  overall_score: number;
  summary: string;
  created_at: string | null;
  answers: AnswerEvaluation[];
};

export const CRITERIA_LABELS: Record<keyof EvaluationCriteria, string> = {
  relevance: "Relevância",
  coherence: "Coerência",
  completeness: "Completude",
  adequacy: "Adequação",
};

// Primeiro tenta a avaliação já salva (GET). Se ainda não existe (404),
// pede para o backend gerar (POST). Assim abrir o resultado de novo pelo
// histórico não chama o Gemini outra vez.
export async function loadEvaluation(sessionId: string): Promise<InterviewEvaluation> {
  try {
    const { data } = await api.get<InterviewEvaluation>(`/interviews/${sessionId}/evaluation`);
    return data;
  } catch (error) {
    if ((error as any)?.response?.status !== 404) throw error;
  }
  const { data } = await api.post<InterviewEvaluation>(`/interviews/${sessionId}/evaluation`);
  return data;
}

export function scoreLabel(score: number): string {
  if (score >= 9) return "Excelente";
  if (score >= 7) return "Boa";
  if (score >= 4) return "Regular";
  return "Precisa melhorar";
}
