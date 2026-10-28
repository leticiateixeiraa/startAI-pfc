import { createFileRoute, Link, redirect, useNavigate } from "@tanstack/react-router";
import { useState, type FormEvent } from "react";
import { CURRENT_TERMS_VERSION, entrar, cadastrar } from "../services/authService";
import { getErrorMessage } from "../services/api";
import { FormField, PasswordRequirements } from "../components/form/FormField";
import {
  validateEmail,
  validateName,
  validatePassword,
  validatePasswordConfirmation,
} from "../lib/validation";

export const Route = createFileRoute("/register")({
  beforeLoad: () => {
    if (localStorage.getItem("access_token")) {
      throw redirect({ to: "/home" });
    }
  },
  component: RegisterPage,
});

type Field = "name" | "email" | "password" | "confirmation" | "terms";
type FieldErrors = Partial<Record<Field, string>>;

function RegisterPage() {
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [termsAccepted, setTermsAccepted] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Mesmas regras do backend (app/auth/schemas.py), centralizadas em lib/validation.
  function validate(values = { name, email, password, confirmation, termsAccepted }): FieldErrors {
    const errors: FieldErrors = {};
    const nameError = validateName(values.name);
    const emailError = validateEmail(values.email);
    const passwordError = validatePassword(values.password);
    const confirmationError = validatePasswordConfirmation(values.password, values.confirmation);
    if (nameError) errors.name = nameError;
    if (emailError) errors.email = emailError;
    if (passwordError) errors.password = passwordError;
    if (confirmationError) errors.confirmation = confirmationError;
    if (!values.termsAccepted) {
      errors.terms = "Você precisa aceitar o Termo de Uso e a Política de Privacidade para continuar.";
    }
    return errors;
  }

  // Depois da primeira tentativa de envio, os erros se atualizam enquanto a pessoa corrige.
  function update(changes: Partial<{ name: string; email: string; password: string; confirmation: string; termsAccepted: boolean }>) {
    const values = { name, email, password, confirmation, termsAccepted, ...changes };
    if (changes.name !== undefined) setName(changes.name);
    if (changes.email !== undefined) setEmail(changes.email);
    if (changes.password !== undefined) setPassword(changes.password);
    if (changes.confirmation !== undefined) setConfirmation(changes.confirmation);
    if (changes.termsAccepted !== undefined) setTermsAccepted(changes.termsAccepted);
    if (submitted) setFieldErrors(validate(values));
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSubmitted(true);

    const errors = validate();
    setFieldErrors(errors);
    if (Object.keys(errors).length > 0) return;

    setIsSubmitting(true);
    const cleanEmail = email.trim();
    try {
      await cadastrar({
        name: name.trim().replace(/\s+/g, " "),
        email: cleanEmail,
        password,
        terms_accepted: termsAccepted,
        terms_version: CURRENT_TERMS_VERSION,
      });
      await entrar({ email: cleanEmail, password });
      navigate({ to: "/home" });
    } catch (requestError: any) {
      setError(getErrorMessage(requestError, "Não foi possível criar a conta."));
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
        <h1 className="text-3xl font-bold tracking-tight text-foreground">Crie sua conta</h1>
        <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
          Comece a praticar sua comunicação com entrevistas simuladas.
        </p>

        <div className="mt-8 flex flex-col gap-5">
          <FormField
            label="Nome"
            autoComplete="name"
            maxLength={120}
            value={name}
            error={fieldErrors.name}
            onChange={(event) => update({ name: event.target.value })}
          />
          <FormField
            label="E-mail"
            type="email"
            autoComplete="email"
            value={email}
            error={fieldErrors.email}
            onChange={(event) => update({ email: event.target.value })}
          />
          <FormField
            label="Senha"
            type="password"
            autoComplete="new-password"
            value={password}
            error={fieldErrors.password}
            onChange={(event) => update({ password: event.target.value })}
          />
          <PasswordRequirements password={password} />
          <FormField
            label="Confirme a senha"
            type="password"
            autoComplete="new-password"
            value={confirmation}
            error={fieldErrors.confirmation}
            onChange={(event) => update({ confirmation: event.target.value })}
          />
        </div>

        <label className="mt-6 flex items-start gap-2.5 text-sm text-card-foreground">
          <input
            type="checkbox"
            checked={termsAccepted}
            aria-invalid={fieldErrors.terms ? true : undefined}
            onChange={(event) => update({ termsAccepted: event.target.checked })}
            className="mt-0.5 h-4 w-4 shrink-0 rounded border-input accent-primary"
          />
          <span>
            Li e aceito o{" "}
            <Link to="/termos" target="_blank" className="font-medium text-primary hover:underline">
              Termo de Uso
            </Link>{" "}
            e a{" "}
            <Link to="/privacidade" target="_blank" className="font-medium text-primary hover:underline">
              Política de Privacidade
            </Link>
            .
          </span>
        </label>
        {fieldErrors.terms && (
          <p className="mt-2 text-xs font-medium text-destructive">{fieldErrors.terms}</p>
        )}

        {error && <p className="mt-5 text-sm text-destructive" role="alert">{error}</p>}

        <button
          type="submit"
          disabled={isSubmitting}
          className="mt-7 w-full rounded-lg bg-primary px-4 py-3 text-sm font-semibold text-primary-foreground transition-colors hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isSubmitting ? "Criando..." : "Criar conta"}
        </button>

        <p className="mt-6 text-center text-sm text-muted-foreground">
          Já tem conta?{" "}
          <Link to="/" className="font-medium text-primary hover:underline">
            Entrar
          </Link>
        </p>
      </form>
    </main>
  );
}
