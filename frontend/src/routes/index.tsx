import { createFileRoute, Link, redirect, useNavigate } from "@tanstack/react-router";
import { useState, type FormEvent } from "react";
import { entrar } from "../services/authService";
import { getErrorMessage } from "../services/api";
import { FormField } from "../components/form/FormField";
import { validateEmail } from "../lib/validation";

export const Route = createFileRoute("/")({
  beforeLoad: () => {
    if (localStorage.getItem("access_token")) {
      throw redirect({ to: "/home" });
    }
  },
  component: LoginPage,
});

function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<{ email?: string; password?: string }>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    const errors = {
      email: validateEmail(email) ?? undefined,
      password: password ? undefined : "Informe sua senha.",
    };
    setFieldErrors(errors);
    if (errors.email || errors.password) return;

    setIsSubmitting(true);
    try {
      await entrar({ email: email.trim(), password });
      navigate({ to: "/home" });
    } catch (requestError: any) {
      setError(getErrorMessage(requestError, "E-mail ou senha inválidos."));
      setIsSubmitting(false);
    }
  }

  return (
    <main className="flex flex-1 items-center justify-center bg-background px-4 py-12">
      <form
        onSubmit={handleSubmit}
        noValidate
        className="w-full max-w-md rounded-2xl border border-border bg-card p-7 shadow-sm sm:p-9"
      >
        <h1 className="text-3xl font-bold tracking-tight text-foreground">Bem-vindo de volta</h1>
        <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
          Entre para preparar sua próxima entrevista simulada.
        </p>

        <div className="mt-8 flex flex-col gap-5">
          <FormField
            label="E-mail"
            type="email"
            autoComplete="email"
            value={email}
            error={fieldErrors.email}
            onChange={(event) => setEmail(event.target.value)}
          />
          <FormField
            label="Senha"
            type="password"
            autoComplete="current-password"
            value={password}
            error={fieldErrors.password}
            onChange={(event) => setPassword(event.target.value)}
          />
        </div>

        <p className="mt-3 text-right text-sm">
          <Link to="/forgot-password" className="font-medium text-primary hover:underline">
            Esqueci minha senha
          </Link>
        </p>

        {error && <p className="mt-5 text-sm text-destructive" role="alert">{error}</p>}

        <button
          type="submit"
          disabled={isSubmitting}
          className="mt-7 w-full rounded-lg bg-primary px-4 py-3 text-sm font-semibold text-primary-foreground transition-colors hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isSubmitting ? "Entrando..." : "Entrar"}
        </button>

        <p className="mt-6 text-center text-sm text-muted-foreground">
          Ainda não tem conta?{" "}
          <Link to="/register" className="font-medium text-primary hover:underline">
            Criar conta
          </Link>
        </p>
      </form>
    </main>
  );
}
