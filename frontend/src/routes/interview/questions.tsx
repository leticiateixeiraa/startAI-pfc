import { createFileRoute, Link, redirect, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { ProgressIndicator } from "@/components/interview/ProgressIndicator";
import { QuestionAudio } from "@/components/interview/QuestionAudio";
import { QuestionCard } from "@/components/interview/QuestionCard";
import { VoiceRecorder } from "@/components/interview/VoiceRecorder";
import { cancelSpeech } from "@/lib/speech";
import { ApiError, submitAnswer, transcribeAudio } from "@/services/interviewApi";
import { getInterviewSession, clearInterviewSession } from "@/services/interviewSession";
import { presentationTypeLabel } from "@/types/interview";

export const Route = createFileRoute("/interview/questions")({
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

function InterviewQuestionsPage() {
  const navigate = useNavigate();
  const session = getInterviewSession();
  const [currentIndex, setCurrentIndex] = useState(0);
  // Os hooks ficam antes do "if (!session) return": o React exige a mesma
  // ordem de hooks em toda renderização.
  const [answer, setAnswer] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [adaptedQuestion, setAdaptedQuestion] = useState<string | null>(null);
  // Soma da duração dos áudios transcritos nesta resposta; null = digitada.
  // Será usada pelo analisador de oratória (palavras por minuto).
  const [voiceSeconds, setVoiceSeconds] = useState<number | null>(null);

  if (!session) {
    return (
      <main className="flex flex-1 flex-col items-center justify-center bg-background px-4">
        <div className="max-w-md text-center">
          <h1 className="text-xl font-semibold text-foreground">Nenhuma entrevista em andamento</h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Configure uma nova simulação para gerar suas perguntas.
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

  const { request, response } = session;
  const questions = [...response.questions].sort((a, b) => a.order - b.order);
  const currentQuestion = adaptedQuestion
    ? { order: currentIndex + 1, text: adaptedQuestion }
    : questions[currentIndex];
  if (!currentQuestion) return null;

  const isLast = currentIndex === questions.length - 1;

  async function handleAnswer() {
    if (!answer.trim() || isSubmitting) return;
    setIsSubmitting(true);
    setErrorMessage(null);

    try {
      const result = await submitAnswer(
        response.session_id,
        answer.trim(),
        voiceSeconds !== null ? { durationSeconds: voiceSeconds } : undefined,
      );
      if (result.finished || isLast) {
        clearInterviewSession();
        navigate({ to: "/interview/result", search: { session: response.session_id } });
        return;
      }
      setAnswer("");
      setVoiceSeconds(null);
      setAdaptedQuestion(result.adapted ? result.question : null);
      setCurrentIndex((index) => index + 1);
    } catch (error) {
      setErrorMessage(error instanceof ApiError ? error.message : "Não foi possível enviar a resposta.");
    } finally {
      setIsSubmitting(false);
    }
  }

  // Texto transcrito entra na caixa de resposta, onde pode ser revisado e
  // corrigido antes do envio. Várias gravações seguidas se somam.
  async function handleAudioReady(wav: Blob, durationSeconds: number) {
    const result = await transcribeAudio(response.session_id, wav, durationSeconds);
    setAnswer((current) => (current.trim() ? `${current.trim()} ${result.transcript}` : result.transcript));
    setVoiceSeconds((current) => (current ?? 0) + (result.duration_seconds ?? durationSeconds));
  }

  return (
    <main className="flex flex-1 flex-col bg-background px-4 py-10">
      <div className="mx-auto flex w-full max-w-2xl flex-1 flex-col">
        <header className="mb-8 text-center">
          <h1 className="text-2xl font-bold tracking-tight text-foreground">Entrevista simulada</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            {request.job_title} • {presentationTypeLabel(request.presentation_type)}
          </p>
        </header>

        <div className="mb-8">
          <ProgressIndicator current={currentIndex + 1} total={questions.length} />
        </div>

        <div className="flex flex-1 items-center justify-center">
          <QuestionCard questionText={currentQuestion.text} />
        </div>
        <QuestionAudio text={currentQuestion.text} />

        <label className="mt-8 flex flex-col gap-2 text-sm font-medium text-card-foreground">
          Sua resposta
          <textarea
            value={answer}
            onChange={(event) => {
              setAnswer(event.target.value);
              if (!event.target.value.trim()) setVoiceSeconds(null);
            }}
            placeholder="Escreva sua resposta ou use o botão de voz abaixo..."
            rows={5}
            className="resize-none rounded-lg border border-input bg-card px-3 py-3 font-normal text-foreground outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
          />
        </label>

        <div className="mt-3">
          <VoiceRecorder disabled={isSubmitting} onAudioReady={handleAudioReady} onStart={cancelSpeech} />
          {voiceSeconds !== null && (
            <p className="mt-2 text-xs text-muted-foreground">
              Texto transcrito do seu áudio. Revise e corrija o que for preciso antes de enviar.
            </p>
          )}
        </div>

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
            to="/interview/setup"
            className="text-sm text-muted-foreground underline-offset-4 transition-colors hover:text-foreground hover:underline"
          >
            Voltar para configuração
          </Link>
        </div>
      </div>
    </main>
  );
}
