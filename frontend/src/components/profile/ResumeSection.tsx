// feat(resume): seção "Currículo" da página Meu perfil. O aluno anexa o
// currículo (PDF ou DOCX) e a IA devolve nota, pontos fortes e melhorias.
import { Link } from "@tanstack/react-router";
import { FileText, Loader2, Upload } from "lucide-react";
import { useEffect, useState } from "react";
import { ScoreBars, formatScore } from "@/components/profile/ProfileCharts";
import { getErrorMessage } from "@/services/api";
import {
  RESUME_MAX_BYTES,
  analyzeResume,
  deleteResumeAnalysis,
  getResumeAnalysis,
  type ResumeAnalysis,
} from "@/services/resumeApi";

function validateFile(file: File): string | null {
  if (!/\.(pdf|docx)$/i.test(file.name)) return "Envie o currículo em PDF ou DOCX.";
  if (file.size > RESUME_MAX_BYTES) return "O arquivo é grande demais. O limite é de 5 MB.";
  if (file.size === 0) return "O arquivo está vazio.";
  return null;
}

function Chips({ items, tone }: { items: string[]; tone: "found" | "missing" }) {
  const style =
    tone === "found"
      ? "bg-emerald-500/10 text-emerald-700 dark:text-emerald-400"
      : "bg-amber-500/10 text-amber-700 dark:text-amber-400";
  return (
    <ul className="mt-2 flex flex-wrap gap-2">
      {items.map((item) => (
        <li key={item} className={`rounded-full px-3 py-1 text-xs font-medium ${style}`}>
          {item}
        </li>
      ))}
    </ul>
  );
}

function AnalysisView({ analysis }: { analysis: ResumeAnalysis }) {
  const role = analysis.target_role ?? analysis.suggested_job_title;
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center gap-5">
        <div className="flex h-20 w-20 shrink-0 flex-col items-center justify-center rounded-2xl bg-primary text-primary-foreground">
          <span className="text-2xl font-extrabold tabular-nums">{formatScore(analysis.overall_score)}</span>
          <span className="text-[10px] font-semibold uppercase tracking-wider opacity-80">de 10</span>
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-sm leading-relaxed text-card-foreground">{analysis.summary}</p>
          <p className="mt-1 text-xs text-muted-foreground">
            {analysis.file_name} · analisado em {new Date(analysis.analyzed_at).toLocaleDateString("pt-BR")}
            {analysis.target_role ? ` · vaga alvo: ${analysis.target_role}` : ""}
          </p>
        </div>
      </div>

      {analysis.criteria.length > 0 && (
        <ScoreBars items={analysis.criteria} max={10} suffix="/10" />
      )}

      <div className="grid gap-6 md:grid-cols-2">
        {analysis.strengths.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold text-card-foreground">O que está bom</h3>
            <ul className="mt-2 space-y-2">
              {analysis.strengths.map((item) => (
                <li key={item} className="flex gap-2 text-sm text-muted-foreground">
                  <span className="mt-0.5 text-emerald-600" aria-hidden>
                    ✓
                  </span>
                  {item}
                </li>
              ))}
            </ul>
          </div>
        )}
        {analysis.skills_found.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold text-card-foreground">Habilidades encontradas</h3>
            <Chips items={analysis.skills_found} tone="found" />
          </div>
        )}
      </div>

      {analysis.improvements.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-card-foreground">Como melhorar</h3>
          <ol className="mt-2 space-y-3">
            {analysis.improvements.map((item, index) => (
              <li key={item.title} className="rounded-xl border border-border bg-background p-4">
                <p className="text-sm font-semibold text-card-foreground">
                  {index + 1}. {item.title}
                </p>
                <p className="mt-1 text-sm leading-relaxed text-muted-foreground">{item.suggestion}</p>
              </li>
            ))}
          </ol>
        </div>
      )}

      {analysis.skills_missing.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-card-foreground">
            Habilidades que a vaga costuma pedir e não aparecem
          </h3>
          <Chips items={analysis.skills_missing} tone="missing" />
        </div>
      )}

      {role && (
        <Link
          to="/interview/setup"
          search={{ cargo: role }}
          className="inline-flex text-sm font-semibold text-primary hover:underline"
        >
          Treinar entrevista para {role}
        </Link>
      )}
    </div>
  );
}

export function ResumeSection({ suggestedRole }: { suggestedRole?: string }) {
  const [analysis, setAnalysis] = useState<ResumeAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [showUploader, setShowUploader] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [role, setRole] = useState(suggestedRole ?? "");
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getResumeAnalysis()
      .then(setAnalysis)
      .catch(() => setError("Não foi possível carregar a análise do seu currículo."))
      .finally(() => setLoading(false));
  }, []);

  function handleFileChange(event: React.ChangeEvent<HTMLInputElement>) {
    const chosen = event.target.files?.[0] ?? null;
    event.target.value = ""; // permite escolher o mesmo arquivo de novo
    if (!chosen) return;
    const problem = validateFile(chosen);
    setError(problem);
    setFile(problem ? null : chosen);
  }

  async function handleAnalyze() {
    if (!file) return;
    setAnalyzing(true);
    setError(null);
    try {
      setAnalysis(await analyzeResume(file, role));
      setFile(null);
      setShowUploader(false);
    } catch (err) {
      setError(getErrorMessage(err, "Não foi possível analisar o currículo. Tente de novo."));
    } finally {
      setAnalyzing(false);
    }
  }

  async function handleDelete() {
    if (!window.confirm("Excluir a análise do seu currículo?")) return;
    try {
      await deleteResumeAnalysis();
      setAnalysis(null);
      setShowUploader(false);
    } catch (err) {
      setError(getErrorMessage(err, "Não foi possível excluir a análise."));
    }
  }

  const uploaderVisible = !loading && (!analysis || showUploader);

  return (
    <section className="rounded-2xl border border-border bg-card p-6 shadow-sm">
      <p className="text-xs font-bold uppercase tracking-wider text-primary">Currículo</p>

      {loading && <p className="mt-2 text-sm text-muted-foreground">Carregando...</p>}

      {!loading && !analysis && (
        <>
          <h2 className="mt-1 text-xl font-extrabold tracking-tight text-card-foreground">
            Veja como a IA avalia o seu currículo
          </h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Anexe o currículo e receba uma nota, os pontos fortes e o que melhorar antes de enviar para as vagas.
          </p>
        </>
      )}

      {!loading && analysis && (
        <div className="mt-3">
          <AnalysisView analysis={analysis} />
          {!showUploader && (
            <div className="mt-5 flex flex-wrap gap-4 border-t border-border pt-4">
              <button
                type="button"
                onClick={() => setShowUploader(true)}
                className="text-sm font-semibold text-primary hover:underline"
              >
                Analisar outro currículo
              </button>
              <button
                type="button"
                onClick={() => void handleDelete()}
                className="text-sm text-muted-foreground underline-offset-4 hover:text-destructive hover:underline"
              >
                Excluir análise
              </button>
            </div>
          )}
        </div>
      )}

      {uploaderVisible && (
        <div className="mt-4 space-y-3 rounded-xl border-2 border-dashed border-primary/25 p-4">
          <div className="flex flex-wrap items-center gap-3">
            <label className="inline-flex cursor-pointer items-center gap-2 rounded-lg border border-input bg-card px-4 py-2 text-sm font-medium text-card-foreground transition-colors hover:bg-accent">
              <Upload className="h-4 w-4" aria-hidden />
              {file ? "Trocar arquivo" : "Escolher arquivo (PDF ou DOCX)"}
              <input
                type="file"
                accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                onChange={handleFileChange}
                disabled={analyzing}
                className="sr-only"
              />
            </label>
            {file && (
              <span className="inline-flex min-w-0 items-center gap-2 text-sm text-card-foreground">
                <FileText className="h-4 w-4 shrink-0" aria-hidden />
                <span className="truncate">{file.name}</span>
              </span>
            )}
          </div>

          <label className="block text-xs font-medium text-muted-foreground">
            Vaga alvo (opcional)
            <input
              type="text"
              value={role}
              onChange={(event) => setRole(event.target.value)}
              maxLength={120}
              disabled={analyzing}
              placeholder="Ex.: Desenvolvedor Back-end Júnior"
              className="mt-1 block w-full rounded-lg border border-input bg-background px-3 py-2 text-sm text-foreground"
            />
          </label>

          <div className="flex flex-wrap items-center gap-3">
            <button
              type="button"
              onClick={() => void handleAnalyze()}
              disabled={!file || analyzing}
              className="inline-flex items-center gap-2 rounded-xl bg-highlight px-5 py-2.5 text-sm font-bold text-highlight-foreground hover:bg-highlight/90 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {analyzing && <Loader2 className="h-4 w-4 animate-spin" aria-hidden />}
              {analyzing ? "Analisando..." : "Analisar com IA"}
            </button>
            {analysis && !analyzing && (
              <button
                type="button"
                onClick={() => {
                  setShowUploader(false);
                  setFile(null);
                  setError(null);
                }}
                className="text-sm text-muted-foreground hover:text-foreground"
              >
                Cancelar
              </button>
            )}
            {analyzing && <span className="text-xs text-muted-foreground">Pode levar até 30 segundos.</span>}
          </div>

          <p className="text-xs text-muted-foreground">
            O arquivo é enviado ao Google Gemini só para a análise e não fica guardado: o StartAI salva apenas o
            resultado, que você pode excluir quando quiser.
          </p>
        </div>
      )}

      {error && (
        <p className="mt-3 text-sm text-destructive" role="alert">
          {error}
        </p>
      )}
    </section>
  );
}
