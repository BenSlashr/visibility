import { useState, useEffect } from 'react'
import { ApiClient } from '../services/api'

interface PromptStats {
  promptId: string
  totalAnalyses: number
  avgVisibilityScore: number
  brandMentionRate: number
  websiteLinkRate: number
  avgCompetitorsMentioned: number
  lastAnalysis?: {
    brand_mentioned: boolean
    website_linked: boolean
    visibility_score: number
    competitors_mentioned: number
    created_at: string
  }
}

interface UsePromptStatsReturn {
  promptStats: Record<string, PromptStats>
  loading: boolean
  error: string | null
  refresh: () => Promise<void>
}

export const usePromptStats = (projectId?: string): UsePromptStatsReturn => {
  const [promptStats, setPromptStats] = useState<Record<string, PromptStats>>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchPromptStats = async () => {
    if (!projectId) return

    try {
      setLoading(true)
      setError(null)
      console.log('🔄 Chargement des statistiques des prompts...')

      // Récupérer toutes les analyses du projet
      const analyses = await ApiClient.get<any[]>(`/analyses/?project_id=${projectId}&limit=1000`)
      
      // Grouper les analyses par prompt_id
      const analysesByPrompt: Record<string, any[]> = {}
      analyses.forEach(analysis => {
        if (!analysesByPrompt[analysis.prompt_id]) {
          analysesByPrompt[analysis.prompt_id] = []
        }
        analysesByPrompt[analysis.prompt_id].push(analysis)
      })

      // Calculer les statistiques pour chaque prompt
      const stats: Record<string, PromptStats> = {}
      
      Object.entries(analysesByPrompt).forEach(([promptId, promptAnalyses]) => {
        // Trier par date (plus récent en premier)
        const sortedAnalyses = promptAnalyses.sort((a, b) => 
          new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        )

        const totalAnalyses = promptAnalyses.length
        const avgVisibilityScore = promptAnalyses.reduce((sum, a) => sum + (a.visibility_score || 0), 0) / totalAnalyses
        const brandMentionRate = (promptAnalyses.filter(a => a.brand_mentioned).length / totalAnalyses) * 100
        const websiteLinkRate = (promptAnalyses.filter(a => a.website_linked).length / totalAnalyses) * 100
        const avgCompetitorsMentioned = promptAnalyses.reduce((sum, a) => sum + (a.competitors_mentioned || 0), 0) / totalAnalyses

        // Dernière analyse pour les données actuelles
        const lastAnalysis = sortedAnalyses[0]

        stats[promptId] = {
          promptId,
          totalAnalyses,
          avgVisibilityScore: Math.round(avgVisibilityScore),
          brandMentionRate: Math.round(brandMentionRate),
          websiteLinkRate: Math.round(websiteLinkRate),
          avgCompetitorsMentioned: Math.round(avgCompetitorsMentioned * 10) / 10,
          lastAnalysis: lastAnalysis ? {
            brand_mentioned: lastAnalysis.brand_mentioned,
            website_linked: lastAnalysis.website_linked,
            visibility_score: lastAnalysis.visibility_score,
            competitors_mentioned: lastAnalysis.competitors_mentioned,
            created_at: lastAnalysis.created_at
          } : undefined
        }
      })

      setPromptStats(stats)
      console.log('✅ Statistiques des prompts chargées:', Object.keys(stats).length, 'prompts')
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erreur inconnue'
      console.error('❌ Erreur lors du chargement des statistiques des prompts:', err)
      setError(`Erreur lors du chargement des statistiques: ${errorMessage}`)
    } finally {
      setLoading(false)
    }
  }

  const refresh = async () => {
    await fetchPromptStats()
  }

  // Chargement initial
  useEffect(() => {
    fetchPromptStats()
  }, [projectId])

  return {
    promptStats,
    loading,
    error,
    refresh
  }
} 