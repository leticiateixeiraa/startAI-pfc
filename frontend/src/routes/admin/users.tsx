// feat(admin): lista de usuários com busca e ativação/desativação de contas.
import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState, type FormEvent } from "react";
import { AdminLayout, ErrorBox, LoadingBox } from "@/components/admin/AdminLayout";
import { requireAdminBeforeLoad } from "@/components/admin/adminGuard";
import { getErrorMessage } from "@/services/api";
import { listAdminUsers, setUserActive, type AdminUser } from "@/services/adminApi";

export const Route = createFileRoute("/admin/users")({
  beforeLoad: requireAdminBeforeLoad,
  head: () => ({ meta: [{ title: "Usuários — Administração StartAI" }] }),
  component: AdminUsersPage,
});

function AdminUsersPage() {
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [search, setSearch] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [pendingId, setPendingId] = useState<string | null>(null);

  async function load(term = search) {
    setIsLoading(true);
    setError(null);
    try {
      setUsers(await listAdminUsers(term.trim() || undefined));
    } catch {
      setError("Não foi possível carregar os usuários.");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void load("");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function handleSearch(event: FormEvent) {
    event.preventDefault();
    void load();
  }

  async function toggle(user: AdminUser) {
    const verb = user.is_active ? "desativar" : "reativar";
    if (!window.confirm(`Deseja ${verb} a conta de ${user.email}?`)) return;
    setPendingId(user.id);
    setActionError(null);
    try {
      const updated = await setUserActive(user.id, !user.is_active);
      setUsers((current) => current.map((item) => (item.id === updated.id ? updated : item)));
    } catch (err) {
      setActionError(getErrorMessage(err, `Não foi possível ${verb} a conta.`));
    } finally {
      setPendingId(null);
    }
  }

  return (
    <AdminLayout
      title="Usuários"
      description="Contas cadastradas. Uma conta desativada perde o acesso na hora e não consegue entrar de novo."
    >
      <form onSubmit={handleSearch} className="mb-4 flex flex-wrap gap-2">
        <input
          type="search"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          maxLength={100}
          placeholder="Buscar por nome ou e-mail"
          className="min-w-0 flex-1 rounded-lg border border-input bg-background px-3 py-2 text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
        />
        <button type="submit" className="rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90">
          Buscar
        </button>
      </form>

      {actionError && <p className="mb-4 text-sm text-destructive">{actionError}</p>}
      {error && <ErrorBox message={error} onRetry={() => void load()} />}
      {!error && isLoading && <LoadingBox text="Carregando usuários..." />}
      {!error && !isLoading && users.length === 0 && <LoadingBox text="Nenhum usuário encontrado." />}
      {!error && !isLoading && users.length > 0 && (
        <div className="overflow-x-auto rounded-xl border border-border bg-card shadow-sm">
          <table className="w-full min-w-[720px] text-left text-sm">
            <thead className="border-b border-border bg-muted/50 text-xs uppercase tracking-wide text-muted-foreground">
              <tr>
                <th className="px-4 py-3 font-semibold">Usuário</th>
                <th className="px-4 py-3 font-semibold">Papel</th>
                <th className="px-4 py-3 font-semibold">Cadastro</th>
                <th className="px-4 py-3 text-right font-semibold">Entrevistas</th>
                <th className="px-4 py-3 font-semibold">Situação</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {users.map((user) => (
                <tr key={user.id}>
                  <td className="px-4 py-3">
                    <p className="font-medium text-card-foreground">{user.name || "Sem nome"}</p>
                    <p className="text-xs text-muted-foreground">{user.email}</p>
                  </td>
                  <td className="px-4 py-3">{user.role === "admin" ? "Administrador" : "Usuário"}</td>
                  <td className="px-4 py-3 text-muted-foreground">
                    {user.created_at ? new Date(user.created_at).toLocaleDateString("pt-BR") : "—"}
                  </td>
                  <td className="px-4 py-3 text-right tabular-nums">{user.interview_count}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`rounded-full px-2.5 py-1 text-xs font-semibold ${
                        user.is_active ? "bg-primary/10 text-primary" : "bg-destructive/10 text-destructive"
                      }`}
                    >
                      {user.is_active ? "Ativa" : "Desativada"}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    {user.role !== "admin" && (
                      <button
                        type="button"
                        disabled={pendingId === user.id}
                        onClick={() => void toggle(user)}
                        className="rounded-lg border border-border px-3 py-1.5 text-xs font-semibold text-foreground hover:bg-accent disabled:opacity-50"
                      >
                        {user.is_active ? "Desativar" : "Reativar"}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </AdminLayout>
  );
}
