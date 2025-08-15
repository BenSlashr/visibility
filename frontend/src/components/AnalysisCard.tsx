import React from 'react'
import { BarChart3, Clock, CheckCircle, XCircle, Eye, DollarSign, Link2, Globe } from 'lucide-react'
import { Button, Badge, Card } from './ui'

interface Analysis {
  id: number
  project_name: string
  prompt_name: string
  ai_model: string
  prompt_executed: string
  ai_response: string
  brand_mentioned: boolean
  website_mentioned: boolean
  brand_position?: number
  links_to_website: number
  tokens_used: number
  processing_time: number
  cost: number
  created_at: string
  web_search_used?: boolean
}

interface AnalysisCardProps {
  analysis: Analysis
  onViewDetails?: (analysis: Analysis) => void
  onRerun?: (analysis: Analysis) => void
}

export const AnalysisCard: React.FC<AnalysisCardProps> = ({
  analysis,
  onViewDetails,
  onRerun
}) => {
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('fr-FR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const getModelIcon = (model: string) => {
    if (model.includes('GPT')) return '🤖'
    if (model.includes('Claude')) return '🧠'
    if (model.includes('Gemini')) return '💎'
    return '🔮'
  }

  const getModelColor = (model: string) => {
    if (model.includes('GPT')) return 'success'
    if (model.includes('Claude')) return 'info'
    if (model.includes('Gemini')) return 'warning'
    return 'default'
  }

  return (
    <Card className="hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <div className="flex items-center space-x-2 mb-2">
            <BarChart3 className="h-4 w-4 text-blue-600" />
            <h3 className="font-semibold text-gray-900 text-sm">
              {analysis.project_name}
            </h3>
            <span className="text-gray-400">•</span>
            <span className="text-sm text-gray-600">{analysis.prompt_name}</span>
          </div>
          
          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-1">
              <span className="text-sm">{getModelIcon(analysis.ai_model)}</span>
              <Badge variant={getModelColor(analysis.ai_model)} size="sm">
                {analysis.ai_model}
              </Badge>
            </div>
            
            <div className="flex items-center space-x-1 text-xs text-gray-500">
              <Clock className="h-3 w-3" />
              <span>{formatDate(analysis.created_at)}</span>
            </div>
          </div>
        </div>

        <div className="flex space-x-1">
          {onViewDetails && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onViewDetails(analysis)}
            >
              <Eye className="h-4 w-4" />
            </Button>
          )}
          {onRerun && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => onRerun(analysis)}
            >
              Relancer
            </Button>
          )}
        </div>
      </div>

      {/* Métriques principales */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="flex items-center space-x-2">
          {analysis.brand_mentioned ? (
            <CheckCircle className="h-4 w-4 text-green-600" />
          ) : (
            <XCircle className="h-4 w-4 text-red-600" />
          )}
          <span className="text-sm">
            Marque {analysis.brand_mentioned ? 'mentionnée' : 'non mentionnée'}
          </span>
          {analysis.brand_position && (
            <Badge variant="info" size="sm">
              Position #{analysis.brand_position}
            </Badge>
          )}
        </div>

        <div className="flex items-center space-x-2">
          {analysis.website_mentioned ? (
            <CheckCircle className="h-4 w-4 text-green-600" />
          ) : (
            <XCircle className="h-4 w-4 text-red-600" />
          )}
          <span className="text-sm">
            Site {analysis.website_mentioned ? 'mentionné' : 'non mentionné'}
          </span>
          {analysis.links_to_website > 0 && (
            <Badge variant="success" size="sm">
              {analysis.links_to_website} lien(s)
            </Badge>
          )}
        </div>
      </div>

      {/* Réponse IA (preview) */}
      <div className="mb-4">
        <p className="text-xs text-gray-500 mb-1">Réponse IA :</p>
        <p className="text-sm text-gray-700 line-clamp-2 bg-gray-50 p-2 rounded text-left">
          {analysis.ai_response}
        </p>
      </div>

      {/* Footer avec métriques techniques */}
      <div className="flex items-center justify-between pt-3 border-t border-gray-200 text-xs text-gray-500">
        <div className="flex items-center space-x-4">
          <span>{analysis.tokens_used} tokens</span>
          <span>{analysis.processing_time}ms</span>
          <div className="flex items-center space-x-1">
            <DollarSign className="h-3 w-3" />
            <span>${analysis.cost.toFixed(4)}</span>
          </div>
        </div>
        
        <div className="flex items-center space-x-1">
          <div className={`w-2 h-2 rounded-full ${
            analysis.brand_mentioned ? 'bg-green-500' : 'bg-red-500'
          }`} />
          <span>Visibilité</span>
        </div>
        {/* Indicateur sources si présent */}
        {typeof (analysis as any).has_sources !== 'undefined' && (analysis as any).has_sources && (
          <div className="flex items-center space-x-1 text-xs text-gray-600">
            <Link2 className="h-3 w-3" />
            <span>Sources</span>
          </div>
        )}
        {/* Indicateur web search */}
        <div className={`flex items-center space-x-1 text-xs ${analysis.web_search_used ? 'text-blue-600' : 'text-gray-400'}`}>
            <Globe className="h-3 w-3" />
            <span>Web</span>
        </div>
      </div>
    </Card>
  )
} 