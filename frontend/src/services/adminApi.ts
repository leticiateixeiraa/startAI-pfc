// feat(admin): chamadas do painel administrativo (/admin/*).
// O back-end confere o papel a cada requisição: usuário comum recebe 403.
import api from "./api";
import type { AuditLog } from "./auditApi";

export type AdminUser = {
  id: string;
  email: string;
  name: string | null;
  role: "user" | "admin";
  is_active: boolean;
  created_at: string | null;
  interview_count: number;
};

export type CountByKey = { key: string; count: number };

export type AdminMetrics = {
  total_users: number;
  active_users: number;
  blocked_users: number;
  new_users_last_30_days: number;
  total_interviews: number;
  finished_interviews: number;
  completion_rate: number;
  total_answers: number;
  average_answers_per_interview: number;
  failed_logins_last_7_days: number;
  interviews_by_type: CountByKey[];
  interviews_per_day: CountByKey[];
};

export type AdminAuditFilters = {
  user_id?: string;
  action?: string;
  date_from?: string;
  date_to?: string;
  limit?: number;
};

export async function getAdminMetrics(): Promise<AdminMetrics> {
  const { data } = await api.get<AdminMetrics>("/admin/metrics");
  return data;
}

export async function listAdminUsers(search?: string): Promise<AdminUser[]> {
  const { data } = await api.get<AdminUser[]>("/admin/users", {
    params: search ? { search } : undefined,
  });
  return data;
}

export async function setUserActive(userId: string, isActive: boolean): Promise<AdminUser> {
  const { data } = await api.patch<AdminUser>(`/admin/users/${userId}`, { is_active: isActive });
  return data;
}

export async function listAdminAuditLogs(filters: AdminAuditFilters): Promise<AuditLog[]> {
  const params = Object.fromEntries(
    Object.entries(filters).filter(([, value]) => value !== undefined && value !== ""),
  );
  const { data } = await api.get<AuditLog[]>("/admin/audit/logs", { params });
  return data;
}
