import React from 'react'
import { useLocation } from 'react-router-dom'
import { Plus, RefreshCw } from 'lucide-react'
import { ProjectSelector } from './ProjectSelector'
import { useCurrentProject } from '../contexts/ProjectContext'
import { Button } from './ui'

interface HeaderProps {
  title?: string
  subtitle?: string
  children?: React.ReactNode
  onNewPrompt?: () => void
  onRefresh?: () => void
  loading?: boolean
}

export const Header: React.FC<HeaderProps> = ({ 
  title, 
  subtitle, 
  children, 
  onNewPrompt, 
  onRefresh, 
  loading = false 
}) => {
  const location = useLocation()
  const { currentProject } = useCurrentProject()
  const [pageActions, setPageActions] = React.useState<{
    onNewPrompt?: () => void
    onRefresh?: () => void
    loading?: boolean
  }>({})

  // Écouter les événements des pages
  React.useEffect(() => {
    const handlePageActions = (event: CustomEvent) => {
      setPageActions(event.detail)
    }

    window.addEventListener('pageActions', handlePageActions as EventListener)
    return () => window.removeEventListener('pageActions', handlePageActions as EventListener)
  }, [])

  // Titre automatique basé sur la route
  const getPageTitle = () => {
    if (title) return title
    
    switch (location.pathname) {
      case '/':
      case '/dashboard':
        return `Dashboard${currentProject ? ` pour ${currentProject.name}` : ''}`
      case '/projects':
        return 'Projets'
      case '/prompts':
        return 'Prompts'
      case '/analyses':
        return 'Analyses'
      case '/settings':
        return 'Paramètres'
      default:
        return 'Visibility Tracker'
    }
  }

  const getPageSubtitle = () => {
    if (subtitle) return subtitle
    
    switch (location.pathname) {
      case '/':
      case '/dashboard':
        return 'Vue d\'ensemble de vos métriques de visibilité'
      case '/projects':
        return 'Gérez vos projets clients'
      case '/prompts':
        return currentProject 
          ? `Templates de prompts pour ${currentProject.name}`
          : 'Sélectionnez un projet pour voir vos prompts'
      case '/analyses':
        return currentProject
          ? `Historique des analyses pour ${currentProject.name}`
          : 'Sélectionnez un projet pour voir vos analyses'
      case '/settings':
        return 'Configuration générale'
      default:
        return ''
    }
  }

  return (
    <div className="sticky top-0 z-20 bg-white/80 dark:bg-gray-950/70 backdrop-blur border-b border-gray-200 dark:border-gray-800 px-4 sm:px-6 lg:px-8 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
              {getPageTitle()}
            </h1>
            {getPageSubtitle() && (
              <p className="text-gray-600 dark:text-gray-400 mt-1">
                {getPageSubtitle()}
              </p>
            )}
          </div>
          {/* Sélecteur de projet - visible partout sauf sur la page projets */}
          {location.pathname !== '/projects' && location.pathname !== '/settings' && (
            <ProjectSelector />
          )}
        </div>
        
        {/* Actions spécifiques à la page */}
        <div className="flex items-center space-x-2">
          {/* Bouton spécifique à la page Prompts */}
          {location.pathname === '/prompts' && (onNewPrompt || pageActions.onNewPrompt) && (
            <Button
              variant="primary"
              onClick={onNewPrompt || pageActions.onNewPrompt}
              className="flex items-center space-x-2"
            >
              <Plus className="h-4 w-4" />
              <span>Nouveau Prompt</span>
            </Button>
          )}
          
          {/* Bouton refresh général */}
          {(onRefresh || pageActions.onRefresh) && (
            <Button
              variant="outline"
              size="sm"
              onClick={onRefresh || pageActions.onRefresh}
              disabled={loading || pageActions.loading}
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${(loading || pageActions.loading) ? 'animate-spin' : ''}`} />
              Actualiser
            </Button>
          )}
          
          {children}
        </div>
      </div>
    </div>
  )
} 