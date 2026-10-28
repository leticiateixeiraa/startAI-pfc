import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  Outlet,
  Link,
  createRootRouteWithContext,
  useRouter,
} from "@tanstack/react-router";
import { useEffect } from "react";

import appCss from "../styles.css?url";
import { reportLovableError } from "../lib/lovable-error-reporting";
import { AppHeader } from "../components/AppHeader";

function NotFoundComponent() {
  return (
    <div className="flex min-h-[70vh] flex-1 items-center justify-center bg-background px-4 py-16">
      <div className="max-w-md text-center">
        <h1 className="text-7xl font-extrabold text-primary">404</h1>
        <h2 className="mt-4 text-xl font-semibold text-foreground">Página não encontrada</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          A página que você procura não existe ou foi movida.
        </p>
        <div className="mt-6">
          <Link
            to="/"
            className="inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
          >
            Voltar ao início
          </Link>
        </div>
      </div>
    </div>
  );
}

function ErrorComponent({ error, reset }: { error: unknown; reset: () => void }) {
  console.error(error);
  const router = useRouter();
  useEffect(() => {
    reportLovableError(error instanceof Error ? error : new Error(String(error)), {
      boundary: "tanstack_root_error_component",
    });
  }, [error]);

  return (
    <div className="flex min-h-[70vh] flex-1 items-center justify-center bg-background px-4 py-16">
      <div className="max-w-md text-center">
        <h1 className="text-xl font-semibold tracking-tight text-foreground">
          Não foi possível carregar a página
        </h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Algo deu errado do nosso lado. Tente recarregar ou volte ao início.
        </p>
        <div className="mt-6 flex flex-wrap justify-center gap-2">
          <button
            onClick={() => {
              router.invalidate();
              reset();
            }}
            className="inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
          >
            Tentar novamente
          </button>
          <a
            href="/"
            className="inline-flex items-center justify-center rounded-md border border-input bg-background px-4 py-2 text-sm font-medium text-foreground transition-colors hover:bg-accent"
          >
            Voltar ao início
          </a>
        </div>
      </div>
    </div>
  );
}

export const Route = createRootRouteWithContext<{ queryClient: QueryClient }>()({
  head: () => ({
    meta: [
      { charSet: "utf-8" },
      { name: "viewport", content: "width=device-width, initial-scale=1" },
      { title: "StartAI — Simulador de entrevistas com IA" },
      {
        name: "description",
        content:
          "Simule entrevistas de emprego com perguntas geradas por inteligência artificial, alinhadas à vaga que você deseja.",
      },
      { name: "author", content: "StartAI" },
      { property: "og:title", content: "StartAI — Simulador de entrevistas com IA" },
      {
        property: "og:description",
        content:
          "Simule entrevistas de emprego com perguntas geradas por inteligência artificial, alinhadas à vaga que você deseja.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
    links: [
      { rel: "preconnect", href: "https://fonts.googleapis.com" },
      { rel: "preconnect", href: "https://fonts.gstatic.com", crossOrigin: "anonymous" },
      {
        rel: "stylesheet",
        href: "https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800&display=swap",
      },
      {
        rel: "stylesheet",
        href: appCss,
      },
      { rel: "icon", href: "/favicon.ico", type: "image/x-icon" },
    ],
  }),
  component: RootComponent,
  notFoundComponent: NotFoundComponent,
  errorComponent: ErrorComponent,
});

// feat(lgpd): rodapé com links para Termo de Uso e Política de Privacidade,
// visível em qualquer tela do sistema (não só durante o cadastro).
function SiteFooter() {
  return (
    <footer className="bg-brand-dark px-4 py-8 text-sm text-white/75">
      <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-3 sm:flex-row sm:px-4">
        <p>
          <span className="font-extrabold text-white">
            Start<span className="text-highlight">AI</span>
          </span>{" "}
          · Treine entrevistas e apresentações com IA
        </p>
        <nav className="flex gap-4" aria-label="Documentos legais">
          <Link to="/termos" className="hover:text-white hover:underline">
            Termo de Uso
          </Link>
          <Link to="/privacidade" className="hover:text-white hover:underline">
            Política de Privacidade
          </Link>
        </nav>
      </div>
    </footer>
  );
}

function RootComponent() {
  const { queryClient } = Route.useRouteContext();

  return (
    <QueryClientProvider client={queryClient}>
      {/* Required: nested routes render here. Removing <Outlet /> breaks all child routes. */}
      <div className="flex min-h-screen flex-col bg-background">
        <AppHeader />
        <Outlet />
        <SiteFooter />
      </div>
    </QueryClientProvider>
  );
}
