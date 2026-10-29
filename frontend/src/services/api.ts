// Instância única de HTTP client, compartilhada por todos os services
// (auth, questions, interview). Anexa o token JWT automaticamente
// quando existir, seguindo o contrato combinado com o time:
//   header Authorization: Bearer <token>

import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000",
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Token expirado ou inválido: o backend responde 401. Sem isto, as rotas do
// front continuariam achando que o usuário está logado (elas só checam se
// existe token no localStorage). O login fica de fora porque lá o 401
// significa "senha errada", e a própria tela mostra a mensagem.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const isLoginRequest = error?.config?.url?.includes("/auth/login");
    if (error?.response?.status === 401 && !isLoginRequest) {
      localStorage.removeItem("access_token");
      localStorage.removeItem("user_role");
      window.location.assign("/");
    }
    return Promise.reject(error);
  },
);

// O FastAPI devolve `detail` como texto (erros nossos) ou como lista
// (erros de validação 422, como a senha fraca). Esta função sempre devolve
// um texto exibível, nos dois casos.
export function getErrorMessage(error: unknown, fallback: string): string {
  const detail = (error as any)?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail.length > 0) {
    const msg = String(detail[0]?.msg ?? "");
    return msg.replace(/^Value error, /, "") || fallback;
  }
  return fallback;
}

export default api;