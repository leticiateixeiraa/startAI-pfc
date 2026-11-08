import api from "./api";

export type InterviewHistoryItem = {
  session_id: string;
  category: string;
  job_title: string | null;
  presentation_type: string | null;
  seniority: string | null;
  finished: boolean;
  answered_count: number;
  created_at: string;
  overall_score: number | null;
};

export async function listInterviewHistory(): Promise<InterviewHistoryItem[]> {
  const { data } = await api.get<InterviewHistoryItem[]>("/interviews/history");
  return data;
}
