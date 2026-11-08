// feat(jobs-frontend): página de vagas recomendadas a partir do perfil do aluno.
import { createFileRoute, Link, redirect } from "@tanstack/react-router";
import { useCallback, useEffect, useState } from "react";
import { ErrorState } from "@/components/interview/ErrorState";
import { getErrorMessage } from "@/services/api";
import { getJobRecommendations, type Job, type JobRecommendations } from "@/services/jobsApi";

export const Route = createFileRoute("/vagas")({
  beforeLoad: () => {
    if (!localStorage.getItem("access_token")) {
      throw redirect({ to: "/" });
    }
  },
  head: () => ({
    meta: [
      { title: "Vagas para você — StartAI" },
      {
        name: "description",
        content: "Vagas reais compatíveis com o cargo que você treinou e com o seu desempenho nas entrevistas.",
      },
    ],
  }),
  component: JobsPage,
});

const money = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 });
const score = new Intl.NumberFormat("pt-BR", { minimumFractionDigits: 1, maximumFractionDigits: 1 });

function formatSalary(job: Job) {
  if (job.salary_min && job.salary_max && job.salary_max !== job.salary_min) {
    return `${money.format(job.salary_min)} a ${money.format(job.salary_max)}`;
  }
  const value = job.salary_min ?? job.salary_max;
  return value ? money.format(value) : null;
}

function formatDate(value: string | null) {
  return value ? new Date(value).toLocaleDateString("pt-BR") : null;
}

// Verde (alta), laranja (média) ou cinza (baixa), igual às notas do resultado.
function compatibilityStyle(value: number) {
  if (value >= 70) return "bg-emerald-50 text-emerald-700 border-emerald-200";
  if (value >= 40) return "bg-amber-50 text-amber-700 border-amber-200";
  return "bg-muted text-muted-foreground border-border";
}

function JobCard({ job }: { job: Job }) {
  const salary = formatSalary(job);
  const posted = formatDate(job.posted_at);
  return (
    <article className="flex flex-col gap-3 rounded-2xl border border-border bg-card p-5 shadow-sm sm:flex-row sm:items-start sm:justify-between">
      <div className="min-w-0 flex-1">
        <h3 className="font-semibold text-card-foreground">{job.title}</h3>
        <p className="mt-0.5 text-sm text-muted-foreground">
          {[job.company, job.location].filter(Boolean).join(" · ") || "Empresa não informada"}
        </p>
        {(salary || posted) && (
          <p className="mt-1 text-xs text-muted-foreground">
            {[salary, posted && `publicada em ${posted}`].filter(Boolean).join(" · ")}
          </p>
        )}
        {job.description && (
          <p className="mt-3 line-clamp-3 text-sm leading-relaxed text-card-foreground">{job.description}</p>
        )}
        {job.reasons.length > 0 && (
          <ul className="mt-3 space-y-1 text-xs text-muted-foreground">
            {job.reasons.map((reason) => (
              <li key={reason} className="flex gap-1.5">
                <span aria-hidden className="text-primary">✓</span>
                {reason}
              </li>
            ))}
          </ul>
        )}
      </div>
      <div className="flex shrink-0 flex-row items-center gap-3 sm:flex-col sm:items-end">
        <span
          className={`rounded-full border px-3 py-1 text-sm font-bold ${compatibilityStyle(job.compatibility)}`}
          title="Compatibilidade com o seu perfil"
        >
          {job.compatibility}% compatível
        </span>
        <a
          href={job.url}
          target="_blank"
          rel="noopener noreferrer"
          className="rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90"
        >
          Ver vaga
        </a>
      </div>
    </article>
  );
}

function JobsPage() {
  const [data, setData] = useState<JobRecommendations | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const load = useCallback(async (refresh = false) => {
    if (refresh) setIsRefreshing(true);
    else setIsLoading(true);
    setError(null);
    try {
      setData(await getJobRecommendations(refresh));
    } catch (err) {
      setError(getErrorMessage(err, "Não foi possível carregar as vagas."));
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const profile = data?.profile;

  return (
    <main className="flex-1 bg-background">
      <section className="bg-primary text-primary-foreground">
        <div className="mx-auto max-w-4xl px-4 pb-10 pt-8 sm:px-8">
          <p className="text-sm font-bold uppercase tracking-wider text-highlight">Vagas para você</p>
          <h1 className="mt-2 text-3xl font-extrabold tracking-tight">Oportunidades compatíveis com o seu perfil</h1>
          <p className="mt-2 max-w-2xl text-primary-foreground/85">
            Vagas reais publicadas no último mês, escolhidas pelo cargo que você treinou e pelo seu desempenho nas
            entrevistas. A candidatura é feita no site de cada vaga.
          </p>
        </div>
      </section>

      <div className="mx-auto max-w-4xl space-y-6 px-4 py-8 sm:px-8">
        {isLoading && (
          <div className="flex flex-col items-center justify-center gap-4 py-16">
            <div className="h-10 w-10 animate-spin rounded-full border-2 border-primary/20 border-t-primary" />
            <p className="text-sm font-medium text-muted-foreground">Buscando vagas para o seu perfil…</p>
          </div>
        )}

        {error && !isLoading && <ErrorState message={error} onRetry={() => void load()} />}

        {data && !isLoading && !profile && (
          <section className="rounded-2xl border-2 border-dashed border-primary/25 bg-card px-6 py-12 text-center">
            <h2 className="text-lg font-semibold text-foreground">Suas vagas aparecem aqui</h2>
            <p className="mx-auto mt-2 max-w-md text-sm leading-relaxed text-muted-foreground">
              {data.message} Assim sabemos o cargo e o nível certos para você.
            </p>
            <div className="mt-6 flex flex-wrap justify-center gap-3">
              <Link
                to="/interview/setup"
                className="rounded-xl bg-highlight px-5 py-2.5 text-sm font-bold text-highlight-foreground hover:bg-highlight/90"
              >
                Fazer uma entrevista
              </Link>
              <Link
                to="/onboarding"
                className="rounded-xl border border-border bg-card px-5 py-2.5 text-sm font-semibold text-foreground hover:border-primary/40"
              >
                Responder questionário
              </Link>
            </div>
          </section>
        )}

        {data && !isLoading && profile && (
          <>
            <section className="rounded-2xl border border-border bg-card p-6 shadow-sm">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <p className="text-xs font-bold uppercase tracking-wider text-primary">Seu perfil</p>
                  <h2 className="mt-1 text-xl font-extrabold tracking-tight text-card-foreground">
                    {profile.job_title} · {profile.recommended_seniority_label}
                  </h2>
                  <p className="mt-1 text-sm text-muted-foreground">
                    {profile.source === "entrevistas"
                      ? `Cargo das suas entrevistas${
                          profile.interviews_count > 1 ? ` (${profile.interviews_count} entrevistas)` : ""
                        }`
                      : `Indicado pelo questionário: ${profile.area}`}
                  </p>
                </div>
                {profile.average_score !== null && (
                  <div className="sm:text-right">
                    <p className="text-xs font-medium text-muted-foreground">Nota média</p>
                    <p className="text-2xl font-extrabold text-card-foreground">{score.format(profile.average_score)}</p>
                  </div>
                )}
              </div>
              <p className="mt-4 rounded-lg bg-muted px-3 py-2 text-sm text-card-foreground">{profile.level_reason}</p>
              {profile.skills.length > 0 && (
                <div className="mt-4 flex flex-wrap gap-2">
                  {profile.skills.map((skill) => (
                    <span key={skill} className="rounded-full bg-primary/10 px-3 py-1 text-xs font-semibold text-primary">
                      {skill}
                    </span>
                  ))}
                </div>
              )}
            </section>

            {data.warning && (
              <p className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800" role="status">
                {data.warning}
              </p>
            )}

            <div className="flex flex-wrap items-center justify-between gap-3">
              <p className="text-sm text-muted-foreground">
                {data.jobs.length} {data.jobs.length === 1 ? "vaga encontrada" : "vagas encontradas"}
                {data.fetched_at && ` · atualizado em ${new Date(data.fetched_at).toLocaleString("pt-BR")}`}
              </p>
              <button
                type="button"
                onClick={() => void load(true)}
                disabled={isRefreshing}
                className="rounded-lg border border-border bg-card px-4 py-2 text-sm font-semibold text-foreground hover:border-primary/40 disabled:opacity-50"
              >
                {isRefreshing ? "Atualizando…" : "Atualizar vagas"}
              </button>
            </div>

            {data.jobs.length === 0 ? (
              <p className="rounded-2xl border border-border bg-card px-6 py-10 text-center text-sm text-muted-foreground">
                Nenhuma vaga publicada no último mês para esse cargo. Tente novamente mais tarde ou treine para
                outro cargo.
              </p>
            ) : (
              <div className="space-y-4">
                {data.jobs.map((job) => (
                  <JobCard key={job.id} job={job} />
                ))}
              </div>
            )}

            <p className="text-center text-xs text-muted-foreground">
              Vagas fornecidas pela{" "}
              <a href="https://br.jooble.org" target="_blank" rel="noopener noreferrer" className="underline">
                Jooble
              </a>
              . O StartAI não participa do processo seletivo.
            </p>
          </>
        )}
      </div>
    </main>
  );
}
