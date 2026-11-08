// feat(onboarding): questionário de primeiro acesso, com perguntas prontas,
// que indica a área da tecnologia com mais afinidade.
import { createFileRoute, redirect, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { ErrorState } from "@/components/interview/ErrorState";
import { OnboardingResultView } from "@/components/profile/OnboardingResultView";
import { getErrorMessage } from "@/services/api";
import {
  getOnboardingQuestions,
  getOnboardingStatus,
  skipOnboarding,
  submitOnboarding,
  type OnboardingQuestion,
  type OnboardingResult,
} from "@/services/onboardingApi";

export const Route = createFileRoute("/onboarding")({
  beforeLoad: () => {
    if (!localStorage.getItem("access_token")) {
      throw redirect({ to: "/" });
    }
  },
  head: () => ({
    meta: [
      { title: "Descubra sua área — StartAI" },
      {
        name: "description",
        content: "Responda algumas perguntas rápidas e descubra qual área da tecnologia combina mais com você.",
      },
    ],
  }),
  component: OnboardingPage,
});

type Step = "loading" | "intro" | "questions" | "result";

function OnboardingPage() {
  const navigate = useNavigate();
  const [step, setStep] = useState<Step>("loading");
  const [questions, setQuestions] = useState<OnboardingQuestion[]>([]);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [current, setCurrent] = useState(0);
  const [result, setResult] = useState<OnboardingResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSending, setIsSending] = useState(false);

  async function load() {
    setError(null);
    setStep("loading");
    try {
      const [status, list] = await Promise.all([getOnboardingStatus(), getOnboardingQuestions()]);
      setQuestions(list);
      if (status.result) {
        setResult(status.result);
        setStep("result");
      } else {
        setStep("intro");
      }
    } catch (err) {
      setError(getErrorMessage(err, "Não foi possível carregar o questionário."));
    }
  }

  useEffect(() => {
    void load();
  }, []);

  function restart() {
    setAnswers({});
    setCurrent(0);
    setStep("questions");
  }

  async function handleSkip() {
    setIsSending(true);
    try {
      await skipOnboarding();
    } catch {
      // Se não conseguir registrar, o aluno só verá o questionário de novo depois.
    }
    navigate({ to: "/home" });
  }

  async function handleSubmit() {
    setIsSending(true);
    setError(null);
    try {
      setResult(await submitOnboarding(answers));
      setStep("result");
    } catch (err) {
      setError(getErrorMessage(err, "Não foi possível enviar suas respostas."));
    } finally {
      setIsSending(false);
    }
  }

  const question = questions[current];
  const isLast = current === questions.length - 1;
  const selected = question ? answers[question.id] : undefined;

  return (
    <main className="flex-1 bg-background">
      <section className="bg-primary text-primary-foreground">
        <div className="mx-auto max-w-3xl px-4 pb-10 pt-8 sm:px-8">
          <p className="text-sm font-bold uppercase tracking-wider text-highlight">Primeiros passos</p>
          <h1 className="mt-2 text-3xl font-extrabold tracking-tight">Qual área da tecnologia combina com você?</h1>
          <p className="mt-2 max-w-2xl text-primary-foreground/85">
            Responda {questions.length || "algumas"} perguntas rápidas. Não existe resposta certa: escolha o que
            mais tem a ver com você.
          </p>
        </div>
      </section>

      <div className="mx-auto max-w-3xl px-4 py-8 sm:px-8">
        {error && step !== "questions" && <ErrorState message={error} onRetry={() => void load()} />}

        {step === "loading" && !error && (
          <div className="flex justify-center py-16">
            <div className="h-10 w-10 animate-spin rounded-full border-2 border-primary/20 border-t-primary" />
          </div>
        )}

        {step === "intro" && (
          <section className="rounded-2xl border border-border bg-card p-6 text-center shadow-sm sm:p-8">
            <h2 className="text-xl font-bold text-card-foreground">Vamos descobrir sua área?</h2>
            <p className="mx-auto mt-2 max-w-md text-sm leading-relaxed text-muted-foreground">
              Leva menos de 2 minutos. No fim você vê a área com mais afinidade, os cargos dela, o que estudar e
              pode treinar uma entrevista para essa vaga.
            </p>
            <div className="mt-6 flex flex-wrap justify-center gap-3">
              <button
                type="button"
                onClick={restart}
                className="rounded-xl bg-highlight px-5 py-2.5 text-sm font-bold text-highlight-foreground hover:bg-highlight/90"
              >
                Começar
              </button>
              <button
                type="button"
                onClick={() => void handleSkip()}
                disabled={isSending}
                className="rounded-xl border border-border px-5 py-2.5 text-sm font-semibold text-foreground hover:border-primary/40 disabled:opacity-50"
              >
                Pular por enquanto
              </button>
            </div>
            <p className="mt-4 text-xs text-muted-foreground">Você pode responder depois em “Meu perfil”.</p>
          </section>
        )}

        {step === "questions" && question && (
          <section className="rounded-2xl border border-border bg-card p-6 shadow-sm sm:p-8">
            <div className="flex items-center justify-between text-xs font-semibold text-muted-foreground">
              <span>
                Pergunta {current + 1} de {questions.length}
              </span>
              <span>{Math.round(((current + 1) / questions.length) * 100)}%</span>
            </div>
            <div className="mt-2 h-2 overflow-hidden rounded-full bg-muted">
              <div
                className="h-full rounded-full bg-primary transition-all"
                style={{ width: `${((current + 1) / questions.length) * 100}%` }}
              />
            </div>

            <fieldset className="mt-6">
              <legend className="text-lg font-bold text-card-foreground">{question.text}</legend>
              <div className="mt-4 grid gap-2">
                {question.options.map((option) => {
                  const checked = selected === option.id;
                  return (
                    <label
                      key={option.id}
                      className={`flex cursor-pointer items-center gap-3 rounded-xl border px-4 py-3 text-sm transition-colors ${
                        checked
                          ? "border-primary bg-primary/10 font-semibold text-foreground"
                          : "border-border text-card-foreground hover:border-primary/40"
                      }`}
                    >
                      <input
                        type="radio"
                        name={question.id}
                        value={option.id}
                        checked={checked}
                        onChange={() => setAnswers((prev) => ({ ...prev, [question.id]: option.id }))}
                        className="size-4 accent-[var(--primary)]"
                      />
                      {option.text}
                    </label>
                  );
                })}
              </div>
            </fieldset>

            {error && (
              <p className="mt-4 text-sm text-destructive" role="alert">
                {error}
              </p>
            )}

            <div className="mt-6 flex justify-between gap-3">
              <button
                type="button"
                onClick={() => setCurrent((value) => value - 1)}
                disabled={current === 0 || isSending}
                className="rounded-xl border border-border px-5 py-2.5 text-sm font-semibold text-foreground hover:border-primary/40 disabled:invisible"
              >
                Voltar
              </button>
              <button
                type="button"
                onClick={() => (isLast ? void handleSubmit() : setCurrent((value) => value + 1))}
                disabled={!selected || isSending}
                className="rounded-xl bg-primary px-5 py-2.5 text-sm font-bold text-primary-foreground hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {isLast ? (isSending ? "Calculando..." : "Ver meu resultado") : "Próxima"}
              </button>
            </div>
          </section>
        )}

        {step === "result" && result && <OnboardingResultView result={result} onRestart={restart} />}
      </div>
    </main>
  );
}
