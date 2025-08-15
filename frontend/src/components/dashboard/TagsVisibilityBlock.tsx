import React, { useMemo, useState } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts'
import { useTagsVisibilityChart } from '../../hooks/useTagsVisibilityChart'

interface Props {
  projectId?: string
}

const COLORS = ["#2563eb", "#ef4444", "#10b981", "#f59e0b", "#8b5cf6", "#06b6d4", "#22c55e", "#e11d48", "#a855f7", "#fb923c"]

export const TagsVisibilityBlock: React.FC<Props> = ({ projectId }) => {
  const { data, loading, error } = useTagsVisibilityChart(projectId)
  const [selectedTags, setSelectedTags] = useState<string[]>([])

  const allSeries = useMemo(() => {
    if (!data) return [] as string[]
    // Extraire toutes les clés (tags) présentes dans le jeu de données
    const keys = Object.keys(
      (data.chartData || []).reduce((acc: any, row: any) => {
        Object.keys(row).forEach(k => { if (k !== 'date') acc[k] = true })
        return acc
      }, {})
    )
    return keys
  }, [data])

  const visibleTags = useMemo(() => {
    if (!data) return [] as string[]
    if (selectedTags.length > 0) return selectedTags
    // Par défaut, afficher les 3 meilleurs tags
    return (data.ranking || []).slice(0, 3).map(r => r.tag)
  }, [data, selectedTags])

  const colorOf = (tag: string, idx: number) => COLORS[idx % COLORS.length]

  const toggleTag = (tag: string) => {
    setSelectedTags(prev => {
      if (prev.includes(tag)) return prev.filter(t => t !== tag)
      const next = [...prev, tag]
      // Limiter à 3 tags pour garder un graphe lisible
      return next.slice(-3)
    })
  }

  return (
    <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Visibilité par tags</h3>
          <p className="text-sm text-gray-600">Évolution et classement des tags (clic pour comparer, max 3)</p>
        </div>
        <div className="text-xs text-gray-500">Astuce: cliquez sur un tag à droite pour l’ajouter/retirer du graphique</div>
      </div>

      {loading || !data ? (
        <div className="text-gray-500 py-16 text-center">Chargement…</div>
      ) : error ? (
        <div className="text-red-600 py-16 text-center">Erreur: {error}</div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Graphique */}
          <div className="lg:col-span-2">
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data.chartData} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="date" tick={{ fontSize: 12 }} stroke="#6b7280" />
                  <YAxis tick={{ fontSize: 12 }} stroke="#6b7280" domain={[0, 100]} />
                  <Tooltip contentStyle={{ backgroundColor: 'white', border: '1px solid #e5e7eb', borderRadius: '8px' }} />
                  {/* Lignes: uniquement les tags sélectionnés (max 3) */}
                  {visibleTags.map((tag) => (
                    <Line key={tag} type="monotone" dataKey={tag} stroke={colorOf(tag, allSeries.indexOf(tag))} strokeWidth={3} dot={false} name={tag} />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            </div>
            {/* Légende compacte */}
            <div className="mt-3 flex flex-wrap items-center gap-3">
              {visibleTags.map((tag) => (
                <div key={tag} className="flex items-center gap-2 text-xs text-gray-700">
                  <span className="inline-block w-3 h-3 rounded" style={{ backgroundColor: colorOf(tag, allSeries.indexOf(tag)) }} />
                  <span>{tag}</span>
                </div>
              ))}
              <div className="ml-auto text-sm text-gray-500">{data.totalAnalyses} analyses</div>
            </div>
          </div>

          {/* Classement */}
          <div className="lg:col-span-1">
            <div className="rounded-lg border border-gray-200">
              <div className="px-4 py-3 border-b border-gray-200">
                <div className="text-sm font-medium text-gray-900">Classement des tags</div>
                <div className="text-xs text-gray-500">Score, taux, micro-tendance</div>
              </div>
              <div className="divide-y">
                {data.ranking.map((item, idx) => (
                  <button key={item.tag} onClick={() => toggleTag(item.tag)} className={`w-full flex items-center justify-between px-4 py-3 text-left hover:bg-gray-50 ${selectedTags.includes(item.tag) ? 'bg-blue-50' : ''}`}>
                    <div className="flex items-center gap-3">
                      <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold text-white ${idx===0?'bg-green-600':idx===1?'bg-blue-500':idx===2?'bg-purple-600':'bg-gray-400'}`}>{idx+1}</div>
                      <div>
                        <div className="text-sm font-medium text-gray-900 flex items-center gap-2">
                          <span className="inline-block w-3 h-3 rounded" style={{ backgroundColor: colorOf(item.tag, allSeries.indexOf(item.tag)) }} />
                          {item.tag}
                          {selectedTags.includes(item.tag) && <span className="text-[10px] text-blue-600 border border-blue-200 rounded px-1">sélectionné</span>}
                        </div>
                        <div className="text-xs text-gray-500">Visibilité {item.score}% • Taux mention {item.mentionRate}% • Liens {item.linkRate}%</div>
                        {/* sparkline */}
                        <div className="h-8 w-40 mt-1">
                          <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={(item.trend || []).map((v, i) => ({ i, v }))}>
                              <Area type="monotone" dataKey="v" stroke={colorOf(item.tag, allSeries.indexOf(item.tag))} strokeWidth={2} fillOpacity={0.1} fill={colorOf(item.tag, allSeries.indexOf(item.tag))} />
                            </AreaChart>
                          </ResponsiveContainer>
                        </div>
                      </div>
                    </div>
                    <div className="text-lg font-semibold text-gray-900">{item.score}%</div>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}


