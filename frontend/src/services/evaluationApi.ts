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
  // Erros concretos no que o aluno disse e um exemplo de resposta melhor.
  // Avaliações antigas vêm com lista vazia e null.
  mistakes: string[];
  suggested_answer: string | null;
};

export type ScoreItem = {
  key: string;
  label: string;
  score: number;
};

export type Archetype = {
  key: string;
  name: string;
  description: string;
};

export type BehavioralProfile = {
  archetype: Archetype;
  description: string;
  competencies: ScoreItem[];
  star: ScoreItem[];
};

export type InterviewEvaluation = {
  session_id: string;
  presentation_type: string | null;
  overall_score: number;
  summary: string;
  highlights: string[];
  next_steps: string[];
  created_at: string | null;
  answers: AnswerEvaluation[];
  // Só nas entrevistas comportamentais.
  behavioral_profile: BehavioralProfile | null;
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
