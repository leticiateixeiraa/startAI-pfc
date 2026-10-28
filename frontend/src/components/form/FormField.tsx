// Campo de formulário com rótulo, mensagem de erro e acessibilidade
// (aria-invalid + aria-describedby), usado nas telas de autenticação.
import { useId, type InputHTMLAttributes } from "react";
import { Check, Circle } from "lucide-react";
import { passwordChecks } from "@/lib/validation";

type FormFieldProps = InputHTMLAttributes<HTMLInputElement> & {
  label: string;
  error?: string | null;
  hint?: string;
};

export function FormField({ label, error, hint, className = "", ...inputProps }: FormFieldProps) {
  const id = useId();
  const messageId = `${id}-message`;
  return (
    <div className="flex flex-col gap-1.5 text-sm">
      <label htmlFor={id} className="font-medium text-card-foreground">
        {label}
      </label>
      <input
        id={id}
        aria-invalid={error ? true : undefined}
        aria-describedby={error || hint ? messageId : undefined}
        className={`rounded-lg border bg-background px-3 py-2.5 font-normal text-foreground outline-none focus:ring-2 ${
          error
            ? "border-destructive focus:border-destructive focus:ring-destructive/20"
            : "border-input focus:border-primary focus:ring-primary/20"
        } ${className}`}
        {...inputProps}
      />
      {error ? (
        <p id={messageId} className="text-xs font-medium text-destructive">
          {error}
        </p>
      ) : hint ? (
        <p id={messageId} className="text-xs text-muted-foreground">
          {hint}
        </p>
      ) : null}
    </div>
  );
}

// Lista dos requisitos da senha que fica verde enquanto a pessoa digita.
export function PasswordRequirements({ password }: { password: string }) {
  return (
    <ul className="-mt-2 flex flex-col gap-1 text-xs" aria-label="Requisitos da senha">
      {passwordChecks(password).map((check) => (
        <li
          key={check.label}
          className={`flex items-center gap-1.5 ${check.ok ? "text-emerald-700" : "text-muted-foreground"}`}
        >
          {check.ok ? <Check className="size-3.5" aria-hidden /> : <Circle className="size-3" aria-hidden />}
          {check.label}
          <span className="sr-only">{check.ok ? "(atendido)" : "(pendente)"}</span>
        </li>
      ))}
    </ul>
  );
}
