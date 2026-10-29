// feat(admin): moldura comum das telas de administração (título + abas).
import { Link } from "@tanstack/react-router";
import type { ReactNode } from "react";

const TABS = [
  { to: "/admin", label: "Painel" },
  { to: "/admin/users", label: "Usuários" },
  { to: "/admin/audit", label: "Auditoria geral" },
] as const;

type Props = {
  title: string;
  description: string;
  actions?: ReactNode;
  children: ReactNode;
};

export function AdminLayout({ title, description, actions, children }: Props) {
  return (
    <main className="flex-1 bg-background px-4 py-10 sm:px-8">
      <div className="mx-auto max-w-6xl">
        <p className="text-xs font-bold uppercase tracking-wider text-primary">Administração</p>
        <header className="mt-1 mb-6 flex flex-wrap items-end justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-foreground">{title}</h1>
            <p className="mt-2 text-sm text-muted-foreground">{description}</p>
          </div>
          {actions}
        </header>

        <nav className="mb-6 flex gap-1 overflow-x-auto border-b border-border" aria-label="Seções da administração">
          {TABS.map((tab) => (
            <Link
              key={tab.to}
              to={tab.to}
              activeOptions={{ exact: true }}
              className="whitespace-nowrap border-b-2 border-transparent px-4 py-2 text-sm font-semibold text-muted-foreground transition-colors hover:text-foreground"
              activeProps={{ className: "border-primary text-primary" }}
            >
              {tab.label}
            </Link>
          ))}
        </nav>

        {children}
      </div>
    </main>
  );
}

export function LoadingBox({ text = "Carregando..." }: { text?: string }) {
  return <p className="rounded-xl border border-border bg-card p-6 text-sm text-muted-foreground">{text}</p>;
}

export function ErrorBox({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="flex items-center justify-between gap-4 rounded-xl border border-destructive/40 bg-card p-6 text-sm text-destructive">
      <span>{message}</span>
      <button type="button" onClick={onRetry} className="font-semibold underline">
        Tentar novamente
      </button>
    </div>
  );
}
