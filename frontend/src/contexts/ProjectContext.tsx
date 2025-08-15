import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import type { ProjectSummary } from '../types/project'

interface ProjectContextType {
  currentProject: ProjectSummary | null
  setCurrentProject: (project: ProjectSummary | null) => void
  loading: boolean
}

const ProjectContext = createContext<ProjectContextType | undefined>(undefined)

interface ProjectProviderProps {
  children: ReactNode
}

export const ProjectProvider: React.FC<ProjectProviderProps> = ({ children }) => {
  const [currentProject, setCurrentProjectState] = useState<ProjectSummary | null>(null)
  const [loading, setLoading] = useState(true)

  // Charger le projet depuis localStorage au démarrage
  useEffect(() => {
    const savedProject = localStorage.getItem('currentProject')
    if (savedProject) {
      try {
        const project = JSON.parse(savedProject)
        setCurrentProjectState(project)
        console.log('🏠 Projet chargé depuis localStorage:', project.name)
      } catch (error) {
        console.error('❌ Erreur lors du chargement du projet sauvegardé:', error)
        localStorage.removeItem('currentProject')
      }
    }
    setLoading(false)
  }, [])

  // Sauvegarder le projet dans localStorage à chaque changement
  const setCurrentProject = (project: ProjectSummary | null) => {
    setCurrentProjectState(project)
    
    if (project) {
      localStorage.setItem('currentProject', JSON.stringify(project))
      console.log('💾 Projet sauvegardé:', project.name)
      
      // Déclencher un événement pour notifier les autres composants
      window.dispatchEvent(new CustomEvent('projectChanged', { 
        detail: { project } 
      }))
    } else {
      localStorage.removeItem('currentProject')
      console.log('🗑️ Projet supprimé du localStorage')
    }
  }

  const value: ProjectContextType = {
    currentProject,
    setCurrentProject,
    loading
  }

  return (
    <ProjectContext.Provider value={value}>
      {children}
    </ProjectContext.Provider>
  )
}

// Hook personnalisé pour utiliser le context
export const useCurrentProject = (): ProjectContextType => {
  const context = useContext(ProjectContext)
  if (context === undefined) {
    throw new Error('useCurrentProject doit être utilisé dans un ProjectProvider')
  }
  return context
}

// Hook utilitaire pour vérifier si un projet est sélectionné
export const useRequireProject = (): ProjectSummary => {
  const { currentProject } = useCurrentProject()
  
  if (!currentProject) {
    throw new Error('Aucun projet sélectionné')
  }
  
  return currentProject
} 