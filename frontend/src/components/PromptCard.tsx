import React from 'react'
import { MessageSquare, Play, Edit, Trash, Copy, Users, User, Eye } from 'lucide-react'
import { Button, Badge, Card } from './ui'

interface PromptCardProps {
  prompt: any // Utilisation d'any temporairement pour éviter les conflits de types
  onEdit?: (prompt: any) => void
  onDelete?: (promptId: string) => void
  onRun?: (prompt: any) => void
  onDuplicate?: (prompt: any) => void
  onDetails?: (prompt: any) => void
  isExecuting?: boolean
}

export const PromptCard: React.FC<PromptCardProps> = ({
  prompt,
  onEdit,
  onDelete,
  onRun,
  onDuplicate,
  onDetails,
  isExecuting = false
}) => {
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('fr-FR')
  }

  const getVariablesCount = () => {
    if (!prompt.template) return 0
    const matches = prompt.template.match(/\{\{(\w+)\}\}/g)
    return matches ? matches.length : 0
  }

  const getAIModelsInfo = () => {
    if (prompt.is_multi_agent) {
      const modelNames = prompt.ai_model_names || []
      return {
        isMultiAgent: true,
        count: modelNames.length,
        names: modelNames,
        display: modelNames.length > 0 ? `${modelNames.length} modèles` : 'Aucun modèle'
      }
    } else {
      return {
        isMultiAgent: false,
        count: 1,
        names: [prompt.ai_model_name || 'Modèle inconnu'],
        display: prompt.ai_model_name || 'Modèle inconnu'
      }
    }
  }

  const aiModelsInfo = getAIModelsInfo()

  return (
    <Card className="hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2">
            <MessageSquare className="h-5 w-5 text-blue-600" />
            {aiModelsInfo.isMultiAgent ? (
              <Users className="h-4 w-4 text-purple-600" />
            ) : (
              <User className="h-4 w-4 text-green-600" />
            )}
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              {prompt.name}
            </h3>
            {aiModelsInfo.isMultiAgent && (
              <Badge variant="info" className="mt-1">
                Multi-agents
              </Badge>
            )}
          </div>
        </div>
        
        <div className="flex items-center space-x-1">
          {prompt.is_active ? (
            <Badge variant="success">Actif</Badge>
          ) : (
            <Badge variant="default">Inactif</Badge>
          )}
        </div>
      </div>

      {/* Description */}
      {prompt.description && (
        <p className="text-gray-600 text-sm mb-4 line-clamp-2">
          {prompt.description}
        </p>
      )}

      {/* Modèles IA */}
      <div className="mb-4">
        <div className="flex items-center space-x-2 mb-2">
          <span className="text-sm font-medium text-gray-700">
            {aiModelsInfo.isMultiAgent ? 'Modèles IA :' : 'Modèle IA :'}
          </span>
        </div>
        {aiModelsInfo.isMultiAgent ? (
          <div className="flex flex-wrap gap-1">
            {aiModelsInfo.names.map((name: string, index: number) => (
              <Badge key={index} variant="info" className="text-xs">
                {name}
              </Badge>
            ))}
            {aiModelsInfo.count === 0 && (
              <span className="text-xs text-gray-500">Aucun modèle sélectionné</span>
            )}
          </div>
        ) : (
          <Badge variant="info" className="text-xs">
            {aiModelsInfo.display}
          </Badge>
        )}
      </div>

      {/* Template preview */}
      <div className="mb-4">
        <span className="text-sm font-medium text-gray-700">Template :</span>
        <div className="mt-1 p-2 bg-gray-50 rounded text-sm text-gray-800 font-mono line-clamp-3">
          {prompt.template}
        </div>
      </div>

      {/* Stats */}
      <div className="flex items-center justify-between text-sm text-gray-500 mb-4">
        <div className="flex items-center space-x-4">
          <span>{getVariablesCount()} variable{getVariablesCount() !== 1 ? 's' : ''}</span>
          <span>{prompt.execution_count || 0} exécution{(prompt.execution_count || 0) !== 1 ? 's' : ''}</span>
        </div>
        <span>Créé le {formatDate(prompt.created_at)}</span>
      </div>

      {/* Tags */}
      {prompt.tags && prompt.tags.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-4">
          {prompt.tags.map((tag: string, index: number) => (
            <Badge key={index} variant="default" className="text-xs">
              {tag}
            </Badge>
          ))}
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center justify-between pt-4 border-t">
        <div className="flex items-center space-x-2">
          <Button
            size="sm"
            onClick={() => onRun?.(prompt)}
            disabled={isExecuting || !prompt.is_active}
            className="flex items-center space-x-1"
          >
            <Play className="h-4 w-4" />
            <span>{isExecuting ? 'Exécution...' : 'Exécuter'}</span>
          </Button>
          
          {aiModelsInfo.isMultiAgent && (
            <span className="text-xs text-gray-500">
              ({aiModelsInfo.count} modèle{aiModelsInfo.count !== 1 ? 's' : ''})
            </span>
          )}
        </div>

        <div className="flex items-center space-x-1">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => onDetails?.(prompt)}
            title="Voir les détails et association SERP"
          >
            <Eye className="h-4 w-4" />
          </Button>
          
          <Button
            variant="secondary"
            size="sm"
            onClick={() => onEdit?.(prompt)}
          >
            <Edit className="h-4 w-4" />
          </Button>
          
          <Button
            variant="secondary"
            size="sm"
            onClick={() => onDuplicate?.(prompt)}
          >
            <Copy className="h-4 w-4" />
          </Button>
          
          <Button
            variant="secondary"
            size="sm"
            onClick={() => onDelete?.(prompt.id)}
            className="text-red-600 hover:text-red-700"
          >
            <Trash className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </Card>
  )
} 