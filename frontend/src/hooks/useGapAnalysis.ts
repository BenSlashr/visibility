import { useState, useEffect } from 'react'
import { AnalysesAPI } from '../services/analyses'

interface GapAnalysisParams {
  project_id?: string
  date_from?: string
  date_to?: string
  competitor_filter?: string
  priority_filter?: string
}

interface GapAnalysisItem {
  id: string
  query: string
  prompt_id: string
  competitor_name: string
  competitor_mentions: number
  competitor_rate: number
  our_mentions: number
  our_rate: number
  gap_score: number
  frequency_estimate: number
  last_seen: string
  gap_type: 'critical' | 'medium' | 'low'
  business_relevance: 'high' | 'medium' | 'low'
  suggested_action: string
  content_exists: boolean
}

interface GapAnalysisStats {
  total_gaps: number
  critical_gaps: number
  medium_gaps: number
  low_gaps: number
  average_gap_score: number
  potential_monthly_mentions: number
  total_analyses_analyzed: number
}

interface GapAnalysisData {
  gaps: GapAnalysisItem[]
  stats: GapAnalysisStats
}

export const useGapAnalysis = (params: GapAnalysisParams) => {
  const [data, setData] = useState<GapAnalysisData | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchGapAnalysis = async () => {
      if (!params.project_id) {
        setData(null)
        return
      }

      try {
        setLoading(true)
        setError(null)
        
        const result = await AnalysesAPI.getGapAnalysis({
          project_id: params.project_id,
          date_from: params.date_from,
          date_to: params.date_to,
          competitor_filter: params.competitor_filter,
          priority_filter: params.priority_filter
        })
        
        setData(result)
      } catch (err: any) {
        console.error('Erreur lors du chargement du gap analysis:', err)
        setError(err?.message || 'Erreur lors du chargement des données')
      } finally {
        setLoading(false)
      }
    }

    fetchGapAnalysis()
  }, [
    params.project_id, 
    params.date_from, 
    params.date_to, 
    params.competitor_filter, 
    params.priority_filter
  ])

  const refresh = () => {
    if (params.project_id) {
      // Forcer un nouveau fetch en modifiant légèrement les paramètres
      setLoading(true)
      setError(null)
      
      AnalysesAPI.getGapAnalysis({
        project_id: params.project_id,
        date_from: params.date_from,
        date_to: params.date_to,
        competitor_filter: params.competitor_filter,
        priority_filter: params.priority_filter
      })
      .then(setData)
      .catch((err) => {
        setError(err?.message || 'Erreur lors du chargement des données')
      })
      .finally(() => setLoading(false))
    }
  }

  return {
    data,
    loading,
    error,
    refresh
  }
}