import { createFileRoute, Link, redirect } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { getCurrentUser, type CurrentUser } from "../services/authService";
import {
  listInterviewHistory,
  type InterviewHistoryItem,
} from "../services/interviewHistoryApi";
import { presentationTypeLabel } from "../types/interview";

export const Route = createFileRoute("/home")({
  beforeLoad: () => {
    if (!localStorage.getItem("access_token")) {
      throw redirect({ to: "/" });
    }
  },
  head: () => ({
    meta: [
      { title: "Início — StartAI" },
      {
        name: "description",
        content: "Veja suas entrevistas anteriores e comece uma nova simulação.",
      },
    ],
  }),
  component: HomePage,
});

const categoryLabels: Record<string, string> = {
  entrevista_de_emprego: "Entrevista de emprego",
  apresentacao_academica: "Apresentação acadêmica",
};

function HomePage() {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [interviews, setInterviews] = useState<InterviewHistoryItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadHome() {
      try {
        const [currentUser, history] = await Promise.all([
          getCurrentUser(),
          listInterviewHistory(),
        ]);
        setUser(currentUser);
        setInterviews(history);
      } catch {
        setError("Não foi possível carregar seu histórico.");
      } finally {
        setIsLoading(false);
      }
    }

    void loadHome();
  }, []);

  const firstName = user?.name?.trim().split(" ")[0] || "estudante";

  return (
    <main className="flex-1 bg-background">
      {/* Faixa de boas-vindas em roxo, continuando o cabeçalho */}
      <section className="bg-primary text-primary-foreground">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-6 px-4 pb-10 pt-8 sm:px-8 sm:pb-12">
          <div>
            <p className="text-sm font-bold uppercase tracking-wider text-highlight">Seu espaço de treino</p>
            <h1 className="mt-2 text-3xl font-extrabold tracking-tight sm:text-4xl">
              Olá, {firstName}!
            </h1>
            <p className="mt-2 max-w-xl text-base text-primary-foreground/85">
              Continue praticando ou comece uma nova simulação com perguntas geradas por IA.
            </p>
          </div>
          <Link
            to="/interview/setup"
            className="rounded-xl bg-highlight px-5 py-3 text-base font-bold text-highlight-foreground shadow-sm transition-transform hover:-translate-y-0.5 hover:bg-highlight/90"
          >
            Começar nova entrevista
          </Link>
        </div>
      </section>

      <div className="mx-auto max-w-6xl px-4 pb-12 sm:px-8">
        <section className="pt-10">
          <div className="flex items-end justify-between gap-4">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wider text-primary">Seu percurso</p>
              <h2 className="mt-2 text-2xl font-extrabold tracking-tight text-foreground">
                Entrevistas anteriores
              </h2>
            </div>
            {!isLoading && interviews.length > 0 && (
              <span className="text-sm text-muted-foreground">
                {interviews.length} {interviews.length === 1 ? "sessão" : "sessões"}
              </span>
            )}
          </div>

          {isLoading && (
            <div className="mt-6 rounded-xl border border-border bg-card p-8 text-sm text-muted-foreground">
              Carregando seu histórico...
            </div>
          )}

          {error && !isLoading && (
            <div className="mt-6 rounded-xl border border-destructive/30 bg-card p-8 text-sm text-destructive">
              {error}
            </div>
          )}

          {!isLoading && !error && interviews.length === 0 && (
            <div className="mt-6 rounded-2xl border-2 border-dashed border-primary/25 bg-card px-6 py-12 text-center">
              <h3 className="text-lg font-semibold text-foreground">Sua primeira prática começa aqui</h3>
              <p className="mx-auto mt-2 max-w-md text-sm leading-relaxed text-muted-foreground">
                Faça uma entrevista simulada e acompanhe suas sessões nesta página.
              </p>
              <Link
                to="/interview/setup"
                className="mt-6 inline-flex rounded-xl bg-highlight px-5 py-2.5 text-sm font-bold text-highlight-foreground hover:bg-highlight/90"
              >
                Começar agora
              </Link>
            </div>
          )}

          {!isLoading && !error && interviews.length > 0 && (
            <div className="mt-6 grid gap-4 md:grid-cols-2">
              {interviews.map((interview) => (
                <article
                  key={interview.session_id}
                  className="rounded-2xl border border-border bg-card p-5 shadow-sm transition-all hover:-translate-y-0.5 hover:border-primary/40 hover:shadow-md"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <p className="inline-block rounded-full bg-secondary px-2.5 py-1 text-xs font-bold text-secondary-foreground">
                        {categoryLabels[interview.category] ?? interview.category}
                      </p>
                      <h3 className="mt-2 text-lg font-semibold text-card-foreground">
                        {interview.presentation_type
                          ? presentationTypeLabel(interview.presentation_type)
                          : "Entrevista simulada"}
                      </h3>
                    </div>
                    <span
                      className={`rounded-full px-2.5 py-1 text-xs font-semibold ${
                        interview.finished
                          ? "bg-emerald-100 text-emerald-700"
                          : "bg-amber-100 text-amber-700"
                      }`}
                    >
                      {interview.finished ? "Concluída" : "Em andamento"}
                    </span>
                  </div>
                  <div className="mt-6 flex items-center justify-between border-t border-border pt-4 text-sm text-muted-foreground">
                    <span>{interview.answered_count} respostas registradas</span>
                    <time dateTime={interview.created_at}>
                      {new Date(interview.created_at).toLocaleDateString("pt-BR")}
                    </time>
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
