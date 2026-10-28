import { createFileRoute, Link, redirect } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { listAuditLogs, type AuditLog } from "../services/auditApi";

export const Route = createFileRoute("/audit")({
  beforeLoad: () => {
    if (!localStorage.getItem("access_token")) {
      throw redirect({ to: "/" });
    }
  },
  component: AuditPage,
});

const actionLabels: Record<string, string> = {
  "auth.registered": "Conta criada",
  "auth.login": "Login realizado",
  "interview.started": "Entrevista iniciada",
  "interview.answer_submitted": "Resposta enviada",
  "roadmap.created": "Roadmap criado",
  "roadmap.item_updated": "Etapa atualizada",
};

function AuditPage() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadLogs() {
    setIsLoading(true);
    setError(null);
    try {
      setLogs(await listAuditLogs());
    } catch {
      setError("Não foi possível carregar os registros de auditoria.");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadLogs();
  }, []);

  return (
    <main className="flex-1 bg-background px-4 py-10 sm:px-8">
      <div className="mx-auto max-w-5xl">
        <header className="mb-8 flex flex-wrap items-end justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-foreground">Auditoria da conta</h1>
            <p className="mt-2 text-sm text-muted-foreground">
              Acompanhe acessos e ações realizadas nas suas entrevistas e roadmaps.
            </p>
          </div>
          <div className="flex gap-3 text-sm">
            <Link
              to="/home"
              className="rounded-lg border border-border px-3 py-2 font-medium text-foreground hover:bg-accent"
            >
              Voltar para início
            </Link>
            <button
              type="button"
              onClick={() => void loadLogs()}
              className="rounded-lg border border-border px-3 py-2 font-medium text-foreground hover:bg-accent"
            >
              Atualizar
            </button>
            <Link
              to="/interview/setup"
              className="rounded-lg bg-primary px-3 py-2 font-medium text-primary-foreground hover:bg-primary/90"
            >
              Nova entrevista
            </Link>
          </div>
        </header>

        <section className="overflow-hidden rounded-xl border border-border bg-card shadow-sm">
          {isLoading && <p className="p-6 text-sm text-muted-foreground">Carregando registros...</p>}
          {error && (
            <div className="flex items-center justify-between gap-4 p-6 text-sm text-destructive">
              <span>{error}</span>
              <button type="button" onClick={() => void loadLogs()} className="font-semibold underline">
                Tentar novamente
              </button>
            </div>
          )}
          {!isLoading && !error && logs.length === 0 && (
            <p className="p-6 text-sm text-muted-foreground">Nenhum registro encontrado.</p>
          )}
          {!isLoading && !error && logs.length > 0 && (
            <div className="divide-y divide-border">
              {logs.map((log) => (
                <article key={log.id} className="flex flex-wrap items-center justify-between gap-3 p-5">
                  <div>
                    <p className="font-medium text-card-foreground">
                      {actionLabels[log.action] ?? log.action}
                    </p>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {new Date(log.created_at).toLocaleString("pt-BR")}
                      {log.resource_type ? ` • ${log.resource_type}` : ""}
                    </p>
                  </div>
                  <code className="max-w-full break-all rounded bg-muted px-2 py-1 text-xs text-muted-foreground">
                    {log.action}
                  </code>
                </article>
              ))}
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
