import React from 'react'
import { FolderOpen, BarChart3, Target, DollarSign, TrendingUp } from 'lucide-react'
import { useCurrentProject } from '../contexts/ProjectContext'

export const ProjectCentricMessage: React.FC = () => {
  const { currentProject } = useCurrentProject()

  if (!currentProject) {
    return (
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-6">
        <div className="flex items-start space-x-3">
          <FolderOpen className="h-6 w-6 text-blue-600 mt-0.5" />
          <div>
            <h3 className="text-lg font-semibold text-blue-900 mb-2">
              🎯 Sélectionnez un projet pour commencer
            </h3>
            <p className="text-blue-700 mb-3">
              Cette application est <strong>projet-centrée</strong>. Toutes les données sont contextualisées par projet.
            </p>
            <div className="text-sm text-blue-600">
              <p>• Chaque projet a ses propres analyses, prompts et concurrents</p>
              <p>• Les coûts sont calculés par projet pour la facturation client</p>
              <p>• Le dashboard s'adapte automatiquement au projet sélectionné</p>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
      <div className="flex items-start space-x-3">
        <Target className="h-5 w-5 text-green-600 mt-0.5" />
        <div className="flex-1">
          <h4 className="font-medium text-green-900 mb-1">
            📁 Dashboard pour : <span className="font-bold">{currentProject.name}</span>
          </h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs text-green-700">
            <div className="flex items-center space-x-1">
              <BarChart3 className="h-3 w-3" />
              <span>{currentProject.analyses_count || 0} analyses</span>
            </div>
            <div className="flex items-center space-x-1">
              <TrendingUp className="h-3 w-3" />
              <span>{currentProject.keywords_count || 0} mots-clés</span>
            </div>
            <div className="flex items-center space-x-1">
              <Target className="h-3 w-3" />
              <span>{currentProject.competitors_count || 0} concurrents</span>
            </div>
            <div className="flex items-center space-x-1">
              <DollarSign className="h-3 w-3" />
              <span>Coûts séparés</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
} 