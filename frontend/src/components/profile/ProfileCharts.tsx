// feat(behavioral): gráficos do perfil comportamental e do questionário de área.
// Usam as cores do tema (--chart-1/--chart-2), as mesmas do painel admin.
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { ScoreItem } from "@/services/evaluationApi";

const decimal = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 1 });

export function formatScore(value: number) {
  return decimal.format(value);
}

// Radar das competências (0 a 10). Os valores também aparecem em lista ao
// lado, para quem não consegue ler o gráfico.
export function CompetencyRadar({ items }: { items: ScoreItem[] }) {
  return (
    <div className="grid items-center gap-6 md:grid-cols-[1fr_14rem]">
      <div className="h-72" role="img" aria-label="Gráfico radar das competências comportamentais">
        <ResponsiveContainer width="100%" height="100%">
          <RadarChart data={items} outerRadius="70%">
            <PolarGrid stroke="var(--border)" />
            <PolarAngleAxis dataKey="label" tick={{ fontSize: 11, fill: "var(--muted-foreground)" }} />
            <PolarRadiusAxis domain={[0, 10]} tickCount={6} tick={false} axisLine={false} />
            <Tooltip formatter={(value) => [`${formatScore(Number(value))}/10`, "Nota"]} />
            <Radar
              dataKey="score"
              stroke="var(--chart-1)"
              strokeWidth={2}
              fill="var(--chart-1)"
              fillOpacity={0.22}
              dot={{ r: 4, fill: "var(--chart-1)", stroke: "var(--card)", strokeWidth: 2 }}
            />
          </RadarChart>
        </ResponsiveContainer>
      </div>
      <ScoreBars items={items} max={10} suffix="/10" />
    </div>
  );
}

// Barras horizontais simples, com o valor sempre visível.
export function ScoreBars({
  items,
  max,
  suffix = "",
}: {
  items: ScoreItem[];
  max: number;
  suffix?: string;
}) {
  return (
    <dl className="space-y-3">
      {items.map((item) => (
        <div key={item.key}>
          <div className="flex justify-between gap-3 text-xs font-medium">
            <dt className="text-muted-foreground">{item.label}</dt>
            <dd className="tabular-nums text-foreground">
              {formatScore(item.score)}
              {suffix}
            </dd>
          </div>
          <div className="mt-1 h-2 overflow-hidden rounded-full bg-muted">
            <div
              className="h-full rounded-full bg-chart-1"
              style={{ width: `${Math.min(100, (item.score / max) * 100)}%` }}
            />
          </div>
        </div>
      ))}
    </dl>
  );
}

export type EvolutionPoint = {
  label: string;
  competencias: number;
  nota: number | null;
};

// Evolução entrevista a entrevista: média das competências e nota geral da
// avaliação, as duas na mesma escala de 0 a 10 (um eixo só).
export function EvolutionChart({ data }: { data: EvolutionPoint[] }) {
  return (
    <div className="h-64">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 8, right: 16, left: -16, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
          <XAxis dataKey="label" tick={{ fontSize: 12 }} stroke="var(--muted-foreground)" />
          <YAxis domain={[0, 10]} tickCount={6} tick={{ fontSize: 12 }} stroke="var(--muted-foreground)" />
          <Tooltip formatter={(value) => formatScore(Number(value))} />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Line
            type="monotone"
            name="Média das competências"
            dataKey="competencias"
            stroke="var(--chart-1)"
            strokeWidth={2}
            dot={{ r: 4 }}
            activeDot={{ r: 6 }}
          />
          <Line
            type="monotone"
            name="Nota da entrevista"
            dataKey="nota"
            stroke="var(--chart-2)"
            strokeWidth={2}
            strokeDasharray="6 4"
            dot={{ r: 4 }}
            activeDot={{ r: 6 }}
            connectNulls
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
