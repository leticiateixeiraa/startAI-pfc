// feat(admin): painel com big numbers e gráficos da plataforma (dashboard).
import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { AdminLayout, ErrorBox, LoadingBox } from "@/components/admin/AdminLayout";
import { requireAdminBeforeLoad } from "@/components/admin/adminGuard";
import { getAdminMetrics, type AdminMetrics } from "@/services/adminApi";
import { PRESENTATION_TYPES } from "@/types/interview";

export const Route = createFileRoute("/admin/")({
  beforeLoad: requireAdminBeforeLoad,
  head: () => ({ meta: [{ title: "Painel administrativo — StartAI" }] }),
  component: AdminDashboardPage,
});

const TYPE_LABELS: Record<string, string> = {
  ...Object.fromEntries(PRESENTATION_TYPES.map((type) => [type.value, type.label])),
  entrevista_de_emprego: "Entrevista (sem tipo)",
  apresentacao_academica: "Apresentação acadêmica",
  nao_informado: "Não informado",
};

const percent = new Intl.NumberFormat("pt-BR", { style: "percent", maximumFractionDigits: 0 });
const integer = new Intl.NumberFormat("pt-BR");

function formatDay(iso: string) {
  const [, month, day] = iso.split("-");
  return `${day}/${month}`;
}

function StatCard({ label, value, detail }: { label: string; value: string; detail?: string }) {
  return (
    <div className="rounded-xl border border-border bg-card p-5 shadow-sm">
      <p className="text-sm font-medium text-muted-foreground">{label}</p>
      <p className="mt-2 text-3xl font-extrabold tracking-tight text-card-foreground">{value}</p>
      {detail && <p className="mt-1 text-xs text-muted-foreground">{detail}</p>}
    </div>
  );
}

function ChartCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="rounded-xl border border-border bg-card p-5 shadow-sm">
      <h2 className="mb-4 text-base font-semibold text-card-foreground">{title}</h2>
      <div className="h-64">{children}</div>
    </section>
  );
}

function AdminDashboardPage() {
  const [metrics, setMetrics] = useState<AdminMetrics | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setError(null);
    try {
      setMetrics(await getAdminMetrics());
    } catch {
      setError("Não foi possível carregar as métricas.");
    }
  }

  useEffect(() => {
    void load();
  }, []);

  const perDay = metrics?.interviews_per_day.map((item) => ({ dia: formatDay(item.key), entrevistas: item.count }));
  const byType = metrics?.interviews_by_type.map((item) => ({
    tipo: TYPE_LABELS[item.key] ?? item.key,
    entrevistas: item.count,
  }));

  return (
    <AdminLayout
      title="Painel da plataforma"
      description="Números gerais de uso do StartAI. Nenhuma resposta de entrevista é exibida aqui."
      actions={
        <button
          type="button"
          onClick={() => void load()}
          className="rounded-lg border border-border px-3 py-2 text-sm font-medium text-foreground hover:bg-accent"
        >
          Atualizar
        </button>
      }
    >
      {error && <ErrorBox message={error} onRetry={() => void load()} />}
      {!error && !metrics && <LoadingBox text="Carregando métricas..." />}
      {metrics && perDay && byType && (
        <div className="space-y-6">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard
              label="Usuários cadastrados"
              value={integer.format(metrics.total_users)}
              detail={`${integer.format(metrics.new_users_last_30_days)} nos últimos 30 dias`}
            />
            <StatCard
              label="Entrevistas realizadas"
              value={integer.format(metrics.total_interviews)}
              detail={`${integer.format(metrics.total_answers)} respostas enviadas`}
            />
            <StatCard
              label="Taxa de conclusão"
              value={percent.format(metrics.completion_rate)}
              detail={`${integer.format(metrics.finished_interviews)} entrevistas concluídas`}
            />
            <StatCard
              label="Logins com falha"
              value={integer.format(metrics.failed_logins_last_7_days)}
              detail={`Últimos 7 dias • ${integer.format(metrics.blocked_users)} contas desativadas`}
            />
          </div>

          <div className="grid gap-6 lg:grid-cols-5">
            <div className="lg:col-span-3">
              <ChartCard title="Entrevistas por dia (últimos 30 dias)">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={perDay} margin={{ top: 8, right: 16, left: -16, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                    <XAxis dataKey="dia" tick={{ fontSize: 12 }} interval={4} stroke="var(--muted-foreground)" />
                    <YAxis allowDecimals={false} tick={{ fontSize: 12 }} stroke="var(--muted-foreground)" />
                    <Tooltip />
                    <Line type="monotone" dataKey="entrevistas" stroke="var(--chart-1)" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </ChartCard>
            </div>
            <div className="lg:col-span-2">
              <ChartCard title="Entrevistas por tipo">
                {byType.length === 0 ? (
                  <p className="text-sm text-muted-foreground">Nenhuma entrevista ainda.</p>
                ) : (
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={byType} layout="vertical" margin={{ top: 0, right: 16, left: 8, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" horizontal={false} />
                      <XAxis type="number" allowDecimals={false} tick={{ fontSize: 12 }} stroke="var(--muted-foreground)" />
                      <YAxis type="category" dataKey="tipo" width={130} tick={{ fontSize: 12 }} stroke="var(--muted-foreground)" />
                      <Tooltip />
                      <Bar dataKey="entrevistas" fill="var(--chart-1)" radius={[0, 4, 4, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                )}
              </ChartCard>
            </div>
          </div>
        </div>
      )}
    </AdminLayout>
  );
}
