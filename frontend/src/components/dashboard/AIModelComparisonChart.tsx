import React, { useMemo, useState } from 'react'
import { 
  LineChart,
  Line,
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer 
} from 'recharts'
import { Brain, Award, Filter } from 'lucide-react'
import { useAIModelComparison } from '../../hooks/useAIModelComparison'
import { Loading } from '../ui'

interface AIModelComparisonChartProps {
  timeFilter: string
  projectId?: string
}

export const AIModelComparisonChart: React.FC<AIModelComparisonChartProps> = ({ 
  timeFilter, 
  projectId 
}) => {
  const [metricFilter, setMetricFilter] = useState<'visibility' | 'mentions' | 'links'>('visibility')
  
  const { data, loading, error } = useAIModelComparison(timeFilter, projectId, metricFilter)

  // IMPORTANT: Tous les hooks doivent être appelés avant tout return conditionnel
  // Palette élégante et cohérente (useMemo doit rester avant les returns)
  const colors = useMemo(() => [
    '#2563eb', // Bleu
    '#ef4444', // Rouge
    '#059669', // Vert
    '#f59e0b', // Orange
    '#7c3aed', // Violet
    '#db2777', // Rose
    '#6b7280', // Gris
    '#0d9488', // Teal
  ], [])

  if (loading) {
    return (
      <div className="card p-6">
        <div className="flex items-center justify-center h-80">
          <Loading size="lg" text="Chargement de la comparaison IA..." />
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="card p-6">
        <div className="flex items-center justify-center h-80 text-red-600">
          ❌ Erreur lors du chargement de la comparaison IA
        </div>
      </div>
    )
  }

  if (!data || !Array.isArray(data.models) || data.models.length === 0) {
    return (
      <div className="card p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="section-title">Comparaison des modèles IA</h3>
            <p className="muted">
              {projectId ? 'Aucune donnée de comparaison disponible' : 'Sélectionnez un projet pour voir la comparaison'}
            </p>
          </div>
        </div>
        <div className="flex items-center justify-center h-80 text-gray-500">
          <div className="text-center">
            <div className="text-4xl mb-4">🤖</div>
            <p>Aucune donnée de comparaison IA</p>
            <p className="text-sm mt-2">Exécutez des prompts avec différents modèles</p>
          </div>
        </div>
      </div>
    )
  }

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (!active || !payload || !payload.length) return null
    return (
      <div className="rounded-md border border-gray-200 bg-white p-3 shadow-sm">
        <div className="text-xs text-gray-500 mb-1">{label}</div>
        <div className="space-y-1">
          {payload.map((p: any) => (
            <div key={p.dataKey} className="flex items-center gap-2 text-sm">
              <span className="inline-block w-2.5 h-2.5 rounded-full" style={{ backgroundColor: p.color }} />
              <span className="text-gray-700">{p.name}</span>
              <span className="ml-auto font-medium text-gray-900">{Math.round(p.value)}%</span>
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="card p-6">
      {/* En-tête */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="section-title">Comparaison des modèles IA</h3>
          <p className="muted">Performance de {(data?.models?.length ?? 0)} modèles sur {(data?.totalAnalyses ?? 0)} analyses</p>
        </div>
        <div className="flex items-center space-x-2">
          <Filter className="h-4 w-4 text-gray-500" />
          <select
            value={metricFilter}
            onChange={(e) => setMetricFilter(e.target.value as any)}
            className="text-sm border border-gray-300 rounded-md px-3 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="visibility">Score de visibilité</option>
            <option value="mentions">Mentions de marque</option>
            <option value="links">Liens vers le site</option>
          </select>
        </div>
      </div>

      {/* KPIs compacts */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
        <div className="rounded-md border border-gray-200 p-3 text-center">
          <div className="flex items-center justify-center space-x-1 mb-1">
            <Award className="h-4 w-4 text-yellow-600" />
            <span className="text-sm text-gray-600">Meilleur modèle</span>
          </div>
          <div className="text-base font-semibold text-gray-900">{data.bestModel?.name || '—'}</div>
          <div className="text-xs text-gray-500">{data.bestModel ? `${data.bestModel.avgScore}% moy.` : '—'}</div>
        </div>
        <div className="rounded-md border border-gray-200 p-3 text-center">
          <div className="flex items-center justify-center space-x-1 mb-1">
            <Brain className="h-4 w-4 text-blue-600" />
            <span className="text-sm text-gray-600">Modèles testés</span>
          </div>
          <div className="text-base font-semibold text-gray-900">{data.models?.length ?? 0}</div>
        </div>
        <div className="rounded-md border border-gray-200 p-3 text-center">
          <div className="text-sm text-gray-600 mb-1">Écart max</div>
          <div className="text-base font-semibold text-gray-900">{data?.maxGap ?? 0}%</div>
          <div className="text-xs text-gray-500">entre modèles</div>
        </div>
        <div className="rounded-md border border-gray-200 p-3 text-center">
          <div className="text-sm text-gray-600 mb-1">Analyses</div>
          <div className="text-base font-semibold text-gray-900">{data?.totalAnalyses ?? 0}</div>
        </div>
      </div>

      {/* Courbe */}
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data.chartData || []} margin={{ top: 8, right: 24, left: 12, bottom: 8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey="date" tick={{ fontSize: 12 }} stroke="#6b7280" />
            <YAxis tick={{ fontSize: 12 }} stroke="#6b7280" domain={[0, 100]} />
            <Legend wrapperStyle={{ paddingTop: 8 }} />
            <Tooltip content={<CustomTooltip />} />
            {(data.models || []).map((model: any, index: number) => (
              <Line
                key={model.id}
                type="monotone"
                dataKey={`model_${model.id}`}
                stroke={colors[index % colors.length]}
                strokeWidth={2.5}
                dot={{ r: 3, strokeWidth: 1.5, fill: colors[index % colors.length] }}
                name={model.name}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
} 