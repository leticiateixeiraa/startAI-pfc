// feat(roadmap-ia): seção da tela de resultado que carrega (ou gera, na
// primeira visita) a trilha de estudos da entrevista.
import { useCallback, useEffect, useRef, useState } from "react";
import { ErrorState } from "@/components/interview/ErrorState";
import { RoadmapView } from "@/components/roadmap/RoadmapView";
import { getErrorMessage } from "@/services/api";
import { loadInterviewRoadmap, type Roadmap } from "@/services/roadmapApi";

export function InterviewRoadmapSection({ sessionId }: { sessionId: string }) {
  const [roadmap, setRoadmap] = useState<Roadmap | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  // Mesma trava da avaliação: no StrictMode o efeito roda duas vezes em dev.
  const requested = useRef(false);

  const fetchRoadmap = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      setRoadmap(await loadInterviewRoadmap(sessionId));
    } catch (err) {
      setError(getErrorMessage(err, "Não foi possível montar sua trilha de estudos."));
    } finally {
      setIsLoading(false);
    }
  }, [sessionId]);

  useEffect(() => {
    if (requested.current) return;
    requested.current = true;
    void fetchRoadmap();
  }, [fetchRoadmap]);

  return (
    <section id="trilha" className="mt-10 scroll-mt-24">
      <p className="text-xs font-bold uppercase tracking-wider text-primary">Próximos passos</p>
      <h2 className="mt-1 text-2xl font-extrabold tracking-tight text-foreground">Sua trilha de estudos</h2>
      <p className="mt-1 text-sm text-muted-foreground">
        Um plano montado a partir desta entrevista para você chegar pronto à vaga: o que estudar, dicas,
        sites para treinar e vídeos. Marque as etapas conforme for concluindo.
      </p>

      <div className="mt-5">
        {isLoading && (
          <div className="flex flex-col items-center justify-center gap-4 rounded-2xl border border-border bg-card py-12">
            <div className="h-10 w-10 animate-spin rounded-full border-2 border-primary/20 border-t-primary" />
            <p className="text-sm font-medium text-muted-foreground">Montando sua trilha de estudos…</p>
          </div>
        )}
        {error && !isLoading && <ErrorState message={error} onRetry={() => void fetchRoadmap()} />}
        {roadmap && !isLoading && <RoadmapView roadmap={roadmap} />}
      </div>
    </section>
  );
}
