// feat(jobs): recomendação de vagas compatíveis com o perfil (GET /jobs/recommendations).
import api from "./api";

export type JobProfile = {
  job_title: string;
  source: "entrevistas" | "questionario";
  area: string | null;
  practiced_seniority: string;
  recommended_seniority: string;
  recommended_seniority_label: string;
  level_reason: string;
  average_score: number | null;
  interviews_count: number;
  skills: string[];
};

export type Job = {
  id: string;
  title: string;
  company: string | null;
  location: string | null;
  salary_min: number | null;
  salary_max: number | null;
  url: string;
  description: string | null;
  posted_at: string | null;
  compatibility: number;
  reasons: string[];
};

export type JobRecommendations = {
  profile: JobProfile | null;
  jobs: Job[];
  fetched_at: string | null;
  from_cache: boolean;
  warning: string | null;
  message: string | null;
};

// refresh = true ignora as vagas salvas e busca de novo (botão "Atualizar vagas").
export async function getJobRecommendations(refresh = false): Promise<JobRecommendations> {
  const { data } = await api.get<JobRecommendations>("/jobs/recommendations", {
    params: refresh ? { refresh: true } : undefined,
  });
  return data;
}
