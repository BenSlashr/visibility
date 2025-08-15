import React, { useState, useEffect } from 'react'
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip as RechartsTooltip, 
  Legend as RechartsLegend, 
  ResponsiveContainer 
} from 'recharts'
import { motion } from 'framer-motion'
import { TrendingUp, TrendingDown, Tag } from 'lucide-react'
import { useVisibilityChart } from '../../hooks/useVisibilityChart'
import { PromptsAPI } from '../../services/prompts'
import { Loading } from '../ui'

interface VisibilityChartProps {
  timeFilter: string
  projectId?: string
  tagFilter?: string
  modelId?: string
  onPointClick?: (payload: { date: string }) => void
  variant?: 'card' | 'embedded'
}

export const VisibilityChart: React.FC<VisibilityChartProps> = ({ timeFilter, projectId, tagFilter = '', modelId, onPointClick, variant = 'card' }) => {
  const [selectedTag, setSelectedTag] = useState<string>('')
  const [availableTags, setAvailableTags] = useState<string[]>([])
  const [loadingTags, setLoadingTags] = useState(false)
  
  const { data, loading, error } = useVisibilityChart(timeFilter, projectId, selectedTag || tagFilter, modelId)
  const [visibleKeys, setVisibleKeys] = useState<Record<string, boolean>>({
    visibilityScore: true,
    brandMentioned: true,
    websiteLinked: true,
  })

  const toggleKey = (key: string) => setVisibleKeys(v => ({ ...v, [key]: !v[key] }))

  const legendPayload = [
    { id: 'visibilityScore', value: 'Score de visibilité', color: '#3b82f6' },
    { id: 'brandMentioned', value: 'Taux de mention', color: '#10b981' },
    { id: 'websiteLinked', value: 'Taux de liens', color: '#8b5cf6' },
  ]

  const CustomLegend = () => (
    <div className="flex flex-wrap gap-4 text-sm">
      {legendPayload.map(item => (
        <button
          key={item.id}
          onClick={() => toggleKey(item.id)}
          className={`inline-flex items-center gap-2 ${visibleKeys[item.id] ? 'opacity-100' : 'opacity-40'} hover:opacity-100`}
        >
          <span className="inline-block w-3 h-3 rounded-full" style={{ backgroundColor: item.color }} />
          {item.value}
        </button>
      ))}
    </div>
  )

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (!active || !payload || !payload.length) return null
    return (
      <div className="rounded-md border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-3 shadow">
        <div className="text-xs text-gray-600 dark:text-gray-400 mb-1">{label}</div>
        {payload.map((p: any) => {
          const prevKey = `${p.dataKey}Prev`
          const prev = p?.payload?.[prevKey]
          const val = Math.round(p.value)
          const delta = typeof prev === 'number' ? val - Math.round(prev) : undefined
          return (
          <div key={p.dataKey} className="flex items-center gap-2 text-sm">
            <span className="inline-block w-3 h-3 rounded-full" style={{ backgroundColor: p.color }} />
            <span className="text-gray-800 dark:text-gray-100">{p.name}:</span>
            <span className="font-medium text-gray-900 dark:text-gray-50">{val}%</span>
            {typeof delta === 'number' && (
              <span className={`text-xs ${delta >= 0 ? 'text-green-600' : 'text-red-600'}`}> {delta >= 0 ? '+' : ''}{delta}%</span>
            )}
          </div>
        )})}
      </div>
    )
  }

  // Charger les tags disponibles quand le projet change
  useEffect(() => {
    const loadTags = async () => {
      if (!projectId) {
        setAvailableTags([])
        return
      }

      try {
        setLoadingTags(true)
        const prompts = await PromptsAPI.getAll({ project_id: projectId, limit: 1000 })
        
        // Extraire tous les tags uniques
        const allTags = new Set<string>()
        prompts.forEach(prompt => {
          if (prompt.tags && prompt.tags.length > 0) {
            prompt.tags.forEach(tag => allTags.add(tag))
          }
        })
        
        setAvailableTags(Array.from(allTags).sort())
      } catch (error) {
        console.error('❌ Erreur lors du chargement des tags:', error)
      } finally {
        setLoadingTags(false)
      }
    }

    loadTags()
  }, [projectId])

  // Réinitialiser le tag sélectionné quand le projet change
  useEffect(() => {
    setSelectedTag('')
  }, [projectId])

  if (loading) {
    return (
      <div className={variant === 'card' ? 'card p-6' : 'p-6'}>
        <div className="flex items-center justify-center h-80">
          <Loading size="lg" text="Chargement du graphique..." />
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className={variant === 'card' ? 'card p-6' : 'p-6'}>
        <div className="flex items-center justify-center h-80 text-red-600">
          ❌ Erreur lors du chargement du graphique
        </div>
      </div>
    )
  }

  if (!data || data.chartData.length === 0) {
    return (
      <div className={variant === 'card' ? 'card p-6' : 'p-6'}>
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="section-title">Évolution de la visibilité</h3>
            <p className="muted">
              {projectId ? 'Aucune donnée disponible pour cette période' : 'Sélectionnez un projet pour voir les données'}
            </p>
          </div>
        </div>
        <div className="flex items-center justify-center h-80 text-gray-500">
          <div className="text-center">
            <div className="text-4xl mb-4">📊</div>
            <p>Aucune analyse disponible</p>
            <p className="text-sm mt-2">Exécutez des prompts pour voir l'évolution</p>
          </div>
        </div>
      </div>
    )
  }

  const Wrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
    variant === 'card' 
      ? <motion.div className="card p-6" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.2 }}>{children}</motion.div>
      : <div className="p-6">{children}</div>
  )

  return (
    <Wrapper>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="section-title">Évolution de la visibilité</h3>
          <p className="muted">
            Suivi des performances au fil du temps ({data.totalAnalyses} analyses)
            {selectedTag && <span className="text-blue-600"> • Tag: {selectedTag}</span>}
          </p>
        </div>
        
        <div className="flex items-center space-x-4">
          {/* Filtre par tag */}
          {availableTags.length > 0 && (
            <div className="flex items-center space-x-2">
              <Tag className="h-4 w-4 text-gray-500" />
              <select
                value={selectedTag}
                onChange={(e) => setSelectedTag(e.target.value)}
                disabled={loadingTags}
                className="text-sm border border-gray-300 rounded-md px-3 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Tous les tags</option>
                {availableTags.map(tag => (
                  <option key={tag} value={tag}>{tag}</option>
                ))}
              </select>
            </div>
          )}

          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">{data.currentScore}%</div>
            <div className="text-xs text-gray-600">Score actuel</div>
          </div>
          <div className="flex items-center space-x-1">
            {data.weeklyChange >= 0 ? (
              <TrendingUp className="h-4 w-4 text-green-600" />
            ) : (
              <TrendingDown className="h-4 w-4 text-red-600" />
            )}
            <span className={`text-sm font-medium ${
              data.weeklyChange >= 0 ? 'text-green-600' : 'text-red-600'
            }`}>
              {data.weeklyChange >= 0 ? '+' : ''}{data.weeklyChange}%
            </span>
            <span className="text-xs text-gray-600">vs période précédente</span>
          </div>
        </div>
      </div>

      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart 
            data={data.chartData.map((p: any) => ({
              // Affichage lisible sur l'axe X
              date: new Date(p.isoDate).toLocaleDateString('fr-FR', { month: 'short', day: 'numeric' }),
              ...p,
            }))} 
            margin={{ top: 5, right: 30, left: 20, bottom: 5 }} 
            onClick={(e: any) => {
              if (onPointClick && e && e.activePayload && e.activePayload[0]) {
                const original = e.activePayload[0].payload
                const isoDate = original?.isoDate
                if (isoDate) onPointClick({ date: isoDate })
              }
            }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke={document.documentElement.classList.contains('dark') ? '#1f2937' : '#f0f0f0'} />
            <XAxis 
              dataKey="date" 
              tick={{ fontSize: 12 }}
              stroke="#6b7280"
            />
            <YAxis 
              tick={{ fontSize: 12 }}
              stroke="#6b7280"
              domain={[0, 100]}
            />
            <RechartsTooltip content={<CustomTooltip />} wrapperStyle={{ backdropFilter: 'blur(8px)' }} />
            <RechartsLegend content={<CustomLegend />} />

            {visibleKeys.visibilityScore && (
            <Line 
              type="monotone" 
              dataKey="visibilityScore" 
              stroke="#3b82f6" 
              strokeWidth={3}
              dot={{ fill: '#3b82f6', strokeWidth: 2, r: 4 }}
              name="Score de visibilité"
            />)}
            {visibleKeys.brandMentioned && (
            <Line 
              type="monotone" 
              dataKey="brandMentioned" 
              stroke="#10b981" 
              strokeWidth={2}
              dot={{ fill: '#10b981', strokeWidth: 2, r: 3 }}
              name="Taux de mention"
            />)}
            {visibleKeys.websiteLinked && (
            <Line 
              type="monotone" 
              dataKey="websiteLinked" 
              stroke="#8b5cf6" 
              strokeWidth={2}
              dot={{ fill: '#8b5cf6', strokeWidth: 2, r: 3 }}
              name="Taux de liens"
            />)}
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-4 grid grid-cols-3 gap-4 text-center border-t pt-4">
        <div>
          <div className="text-sm font-medium text-gray-900">Score moyen</div>
          <div className="text-2xl font-bold text-blue-600">{data.currentScore}%</div>
        </div>
        <div>
          <div className="text-sm font-medium text-gray-900">Évolution</div>
          <div className={`text-2xl font-bold ${
            data.weeklyChange >= 0 ? 'text-green-600' : 'text-red-600'
          }`}>
            {data.weeklyChange >= 0 ? '+' : ''}{data.weeklyChange}%
          </div>
        </div>
        <div>
          <div className="text-sm font-medium text-gray-900">Analyses</div>
          <div className="text-2xl font-bold text-gray-900">{data.totalAnalyses}</div>
        </div>
      </div>
    </Wrapper>
  )
} 