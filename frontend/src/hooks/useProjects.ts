import { useState, useEffect, useCallback } from 'react'
import { ProjectsAPI } from '../services/projects'
import type { 
  Project, 
  ProjectCreate, 
  ProjectUpdate, 
  ProjectSummary,
  Competitor,
  CompetitorCreate
} from '../types/project'

interface UseProjectsReturn {
  projects: ProjectSummary[]
  loading: boolean
  error: string | null
  createProject: (project: ProjectCreate) => Promise<Project | null>
  updateProject: (id: string, project: ProjectUpdate) => Promise<Project | null>
  deleteProject: (id: string) => Promise<boolean>
  updateKeywords: (id: string, keywords: string[]) => Promise<Project | null>
  addCompetitor: (projectId: string, competitor: CompetitorCreate) => Promise<Competitor | null>
  removeCompetitor: (projectId: string, competitorId: string) => Promise<boolean>
  refresh: () => Promise<void>
}

export const useProjects = (): UseProjectsReturn => {
  const [projects, setProjects] = useState<ProjectSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchProjects = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      console.log('🔄 Chargement des projets...')
      
      const projectsData = await ProjectsAPI.getAll({ limit: 1000 })
      setProjects(projectsData)
      console.log('✅ Projets chargés:', projectsData.length)
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erreur inconnue'
      console.error('❌ Erreur lors du chargement des projets:', err)
      setError(`Erreur lors du chargement des projets: ${errorMessage}`)
    } finally {
      setLoading(false)
    }
  }, [])

  const createProject = async (project: ProjectCreate): Promise<Project | null> => {
    try {
      console.log('🚀 Création du projet:', project.name)
      setError(null)
      
      const newProject = await ProjectsAPI.create(project)
      console.log('✅ Projet créé:', newProject.id)
      
      // Recharger la liste des projets
      await fetchProjects()
      
      return newProject
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erreur inconnue'
      console.error('❌ Erreur lors de la création du projet:', err)
      setError(`Erreur lors de la création: ${errorMessage}`)
      return null
    }
  }

  const updateProject = async (id: string, project: ProjectUpdate): Promise<Project | null> => {
    try {
      console.log('🔄 Mise à jour du projet:', id)
      setError(null)
      
      const updatedProject = await ProjectsAPI.update(id, project)
      console.log('✅ Projet mis à jour:', updatedProject.id)
      
      // Recharger la liste des projets
      await fetchProjects()
      
      return updatedProject
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erreur inconnue'
      console.error('❌ Erreur lors de la mise à jour du projet:', err)
      setError(`Erreur lors de la mise à jour: ${errorMessage}`)
      return null
    }
  }

  const deleteProject = async (id: string): Promise<boolean> => {
    try {
      console.log('🗑️ Suppression du projet:', id)
      setError(null)
      
      await ProjectsAPI.delete(id)
      console.log('✅ Projet supprimé')
      
      // Recharger la liste des projets
      await fetchProjects()
      
      return true
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erreur inconnue'
      console.error('❌ Erreur lors de la suppression du projet:', err)
      setError(`Erreur lors de la suppression: ${errorMessage}`)
      return false
    }
  }

  const updateKeywords = async (id: string, keywords: string[]): Promise<Project | null> => {
    try {
      console.log('🔄 Mise à jour des mots-clés:', id, keywords)
      setError(null)
      
      const updatedProject = await ProjectsAPI.updateKeywords(id, keywords)
      console.log('✅ Mots-clés mis à jour')
      
      // Recharger la liste des projets
      await fetchProjects()
      
      return updatedProject
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erreur inconnue'
      console.error('❌ Erreur lors de la mise à jour des mots-clés:', err)
      setError(`Erreur lors de la mise à jour des mots-clés: ${errorMessage}`)
      return null
    }
  }

  const addCompetitor = async (projectId: string, competitor: CompetitorCreate): Promise<Competitor | null> => {
    try {
      console.log('🚀 Ajout du concurrent:', competitor.name, 'au projet', projectId)
      setError(null)
      
      const newCompetitor = await ProjectsAPI.addCompetitor(projectId, competitor)
      console.log('✅ Concurrent ajouté:', newCompetitor.id)
      
      // Recharger la liste des projets pour mettre à jour les compteurs
      await fetchProjects()
      
      return newCompetitor
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erreur inconnue'
      console.error('❌ Erreur lors de l\'ajout du concurrent:', err)
      setError(`Erreur lors de l'ajout du concurrent: ${errorMessage}`)
      return null
    }
  }

  const removeCompetitor = async (projectId: string, competitorId: string): Promise<boolean> => {
    try {
      console.log('🗑️ Suppression du concurrent:', competitorId, 'du projet', projectId)
      setError(null)
      
      await ProjectsAPI.removeCompetitor(projectId, competitorId)
      console.log('✅ Concurrent supprimé')
      
      // Recharger la liste des projets pour mettre à jour les compteurs
      await fetchProjects()
      
      return true
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erreur inconnue'
      console.error('❌ Erreur lors de la suppression du concurrent:', err)
      setError(`Erreur lors de la suppression du concurrent: ${errorMessage}`)
      return false
    }
  }

  const refresh = useCallback(async () => {
    await fetchProjects()
  }, [fetchProjects])

  // Chargement initial
  useEffect(() => {
    fetchProjects()
  }, [fetchProjects])

  return {
    projects,
    loading,
    error,
    createProject,
    updateProject,
    deleteProject,
    updateKeywords,
    addCompetitor,
    removeCompetitor,
    refresh
  }
}

// Hook pour récupérer un projet spécifique
export const useProject = (id: string) => {
  const [project, setProject] = useState<Project | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!id) return

    const fetchProject = async () => {
      try {
        setLoading(true)
        setError(null)
        const projectData = await ProjectsAPI.getById(id)
        setProject(projectData)
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Erreur inconnue'
        setError(`Erreur lors du chargement du projet: ${errorMessage}`)
      } finally {
        setLoading(false)
      }
    }

    fetchProject()
  }, [id])

  return { project, loading, error }
}

 