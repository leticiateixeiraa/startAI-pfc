// feat(lgpd): página "Minha conta", com os dados do usuário e a exclusão da conta.
import { createFileRoute, Link, redirect } from "@tanstack/react-router";
import { useEffect, useState, type FormEvent } from "react";
import { getErrorMessage } from "@/services/api";
import { excluirMinhaConta, getCurrentUser, type CurrentUser } from "@/services/authService";

export const Route = createFileRoute("/conta")({
  beforeLoad: () => {
    if (!localStorage.getItem("access_token")) {
      throw redirect({ to: "/" });
    }
  },
  head: () => ({ meta: [{ title: "Minha conta — StartAI" }] }),
  component: AccountPage,
});

// O que some e o que fica, igual à regra do backend (app/lgpd/service.py).
const APAGADOS = [
  "Seus dados de cadastro (nome, e-mail e senha)",
  "Todas as entrevistas, perguntas e respostas",
  "As avaliações da IA e as notas",
  "Trilhas de estudo e pedidos de redefinição de senha",
];

function AccountPage() {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [password, setPassword] = useState("");
  const [confirmed, setConfirmed] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [deleted, setDeleted] = useState(false);

  useEffect(() => {
    getCurrentUser()
      .then(setUser)
      .catch(() => setLoadError("Não foi possível carregar os seus dados."));
  }, []);

  async function handleDelete(event: FormEvent) {
    event.preventDefault();
    if (!password || !confirmed || isDeleting) return;
    setIsDeleting(true);
    setDeleteError(null);
    try {
      await excluirMinhaConta(password);
      setDeleted(true);
    } catch (err) {
      setDeleteError(getErrorMessage(err, "Não foi possível excluir a conta."));
    } finally {
      setIsDeleting(false);
    }
  }

  if (deleted) {
    return (
      <main className="flex flex-1 items-center justify-center bg-background px-4 py-12">
        <div className="w-full max-w-md rounded-2xl border border-border bg-card p-8 text-center shadow-sm">
          <h1 className="text-2xl font-bold tracking-tight text-foreground">Conta excluída</h1>
          <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
            Seus dados foram apagados do StartAI. Os registros de segurança foram mantidos sem
            nenhuma informação que identifique você.
          </p>
          {/* Recarrega a página para o cabeçalho voltar ao modo "deslogado". */}
          <a
            href="/"
            className="mt-6 inline-flex rounded-xl bg-primary px-5 py-2.5 text-sm font-semibold text-primary-foreground hover:bg-primary/90"
          >
            Ir para a página inicial
          </a>
        </div>
      </main>
    );
  }

  return (
    <main className="flex-1 bg-background px-4 py-10 sm:px-8">
      <div className="mx-auto max-w-2xl space-y-6">
        <header>
          <h1 className="text-3xl font-bold tracking-tight text-foreground">Minha conta</h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Seus dados e seus direitos sobre eles, conforme a{" "}
            <Link to="/privacidade" className="font-medium text-primary hover:underline">
              Política de Privacidade
            </Link>
            .
          </p>
        </header>

        <section className="rounded-2xl border border-border bg-card p-6 shadow-sm">
          <h2 className="text-base font-semibold text-card-foreground">Seus dados</h2>
          {loadError && <p className="mt-3 text-sm text-destructive">{loadError}</p>}
          {!loadError && !user && <p className="mt-3 text-sm text-muted-foreground">Carregando...</p>}
          {user && (
            <dl className="mt-4 grid gap-4 text-sm sm:grid-cols-2">
              <div>
                <dt className="text-muted-foreground">Nome</dt>
                <dd className="font-medium text-card-foreground">{user.name || "Não informado"}</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">E-mail</dt>
                <dd className="break-all font-medium text-card-foreground">{user.email}</dd>
              </div>
            </dl>
          )}
          <p className="mt-4 text-sm text-muted-foreground">
            O histórico de acessos e ações da sua conta fica em{" "}
            <Link to="/audit" className="font-medium text-primary hover:underline">
              Auditoria
            </Link>
            .
          </p>
        </section>

        <section className="rounded-2xl border border-destructive/40 bg-card p-6 shadow-sm">
          <h2 className="text-base font-semibold text-destructive">Excluir minha conta</h2>
          <p className="mt-2 text-sm text-card-foreground">
            A exclusão é <strong>definitiva</strong> e não pode ser desfeita. Serão apagados:
          </p>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-card-foreground">
            {APAGADOS.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
          <p className="mt-3 text-sm text-muted-foreground">
            Os registros de segurança (auditoria) são mantidos de forma anônima, sem vínculo com
            você nem endereço IP.
          </p>

          <form onSubmit={handleDelete} className="mt-5 flex flex-col gap-4">
            <label className="flex flex-col gap-1.5 text-sm font-medium text-card-foreground">
              Digite sua senha para confirmar
              <input
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                autoComplete="current-password"
                className="rounded-lg border border-input bg-background px-3 py-2.5 font-normal text-foreground outline-none focus:border-destructive focus:ring-2 focus:ring-destructive/20"
              />
            </label>
            <label className="flex items-start gap-2 text-sm text-card-foreground">
              <input
                type="checkbox"
                checked={confirmed}
                onChange={(event) => setConfirmed(event.target.checked)}
                className="mt-0.5 size-4 accent-[var(--destructive)]"
              />
              Entendo que meus dados serão apagados e que não será possível recuperá-los.
            </label>

            {deleteError && (
              <p className="text-sm text-destructive" role="alert">
                {deleteError}
              </p>
            )}

            <button
              type="submit"
              disabled={!password || !confirmed || isDeleting}
              className="self-start rounded-lg bg-destructive px-5 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-destructive/90 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isDeleting ? "Excluindo..." : "Excluir minha conta"}
            </button>
          </form>
        </section>
      </div>
    </main>
  );
}
