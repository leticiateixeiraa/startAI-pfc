// feat(evaluation): tela de resultado da entrevista, com nota e feedback da IA.
import { createFileRoute, Link, redirect } from "@tanstack/react-router";
import { useCallback, useEffect, useRef, useState } from "react";
import { ErrorState } from "@/components/interview/ErrorState";
import { getErrorMessage } from "@/services/api";
import {
  CRITERIA_LABELS,
  loadEvaluation,
  scoreLabel,
  type AnswerEvaluation,
  type EvaluationCriteria,
  type InterviewEvaluation,
} from "@/services/evaluationApi";

export const Route = createFileRoute("/interview/result")({
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
      { title: "Resultado da entrevista — StartAI" },
      {
        name: "description",
        content: "Veja a nota e o feedback da IA para cada resposta da sua entrevista.",
      },
    ],
  }),
  component: InterviewResultPage,
});

const number = new Intl.NumberFormat("pt-BR", { minimumFractionDigits: 1, maximumFractionDigits: 1 });

// Cor da nota: verde (boa), laranja (regular) ou vermelho (precisa melhorar).
function scoreColor(score: number) {
  if (score >= 7) return "text-emerald-600";
  if (score >= 4) return "text-amber-600";
  return "text-destructive";
}

function barColor(score: number) {
  if (score >= 7) return "bg-emerald-500";
  if (score >= 4) return "bg-amber-500";
  return "bg-destructive";
}

function CriteriaBars({ criteria }: { criteria: EvaluationCriteria }) {
  return (
    <dl className="grid gap-3 sm:grid-cols-2">
      {(Object.keys(CRITERIA_LABELS) as Array<keyof EvaluationCriteria>).map((key) => (
        <div key={key}>
          <div className="flex justify-between text-xs font-medium text-muted-foreground">
            <dt>{CRITERIA_LABELS[key]}</dt>
            <dd>{criteria[key]}/10</dd>
          </div>
          <div className="mt-1 h-2 overflow-hidden rounded-full bg-muted">
            <div
              className={`h-full rounded-full ${barColor(criteria[key])}`}
              style={{ width: `${criteria[key] * 10}%` }}
            />
          </div>
        </div>
      ))}
    </dl>
  );
}

function PointList({ title, items, tone }: { title: string; items: string[]; tone: "good" | "improve" }) {
  if (items.length === 0) return null;
  return (
    <div>
      <h4 className={`text-sm font-semibold ${tone === "good" ? "text-emerald-700" : "text-amber-700"}`}>
        {title}
      </h4>
      <ul className="mt-1 list-disc space-y-1 pl-5 text-sm text-card-foreground">
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  );
}

function AnswerCard({ item, position }: { item: AnswerEvaluation; position: number }) {
  const [showAnswer, setShowAnswer] = useState(false);

  return (
    <article className="rounded-2xl border border-border bg-card p-5 shadow-sm">
      <header className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs font-bold uppercase tracking-wider text-primary">Pergunta {position}</p>
          <h3 className="mt-1 font-semibold text-card-foreground">{item.question}</h3>
        </div>
        <p className={`shrink-0 text-2xl font-extrabold ${scoreColor(item.score)}`}>
          {number.format(item.score)}
        </p>
      </header>

      <button
        type="button"
        onClick={() => setShowAnswer((value) => !value)}
        className="mt-2 text-xs font-medium text-muted-foreground underline-offset-4 hover:text-foreground hover:underline"
      >
        {showAnswer ? "Esconder minha resposta" : "Ver minha resposta"}
      </button>
      {showAnswer && (
        <p className="mt-2 rounded-lg bg-muted px-3 py-2 text-sm text-foreground">{item.answer}</p>
      )}

      <div className="mt-4">
        <CriteriaBars criteria={item.criteria} />
      </div>

      <p className="mt-4 text-sm leading-relaxed text-card-foreground">{item.feedback}</p>

      <div className="mt-4 grid gap-4 sm:grid-cols-2">
        <PointList title="Pontos fortes" items={item.strengths} tone="good" />
        <PointList title="O que melhorar" items={item.improvements} tone="improve" />
      </div>
    </article>
  );
}

function InterviewResultPage() {
  const { session } = Route.useSearch();
  const [evaluation, setEvaluation] = useState<InterviewEvaluation | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  // O StrictMode roda o efeito duas vezes em dev; sem esta trava a avaliação
  // seria pedida duas vezes ao Gemini.
  const requested = useRef(false);

  const fetchEvaluation = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      setEvaluation(await loadEvaluation(session));
    } catch (err) {
      setError(getErrorMessage(err, "Não foi possível carregar a avaliação."));
    } finally {
      setIsLoading(false);
    }
  }, [session]);

  useEffect(() => {
    if (!session || requested.current) return;
    requested.current = true;
    void fetchEvaluation();
  }, [session, fetchEvaluation]);

  if (!session) {
    return (
      <main className="flex flex-1 flex-col items-center justify-center bg-background px-4 text-center">
        <h1 className="text-xl font-semibold text-foreground">Entrevista não informada</h1>
        <Link to="/home" className="mt-4 text-sm font-medium text-primary hover:underline">
          Voltar para o início
        </Link>
      </main>
    );
  }

  return (
    <main className="flex-1 bg-background">
      <section className="bg-primary text-primary-foreground">
        <div className="mx-auto max-w-4xl px-4 pb-10 pt-8 sm:px-8">
          <p className="text-sm font-bold uppercase tracking-wider text-highlight">Resultado da entrevista</p>
          <h1 className="mt-2 text-3xl font-extrabold tracking-tight">Avaliação das suas respostas</h1>
          <p className="mt-2 max-w-2xl text-primary-foreground/85">
            A IA avaliou cada resposta em relevância, coerência, completude e adequação, de 0 a 10.
          </p>
        </div>
      </section>

      <div className="mx-auto max-w-4xl px-4 py-8 sm:px-8">
        {isLoading && (
          <div className="flex flex-col items-center justify-center gap-4 py-16">
            <div className="h-10 w-10 animate-spin rounded-full border-2 border-primary/20 border-t-primary" />
            <p className="text-sm font-medium text-muted-foreground">A IA está avaliando suas respostas…</p>
          </div>
        )}

        {error && !isLoading && <ErrorState message={error} onRetry={() => void fetchEvaluation()} />}

        {evaluation && !isLoading && (
          <>
            <section className="flex flex-col gap-6 rounded-2xl border border-border bg-card p-6 shadow-sm sm:flex-row sm:items-center">
              <div className="text-center sm:w-40 sm:shrink-0">
                <p className={`text-5xl font-extrabold ${scoreColor(evaluation.overall_score)}`}>
                  {number.format(evaluation.overall_score)}
                </p>
                <p className="mt-1 text-sm font-semibold text-muted-foreground">
                  {scoreLabel(evaluation.overall_score)}
                </p>
              </div>
              <div className="sm:border-l sm:border-border sm:pl-6">
                <h2 className="text-base font-semibold text-card-foreground">Resumo geral</h2>
                <p className="mt-1 text-sm leading-relaxed text-card-foreground">{evaluation.summary}</p>
              </div>
            </section>

            <div className="mt-6 space-y-4">
              {evaluation.answers.map((item, index) => (
                <AnswerCard key={item.order_index} item={item} position={index + 1} />
              ))}
            </div>
          </>
        )}

        <nav className="mt-8 flex flex-wrap justify-center gap-3">
          <Link
            to="/home"
            className="rounded-xl border border-border bg-card px-5 py-2.5 text-sm font-semibold text-foreground hover:border-primary/40"
          >
            Voltar para o início
          </Link>
          <Link
            to="/interview/setup"
            className="rounded-xl bg-highlight px-5 py-2.5 text-sm font-bold text-highlight-foreground hover:bg-highlight/90"
          >
            Fazer outra entrevista
          </Link>
        </nav>
      </div>
    </main>
  );
}
