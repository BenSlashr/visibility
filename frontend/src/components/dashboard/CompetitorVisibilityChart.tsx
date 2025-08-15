import React from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { useCompetitorVisibilityChart } from '../../hooks/useCompetitorVisibilityChart'
import { Loading } from '../ui'

interface CompetitorVisibilityChartProps {
  timeFilter: string
  projectId?: string
}

export const CompetitorVisibilityChart: React.FC<CompetitorVisibilityChartProps> = ({ 
  timeFilter, 
  projectId 
}) => {
  const { data, loading, error } = useCompetitorVisibilityChart(timeFilter, projectId)

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
        <div className="flex items-center justify-center h-80">
          <Loading size="lg" text="Chargement de la comparaison..." />
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
        <div className="flex items-center justify-center h-80 text-red-600">
          ❌ Erreur lors du chargement de la comparaison
        </div>
      </div>
    )
  }

  if (!data || data.chartData.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Comparaison avec les concurrents</h3>
            <p className="text-sm text-gray-600">
              {projectId ? 'Aucune donnée de comparaison disponible' : 'Sélectionnez un projet pour voir la comparaison'}
            </p>
          </div>
        </div>
        <div className="flex items-center justify-center h-80 text-gray-500">
          <div className="text-center">
            <div className="text-4xl mb-4">🏆</div>
            <p>Aucune donnée de comparaison</p>
            <p className="text-sm mt-2">Ajoutez des concurrents et exécutez des analyses</p>
          </div>
        </div>
      </div>
    )
  }

  // Couleurs pour le graphique
  const colors = [
    '#3b82f6', // Bleu pour le site principal
    '#ef4444', // Rouge pour concurrent 1
    '#10b981', // Vert pour concurrent 2
    '#f59e0b', // Orange pour concurrent 3
    '#8b5cf6', // Violet pour concurrent 4
    '#ec4899', // Rose pour concurrent 5
  ]

  return (
    <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Visibility score</h3>
          <p className="text-sm text-gray-600">Pourcentage de réponses IA qui mentionnent votre marque/site</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Graphique réduit */}
        <div className="lg:col-span-2">
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data.chartData} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="date" tick={{ fontSize: 12 }} stroke="#6b7280" />
                <YAxis tick={{ fontSize: 12 }} stroke="#6b7280" domain={[0, 100]} />
                <Tooltip contentStyle={{ backgroundColor: 'white', border: '1px solid #e5e7eb', borderRadius: '8px' }}
                  formatter={(value: any, name: string) => [ `${value}%`, name === 'mainSite' ? 'Votre site' : name ]}
                />
                {/* Lignes */}
                <Line type="monotone" dataKey="mainSite" stroke={colors[0]} strokeWidth={3} dot={{ r: 3 }} name="Votre site" />
                {data.competitors.map((competitor, index) => (
                  <Line key={competitor.id} type="monotone" dataKey={`competitor_${competitor.id}`} stroke={colors[(index + 1) % colors.length]} strokeWidth={2} dot={false} name={competitor.name} />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-2 flex items-center justify-end">
            <div className="text-sm text-gray-500">{data.totalAnalyses} analyses</div>
          </div>
        </div>

        {/* Classement à droite */}
        <div className="lg:col-span-1">
          <div className="rounded-lg border border-gray-200">
            <div className="px-4 py-3 border-b border-gray-200">
              <div className="text-sm font-medium text-gray-900">Classement des marques</div>
              <div className="text-xs text-gray-500">Rang actuel et score moyen</div>
            </div>
            <div className="divide-y">
              {data.competitorRanking.map((item, index) => (
                <div key={item.id} className="flex items-center justify-between px-4 py-3">
                  <div className="flex items-center gap-3">
                    <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold text-white ${
                      index === 0 ? 'bg-green-600' : index === 1 ? 'bg-blue-500' : index === 2 ? 'bg-purple-600' : 'bg-gray-400'
                    }`}>{index + 1}</div>
                    <div>
                      <div className={`text-sm font-medium ${item.isMainSite ? 'text-blue-600' : 'text-gray-900'}`}>{item.name}{item.isMainSite && ' (vous)'}</div>
                      <div className="text-xs text-gray-500">Visibilité {item.score}% • Taux de mention {item.mentionRate}% • Taux de liens {item.linkRate}%</div>
                    </div>
                  </div>
                  <div className="text-lg font-semibold text-gray-900">{item.score}%</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
} 