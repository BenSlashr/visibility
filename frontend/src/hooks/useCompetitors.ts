import { useState, useEffect, useCallback } from 'react'
import { ProjectsAPI } from '../services/projects'
import type { Competitor, CompetitorCreate } from '../types/project'

interface UseCompetitorsReturn {
  competitors: Competitor[]
  loading: boolean
  error: string | null
  addCompetitor: (competitor: CompetitorCreate) => Promise<Competitor | null>
  removeCompetitor: (competitorId: string) => Promise<boolean>
  refresh: () => Promise<void>
}

export const useCompetitors = (projectId?: string): UseCompetitorsReturn => {
  const [competitors, setCompetitors] = useState<Competitor[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchCompetitors = useCallback(async () => {
    if (!projectId) {
      setCompetitors([])
      setLoading(false)
      return
    }

    try {
      setLoading(true)
      setError(null)
      console.log('🔄 Chargement des concurrents pour le projet:', projectId)
      
      const competitorsData = await ProjectsAPI.getCompetitors(projectId)
      setCompetitors(competitorsData)
      console.log('✅ Concurrents chargés:', competitorsData.length)
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erreur inconnue'
      console.error('❌ Erreur lors du chargement des concurrents:', err)
      setError(`Erreur lors du chargement des concurrents: ${errorMessage}`)
    } finally {
      setLoading(false)
    }
  }, [projectId])

  const addCompetitor = async (competitor: CompetitorCreate): Promise<Competitor | null> => {
    if (!projectId) {
      setError('Aucun projet sélectionné')
      return null
    }

    try {
      console.log('🚀 Ajout du concurrent:', competitor.name)
      setError(null)
      
      const newCompetitor = await ProjectsAPI.addCompetitor(projectId, competitor)
      console.log('✅ Concurrent ajouté:', newCompetitor.id)
      
      // Ajouter à la liste locale
      setCompetitors(prev => [...prev, newCompetitor])
      
      return newCompetitor
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erreur inconnue'
      console.error('❌ Erreur lors de l\'ajout du concurrent:', err)
      setError(`Erreur lors de l'ajout du concurrent: ${errorMessage}`)
      return null
    }
  }

  const removeCompetitor = async (competitorId: string): Promise<boolean> => {
    if (!projectId) {
      setError('Aucun projet sélectionné')
      return false
    }

    try {
      console.log('🗑️ Suppression du concurrent:', competitorId)
      setError(null)
      
      await ProjectsAPI.removeCompetitor(projectId, competitorId)
      console.log('✅ Concurrent supprimé')
      
      // Supprimer de la liste locale
      setCompetitors(prev => prev.filter(c => c.id !== competitorId))
      
      return true
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erreur inconnue'
      console.error('❌ Erreur lors de la suppression du concurrent:', err)
      setError(`Erreur lors de la suppression du concurrent: ${errorMessage}`)
      return false
    }
  }

  const refresh = useCallback(async () => {
    await fetchCompetitors()
  }, [fetchCompetitors])

  // Chargement initial et rechargement quand le projet change
  useEffect(() => {
    fetchCompetitors()
  }, [fetchCompetitors])

  return {
    competitors,
    loading,
    error,
    addCompetitor,
    removeCompetitor,
    refresh
  }
} 