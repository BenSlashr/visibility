/**
 * Hook React pour gérer les données NLP d'une analyse
 */

import { useState, useEffect } from 'react'
import { NLPService, AnalysisNLPResponse } from '../services/nlp'

interface UseNLPAnalysisReturn {
  nlpData: AnalysisNLPResponse | null
  loading: boolean
  error: string | null
  reanalyze: () => Promise<void>
  refresh: () => Promise<void>
}

export const useNLPAnalysis = (analysisId: string | null): UseNLPAnalysisReturn => {
  const [nlpData, setNlpData] = useState<AnalysisNLPResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchNLPData = async () => {
    if (!analysisId) return

    try {
      setLoading(true)
      setError(null)
      
      const data = await NLPService.getAnalysisNLP(analysisId)
      setNlpData(data)
    } catch (err: any) {
      console.error('Erreur lors du chargement des données NLP:', err)
      setError(err?.message || 'Erreur lors du chargement des données NLP')
    } finally {
      setLoading(false)
    }
  }

  const reanalyze = async () => {
    if (!analysisId) return

    try {
      setLoading(true)
      setError(null)
      
      await NLPService.reanalyzeAnalysisNLP(analysisId)
      // Recharger les données après re-analyse
      await fetchNLPData()
    } catch (err: any) {
      console.error('Erreur lors de la re-analyse NLP:', err)
      setError(err?.message || 'Erreur lors de la re-analyse NLP')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchNLPData()
  }, [analysisId])

  return {
    nlpData,
    loading,
    error,
    reanalyze,
    refresh: fetchNLPData
  }
}