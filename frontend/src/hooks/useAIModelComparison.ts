import { useState, useEffect } from 'react'
import { AnalysesAPI } from '../services/analyses'
// import type { AnalysisSummary } from '../types/analysis'

interface ChartDataPoint {
  date: string
  [key: string]: number | string // Pour les données des modèles dynamiques
}

interface AIModelInfo {
  id: string
  name: string
  provider: string
  avgScore: number
  totalAnalyses: number
  brandMentionRate: number
  websiteLinkRate: number
}

interface AIModelComparisonData {
  chartData: ChartDataPoint[]
  models: AIModelInfo[]
  bestModel: AIModelInfo
  maxGap: number
  totalAnalyses: number
  modelRanking: AIModelInfo[]
}

interface UseAIModelComparisonReturn {
  data: AIModelComparisonData | null
  loading: boolean
  error: string | null
  refresh: (timeFilter?: string, projectId?: string, metricFilter?: string) => Promise<void>
}

export const useAIModelComparison = (
  timeFilter: string = 'last7days', 
  projectId?: string,
  metricFilter: string = 'all'
): UseAIModelComparisonReturn => {
  const [data, setData] = useState<AIModelComparisonData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadAIModelComparisonData = async (
    filter: string = timeFilter, 
    currentProjectId?: string,
    currentMetricFilter: string = metricFilter
  ) => {
    try {
      setLoading(true)
      setError(null)

      console.log(`🔄 Chargement comparaison IA (${filter}, ${currentMetricFilter}) pour le projet:`, currentProjectId)

      if (!currentProjectId) {
        setData({
          chartData: [],
          models: [],
          bestModel: { id: '', name: '', provider: '', avgScore: 0, totalAnalyses: 0, brandMentionRate: 0, websiteLinkRate: 0 },
          maxGap: 0,
          totalAnalyses: 0,
          modelRanking: []
        })
        setLoading(false)
        return
      }

      // Déterminer période
      const daysCount = filter === 'last24h' ? 1 : filter === 'last7days' ? 7 : filter === 'last30days' ? 30 : 7
      const dateTo = new Date()
      const dateFrom = new Date()
      dateFrom.setDate(dateTo.getDate() - daysCount)

      // Récupérer la comparaison agrégée depuis l'API
      const payload = await AnalysesAPI.getModelComparison({
        project_id: currentProjectId,
        date_from: dateFrom.toISOString().split('T')[0],
        date_to: dateTo.toISOString().split('T')[0],
        metric: currentMetricFilter
      })

      if (!payload || !payload.models || payload.models.length === 0) {
        setData({
          chartData: [],
          models: [],
          bestModel: { id: '', name: '', provider: '', avgScore: 0, totalAnalyses: 0, brandMentionRate: 0, websiteLinkRate: 0 },
          maxGap: 0,
          totalAnalyses: 0,
          modelRanking: []
        })
        setLoading(false)
        return
      }
      // Sécuriser la forme des séries (model_{id} cohérent avec data.models[].id)
      const models: AIModelInfo[] = (payload.models || []).map((m: any) => ({
        id: m.id,
        name: m.name,
        provider: m.provider || '',
        avgScore: m.avgScore || 0,
        totalAnalyses: m.totalAnalyses || 0,
        brandMentionRate: m.brandMentionRate || 0,
        websiteLinkRate: m.websiteLinkRate || 0
      }))
      const clamp = (n: any) => {
        const x = Number(n)
        if (!isFinite(x) || isNaN(x)) return 0
        if (x < 0) return 0
        if (x > 100) return 100
        return x
      }

      const chartData: ChartDataPoint[] = (payload.chartData || payload.chartdata || []).map((row: any) => {
        const safe: any = { date: row.date }
        models.forEach((m) => {
          const key = `model_${m.id}`
          // Accepter soit model_{id} (nouvelle forme), soit model_{name} (ancienne forme) en secours
          if (row[key] !== undefined) safe[key] = clamp(row[key])
          else if (row[`model_${m.name}`] !== undefined) safe[key] = clamp(row[`model_${m.name}`])
          else safe[key] = 0
        })
        return safe
      })

      const comparisonData: AIModelComparisonData = {
        chartData,
        models,
        bestModel: payload.bestModel || models[0] || { id: '', name: '', provider: '', avgScore: 0, totalAnalyses: 0, brandMentionRate: 0, websiteLinkRate: 0 },
        maxGap: payload.maxGap || 0,
        totalAnalyses: payload.totalAnalyses || 0,
        modelRanking: payload.modelRanking || []
      }

      setData(comparisonData)
      console.log('✅ Données de comparaison IA traitées:', comparisonData)
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erreur inconnue'
      console.error('❌ Erreur lors du chargement de la comparaison IA:', err)
      setError(`Erreur lors du chargement: ${errorMessage}`)
    } finally {
      setLoading(false)
    }
  }

  const refresh = async (filter?: string, currentProjectId?: string, currentMetricFilter?: string) => {
    await loadAIModelComparisonData(
      filter || timeFilter, 
      currentProjectId || projectId,
      currentMetricFilter || metricFilter
    )
  }

  // Chargement initial et rechargement quand les paramètres changent
  useEffect(() => {
    loadAIModelComparisonData(timeFilter, projectId, metricFilter)
  }, [timeFilter, projectId, metricFilter])

  return {
    data,
    loading,
    error,
    refresh
  }
} 