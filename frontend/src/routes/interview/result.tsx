// feat(evaluation): tela de resultado da entrevista, com nota e feedback da IA.
import { createFileRoute, Link, redirect } from "@tanstack/react-router";
import { useCallback, useEffect, useRef, useState } from "react";
import { ErrorState } from "@/components/interview/ErrorState";
import { CompetencyRadar, ScoreBars } from "@/components/profile/ProfileCharts";
import { getErrorMessage } from "@/services/api";
import { seniorityLabel } from "@/types/interview";
import {
  CRITERIA_LABELS,
  loadEvaluation,
  scoreLabel,
  type AnswerEvaluation,
  type BehavioralProfile,
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

const TONE_CLASS = {
  good: "text-emerald-700",
  improve: "text-amber-700",
  error: "text-destructive",
} as const;

function PointList({ title, items, tone }: { title: string; items: string[]; tone: keyof typeof TONE_CLASS }) {
  if (items.length === 0) return null;
  return (
    <div>
      <h4 className={`text-sm font-semibold ${TONE_CLASS[tone]}`}>{title}</h4>
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
  const [showSuggestion, setShowSuggestion] = useState(false);

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

      {/* feat(feedback): erros concretos no que foi dito e exemplo de resposta melhor */}
      {item.mistakes.length > 0 && (
        <div className="mt-4 rounded-xl border border-destructive/25 bg-destructive/5 p-4">
          <PointList title="Erros e pontos de atenção no que você disse" items={item.mistakes} tone="error" />
        </div>
      )}

      {item.suggested_answer && (
        <div className="mt-4">
          <button
            type="button"
            onClick={() => setShowSuggestion((value) => !value)}
            aria-expanded={showSuggestion}
            className="text-sm font-semibold text-primary underline-offset-4 hover:underline"
          >
            {showSuggestion ? "Esconder exemplo de resposta" : "Ver como você poderia responder"}
          </button>
          {showSuggestion && (
            <div className="mt-2 rounded-lg border-l-4 border-primary bg-secondary/60 px-4 py-3">
              <p className="text-sm leading-relaxed text-foreground">{item.suggested_answer}</p>
              <p className="mt-2 text-xs text-muted-foreground">
                Os trechos entre colchetes são informações que você pode completar com a sua experiência.
              </p>
            </div>
          )}
        </div>
      )}
    </article>
  );
}

// feat(behavioral): perfil traçado a partir desta entrevista comportamental.
function BehavioralProfileSection({ profile }: { profile: BehavioralProfile }) {
  return (
    <section className="mt-6 rounded-2xl border border-border bg-card p-6 shadow-sm">
      <p className="text-xs font-bold uppercase tracking-wider text-primary">Seu perfil comportamental</p>
      <h2 className="mt-1 text-2xl font-extrabold tracking-tight text-card-foreground">{profile.archetype.name}</h2>
      <p className="mt-1 text-sm text-muted-foreground">{profile.archetype.description}</p>
      <p className="mt-3 text-sm leading-relaxed text-card-foreground">{profile.description}</p>

      <div className="mt-6">
        <h3 className="mb-2 text-sm font-semibold text-card-foreground">Competências demonstradas</h3>
        <CompetencyRadar items={profile.competencies} />
      </div>

      <div className="mt-6 border-t border-border pt-6">
        <h3 className="text-sm font-semibold text-card-foreground">Uso do método STAR</h3>
        <p className="mb-3 mt-1 text-xs text-muted-foreground">
          O quanto suas respostas deixaram claros a situação, a tarefa, a sua ação e o resultado.
        </p>
        <ScoreBars items={profile.star} max={10} suffix="/10" />
      </div>

      <Link to="/perfil" className="mt-6 inline-block text-sm font-semibold text-primary hover:underline">
        Ver meu perfil completo e a evolução →
      </Link>
    </section>
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
            A IA avaliou cada resposta em relevância, coerência, completude e adequação, de 0 a 10, e
            apontou o que você fez bem, os erros e como melhorar.
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
                {evaluation.seniority && (
                  <p className="mt-2 inline-block rounded-full bg-secondary px-2.5 py-1 text-xs font-bold text-secondary-foreground">
                    Avaliada para o nível {seniorityLabel(evaluation.seniority)}
                  </p>
                )}
              </div>
              <div className="sm:border-l sm:border-border sm:pl-6">
                <h2 className="text-base font-semibold text-card-foreground">Resumo geral</h2>
                <p className="mt-1 text-sm leading-relaxed text-card-foreground">{evaluation.summary}</p>
              </div>
            </section>

            {(evaluation.highlights.length > 0 || evaluation.next_steps.length > 0) && (
              <section className="mt-4 grid gap-4 rounded-2xl border border-border bg-card p-6 shadow-sm sm:grid-cols-2">
                <PointList title="O que você fez bem" items={evaluation.highlights} tone="good" />
                <PointList title="Prioridades para a próxima entrevista" items={evaluation.next_steps} tone="improve" />
              </section>
            )}

            {evaluation.behavioral_profile && <BehavioralProfileSection profile={evaluation.behavioral_profile} />}

            <h2 className="mt-8 text-lg font-bold text-foreground">Feedback de cada resposta</h2>
            <div className="mt-3 space-y-4">
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
