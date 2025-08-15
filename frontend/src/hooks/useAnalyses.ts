import { useState, useEffect, useCallback } from 'react'
import { AnalysesAPI } from '../services/analyses'
import { PromptsAPI } from '../services/prompts'
import type { 
  AnalysisSummary, 
  AnalysisFilters,
  Analysis
} from '../types/analysis'
import type { PromptExecuteRequest } from '../types/prompt'

interface UseAnalysesReturn {
  analyses: AnalysisSummary[]
  loading: boolean
  error: string | null
  fetchAnalyses: (filters?: AnalysisFilters) => Promise<void>
  executePrompt: (promptId: string, request?: PromptExecuteRequest) => Promise<Analysis | null>
  getRecentAnalyses: (days?: number) => Promise<AnalysisSummary[]>
  refresh: () => Promise<void>
}

export const useAnalyses = (initialFilters?: AnalysisFilters): UseAnalysesReturn => {
  const [analyses, setAnalyses] = useState<AnalysisSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchAnalyses = useCallback(async (filters?: AnalysisFilters) => {
    try {
      setLoading(true)
      setError(null)
      console.log('🔄 Chargement des analyses...', filters)
      
      const analysesData = await AnalysesAPI.getAll(filters || initialFilters)
      setAnalyses(analysesData)
      console.log('✅ Analyses chargées:', analysesData.length)
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erreur inconnue'
      console.error('❌ Erreur lors du chargement des analyses:', err)
      setError(`Erreur lors du chargement des analyses: ${errorMessage}`)
    } finally {
      setLoading(false)
    }
  }, [initialFilters])

  const executePrompt = async (promptId: string, request?: PromptExecuteRequest): Promise<Analysis | null> => {
    try {
      console.log('🚀 Exécution du prompt:', promptId)
      setError(null)
      
      // Exécuter le prompt via l'API
      const result = await PromptsAPI.execute(promptId, request)
      
      if (result.success && result.analysis_id) {
        // Récupérer l'analyse complète créée
        const newAnalysis = await AnalysesAPI.getById(result.analysis_id)
        
        // Recharger la liste des analyses
        await fetchAnalyses()
        
        console.log('✅ Prompt exécuté avec succès:', result.analysis_id)
        return newAnalysis
      } else {
        throw new Error(result.error || 'Erreur lors de l\'exécution')
      }
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erreur inconnue'
      console.error('❌ Erreur lors de l\'exécution du prompt:', err)
      setError(`Erreur lors de l'exécution: ${errorMessage}`)
      return null
    }
  }

  const getRecentAnalyses = async (days: number = 7): Promise<AnalysisSummary[]> => {
    try {
      console.log(`🔄 Chargement des analyses récentes (${days} jours)...`)
      const recentAnalyses = await AnalysesAPI.getRecent(days)
      console.log('✅ Analyses récentes chargées:', recentAnalyses.length)
      return recentAnalyses
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erreur inconnue'
      console.error('❌ Erreur lors du chargement des analyses récentes:', err)
      setError(`Erreur lors du chargement des analyses récentes: ${errorMessage}`)
      return []
    }
  }

  const refresh = useCallback(async () => {
    await fetchAnalyses()
  }, [fetchAnalyses])

  // Chargement initial
  useEffect(() => {
    fetchAnalyses()
  }, [])

  return {
    analyses,
    loading,
    error,
    fetchAnalyses,
    executePrompt,
    getRecentAnalyses,
    refresh
  }
}

// Hook spécialisé pour les analyses récentes (dashboard)
export const useRecentAnalyses = (days: number = 7) => {
  const [recentAnalyses, setRecentAnalyses] = useState<AnalysisSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadRecentAnalyses = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const analyses = await AnalysesAPI.getRecent(days, 5) // Limiter à 5 pour le dashboard
      setRecentAnalyses(analyses)
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erreur inconnue'
      console.error('❌ Erreur lors du chargement des analyses récentes:', err)
      setError(`Erreur lors du chargement: ${errorMessage}`)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadRecentAnalyses()
  }, [days])

  return {
    recentAnalyses,
    loading,
    error,
    refresh: loadRecentAnalyses
  }
} 