// feat(roadmap-ia): trilha de estudos em linha do tempo, com dicas, recursos
// (sites do catálogo e buscas de vídeo) e progresso marcado pelo aluno.
import {
  BookOpen,
  CheckCircle2,
  Circle,
  Clock,
  Dumbbell,
  ExternalLink,
  Globe,
  GraduationCap,
  Lightbulb,
  PlayCircle,
  Target,
  type LucideIcon,
} from "lucide-react";
import { useState } from "react";
import {
  roadmapProgress,
  updateRoadmapItemStatus,
  type Roadmap,
  type RoadmapItem,
  type RoadmapResource,
  type RoadmapResourceType,
} from "@/services/roadmapApi";

const RESOURCE_TYPES: Record<RoadmapResourceType, { label: string; icon: LucideIcon }> = {
  video: { label: "Vídeo", icon: PlayCircle },
  pratica: { label: "Prática", icon: Dumbbell },
  curso: { label: "Curso", icon: GraduationCap },
  documentacao: { label: "Documentação", icon: BookOpen },
  site: { label: "Site", icon: Globe },
};

function ResourceLink({ resource }: { resource: RoadmapResource }) {
  const type = RESOURCE_TYPES[resource.type] ?? RESOURCE_TYPES.site;
  const Icon = type.icon;
  return (
    <a
      href={resource.url}
      target="_blank"
      rel="noopener noreferrer"
      className="group flex items-start gap-3 rounded-xl border border-border bg-background p-3 transition-colors hover:border-primary/40"
    >
      <span className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-secondary text-primary">
        <Icon className="size-4" aria-hidden />
      </span>
      <span className="min-w-0 flex-1">
        <span className="flex items-center gap-1.5 text-sm font-semibold text-foreground group-hover:text-primary">
          <span className="truncate">{resource.title}</span>
          <ExternalLink className="size-3.5 shrink-0 opacity-60" aria-hidden />
        </span>
        <span className="block text-xs text-muted-foreground">
          {type.label}
          {resource.description ? ` · ${resource.description}` : ""}
        </span>
      </span>
    </a>
  );
}

function RoadmapStep({
  item,
  position,
  isLastStep,
  onToggle,
  isSaving,
}: {
  item: RoadmapItem;
  position: number;
  isLastStep: boolean;
  onToggle: () => void;
  isSaving: boolean;
}) {
  const done = item.status === "completed";
  return (
    <li className="relative flex gap-4">
      {/* Linha do tempo: número da etapa e conector até a próxima */}
      <div className="flex flex-col items-center">
        <span
          className={`z-10 flex size-9 shrink-0 items-center justify-center rounded-full text-sm font-bold ${
            done ? "bg-emerald-600 text-white" : "bg-primary text-primary-foreground"
          }`}
        >
          {done ? <CheckCircle2 className="size-5" aria-hidden /> : position}
        </span>
        {!isLastStep && <span className="w-0.5 flex-1 bg-border" aria-hidden />}
      </div>

      <article className={`mb-6 min-w-0 flex-1 rounded-2xl border bg-card p-5 shadow-sm ${done ? "border-emerald-500/40" : "border-border"}`}>
        <header className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0">
            <h4 className={`text-base font-bold text-card-foreground ${done ? "line-through decoration-1 opacity-70" : ""}`}>
              {item.title}
            </h4>
            {item.estimated_time && (
              <p className="mt-1 flex items-center gap-1 text-xs font-medium text-muted-foreground">
                <Clock className="size-3.5" aria-hidden /> {item.estimated_time}
              </p>
            )}
          </div>
          <button
            type="button"
            onClick={onToggle}
            disabled={isSaving}
            aria-pressed={done}
            className={`inline-flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-semibold transition-colors disabled:opacity-50 ${
              done
                ? "border-emerald-500/40 bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10"
                : "border-border text-foreground hover:border-primary/40"
            }`}
          >
            {done ? <CheckCircle2 className="size-4" aria-hidden /> : <Circle className="size-4" aria-hidden />}
            {done ? "Concluída" : "Marcar como concluída"}
          </button>
        </header>

        {item.focus && (
          <p className="mt-3 flex gap-2 rounded-lg bg-secondary/60 px-3 py-2 text-xs text-secondary-foreground">
            <Target className="mt-0.5 size-3.5 shrink-0" aria-hidden />
            <span>
              <strong>Por que esta etapa:</strong> {item.focus}
            </span>
          </p>
        )}

        {item.description && <p className="mt-3 text-sm leading-relaxed text-card-foreground">{item.description}</p>}

        {item.tips.length > 0 && (
          <div className="mt-4">
            <h5 className="flex items-center gap-1.5 text-sm font-semibold text-card-foreground">
              <Lightbulb className="size-4 text-highlight" aria-hidden /> Dicas
            </h5>
            <ul className="mt-1 list-disc space-y-1 pl-5 text-sm text-card-foreground">
              {item.tips.map((tip) => (
                <li key={tip}>{tip}</li>
              ))}
            </ul>
          </div>
        )}

        {item.practice && (
          <div className="mt-4 rounded-lg border-l-4 border-highlight bg-highlight/10 px-4 py-3">
            <h5 className="text-sm font-semibold text-foreground">Exercício prático</h5>
            <p className="mt-1 text-sm leading-relaxed text-foreground">{item.practice}</p>
          </div>
        )}

        {item.resources.length > 0 && (
          <div className="mt-4">
            <h5 className="text-sm font-semibold text-card-foreground">Onde estudar e treinar</h5>
            <div className="mt-2 grid gap-2 sm:grid-cols-2">
              {item.resources.map((resource) => (
                <ResourceLink key={resource.url} resource={resource} />
              ))}
            </div>
          </div>
        )}
      </article>
    </li>
  );
}

export function RoadmapView({ roadmap: initial }: { roadmap: Roadmap }) {
  const [roadmap, setRoadmap] = useState(initial);
  const [savingId, setSavingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const progress = roadmapProgress(roadmap);

  async function toggle(item: RoadmapItem) {
    setSavingId(item.id);
    setError(null);
    try {
      setRoadmap(
        await updateRoadmapItemStatus(roadmap.id, item.id, item.status === "completed" ? "pending" : "completed"),
      );
    } catch {
      setError("Não foi possível salvar o progresso. Tente novamente.");
    } finally {
      setSavingId(null);
    }
  }

  return (
    <div>
      <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
        <h3 className="text-xl font-extrabold tracking-tight text-card-foreground">{roadmap.title}</h3>
        {roadmap.objective && (
          <p className="mt-1 text-sm font-medium text-primary">Objetivo: {roadmap.objective}</p>
        )}
        {roadmap.summary && <p className="mt-2 text-sm leading-relaxed text-card-foreground">{roadmap.summary}</p>}

        <div className="mt-4">
          <div className="flex justify-between text-xs font-semibold text-muted-foreground">
            <span>
              {progress.done} de {progress.total} etapas concluídas
            </span>
            <span>{progress.percent}%</span>
          </div>
          <div
            className="mt-1 h-2 overflow-hidden rounded-full bg-muted"
            role="progressbar"
            aria-valuenow={progress.percent}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-label="Progresso da trilha"
          >
            <div className="h-full rounded-full bg-emerald-500 transition-all" style={{ width: `${progress.percent}%` }} />
          </div>
        </div>
        {error && (
          <p className="mt-3 text-sm text-destructive" role="alert">
            {error}
          </p>
        )}
      </div>

      <ol className="mt-6">
        {roadmap.items.map((item, index) => (
          <RoadmapStep
            key={item.id}
            item={item}
            position={index + 1}
            isLastStep={index === roadmap.items.length - 1}
            onToggle={() => void toggle(item)}
            isSaving={savingId === item.id}
          />
        ))}
      </ol>

      <p className="text-xs text-muted-foreground">
        Os sites vêm de uma lista conferida pela equipe do StartAI. Os vídeos abrem uma busca no YouTube com o
        tema da etapa, para você escolher o que preferir.
      </p>
    </div>
  );
}
