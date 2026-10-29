// feat(auth-frontend): cria tela de cadastro/login e armazenamento do token

import api from "./api";

// feat(lgpd): versão vigente do Termo de Uso / Política de Privacidade,
// deve acompanhar a constante equivalente no backend (auth/schemas.py).
export const CURRENT_TERMS_VERSION = "1.0";

export interface RegisterPayload {
  email: string;
  password: string;
  name?: string;
  terms_accepted: boolean;
  terms_version?: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export type UserRole = "user" | "admin";

export interface CurrentUser {
  id: string;
  email: string;
  name: string | null;
  role: UserRole;
}

// feat(admin): o papel fica salvo só para decidir o que MOSTRAR no menu.
// Quem garante a permissão é o back-end (403 nas rotas /admin para não-admins).
const ROLE_KEY = "user_role";

export function getStoredRole(): UserRole | null {
  try {
    const role = localStorage.getItem(ROLE_KEY);
    return role === "admin" || role === "user" ? role : null;
  } catch {
    return null;
  }
}

function storeRole(role: UserRole) {
  try {
    localStorage.setItem(ROLE_KEY, role);
  } catch {
    // sem localStorage o menu só não mostra o link de administração
  }
}

export async function cadastrar(payload: RegisterPayload) {
  const { data } = await api.post("/auth/register", payload);
  return data;
}

export async function entrar(payload: LoginPayload) {
  const { data } = await api.post<{ access_token: string; token_type: string }>(
    "/auth/login",
    payload
  );
  localStorage.setItem("access_token", data.access_token);
  try {
    await getCurrentUser();
  } catch {
    // o login já deu certo; o papel será buscado de novo pelo cabeçalho
  }
  return data;
}

export function logout() {
  localStorage.removeItem("access_token");
  localStorage.removeItem(ROLE_KEY);
}

export function isAuthenticated(): boolean {
  return Boolean(localStorage.getItem("access_token"));
}

// feat(auth-frontend): busca os dados do usuário autenticado (GET /auth/me)
export async function getCurrentUser(): Promise<CurrentUser> {
  const { data } = await api.get<CurrentUser>("/auth/me");
  storeRole(data.role);
  return data;
}

export async function esqueciSenha(email: string) {
  const { data } = await api.post("/auth/forgot-password", { email });
  return data;
}

export async function redefinirSenha(token: string, novaSenha: string) {
  const { data } = await api.post("/auth/reset-password", { token, new_password: novaSenha });
  return data;
}
// feat(admin): usado no beforeLoad das rotas /admin para tirar dali quem não é admin.
export async function isCurrentUserAdmin(): Promise<boolean> {
  try {
    const user = await getCurrentUser();
    return user.role === "admin";
  } catch {
    return false;
  }
}
