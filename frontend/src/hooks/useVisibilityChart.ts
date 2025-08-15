import { useState, useEffect } from 'react'
import { ApiClient } from '../services/api'
// import type { AnalysisSummary } from '../types/analysis'

interface ChartDataPoint {
  isoDate: string
  visibilityScore: number
  brandMentioned: number
  websiteLinked: number
}

interface VisibilityChartData {
  chartData: ChartDataPoint[]
  currentScore: number
  weeklyChange: number
  totalAnalyses: number
}

interface UseVisibilityChartReturn {
  data: VisibilityChartData | null
  loading: boolean
  error: string | null
  refresh: (timeFilter?: string, projectId?: string, tagFilter?: string) => Promise<void>
}

export const useVisibilityChart = (
  timeFilter: string = 'last7days', 
  projectId?: string, 
  tagFilter: string = '',
  modelId?: string
): UseVisibilityChartReturn => {
  const [data, setData] = useState<VisibilityChartData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadVisibilityData = async (
    filter: string = timeFilter, 
    currentProjectId?: string, 
    currentTagFilter: string = tagFilter
  ) => {
    try {
      setLoading(true)
      setError(null)

      console.log(`🔄 Chargement des données de visibilité (${filter}) pour le projet:`, currentProjectId)

      if (!currentProjectId) {
        // Si aucun projet n'est sélectionné, retourner des données vides
        setData({
          chartData: [],
          currentScore: 0,
          weeklyChange: 0,
          totalAnalyses: 0
        })
        setLoading(false)
        return
      }

      // Utiliser l'endpoint agrégé timeseries pour minimiser le traitement côté client
      const daysCount = filter === 'last24h' ? 1 : filter === 'last7days' ? 7 : filter === 'last30days' ? 30 : 7
      const dateTo = new Date()
      const dateFrom = new Date()
      dateFrom.setDate(dateTo.getDate() - daysCount)
      const params: Record<string, any> = {
        project_id: currentProjectId,
        date_from: dateFrom.toISOString().split('T')[0],
        date_to: dateTo.toISOString().split('T')[0],
        tag: currentTagFilter || undefined
      }
      if (modelId) params.model_id = modelId
      // Utiliser l'alias stable pour éviter les collisions avec /{analysis_id}
      const payload = await ApiClient.get<any>('/analyses/stats/timeseries', params)

      // Adapter la réponse agrégée en chartData
      const rawPoints: Array<{ date: string; avg_visibility_score: number; brand_mention_rate: number; website_link_rate: number }> = payload?.points || []
      const chartData: ChartDataPoint[] = rawPoints.map((p: any) => ({
        isoDate: p.date, // conserver la date ISO pour le drill-down
        visibilityScore: Math.round(p.avg_visibility_score || 0),
        brandMentioned: Math.round(p.brand_mention_rate || 0),
        websiteLinked: Math.round(p.website_link_rate || 0),
      }))

      // Ajouter les valeurs précédentes pour les deltas tooltips
      for (let i = 0; i < chartData.length; i++) {
        const prev = chartData[i - 1]
        ;(chartData[i] as any).visibilityScorePrev = prev ? prev.visibilityScore : undefined
        ;(chartData[i] as any).brandMentionedPrev = prev ? prev.brandMentioned : undefined
        ;(chartData[i] as any).websiteLinkedPrev = prev ? prev.websiteLinked : undefined
      }

      // Calculer les métriques globales
      const allScores: number[] = (payload?.points || []).map((p: any) => Math.round(p.avg_visibility_score || 0))
      const currentScore = allScores.length > 0 ? 
        Math.round(allScores.reduce((sum, score) => sum + score, 0) / allScores.length) : 0

      // Calculer le changement hebdomadaire (si on a assez de données)
      let weeklyChange = 0
      if (chartData.length >= 2) {
        const firstScore: number = chartData[0].visibilityScore
        const lastScore: number = chartData[chartData.length - 1].visibilityScore
        weeklyChange = lastScore - firstScore
      }

      const visibilityData: VisibilityChartData = {
        chartData,
        currentScore,
        weeklyChange,
        totalAnalyses: (payload?.period_analyses_count as number) || (payload?.total_analyses as number) || chartData.length
      }

      setData(visibilityData)
      console.log('✅ Données de visibilité traitées:', visibilityData)
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erreur inconnue'
      console.error('❌ Erreur lors du chargement des données de visibilité:', err)
      setError(`Erreur lors du chargement: ${errorMessage}`)
    } finally {
      setLoading(false)
    }
  }

  const refresh = async (filter?: string, currentProjectId?: string, currentTagFilter?: string) => {
    await loadVisibilityData(filter || timeFilter, currentProjectId || projectId, currentTagFilter || tagFilter)
  }

  // Chargement initial et rechargement quand les paramètres changent
  useEffect(() => {
    loadVisibilityData(timeFilter, projectId, tagFilter)
  }, [timeFilter, projectId, tagFilter, modelId])

  return {
    data,
    loading,
    error,
    refresh
  }
} 