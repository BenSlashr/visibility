import React from 'react'
import { Modal } from '../ui/Modal'
import { Badge } from '../ui/Badge'
import { Card } from '../ui/Card'
import PromptSERPSection from './PromptSERPSection'

interface PromptDetailsModalProps {
  isOpen: boolean
  onClose: () => void
  prompt: any
}

export const PromptDetailsModal: React.FC<PromptDetailsModalProps> = ({
  isOpen,
  onClose,
  prompt
}) => {
  if (!prompt) return null

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('fr-FR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const getVariablesCount = () => {
    if (!prompt.template) return 0
    const matches = prompt.template.match(/\{\{(\w+)\}\}/g)
    return matches ? matches.length : 0
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={prompt.name}
      maxWidth="4xl"
    >
      <div className="space-y-6">
        {/* Informations générales */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-3">
              Informations générales
            </h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">Statut</span>
                <Badge variant={prompt.is_active ? 'success' : 'error'}>
                  {prompt.is_active ? 'Actif' : 'Inactif'}
                </Badge>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">Type</span>
                <Badge variant={prompt.is_multi_agent ? 'info' : 'neutral'}>
                  {prompt.is_multi_agent ? 'Multi-agent' : 'Simple'}
                </Badge>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">Variables</span>
                <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  {getVariablesCount()}
                </span>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">Exécutions</span>
                <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  {prompt.execution_count || 0}
                </span>
              </div>
              
              {prompt.last_executed_at && (
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-400">Dernière exécution</span>
                  <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                    {formatDate(prompt.last_executed_at)}
                  </span>
                </div>
              )}
            </div>
          </Card>

          <Card>
            <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-3">
              Modèles IA
            </h3>
            <div className="space-y-2">
              {prompt.is_multi_agent ? (
                prompt.ai_model_names?.map((modelName: string, index: number) => (
                  <div key={index} className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                    <span className="text-sm text-gray-900 dark:text-gray-100">{modelName}</span>
                  </div>
                )) || <span className="text-sm text-gray-500">Aucun modèle configuré</span>
              ) : (
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span className="text-sm text-gray-900 dark:text-gray-100">
                    {prompt.ai_model_name || 'Modèle inconnu'}
                  </span>
                </div>
              )}
            </div>
          </Card>
        </div>

        {/* Template */}
        <Card>
          <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-3">
            Template
          </h3>
          <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 max-h-48 overflow-y-auto">
            <pre className="text-sm text-gray-900 dark:text-gray-100 whitespace-pre-wrap font-mono">
              {prompt.template}
            </pre>
          </div>
        </Card>

        {/* Description */}
        {prompt.description && (
          <Card>
            <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-3">
              Description
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              {prompt.description}
            </p>
          </Card>
        )}

        {/* Tags */}
        {prompt.tags && prompt.tags.length > 0 && (
          <Card>
            <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-3">
              Tags
            </h3>
            <div className="flex flex-wrap gap-2">
              {prompt.tags.map((tag: string, index: number) => (
                <Badge key={index} variant="neutral" size="sm">
                  {tag}
                </Badge>
              ))}
            </div>
          </Card>
        )}

        {/* Association SERP */}
        <Card>
          <PromptSERPSection
            promptId={prompt.id}
            promptName={prompt.name}
          />
        </Card>

        {/* Dates */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-4 border-t border-gray-200 dark:border-gray-700">
          <div className="text-center">
            <p className="text-xs text-gray-500 dark:text-gray-400">Créé le</p>
            <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
              {formatDate(prompt.created_at)}
            </p>
          </div>
          <div className="text-center">
            <p className="text-xs text-gray-500 dark:text-gray-400">Modifié le</p>
            <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
              {formatDate(prompt.updated_at)}
            </p>
          </div>
        </div>
      </div>
    </Modal>
  )
}

export default PromptDetailsModal