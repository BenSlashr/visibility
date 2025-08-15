import { useState, useEffect } from 'react'
import { apiClient } from '../services/api'

interface DashboardStats {
  totalAnalyses: number
  totalCost: number
  averageVisibilityScore: number
  brandMentionRate: number
  websiteLinkRate: number
  averageTokens: number
  analysesThisWeek: number
  analysesChange: number
  costChange: number
}

interface ProjectAnalysisStats {
  total_analyses: number
  brand_mentions: number
  website_mentions: number
  website_links: number
  average_visibility_score: number
  total_cost: number
  total_tokens: number
  average_processing_time: number
  top_ranking_position: number | null
  brand_mention_rate: number
  website_mention_rate: number
  website_link_rate: number
  analyses_last_7_days: number
  analyses_last_30_days: number
  cost_last_7_days: number
  cost_last_30_days: number
}

interface UseDashboardStatsReturn {
  stats: DashboardStats | null
  loading: boolean
  error: string | null
  refresh: () => Promise<void>
}

export const useDashboardStats = (projectId?: string): UseDashboardStatsReturn => {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchStats = async () => {
    try {
      setLoading(true)
      setError(null)
      console.log('🔄 Chargement des statistiques du dashboard pour le projet:', projectId)

      if (!projectId) {
        // Si aucun projet n'est sélectionné, retourner des stats vides
        setStats({
          totalAnalyses: 0,
          totalCost: 0,
          averageVisibilityScore: 0,
          brandMentionRate: 0,
          websiteLinkRate: 0,
          averageTokens: 0,
          analysesThisWeek: 0,
          analysesChange: 0,
          costChange: 0
        })
        setLoading(false)
        return
      }

      // Récupérer les statistiques spécifiques au projet
      const response = await apiClient.get(`/analyses/stats/project/${projectId}`)
      const projectStats = response.data as ProjectAnalysisStats
      
      // Calculer les changements par rapport à la période précédente
      const analysesChange = (projectStats.analyses_last_7_days || 0) - 
                            ((projectStats.analyses_last_30_days || 0) - (projectStats.analyses_last_7_days || 0))
      
      const costChange = (projectStats.cost_last_7_days || 0) - 
                        ((projectStats.cost_last_30_days || 0) - (projectStats.cost_last_7_days || 0))

      // Construire l'objet des statistiques
      const dashboardStats: DashboardStats = {
        totalAnalyses: projectStats.total_analyses || 0,
        totalCost: projectStats.total_cost || 0,
        averageVisibilityScore: Math.round(projectStats.average_visibility_score || 0),
        brandMentionRate: Math.round((projectStats.brand_mention_rate || 0) * 100),
        websiteLinkRate: Math.round((projectStats.website_link_rate || 0) * 100),
        averageTokens: projectStats.total_analyses > 0 ? 
          Math.round((projectStats.total_tokens || 0) / projectStats.total_analyses) : 0,
        analysesThisWeek: projectStats.analyses_last_7_days || 0,
        analysesChange: analysesChange,
        costChange: costChange
      }

      setStats(dashboardStats)
      console.log('✅ Statistiques du dashboard chargées pour le projet:', dashboardStats)
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erreur inconnue'
      console.error('❌ Erreur lors du chargement des statistiques:', err)
      setError(`Erreur lors du chargement des statistiques: ${errorMessage}`)
    } finally {
      setLoading(false)
    }
  }

  const refresh = async () => {
    await fetchStats()
  }

  // Chargement initial et rechargement quand le projet change
  useEffect(() => {
    fetchStats()
  }, [projectId])

  return {
    stats,
    loading,
    error,
    refresh
  }
} 