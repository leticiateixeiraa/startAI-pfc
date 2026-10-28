import { createFileRoute, Link } from "@tanstack/react-router";
import { useState, type FormEvent } from "react";
import { esqueciSenha } from "../services/authService";
import { getErrorMessage } from "../services/api";

export const Route = createFileRoute("/forgot-password")({
  component: PaginaEsqueciSenha,
});

function PaginaEsqueciSenha() {
  const [email, setEmail] = useState("");
  const [mensagem, setMensagem] = useState<string | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  async function aoEnviar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    setErro(null);
    setEnviando(true);
    try {
      const dados = await esqueciSenha(email);
      setMensagem(dados.message);
    } catch (erroRequisicao) {
      setErro(getErrorMessage(erroRequisicao, "Não foi possível processar o pedido agora."));
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
        <h1 className="text-2xl font-bold tracking-tight text-foreground">Esqueceu sua senha?</h1>
        <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
          Digite seu e-mail e enviaremos um link para redefinir sua senha.
        </p>

        {mensagem ? (
          <p className="mt-6 text-sm text-foreground">{mensagem}</p>
        ) : (
          <>
            <label className="mt-6 flex flex-col gap-1.5 text-sm font-medium text-card-foreground">
              E-mail
              <input
                type="email"
                required
                value={email}
                onChange={(evento) => setEmail(evento.target.value)}
                className="rounded-lg border border-input bg-background px-3 py-2.5 font-normal text-foreground outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
              />
            </label>

            {erro && <p className="mt-4 text-sm text-destructive" role="alert">{erro}</p>}

            <button
              type="submit"
              disabled={enviando}
              className="mt-6 w-full rounded-lg bg-primary px-4 py-3 text-sm font-semibold text-primary-foreground transition-colors hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {enviando ? "Enviando..." : "Enviar link"}
            </button>
          </>
        )}

        <p className="mt-6 text-center text-sm text-muted-foreground">
          <Link to="/" className="font-medium text-primary hover:underline">
            Voltar para o login
          </Link>
        </p>
      </form>
    </main>
  );
}