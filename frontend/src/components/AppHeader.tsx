// Cabeçalho único do StartAI, exibido em todas as telas (via __root.tsx).
// Logado: navegação principal + sair. Deslogado: entrar / criar conta.
import { Link, useNavigate, useRouterState } from "@tanstack/react-router";
import { LogOut, Menu, Mic, X } from "lucide-react";
import { useEffect, useState } from "react";
import { logout } from "@/services/authService";

const NAV_ITEMS = [
  { to: "/home", label: "Início" },
  { to: "/interview/setup", label: "Nova entrevista" },
  { to: "/audit", label: "Auditoria" },
] as const;

function hasToken() {
  try {
    return Boolean(localStorage.getItem("access_token"));
  } catch {
    return false;
  }
}

export function AppHeader() {
  const navigate = useNavigate();
  // Reavalia o login a cada troca de rota (login/logout mudam a URL).
  const pathname = useRouterState({ select: (state) => state.location.pathname });
  const [isLoggedIn, setIsLoggedIn] = useState(hasToken);
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    setIsLoggedIn(hasToken());
    setMenuOpen(false);
  }, [pathname]);

  function handleLogout() {
    logout();
    setIsLoggedIn(false);
    navigate({ to: "/" });
  }

  const linkClass =
    "rounded-lg px-3 py-2 text-sm font-semibold text-primary-foreground/85 transition-colors hover:bg-white/10 hover:text-primary-foreground";
  const activeClass = "bg-white/15 text-primary-foreground";

  return (
    <header className="sticky top-0 z-40 bg-primary text-primary-foreground shadow-md">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-4 px-4 sm:px-8">
        <Link
          to={isLoggedIn ? "/home" : "/"}
          className="flex items-center gap-2.5 text-primary-foreground"
          aria-label="StartAI — página inicial"
        >
          <span className="flex size-9 items-center justify-center rounded-xl bg-highlight text-highlight-foreground">
            <Mic className="size-5" strokeWidth={2.5} aria-hidden />
          </span>
          <span className="text-xl font-extrabold tracking-tight">
            Start<span className="text-highlight">AI</span>
          </span>
        </Link>

        {isLoggedIn ? (
          <>
            <nav className="hidden items-center gap-1 md:flex" aria-label="Navegação principal">
              {NAV_ITEMS.map((item) => (
                <Link
                  key={item.to}
                  to={item.to}
                  className={linkClass}
                  activeProps={{ className: activeClass }}
                >
                  {item.label}
                </Link>
              ))}
              <button
                type="button"
                onClick={handleLogout}
                className="ml-2 inline-flex items-center gap-2 rounded-lg border border-white/30 px-3 py-2 text-sm font-semibold text-primary-foreground transition-colors hover:bg-white/10"
              >
                <LogOut className="size-4" aria-hidden />
                Sair
              </button>
            </nav>
            <button
              type="button"
              onClick={() => setMenuOpen((open) => !open)}
              className="rounded-lg p-2 hover:bg-white/10 md:hidden"
              aria-label={menuOpen ? "Fechar menu" : "Abrir menu"}
              aria-expanded={menuOpen}
            >
              {menuOpen ? <X className="size-6" /> : <Menu className="size-6" />}
            </button>
          </>
        ) : (
          <div className="flex items-center gap-2">
            <Link to="/" className={linkClass} activeOptions={{ exact: true }} activeProps={{ className: activeClass }}>
              Entrar
            </Link>
            <Link
              to="/register"
              className="rounded-lg bg-highlight px-4 py-2 text-sm font-bold text-highlight-foreground transition-colors hover:bg-highlight/90"
            >
              Criar conta
            </Link>
          </div>
        )}
      </div>

      {isLoggedIn && menuOpen && (
        <nav className="border-t border-white/15 px-4 pb-4 pt-2 md:hidden" aria-label="Navegação principal">
          {NAV_ITEMS.map((item) => (
            <Link
              key={item.to}
              to={item.to}
              className={`block ${linkClass}`}
              activeProps={{ className: activeClass }}
            >
              {item.label}
            </Link>
          ))}
          <button
            type="button"
            onClick={handleLogout}
            className={`mt-1 flex w-full items-center gap-2 text-left ${linkClass}`}
          >
            <LogOut className="size-4" aria-hidden />
            Sair
          </button>
        </nav>
      )}
    </header>
  );
}
