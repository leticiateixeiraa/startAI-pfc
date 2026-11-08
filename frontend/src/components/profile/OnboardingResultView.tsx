// feat(onboarding): resultado do questionário de área (tela do questionário e Meu perfil).
import { Link } from "@tanstack/react-router";
import { ScoreBars } from "@/components/profile/ProfileCharts";
import type { OnboardingResult } from "@/services/onboardingApi";

export function OnboardingResultView({
  result,
  onRestart,
}: {
  result: OnboardingResult;
  onRestart?: () => void;
}) {
  const area = result.recommended_area;
  const top = result.ranking.filter((item) => item.percent > 0).slice(0, 5);

  return (
    <div className="space-y-6">
      <section className="rounded-2xl border border-border bg-card p-6 shadow-sm sm:p-8">
        <p className="text-xs font-bold uppercase tracking-wider text-primary">Área com mais afinidade</p>
        <h2 className="mt-1 text-2xl font-extrabold tracking-tight text-card-foreground">{area.name}</h2>
        <p className="mt-2 text-sm leading-relaxed text-card-foreground">{area.description}</p>

        <div className="mt-6 grid gap-6 sm:grid-cols-2">
          <div>
            <h3 className="text-sm font-semibold text-card-foreground">Cargos comuns</h3>
            <ul className="mt-1 list-disc space-y-1 pl-5 text-sm text-card-foreground">
              {area.roles.map((role) => (
                <li key={role}>{role}</li>
              ))}
            </ul>
          </div>
          <div>
            <h3 className="text-sm font-semibold text-card-foreground">Por onde começar a estudar</h3>
            <ul className="mt-1 list-disc space-y-1 pl-5 text-sm text-card-foreground">
              {area.skills.map((skill) => (
                <li key={skill}>{skill}</li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      <section className="rounded-2xl border border-border bg-card p-6 shadow-sm sm:p-8">
        <h3 className="text-base font-semibold text-card-foreground">Sua afinidade com cada área</h3>
        <p className="mb-4 mt-1 text-xs text-muted-foreground">
          Porcentagem dos pontos das suas respostas que foi para cada área.
        </p>
        <ScoreBars
          items={top.map((item) => ({ key: item.key, label: item.name, score: item.percent }))}
          max={100}
          suffix="%"
        />
      </section>

      <nav className="flex flex-wrap justify-center gap-3">
        <Link
          to="/interview/setup"
          search={{ cargo: area.suggested_job_title }}
          className="rounded-xl bg-highlight px-5 py-2.5 text-sm font-bold text-highlight-foreground hover:bg-highlight/90"
        >
          Treinar entrevista para {area.suggested_job_title}
        </Link>
        <Link
          to="/home"
          className="rounded-xl border border-border bg-card px-5 py-2.5 text-sm font-semibold text-foreground hover:border-primary/40"
        >
          Ir para o início
        </Link>
        {onRestart && (
          <button
            type="button"
            onClick={onRestart}
            className="rounded-xl px-5 py-2.5 text-sm font-semibold text-muted-foreground hover:text-foreground"
          >
            Refazer questionário
          </button>
        )}
      </nav>
    </div>
  );
}
