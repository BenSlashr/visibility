import React, { useState, useEffect, useRef } from 'react'
import { ChevronDown, FolderOpen, Plus } from 'lucide-react'
import { useCurrentProject } from '../contexts/ProjectContext'
import { useProjects } from '../hooks/useProjects'
import { Button, Loading } from './ui'
import { clsx } from 'clsx'

export const ProjectSelector: React.FC = () => {
  const { currentProject, setCurrentProject } = useCurrentProject()
  const { projects, loading: projectsLoading } = useProjects()
  const [isOpen, setIsOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  // Fermer le dropdown en cliquant à l'extérieur
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // Sélectionner automatiquement le premier projet si aucun n'est sélectionné
  useEffect(() => {
    if (!currentProject && projects.length > 0 && !projectsLoading) {
      console.log('🎯 Auto-sélection du premier projet:', projects[0].name)
      setCurrentProject(projects[0])
    }
  }, [currentProject, projects, projectsLoading, setCurrentProject])

  const handleProjectSelect = (project: typeof projects[0]) => {
    console.log('📁 Changement de projet:', project.name)
    setCurrentProject(project)
    setIsOpen(false)
    
    // Scroll vers le haut pour voir le changement
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  if (projectsLoading) {
    return (
      <div className="flex items-center space-x-2 px-3 py-2 bg-white rounded-lg border border-gray-200">
        <FolderOpen className="h-4 w-4 text-gray-400" />
        <Loading size="sm" />
        <span className="text-sm text-gray-500">Chargement...</span>
      </div>
    )
  }

  if (projects.length === 0) {
    return (
      <div className="flex items-center space-x-2 px-3 py-2 bg-gray-100 rounded-lg border border-gray-200">
        <FolderOpen className="h-4 w-4 text-gray-400" />
        <span className="text-sm text-gray-500">Aucun projet</span>
        <Button size="sm" variant="ghost">
          <Plus className="h-3 w-3" />
        </Button>
      </div>
    )
  }

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Bouton sélecteur */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={clsx(
          "flex items-center space-x-2 px-3 py-2 bg-white rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors",
          isOpen && "ring-2 ring-blue-500 ring-opacity-20"
        )}
      >
        <FolderOpen className="h-4 w-4 text-blue-600" />
        <span className="font-medium text-gray-900 min-w-0 truncate max-w-48">
          {currentProject?.name || 'Sélectionner un projet'}
        </span>
        <ChevronDown className={clsx(
          "h-4 w-4 text-gray-400 transition-transform",
          isOpen && "rotate-180"
        )} />
      </button>

      {/* Dropdown */}
      {isOpen && (
        <div className="absolute top-full left-0 mt-1 w-72 bg-white border border-gray-200 rounded-lg shadow-lg z-50 max-h-80 overflow-y-auto">
          {/* Header */}
          <div className="px-3 py-2 border-b border-gray-100">
            <div className="text-xs font-medium text-gray-500 uppercase tracking-wide">
              Projets ({projects.length})
            </div>
          </div>

          {/* Liste des projets */}
          <div className="py-1">
            {projects.map((project) => (
              <button
                key={project.id}
                onClick={() => handleProjectSelect(project)}
                className={clsx(
                  "w-full px-3 py-2 text-left hover:bg-gray-50 transition-colors",
                  currentProject?.id === project.id && "bg-blue-50 border-r-2 border-blue-500"
                )}
              >
                <div className="flex items-center justify-between">
                  <div className="min-w-0 flex-1">
                    <div className={clsx(
                      "font-medium truncate",
                      currentProject?.id === project.id ? "text-blue-900" : "text-gray-900"
                    )}>
                      {project.name}
                    </div>
                    {project.description && (
                      <div className="text-xs text-gray-500 truncate mt-0.5">
                        {project.description}
                      </div>
                    )}
                    <div className="flex items-center space-x-3 mt-1">
                      <span className="text-xs text-gray-400">
                        {project.analyses_count || 0} analyses
                      </span>
                      <span className="text-xs text-gray-400">
                        {project.keywords_count || 0} mots-clés
                      </span>
                      <span className="text-xs text-gray-400">
                        {project.competitors_count || 0} concurrents
                      </span>
                    </div>
                  </div>
                  
                  {currentProject?.id === project.id && (
                    <div className="ml-2 h-2 w-2 bg-blue-500 rounded-full"></div>
                  )}
                </div>
              </button>
            ))}
          </div>

          {/* Footer */}
          <div className="px-3 py-2 border-t border-gray-100">
            <Button variant="ghost" size="sm" className="w-full justify-start">
              <Plus className="h-3 w-3 mr-2" />
              Nouveau projet
            </Button>
          </div>
        </div>
      )}
    </div>
  )
} 