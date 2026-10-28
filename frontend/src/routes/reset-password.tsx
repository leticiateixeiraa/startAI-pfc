import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState, type FormEvent } from "react";
import { redefinirSenha } from "../services/authService";
import { getErrorMessage } from "../services/api";
import { FormField, PasswordRequirements } from "../components/form/FormField";
import { validatePassword, validatePasswordConfirmation } from "../lib/validation";

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
  const [confirmacao, setConfirmacao] = useState("");
  const [errosCampos, setErrosCampos] = useState<{ senha?: string; confirmacao?: string }>({});
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

    // Mesmas regras de senha do cadastro (RN04 do RF03).
    const erroSenha = validatePassword(senha);
    const erroConfirmacao = validatePasswordConfirmation(senha, confirmacao);
    setErrosCampos({ senha: erroSenha ?? undefined, confirmacao: erroConfirmacao ?? undefined });
    if (erroSenha || erroConfirmacao) return;

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
        noValidate
        className="w-full max-w-md rounded-2xl border border-border bg-card p-7 shadow-sm sm:p-9"
      >
        <h1 className="text-2xl font-bold tracking-tight text-foreground">Nova senha</h1>

        {sucesso ? (
          <p className="mt-6 text-sm text-foreground">
            Senha redefinida! Levando você para o login...
          </p>
        ) : (
          <>
            <div className="mt-6 flex flex-col gap-5">
              <FormField
                label="Nova senha"
                type="password"
                autoComplete="new-password"
                value={senha}
                error={errosCampos.senha}
                onChange={(evento) => setSenha(evento.target.value)}
              />
              <PasswordRequirements password={senha} />
              <FormField
                label="Confirme a nova senha"
                type="password"
                autoComplete="new-password"
                value={confirmacao}
                error={errosCampos.confirmacao}
                onChange={(evento) => setConfirmacao(evento.target.value)}
              />
            </div>

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