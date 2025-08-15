import { useState, useEffect, useCallback } from 'react'
import { SERPService } from '../services/serp'
import type {
  SERPSummaryResponse,
  SERPKeywordListResponse,
  SERPImportResponse,
  AutoMatchResponse,
  PromptSERPAssociationResponse,
  SERPUploadFormData,
  PromptSERPAssociationRequest,
  SERPUploadState,
  SERPMatchingState,
  SERPDashboardData
} from '../types/serp'

/**
 * Hook pour gérer les données SERP d'un projet
 */
export const useSERPProject = (projectId?: string) => {
  const [data, setData] = useState<SERPDashboardData>({
    isLoading: true,
    error: undefined
  })

  const fetchSERPData = useCallback(async () => {
    if (!projectId) return

    try {
      setData(prev => ({ ...prev, isLoading: true, error: undefined }))

      const [summary, keywords] = await Promise.all([
        SERPService.getProjectSummary(projectId),
        SERPService.getProjectKeywords(projectId).catch(() => ({ keywords: [] }))
      ])

      setData({
        summary,
        keywords: keywords.keywords.map(k => ({
          ...k,
          import_id: '',
          project_id: projectId,
          keyword_normalized: k.keyword.toLowerCase(),
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        })),
        isLoading: false
      })
    } catch (err) {
      setData({
        isLoading: false,
        error: err instanceof Error ? err.message : 'Erreur lors du chargement des données SERP'
      })
    }
  }, [projectId])

  useEffect(() => {
    fetchSERPData()
  }, [fetchSERPData])

  const refresh = useCallback(() => {
    fetchSERPData()
  }, [fetchSERPData])

  return {
    ...data,
    refresh
  }
}

/**
 * Hook pour l'upload de fichiers CSV SERP
 */
export const useSERPUpload = (projectId?: string) => {
  const [state, setState] = useState<SERPUploadState>({
    isUploading: false
  })

  const uploadCSV = useCallback(async (formData: SERPUploadFormData): Promise<SERPImportResponse | null> => {
    if (!projectId || !formData.file) {
      setState({ isUploading: false, error: 'Projet ou fichier manquant' })
      return null
    }

    try {
      // Valider le fichier
      const validation = SERPService.validateCSVFile(formData.file)
      if (!validation.isValid) {
        setState({ isUploading: false, error: validation.error })
        return null
      }

      setState({ isUploading: true, error: undefined })

      const form = SERPService.createFormData(formData)
      const result = await SERPService.importCSV(projectId, form)

      setState({ 
        isUploading: false, 
        result,
        error: result.success ? undefined : 'Import partiellement réussi'
      })

      return result
    } catch (err) {
      const error = err instanceof Error ? err.message : 'Erreur lors de l\'upload'
      setState({ isUploading: false, error })
      return null
    }
  }, [projectId])

  const reset = useCallback(() => {
    setState({ isUploading: false })
  }, [])

  return {
    ...state,
    uploadCSV,
    reset
  }
}

/**
 * Hook pour le matching automatique des prompts
 */
export const useSERPMatching = (projectId?: string) => {
  const [state, setState] = useState<SERPMatchingState>({
    isMatching: false
  })

  const autoMatch = useCallback(async (): Promise<AutoMatchResponse | null> => {
    if (!projectId) {
      setState({ isMatching: false, error: 'ID de projet manquant' })
      return null
    }

    try {
      setState({ isMatching: true, error: undefined })

      const result = await SERPService.autoMatchPrompts(projectId)

      setState({ 
        isMatching: false, 
        result,
        error: result.success ? undefined : 'Erreur lors du matching'
      })

      return result
    } catch (err) {
      const error = err instanceof Error ? err.message : 'Erreur lors du matching automatique'
      setState({ isMatching: false, error })
      return null
    }
  }, [projectId])

  const reset = useCallback(() => {
    setState({ isMatching: false })
  }, [])

  return {
    ...state,
    autoMatch,
    reset
  }
}

/**
 * Hook pour gérer l'association SERP d'un prompt
 */
export const useSERPAssociation = (promptId?: string) => {
  const [association, setAssociation] = useState<PromptSERPAssociationResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchAssociation = useCallback(async () => {
    if (!promptId) return

    try {
      setLoading(true)
      setError(null)

      const result = await SERPService.getPromptAssociation(promptId)
      setAssociation(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur lors du chargement de l\'association')
    } finally {
      setLoading(false)
    }
  }, [promptId])

  const updateAssociation = useCallback(async (data: PromptSERPAssociationRequest): Promise<boolean> => {
    if (!promptId) return false

    try {
      setLoading(true)
      setError(null)

      await SERPService.setPromptAssociation(promptId, data)
      await fetchAssociation() // Recharger l'association

      return true
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur lors de la mise à jour de l\'association')
      return false
    } finally {
      setLoading(false)
    }
  }, [promptId, fetchAssociation])

  const removeAssociation = useCallback(async (): Promise<boolean> => {
    if (!promptId) return false

    try {
      setLoading(true)
      setError(null)

      await SERPService.removePromptAssociation(promptId)
      await fetchAssociation() // Recharger l'association

      return true
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur lors de la suppression de l\'association')
      return false
    } finally {
      setLoading(false)
    }
  }, [promptId, fetchAssociation])

  useEffect(() => {
    fetchAssociation()
  }, [fetchAssociation])

  return {
    association,
    loading,
    error,
    setAssociation: updateAssociation,
    removeAssociation,
    refresh: fetchAssociation
  }
}

/**
 * Hook pour prévisualiser un fichier CSV
 */
export const useCSVPreview = () => {
  const [preview, setPreview] = useState<{ headers: string[]; rows: string[][] } | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const previewFile = useCallback(async (file: File) => {
    try {
      setLoading(true)
      setError(null)

      const validation = SERPService.validateCSVFile(file)
      if (!validation.isValid) {
        setError(validation.error!)
        return
      }

      const result = await SERPService.previewCSV(file)
      setPreview(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur lors de la prévisualisation')
      setPreview(null)
    } finally {
      setLoading(false)
    }
  }, [])

  const reset = useCallback(() => {
    setPreview(null)
    setError(null)
    setLoading(false)
  }, [])

  return {
    preview,
    loading,
    error,
    previewFile,
    reset
  }
}

/**
 * Hook utilitaire pour les métriques SERP
 */
export const useSERPMetrics = (keywords?: Array<{ keyword: string; position: number; volume?: number }>) => {
  const metrics = SERPService.calculatePerformanceMetrics(keywords || [])

  return metrics
}

/**
 * Hook pour les insights SERP
 */
export const useSERPInsights = (summary?: SERPSummaryResponse, keywords?: Array<{ keyword: string; position: number; volume?: number }>) => {
  const insights = summary ? SERPService.generateInsights(summary, keywords) : []

  return insights
}

/**
 * Hook pour récupérer les suggestions de matching
 */
export const useSERPSuggestions = (projectId?: string, enabled: boolean = false) => {
  const [suggestions, setSuggestions] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [stats, setStats] = useState<any>(null)

  const fetchSuggestions = useCallback(async () => {
    if (!projectId || !enabled) return

    try {
      setLoading(true)
      setError(null)

      const result = await SERPService.getMatchingSuggestions(projectId)
      setSuggestions(result.success ? result.suggestions || [] : [])
      setStats(result.stats || null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur lors de la récupération des suggestions')
      setSuggestions([])
      setStats(null)
    } finally {
      setLoading(false)
    }
  }, [projectId, enabled])

  useEffect(() => {
    if (enabled) {
      fetchSuggestions()
    } else {
      // Vider les suggestions quand le modal se ferme
      setSuggestions([])
      setStats(null)
      setError(null)
    }
  }, [fetchSuggestions, enabled])

  const refresh = useCallback(() => {
    fetchSuggestions()
  }, [fetchSuggestions])

  return {
    suggestions,
    loading,
    error,
    stats,
    refresh
  }
}

/**
 * Hook pour récupérer les associations d'un projet
 */
export const useSERPAssociations = (projectId?: string) => {
  const [associations, setAssociations] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchAssociations = useCallback(async () => {
    if (!projectId) return

    try {
      setLoading(true)
      setError(null)

      const result = await SERPService.getProjectAssociations(projectId)
      setAssociations(result.associations || [])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur lors de la récupération des associations')
      setAssociations([])
    } finally {
      setLoading(false)
    }
  }, [projectId])

  useEffect(() => {
    fetchAssociations()
  }, [fetchAssociations])

  const refresh = useCallback(() => {
    fetchAssociations()
  }, [fetchAssociations])

  return {
    associations,
    loading,
    error,
    refresh
  }
}