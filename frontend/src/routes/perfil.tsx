// feat(behavioral): página "Meu perfil" — área de interesse (questionário de
// primeiro acesso) e perfil comportamental consolidado, com gráficos.
import { createFileRoute, Link, redirect } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { ErrorState } from "@/components/interview/ErrorState";
import {
  CompetencyRadar,
  EvolutionChart,
  ScoreBars,
  formatScore,
} from "@/components/profile/ProfileCharts";
import { ResumeSection } from "@/components/profile/ResumeSection";
import { getOnboardingStatus, type OnboardingStatus } from "@/services/onboardingApi";
import { getBehavioralProfile, type ConsolidatedProfile } from "@/services/profileApi";
import { listRoadmaps, roadmapProgress, type Roadmap } from "@/services/roadmapApi";

export const Route = createFileRoute("/perfil")({
  beforeLoad: () => {
    if (!localStorage.getItem("access_token")) {
      throw redirect({ to: "/" });
    }
  },
  head: () => ({
    meta: [
      { title: "Meu perfil — StartAI" },
      {
        name: "description",
        content: "Veja sua área de interesse na tecnologia e o perfil comportamental traçado nas entrevistas.",
      },
    ],
  }),
  component: ProfilePage,
});

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-border bg-card p-4 shadow-sm">
      <p className="text-xs font-medium text-muted-foreground">{label}</p>
      <p className="mt-1 text-lg font-extrabold tracking-tight text-card-foreground">{value}</p>
    </div>
  );
}

function Card({ title, description, children }: { title: string; description?: string; children: React.ReactNode }) {
  return (
    <section className="rounded-2xl border border-border bg-card p-6 shadow-sm">
      <h3 className="text-base font-semibold text-card-foreground">{title}</h3>
      {description && <p className="mt-1 text-xs text-muted-foreground">{description}</p>}
      <div className="mt-4">{children}</div>
    </section>
  );
}

function CareerAreaSection({ onboarding }: { onboarding: OnboardingStatus }) {
  const result = onboarding.result;
  return (
    <section className="rounded-2xl border border-border bg-card p-6 shadow-sm">
      <p className="text-xs font-bold uppercase tracking-wider text-primary">Área de interesse</p>
      {result ? (
        <>
          <h2 className="mt-1 text-xl font-extrabold tracking-tight text-card-foreground">
            {result.recommended_area.name}
          </h2>
          <p className="mt-1 text-sm leading-relaxed text-muted-foreground">{result.recommended_area.description}</p>
          <div className="mt-4 flex flex-wrap gap-4">
            <Link to="/onboarding" className="text-sm font-semibold text-primary hover:underline">
              Ver resultado completo ou refazer
            </Link>
            <Link
              to="/interview/setup"
              search={{ cargo: result.recommended_area.suggested_job_title }}
              className="text-sm font-semibold text-primary hover:underline"
            >
              Treinar entrevista para essa área
            </Link>
          </div>
        </>
      ) : (
        <>
          <h2 className="mt-1 text-xl font-extrabold tracking-tight text-card-foreground">
            Descubra qual área combina com você
          </h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Um questionário rápido, de menos de 2 minutos, indica a área da tecnologia com mais afinidade.
          </p>
          <Link
            to="/onboarding"
            className="mt-4 inline-flex rounded-xl bg-highlight px-5 py-2.5 text-sm font-bold text-highlight-foreground hover:bg-highlight/90"
          >
            Responder questionário
          </Link>
        </>
      )}
    </section>
  );
}

function BehavioralSection({ profile }: { profile: ConsolidatedProfile }) {
  if (profile.interviews_count === 0 || !profile.archetype) {
    return (
      <section className="rounded-2xl border-2 border-dashed border-primary/25 bg-card px-6 py-12 text-center">
        <h2 className="text-lg font-semibold text-foreground">Seu perfil comportamental aparece aqui</h2>
        <p className="mx-auto mt-2 max-w-md text-sm leading-relaxed text-muted-foreground">
          Faça uma entrevista do tipo <strong>Comportamental</strong> e veja a avaliação: a IA traça suas
          competências e o uso do método STAR, e esta página junta todas as entrevistas.
        </p>
        <Link
          to="/interview/setup"
          className="mt-6 inline-flex rounded-xl bg-highlight px-5 py-2.5 text-sm font-bold text-highlight-foreground hover:bg-highlight/90"
        >
          Fazer entrevista comportamental
        </Link>
      </section>
    );
  }

  const labelOf = (key: string | null) =>
    profile.competencies.find((item) => item.key === key)?.label ?? "—";
  const weakestStar = profile.star.reduce((weakest, item) => (item.score < weakest.score ? item : weakest));
  const evolution = profile.history.map((item, index) => {
    const values = Object.values(item.competencies);
    return {
      label: `${index + 1}ª`,
      competencias: Number((values.reduce((sum, value) => sum + value, 0) / values.length).toFixed(1)),
      nota: item.overall_score,
    };
  });

  return (
    <div className="space-y-6">
      <section className="rounded-2xl border border-border bg-card p-6 shadow-sm">
        <p className="text-xs font-bold uppercase tracking-wider text-primary">Perfil comportamental</p>
        <h2 className="mt-1 text-2xl font-extrabold tracking-tight text-card-foreground">{profile.archetype.name}</h2>
        <p className="mt-1 text-sm text-muted-foreground">{profile.archetype.description}</p>
        {profile.latest_description && (
          <p className="mt-3 text-sm leading-relaxed text-card-foreground">
            <span className="font-semibold">Na sua última entrevista: </span>
            {profile.latest_description}
          </p>
        )}
        <div className="mt-5 grid gap-3 sm:grid-cols-3">
          <StatCard label="Entrevistas comportamentais" value={String(profile.interviews_count)} />
          <StatCard label="Ponto mais forte" value={labelOf(profile.strongest)} />
          <StatCard label="Para desenvolver" value={labelOf(profile.weakest)} />
        </div>
      </section>

      <Card
        title="Competências"
        description={`Média de 0 a 10 em ${profile.interviews_count} ${
          profile.interviews_count === 1 ? "entrevista" : "entrevistas"
        }.`}
      >
        <CompetencyRadar items={profile.competencies} />
      </Card>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card title="Uso do método STAR" description="Situação, tarefa, ação e resultado nas suas respostas.">
          <ScoreBars items={profile.star} max={10} suffix="/10" />
          <p className="mt-4 text-xs text-muted-foreground">
            Parte mais fraca: <strong className="text-foreground">{weakestStar.label}</strong> (
            {formatScore(weakestStar.score)}/10). Dê mais atenção a ela nas próximas histórias.
          </p>
        </Card>

        <Card title="Sua evolução" description="Entrevista a entrevista, na ordem em que foram feitas.">
          {evolution.length < 2 ? (
            <p className="text-sm text-muted-foreground">
              Faça mais uma entrevista comportamental para ver o gráfico de evolução.
            </p>
          ) : (
            <EvolutionChart data={evolution} />
          )}
        </Card>
      </div>
    </div>
  );
}

// feat(roadmap-ia): trilhas de estudo geradas nas entrevistas, com o progresso.
function RoadmapsSection({ roadmaps }: { roadmaps: Roadmap[] }) {
  const generated = roadmaps.filter((roadmap) => roadmap.session_id);
  return (
    <section className="rounded-2xl border border-border bg-card p-6 shadow-sm">
      <p className="text-xs font-bold uppercase tracking-wider text-primary">Trilhas de estudo</p>
      {generated.length === 0 ? (
        <p className="mt-2 text-sm text-muted-foreground">
          Ao ver a avaliação de uma entrevista, o StartAI monta uma trilha de estudos para você. Ela aparece aqui.
        </p>
      ) : (
        <ul className="mt-3 divide-y divide-border">
          {generated.map((roadmap) => {
            const progress = roadmapProgress(roadmap);
            return (
              <li key={roadmap.id} className="flex flex-wrap items-center justify-between gap-3 py-3">
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-semibold text-card-foreground">{roadmap.title}</p>
                  <div className="mt-1.5 flex items-center gap-2">
                    <div className="h-1.5 w-32 overflow-hidden rounded-full bg-muted">
                      <div className="h-full rounded-full bg-emerald-500" style={{ width: `${progress.percent}%` }} />
                    </div>
                    <span className="text-xs text-muted-foreground">
                      {progress.done}/{progress.total} etapas
                    </span>
                  </div>
                </div>
                <Link
                  to="/interview/result"
                  search={{ session: roadmap.session_id ?? "" }}
                  hash="trilha"
                  className="text-sm font-semibold text-primary hover:underline"
                >
                  Abrir trilha
                </Link>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}

function ProfilePage() {
  const [onboarding, setOnboarding] = useState<OnboardingStatus | null>(null);
  const [profile, setProfile] = useState<ConsolidatedProfile | null>(null);
  const [roadmaps, setRoadmaps] = useState<Roadmap[]>([]);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setError(null);
    try {
      const [status, behavioral, trilhas] = await Promise.all([
        getOnboardingStatus(),
        getBehavioralProfile(),
        listRoadmaps(),
      ]);
      setOnboarding(status);
      setProfile(behavioral);
      setRoadmaps(trilhas);
    } catch {
      setError("Não foi possível carregar seu perfil.");
    }
  }

  useEffect(() => {
    void load();
  }, []);

  return (
    <main className="flex-1 bg-background">
      <section className="bg-primary text-primary-foreground">
        <div className="mx-auto max-w-5xl px-4 pb-10 pt-8 sm:px-8">
          <p className="text-sm font-bold uppercase tracking-wider text-highlight">Meu perfil</p>
          <h1 className="mt-2 text-3xl font-extrabold tracking-tight">Quem você é nas entrevistas</h1>
          <p className="mt-2 max-w-2xl text-primary-foreground/85">
            Sua área de interesse na tecnologia e o perfil comportamental traçado a partir das suas respostas.
          </p>
        </div>
      </section>

      <div className="mx-auto max-w-5xl space-y-6 px-4 py-8 sm:px-8">
        {error && <ErrorState message={error} onRetry={() => void load()} />}
        {!error && (!onboarding || !profile) && (
          <div className="flex justify-center py-16">
            <div className="h-10 w-10 animate-spin rounded-full border-2 border-primary/20 border-t-primary" />
          </div>
        )}
        {onboarding && profile && (
          <>
            <CareerAreaSection onboarding={onboarding} />
            <ResumeSection suggestedRole={onboarding.result?.recommended_area.suggested_job_title} />
            <RoadmapsSection roadmaps={roadmaps} />
            <BehavioralSection profile={profile} />
          </>
        )}
      </div>
    </main>
  );
}
