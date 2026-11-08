// Service de integração com o backend FastAPI.
//
// Persiste a sessão no backend autenticado.

import type { InterviewRequest, InterviewResponse } from "@/types/interview";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
export class ApiError extends Error {
  readonly status?: number;

  constructor(message: string, status?: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export type AnswerResponse = {
  session_id: string;
  question: string | null;
  order_index: number;
  finished: boolean;
  adapted: boolean;
};

function authHeaders() {
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${localStorage.getItem("access_token") ?? ""}`,
  };
}

async function createInterviewReal(
  request: InterviewRequest,
): Promise<InterviewResponse> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/interviews`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify(request),
    });
  } catch {
    throw new ApiError("Não foi possível conectar ao servidor. Verifique sua conexão.");
  }

  if (!response.ok) {
    if (response.status === 401) {
      localStorage.removeItem("access_token");
      window.location.assign("/");
      throw new ApiError("Sua sessão expirou. Faça login novamente.", 401);
    }

    // O backend retorna erros no padrão { "detail": "mensagem" }.
    let detail: string | undefined;
    try {
      const body = (await response.json()) as { detail?: string };
      detail = body.detail;
    } catch {
      detail = undefined;
    }
    throw new ApiError(
      detail ?? "Não foi possível gerar as perguntas. Tente novamente.",
      response.status,
    );
  }

  const body = (await response.json()) as {
    session_id: string;
    questions: Array<string | { order: number; text: string }>;
  };

  return {
    session_id: body.session_id,
    questions: body.questions.map((question, index) =>
      typeof question === "string" ? { order: index + 1, text: question } : question,
    ),
  };
}

export async function submitAnswer(
  sessionId: string,
  answerText: string,
): Promise<AnswerResponse> {
  const response = await fetch(`${API_BASE_URL}/interviews/${sessionId}/answer`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({ answer_text: answerText }),
  });

  if (response.status === 401) {
    localStorage.removeItem("access_token");
    window.location.assign("/");
    throw new ApiError("Sua sessão expirou. Faça login novamente.", 401);
  }

  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as { detail?: string };
    throw new ApiError(body.detail ?? "Não foi possível enviar a resposta.", response.status);
  }

  return (await response.json()) as AnswerResponse;
}

export async function createInterview(
  request: InterviewRequest,
): Promise<InterviewResponse> {
  return createInterviewReal(request);
}
