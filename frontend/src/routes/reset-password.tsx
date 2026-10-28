import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState, type FormEvent } from "react";
import { redefinirSenha } from "../services/authService";
import { getErrorMessage } from "../services/api";

export const Route = createFileRoute("/reset-password")({
  validateSearch: (busca: Record<string, unknown>) => ({
    token: typeof busca.token === "string" ? busca.token : "",
  }),
  component: PaginaRedefinirSenha,
});

function PaginaRedefinirSenha() {
  const { token } = Route.useSearch();
  const navegar = useNavigate();
  const [senha, setSenha] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [sucesso, setSucesso] = useState(false);
  const [enviando, setEnviando] = useState(false);

  async function aoEnviar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    setErro(null);

    if (!token) {
      setErro("Link inválido. Solicite uma nova redefinição.");
      return;
    }

    setEnviando(true);
    try {
      await redefinirSenha(token, senha);
      setSucesso(true);
      setTimeout(() => navegar({ to: "/" }), 2500);
    } catch (erroRequisicao) {
      setErro(getErrorMessage(erroRequisicao, "Não foi possível redefinir a senha."));
    } finally {
      setEnviando(false);
    }
  }

  return (
    <main className="flex flex-1 items-center justify-center bg-background px-4 py-12">
      <form
        onSubmit={aoEnviar}
        className="w-full max-w-md rounded-2xl border border-border bg-card p-7 shadow-sm sm:p-9"
      >
        <h1 className="text-2xl font-bold tracking-tight text-foreground">Nova senha</h1>

        {sucesso ? (
          <p className="mt-6 text-sm text-foreground">
            Senha redefinida! Levando você para o login...
          </p>
        ) : (
          <>
            <label className="mt-6 flex flex-col gap-1.5 text-sm font-medium text-card-foreground">
              Nova senha
              <input
                type="password"
                required
                minLength={8}
                value={senha}
                onChange={(evento) => setSenha(evento.target.value)}
                className="rounded-lg border border-input bg-background px-3 py-2.5 font-normal text-foreground outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
              />
            </label>

            {erro && <p className="mt-4 text-sm text-destructive" role="alert">{erro}</p>}

            <button
              type="submit"
              disabled={enviando}
              className="mt-6 w-full rounded-lg bg-primary px-4 py-3 text-sm font-semibold text-primary-foreground transition-colors hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {enviando ? "Salvando..." : "Redefinir senha"}
            </button>
          </>
        )}
      </form>
    </main>
  );
}