// feat(onboarding): questionário de primeiro acesso (área da tecnologia).
import api from "./api";

export type OnboardingQuestion = {
  id: string;
  text: string;
  options: { id: string; text: string }[];
};

export type CareerArea = {
  key: string;
  name: string;
  description: string;
  roles: string[];
  skills: string[];
  suggested_job_title: string;
};

export type OnboardingResult = {
  recommended_area: CareerArea;
  ranking: { key: string; name: string; percent: number }[];
  completed_at: string | null;
};

export type OnboardingStatus = {
  status: "pending" | "completed" | "skipped";
  result: OnboardingResult | null;
};

export async function getOnboardingStatus(): Promise<OnboardingStatus> {
  const { data } = await api.get<OnboardingStatus>("/onboarding/me");
  return data;
}

export async function getOnboardingQuestions(): Promise<OnboardingQuestion[]> {
  const { data } = await api.get<OnboardingQuestion[]>("/onboarding/questions");
  return data;
}

export async function submitOnboarding(answers: Record<string, string>): Promise<OnboardingResult> {
  const { data } = await api.post<OnboardingResult>("/onboarding", { answers });
  return data;
}

export async function skipOnboarding(): Promise<OnboardingStatus> {
  const { data } = await api.post<OnboardingStatus>("/onboarding/skip");
  return data;
}
