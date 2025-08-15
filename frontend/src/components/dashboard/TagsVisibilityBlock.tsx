import React, { useMemo, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Legend,
} from "recharts";
import { useTagsVisibilityChart } from '../../hooks/useTagsVisibilityChart'

interface Props {
  projectId?: string
}

const TAG_COLORS: Record<string, string> = {
  audit: "#0ea5e9", // cyan-500
  "stratégie": "#f59e0b", // amber-500
  "visibilité": "#ef4444", // red-500
  analyse: "#10b981", // emerald-500
  seo: "#8b5cf6", // violet-500
  marketing: "#06b6d4", // cyan-500
  concurrence: "#f97316", // orange-500
  recherche: "#84cc16", // lime-500
  contenu: "#ec4899", // pink-500
};

const numberFmt = (n: number) => new Intl.NumberFormat("fr-FR").format(n);

export const TagsVisibilityBlock: React.FC<Props> = ({ projectId }) => {
  const { data, loading, error } = useTagsVisibilityChart(projectId)
  const [selectedTags, setSelectedTags] = useState<string[]>([])
  const [range, setRange] = useState("30j");

  // Initialiser selectedTags avec les 3 premiers tags quand les données arrivent
  useMemo(() => {
    if (data && data.ranking && selectedTags.length === 0) {
      const topTags = data.ranking.slice(0, 3).map(r => r.tag)
      setSelectedTags(topTags)
    }
  }, [data, selectedTags.length])

  const top = useMemo(() => data?.ranking?.[0], [data]);

  const toggleTag = (tag: string) => {
    setSelectedTags((prev) =>
      prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag]
    );
  };

  if (loading || !data) {
    return (
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="text-slate-500 py-16 text-center">Chargement…</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="text-red-600 py-16 text-center">Erreur: {error}</div>
      </div>
    )
  }

  return (
    <div className="w-full">
      {/* Header */}
      <div className="mb-6 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-slate-900">Visibilité par tags</h1>
          <p className="mt-1 text-sm text-slate-500">Évolution, classement et taux associés. Données basées sur des prompts taggés.</p>
        </div>

        {/* Quick KPIs */}
        <div className="flex flex-wrap items-center gap-3">
          <KPI label="Analyses" value={data.totalAnalyses || 0} suffix="" />
          {top && (
            <KPI label="Tag n°1" valueLabel={top.tag} value={top.score} suffix="%" />
          )}
          <KPI 
            label="Taux de mention moyen" 
            value={
              data.ranking.length > 0
                ? Math.round(
                    data.ranking.reduce((a, b) => a + b.mentionRate, 0) / data.ranking.length
                  )
                : 0
            } 
            suffix="%" 
          />
        </div>
      </div>

      {/* Surface */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-10">
        {/* Left: big chart */}
        <div className="col-span-1 lg:col-span-7">
          <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
            <div className="mb-3 flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
              <div className="flex flex-wrap items-center gap-2">
                {data.ranking.slice(0, 6).map((item) => {
                  const color = TAG_COLORS[item.tag] || "#64748b"
                  return (
                    <button
                      key={item.tag}
                      onClick={() => toggleTag(item.tag)}
                      className={`inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-sm transition ${
                        selectedTags.includes(item.tag)
                          ? "border-slate-300 bg-slate-50 text-slate-900"
                          : "border-slate-200 text-slate-500 hover:bg-slate-50"
                      }`}
                      aria-pressed={selectedTags.includes(item.tag)}
                    >
                      <span
                        className="inline-block h-2.5 w-2.5 rounded-full"
                        style={{ backgroundColor: color }}
                        aria-hidden
                      />
                      {item.tag}
                    </button>
                  )
                })}
              </div>

              <div className="flex items-center gap-2 text-sm">
                <label className="text-slate-500">Période</label>
                <div className="inline-flex overflow-hidden rounded-full border border-slate-200">
                  {["7j", "30j", "90j"].map((r) => (
                    <button
                      key={r}
                      onClick={() => setRange(r)}
                      className={`px-3 py-1.5 ${
                        range === r ? "bg-slate-900 text-white" : "bg-white text-slate-700 hover:bg-slate-50"
                      }`}
                      aria-pressed={range === r}
                    >
                      {r}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div className="h-80 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data.chartData} margin={{ top: 10, right: 20, bottom: 0, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="date" tick={{ fill: "#64748b" }} axisLine={{ stroke: "#cbd5e1" }} />
                  <YAxis tick={{ fill: "#64748b" }} axisLine={{ stroke: "#cbd5e1" }} domain={[0, 100]} />
                  <Tooltip
                    contentStyle={{ borderRadius: 12, border: "1px solid #e2e8f0" }}
                    formatter={(value: any, name: any) => [value + "%", name]}
                  />
                  <Legend wrapperStyle={{ paddingTop: 8 }} />

                  {selectedTags.map((tag) => {
                    const color = TAG_COLORS[tag] || "#64748b"
                    return (
                      <Line 
                        key={tag}
                        type="monotone" 
                        dataKey={tag} 
                        name={tag} 
                        stroke={color} 
                        strokeWidth={3} 
                        dot={false} 
                      />
                    )
                  })}
                </LineChart>
              </ResponsiveContainer>
            </div>

            <div className="mt-3 flex items-center justify-between text-xs text-slate-500">
              <span>{numberFmt(data.totalAnalyses || 0)} analyses</span>
              <span>0–100 = score de visibilité</span>
            </div>
          </div>
        </div>

        {/* Right: leaderboard */}
        <div className="col-span-1 lg:col-span-3">
          <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-sm font-medium text-slate-900">Classement des tags</h2>
              <span className="text-xs text-slate-500">Score moyen & taux</span>
            </div>

            <ul className="space-y-2 max-h-80 overflow-y-auto pr-1">
              {data.ranking.map((row, idx) => (
                <li key={row.tag} className="group rounded-xl border border-slate-100 p-3 hover:bg-slate-50">
                  <div className="flex items-center gap-3">
                    <span className="grid h-6 w-6 place-items-center rounded-full bg-slate-900 text-xs font-semibold text-white">
                      {idx + 1}
                    </span>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center justify-between">
                        <button
                          onClick={() => toggleTag(row.tag)}
                          className="truncate text-sm font-medium text-slate-900 hover:underline"
                          title="Ajouter/retirer du graphique"
                        >
                          {row.tag}
                        </button>
                        <span className="text-sm font-semibold text-slate-900">{row.score}%</span>
                      </div>
                      <div className="mt-1 h-2 w-full overflow-hidden rounded-full bg-slate-100">
                        <div
                          className="h-full rounded-full"
                          style={{ width: `${row.score}%`, background: "linear-gradient(90deg,#22d3ee,#6366f1)" }}
                        />
                      </div>
                      <div className="mt-1 flex items-center gap-3 text-xs text-slate-500">
                        <span>Taux de mention {row.mentionRate}%</span>
                        <span>•</span>
                        <span>Taux de liens {row.linkRate}%</span>
                      </div>
                    </div>
                  </div>
                </li>
              ))}
            </ul>

            <p className="mt-4 text-xs text-slate-500">
              Astuce : clique un tag pour le comparer sur le graphique à gauche.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

function KPI({ label, value, suffix = "%", valueLabel }: { label: string; value: number; suffix?: string; valueLabel?: string }) {
  return (
    <div className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-white px-4 py-2 shadow-sm">
      <div className="text-xs text-slate-500">{label}</div>
      <div className="flex items-baseline gap-1">
        {valueLabel && <span className="text-sm font-medium text-slate-900">{valueLabel}</span>}
        <span className="text-lg font-semibold text-slate-900">{numberFmt(value)}</span>
        <span className="text-xs text-slate-400">{suffix}</span>
      </div>
    </div>
  );
}


