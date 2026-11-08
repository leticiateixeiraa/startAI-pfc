// feat(interview-resume): a tela de perguntas carrega o estado salvo no
// backend pelo id da sessão (na URL). Cada resposta já é gravada ao ser
// enviada, então o aluno pode sair no meio e continuar depois de onde parou.
// O texto ainda não enviado fica como rascunho no navegador.
import { createFileRoute, Link, redirect, useNavigate } from "@tanstack/react-router";
import { useCallback, useEffect, useState } from "react";
import { ErrorState } from "@/components/interview/ErrorState";
import { ProgressIndicator } from "@/components/interview/ProgressIndicator";
import { QuestionCard } from "@/components/interview/QuestionCard";
import { ApiError, getInterviewState, submitAnswer, type InterviewState } from "@/services/interviewApi";
import { presentationTypeLabel, seniorityLabel } from "@/types/interview";

export const Route = createFileRoute("/interview/questions")({
  validateSearch: (busca: Record<string, unknown>) => ({
    session: typeof busca.session === "string" ? busca.session : "",
  }),
  beforeLoad: () => {
    if (!localStorage.getItem("access_token")) {
      throw redirect({ to: "/" });
    }
  },
  head: () => ({
    meta: [
      { title: "Entrevista simulada — StartAI" },
      {
        name: "description",
        content: "Navegue pelas perguntas geradas pela IA para a sua entrevista simulada.",
      },
      { property: "og:title", content: "Entrevista simulada — StartAI" },
      {
        property: "og:description",
        content: "Navegue pelas perguntas geradas pela IA para a sua entrevista simulada.",
      },
    ],
  }),
  component: InterviewQuestionsPage,
});

// Rascunho da resposta digitada e ainda não enviada. Fica só neste navegador
// e é apagado quando a resposta é enviada.
const draftKey = (sessionId: string) => `interview_draft:${sessionId}`;

function readDraft(sessionId: string): string {
  try {
    return localStorage.getItem(draftKey(sessionId)) ?? "";
  } catch {
    return "";
  }
}

function writeDraft(sessionId: string, text: string) {
  try {
    if (text) localStorage.setItem(draftKey(sessionId), text);
    else localStorage.removeItem(draftKey(sessionId));
  } catch {
    // sem localStorage o rascunho só não é guardado
  }
}

function InterviewQuestionsPage() {
  const navigate = useNavigate();
  const { session: sessionId } = Route.useSearch();
  const [state, setState] = useState<InterviewState | null>(null);
  const [resumed, setResumed] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [answer, setAnswer] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const goToResult = useCallback(() => {
    writeDraft(sessionId, "");
    navigate({ to: "/interview/result", search: { session: sessionId } });
  }, [navigate, sessionId]);

  const load = useCallback(async () => {
    setLoadError(null);
    try {
      const loaded = await getInterviewState(sessionId);
      if (loaded.finished) {
        goToResult();
        return;
      }
      setState(loaded);
      setResumed(loaded.answered_count > 0);
      setAnswer(readDraft(sessionId));
    } catch (error) {
      setLoadError(error instanceof ApiError ? error.message : "Não foi possível carregar a entrevista.");
    }
  }, [sessionId, goToResult]);

  useEffect(() => {
    if (sessionId) void load();
  }, [sessionId, load]);

  if (!sessionId) {
    return (
      <main className="flex flex-1 flex-col items-center justify-center bg-background px-4">
        <div className="max-w-md text-center">
          <h1 className="text-xl font-semibold text-foreground">Nenhuma entrevista em andamento</h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Configure uma nova simulação ou continue uma entrevista pela página inicial.
          </p>
          <Link
            to="/interview/setup"
            className="mt-6 inline-flex items-center justify-center rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
          >
            Configurar entrevista
          </Link>
        </div>
      </main>
    );
  }

  if (loadError) {
    return (
      <main className="flex flex-1 flex-col items-center justify-center bg-background px-4 py-10">
        <div className="w-full max-w-md">
          <ErrorState message={loadError} onRetry={() => void load()} />
        </div>
      </main>
    );
  }

  if (!state || !state.current_question) {
    return (
      <main className="flex flex-1 items-center justify-center bg-background">
        <div className="h-10 w-10 animate-spin rounded-full border-2 border-primary/20 border-t-primary" />
      </main>
    );
  }

  const position = state.answered_count + 1;
  const isLast = position >= state.total_questions;
  const subtitle = [
    state.job_title,
    state.presentation_type && presentationTypeLabel(state.presentation_type),
    state.seniority && seniorityLabel(state.seniority),
  ]
    .filter(Boolean)
    .join(" • ");

  function handleAnswerChange(text: string) {
    setAnswer(text);
    writeDraft(sessionId, text);
  }

  async function handleAnswer() {
    if (!state || !answer.trim() || isSubmitting) return;
    setIsSubmitting(true);
    setErrorMessage(null);

    try {
      const result = await submitAnswer(sessionId, answer.trim());
      if (result.finished || !result.question) {
        goToResult();
        return;
      }
      handleAnswerChange("");
      setResumed(false);
      setState({ ...state, current_question: result.question, answered_count: state.answered_count + 1 });
    } catch (error) {
      setErrorMessage(error instanceof ApiError ? error.message : "Não foi possível enviar a resposta.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="flex flex-1 flex-col bg-background px-4 py-10">
      <div className="mx-auto flex w-full max-w-2xl flex-1 flex-col">
        <header className="mb-8 text-center">
          <h1 className="text-2xl font-bold tracking-tight text-foreground">Entrevista simulada</h1>
          {subtitle && <p className="mt-1 text-sm text-muted-foreground">{subtitle}</p>}
        </header>

        {resumed && (
          <div className="mb-6 rounded-xl border border-primary/20 bg-primary/5 px-4 py-3 text-sm text-foreground" role="status">
            <strong>Bem-vindo de volta!</strong> Suas {state.answered_count}{" "}
            {state.answered_count === 1 ? "resposta anterior está salva" : "respostas anteriores estão salvas"}.
            Continue de onde parou.
          </div>
        )}

        <div className="mb-8">
          <ProgressIndicator current={position} total={state.total_questions} />
        </div>

        <div className="flex flex-1 items-center justify-center">
          <QuestionCard questionText={state.current_question} />
        </div>

        <label className="mt-8 flex flex-col gap-2 text-sm font-medium text-card-foreground">
          Sua resposta
          <textarea
            value={answer}
            onChange={(event) => handleAnswerChange(event.target.value)}
            placeholder="Escreva sua resposta com detalhes..."
            rows={5}
            className="resize-none rounded-lg border border-input bg-card px-3 py-3 font-normal text-foreground outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
          />
        </label>

        {errorMessage && <p className="mt-3 text-sm text-destructive" role="alert">{errorMessage}</p>}

        <nav className="mt-8 flex items-center justify-between gap-3">
          <button
            type="button"
            onClick={handleAnswer}
            disabled={isSubmitting || !answer.trim()}
            className="ml-auto rounded-lg bg-primary px-5 py-2.5 text-sm font-semibold text-primary-foreground transition-colors hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {isSubmitting ? "Enviando..." : isLast ? "Finalizar entrevista" : "Enviar resposta"}
          </button>
        </nav>

        <div className="mt-6 text-center">
          <Link
            to="/home"
            className="text-sm text-muted-foreground underline-offset-4 transition-colors hover:text-foreground hover:underline"
          >
            Sair e continuar depois
          </Link>
          <p className="mt-1 text-xs text-muted-foreground">
            Suas respostas enviadas e o rascunho desta resposta ficam salvos.
          </p>
        </div>
      </div>
    </main>
  );
}
