// feat(behavioral): perfil comportamental consolidado (GET /profile/behavioral).
import api from "./api";
import type { Archetype, ScoreItem } from "./evaluationApi";

export type ProfileHistoryItem = {
  session_id: string;
  created_at: string | null;
  overall_score: number | null;
  competencies: Record<string, number>;
};

export type ConsolidatedProfile = {
  interviews_count: number;
  archetype: Archetype | null;
  latest_description: string | null;
  strongest: string | null;
  weakest: string | null;
  competencies: ScoreItem[];
  star: ScoreItem[];
  history: ProfileHistoryItem[];
};

export async function getBehavioralProfile(): Promise<ConsolidatedProfile> {
  const { data } = await api.get<ConsolidatedProfile>("/profile/behavioral");
  return data;
}
