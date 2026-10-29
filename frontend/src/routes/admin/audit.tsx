// feat(admin): auditoria de todos os usuários, com filtros.
// O próprio acesso a esta tela fica registrado no back-end (admin.audit_viewed).
import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useMemo, useState, type FormEvent } from "react";
import { AdminLayout, ErrorBox, LoadingBox } from "@/components/admin/AdminLayout";
import { requireAdminBeforeLoad } from "@/components/admin/adminGuard";
import { getErrorMessage } from "@/services/api";
import { listAdminAuditLogs, listAdminUsers, type AdminAuditFilters, type AdminUser } from "@/services/adminApi";
import type { AuditLog } from "@/services/auditApi";

export const Route = createFileRoute("/admin/audit")({
  beforeLoad: requireAdminBeforeLoad,
  head: () => ({ meta: [{ title: "Auditoria geral — Administração StartAI" }] }),
  component: AdminAuditPage,
});

const ACTION_LABELS: Record<string, string> = {
  "auth.registered": "Conta criada",
  "lgpd.consent_accepted": "Termos aceitos (LGPD)",
  "auth.login": "Login realizado",
  "auth.login_failed": "Login com falha",
  "auth.login_blocked": "Login de conta desativada",
  "auth.password_reset_requested": "Redefinição de senha solicitada",
  "auth.password_reset_completed": "Senha redefinida",
  "interview.started": "Entrevista iniciada",
  "interview.answer_submitted": "Resposta enviada",
  "roadmap.created": "Roadmap criado",
  "roadmap.item_updated": "Etapa atualizada",
  "admin.user_blocked": "Conta desativada pelo admin",
  "admin.user_unblocked": "Conta reativada pelo admin",
  "admin.role_granted": "Papel de admin concedido",
  "admin.role_revoked": "Papel de admin removido",
  "admin.audit_viewed": "Auditoria geral consultada",
};

const EMPTY_FILTERS: AdminAuditFilters = { user_id: "", action: "", date_from: "", date_to: "" };

function AdminAuditPage() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [filters, setFilters] = useState<AdminAuditFilters>(EMPTY_FILTERS);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const emailById = useMemo(() => new Map(users.map((user) => [user.id, user.email])), [users]);

  async function load(current = filters) {
    if (current.date_from && current.date_to && current.date_from > current.date_to) {
      setError("A data inicial não pode ser depois da data final.");
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      setLogs(await listAdminAuditLogs({ ...current, limit: 200 }));
    } catch (err) {
      setError(getErrorMessage(err, "Não foi possível carregar a auditoria."));
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void load(EMPTY_FILTERS);
    listAdminUsers().then(setUsers).catch(() => setUsers([]));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function update(field: keyof AdminAuditFilters, value: string) {
    setFilters((current) => ({ ...current, [field]: value }));
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    void load();
  }

  function clear() {
    setFilters(EMPTY_FILTERS);
    void load(EMPTY_FILTERS);
  }

  const fieldClass =
    "w-full rounded-lg border border-input bg-background px-3 py-2 text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/20";

  return (
    <AdminLayout
      title="Auditoria geral"
      description="Eventos de todos os usuários. Senhas e conteúdo das respostas nunca são registrados."
    >
      <form onSubmit={handleSubmit} className="mb-4 grid gap-3 rounded-xl border border-border bg-card p-4 sm:grid-cols-2 lg:grid-cols-5">
        <label className="text-xs font-semibold text-muted-foreground">
          Usuário
          <select value={filters.user_id} onChange={(e) => update("user_id", e.target.value)} className={`mt-1 ${fieldClass}`}>
            <option value="">Todos</option>
            {users.map((user) => (
              <option key={user.id} value={user.id}>
                {user.email}
              </option>
            ))}
          </select>
        </label>
        <label className="text-xs font-semibold text-muted-foreground">
          Ação
          <select value={filters.action} onChange={(e) => update("action", e.target.value)} className={`mt-1 ${fieldClass}`}>
            <option value="">Todas</option>
            {Object.entries(ACTION_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </label>
        <label className="text-xs font-semibold text-muted-foreground">
          De
          <input type="date" value={filters.date_from} onChange={(e) => update("date_from", e.target.value)} className={`mt-1 ${fieldClass}`} />
        </label>
        <label className="text-xs font-semibold text-muted-foreground">
          Até
          <input type="date" value={filters.date_to} onChange={(e) => update("date_to", e.target.value)} className={`mt-1 ${fieldClass}`} />
        </label>
        <div className="flex items-end gap-2">
          <button type="submit" className="flex-1 rounded-lg bg-primary px-3 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90">
            Filtrar
          </button>
          <button type="button" onClick={clear} className="rounded-lg border border-border px-3 py-2 text-sm font-medium hover:bg-accent">
            Limpar
          </button>
        </div>
      </form>

      {error && <ErrorBox message={error} onRetry={() => void load()} />}
      {!error && isLoading && <LoadingBox text="Carregando registros..." />}
      {!error && !isLoading && logs.length === 0 && <LoadingBox text="Nenhum registro encontrado." />}
      {!error && !isLoading && logs.length > 0 && (
        <div className="overflow-x-auto rounded-xl border border-border bg-card shadow-sm">
          <table className="w-full min-w-[720px] text-left text-sm">
            <thead className="border-b border-border bg-muted/50 text-xs uppercase tracking-wide text-muted-foreground">
              <tr>
                <th className="px-4 py-3 font-semibold">Data e hora</th>
                <th className="px-4 py-3 font-semibold">Ação</th>
                <th className="px-4 py-3 font-semibold">Usuário</th>
                <th className="px-4 py-3 font-semibold">IP</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {logs.map((log) => (
                <tr key={log.id}>
                  <td className="whitespace-nowrap px-4 py-3 text-muted-foreground">
                    {new Date(log.created_at).toLocaleString("pt-BR")}
                  </td>
                  <td className="px-4 py-3">
                    <p className="font-medium text-card-foreground">{ACTION_LABELS[log.action] ?? log.action}</p>
                    <code className="text-xs text-muted-foreground">{log.action}</code>
                  </td>
                  <td className="px-4 py-3">
                    {log.user_id ? emailById.get(log.user_id) ?? log.user_id : <span className="text-muted-foreground">Sistema / não identificado</span>}
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">{log.ip_address ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </AdminLayout>
  );
}
