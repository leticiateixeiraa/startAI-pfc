// feat(roadmap-ia): trilha de estudos gerada a partir da avaliação da entrevista.
import api from "./api";

export type RoadmapResourceType = "pratica" | "curso" | "documentacao" | "site" | "video";

export type RoadmapResource = {
  type: RoadmapResourceType;
  title: string;
  url: string;
  description: string | null;
};

export type RoadmapItemStatus = "pending" | "in_progress" | "completed";

export type RoadmapItem = {
  id: string;
  order_index: number;
  title: string;
  description: string | null;
  status: RoadmapItemStatus;
  focus: string | null;
  estimated_time: string | null;
  practice: string | null;
  tips: string[];
  resources: RoadmapResource[];
};

export type Roadmap = {
  id: string;
  session_id: string | null;
  title: string;
  objective: string | null;
  summary: string | null;
  created_at: string;
  updated_at: string;
  items: RoadmapItem[];
};

// Igual à avaliação: primeiro tenta a trilha salva (GET); se ainda não
// existe (404), pede para o backend gerar (POST).
export async function loadInterviewRoadmap(sessionId: string): Promise<Roadmap> {
  try {
    const { data } = await api.get<Roadmap>(`/interviews/${sessionId}/roadmap`);
    return data;
  } catch (error) {
    if ((error as any)?.response?.status !== 404) throw error;
  }
  const { data } = await api.post<Roadmap>(`/interviews/${sessionId}/roadmap`);
  return data;
}

export async function updateRoadmapItemStatus(
  roadmapId: string,
  itemId: string,
  status: RoadmapItemStatus,
): Promise<Roadmap> {
  const { data } = await api.patch<Roadmap>(`/roadmaps/${roadmapId}/items/${itemId}`, { status });
  return data;
}

export async function listRoadmaps(): Promise<Roadmap[]> {
  const { data } = await api.get<Roadmap[]>("/roadmaps");
  return data;
}

export function roadmapProgress(roadmap: Roadmap): { done: number; total: number; percent: number } {
  const total = roadmap.items.length;
  const done = roadmap.items.filter((item) => item.status === "completed").length;
  return { done, total, percent: total ? Math.round((done / total) * 100) : 0 };
}
