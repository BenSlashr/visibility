import React from 'react'
import { useCurrentProject } from '../../contexts/ProjectContext'
import { SERPAssociation } from '../serp/SERPAssociation'
import { useSERPProject } from '../../hooks/useSERP'
import { Card } from '../ui/Card'
import { Badge } from '../ui/Badge'

interface PromptSERPSectionProps {
  promptId: string
  promptName: string
}

export const PromptSERPSection: React.FC<PromptSERPSectionProps> = ({
  promptId,
  promptName
}) => {
  const { currentProject } = useCurrentProject()
  const { summary, keywords, isLoading } = useSERPProject(currentProject?.id)

  // Si pas de projet sélectionné ou pas de données SERP
  if (!currentProject || !summary?.has_serp_data) {
    return (
      <Card className="border border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-gray-200 dark:bg-gray-700 rounded-full flex items-center justify-center">
              <svg className="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                SERP & Corrélations
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {!currentProject ? 'Aucun projet sélectionné' : 'Aucune donnée SERP importée'}
              </p>
            </div>
          </div>
          
          <Badge variant="neutral" size="sm">
            Non disponible
          </Badge>
        </div>
      </Card>
    )
  }

  if (isLoading) {
    return (
      <Card className="border border-gray-200 dark:border-gray-700">
        <div className="flex items-center space-x-3">
          <div className="animate-spin w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full"></div>
          <span className="text-sm text-gray-500">Chargement des associations SERP...</span>
        </div>
      </Card>
    )
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100">
          Association SERP
        </h4>
        <Badge variant="success" size="sm">
          {keywords?.length || 0} mots-clés disponibles
        </Badge>
      </div>
      
      <SERPAssociation
        promptId={promptId}
        promptName={promptName}
        availableKeywords={keywords || []}
      />
    </div>
  )
}

export default PromptSERPSection