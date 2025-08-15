import React, { useState } from 'react'
import { Card } from '../ui/Card'
import { Button } from '../ui/Button'
import { Badge } from '../ui/Badge'
import { SERPService } from '../../services/serp'
import type { MatchingSuggestion, SERPKeyword } from '../../types/serp'

interface SERPSuggestionsProps {
  suggestions: MatchingSuggestion[]
  onSuggestionAccepted: (promptId: string, keywordId: string) => void
  onSuggestionRejected: (promptId: string) => void
  onAllProcessed?: () => void
}

export const SERPSuggestions: React.FC<SERPSuggestionsProps> = ({
  suggestions,
  onSuggestionAccepted,
  onSuggestionRejected,
  onAllProcessed
}) => {
  const [processing, setProcessing] = useState<string | null>(null)
  const [processedSuggestions, setProcessedSuggestions] = useState<Set<string>>(new Set())

  const handleAccept = async (suggestion: MatchingSuggestion) => {
    setProcessing(suggestion.prompt_id)
    
    try {
      await SERPService.setPromptAssociation(suggestion.prompt_id, {
        serp_keyword_id: suggestion.keyword_id
      })
      
      setProcessedSuggestions(prev => new Set([...prev, suggestion.prompt_id]))
      onSuggestionAccepted(suggestion.prompt_id, suggestion.keyword_id)
    } catch (error) {
      console.error('Erreur lors de l\'acceptation:', error)
    } finally {
      setProcessing(null)
    }
  }

  const handleReject = (suggestion: MatchingSuggestion) => {
    setProcessedSuggestions(prev => new Set([...prev, suggestion.prompt_id]))
    onSuggestionRejected(suggestion.prompt_id)
  }

  const remainingSuggestions = suggestions.filter(
    suggestion => !processedSuggestions.has(suggestion.prompt_id)
  )

  const handleAcceptAll = async () => {
    setProcessing('all')
    
    try {
      for (const suggestion of remainingSuggestions) {
        if (suggestion.confidence_level === 'high') {
          await SERPService.setPromptAssociation(suggestion.prompt_id, {
            serp_keyword_id: suggestion.keyword_id
          })
          setProcessedSuggestions(prev => new Set([...prev, suggestion.prompt_id]))
          onSuggestionAccepted(suggestion.prompt_id, suggestion.keyword_id)
        }
      }
      
      onAllProcessed?.()
    } catch (error) {
      console.error('Erreur lors de l\'acceptation en masse:', error)
    } finally {
      setProcessing(null)
    }
  }

  if (suggestions.length === 0) {
    return null
  }

  if (remainingSuggestions.length === 0) {
    return (
      <Card>
        <div className="text-center py-8">
          <div className="w-16 h-16 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
            Toutes les suggestions traitées !
          </h3>
          <p className="text-gray-600 dark:text-gray-400">
            Vous avez traité toutes les suggestions d'association.
          </p>
        </div>
      </Card>
    )
  }

  const highConfidenceSuggestions = remainingSuggestions.filter(s => s.confidence_level === 'high')

  return (
    <Card>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            Suggestions d'association
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            {remainingSuggestions.length} suggestion{remainingSuggestions.length !== 1 ? 's' : ''} à traiter
          </p>
        </div>

        <div className="flex items-center space-x-3">
          {highConfidenceSuggestions.length > 0 && (
            <Button
              size="sm"
              onClick={handleAcceptAll}
              disabled={processing === 'all'}
              loading={processing === 'all'}
            >
              Accepter toutes les suggestions fiables ({highConfidenceSuggestions.length})
            </Button>
          )}
        </div>
      </div>

      <div className="space-y-4">
        {remainingSuggestions.map((suggestion) => (
          <div
            key={suggestion.prompt_id}
            className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700"
          >
            <div className="flex-1 min-w-0">
              <div className="flex items-center space-x-3 mb-2">
                <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                  {suggestion.prompt_name}
                </h4>
                <Badge
                  variant={
                    suggestion.confidence_level === 'high' ? 'success' :
                    suggestion.confidence_level === 'medium' ? 'warning' : 'error'
                  }
                  size="sm"
                >
                  {suggestion.confidence_level === 'high' ? 'Fiable' :
                   suggestion.confidence_level === 'medium' ? 'Moyen' : 'Faible'}
                </Badge>
              </div>

              <div className="space-y-1">
                <div className="flex items-center space-x-4 text-sm text-gray-600 dark:text-gray-400">
                  <span>
                    <strong>Mot-clé:</strong> {suggestion.keyword}
                  </span>
                  <span>
                    <strong>Score:</strong> {(suggestion.score * 100).toFixed(0)}%
                  </span>
                </div>
                
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full transition-all ${
                      suggestion.confidence_level === 'high' ? 'bg-green-500' :
                      suggestion.confidence_level === 'medium' ? 'bg-yellow-500' : 'bg-red-500'
                    }`}
                    style={{ width: `${suggestion.score * 100}%` }}
                  />
                </div>
              </div>
            </div>

            <div className="flex items-center space-x-2 ml-4">
              <Button
                size="sm"
                onClick={() => handleAccept(suggestion)}
                disabled={processing === suggestion.prompt_id || processing === 'all'}
                loading={processing === suggestion.prompt_id}
              >
                ✓ Accepter
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => handleReject(suggestion)}
                disabled={processing === suggestion.prompt_id || processing === 'all'}
              >
                ✗ Rejeter
              </Button>
            </div>
          </div>
        ))}
      </div>

      {/* Statistiques */}
      <div className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <div className="text-lg font-semibold text-green-600 dark:text-green-400">
              {suggestions.filter(s => s.confidence_level === 'high').length}
            </div>
            <div className="text-xs text-gray-500 dark:text-gray-400">
              Fiables
            </div>
          </div>
          <div>
            <div className="text-lg font-semibold text-yellow-600 dark:text-yellow-400">
              {suggestions.filter(s => s.confidence_level === 'medium').length}
            </div>
            <div className="text-xs text-gray-500 dark:text-gray-400">
              Moyennes
            </div>
          </div>
          <div>
            <div className="text-lg font-semibold text-red-600 dark:text-red-400">
              {suggestions.filter(s => s.confidence_level === 'low').length}
            </div>
            <div className="text-xs text-gray-500 dark:text-gray-400">
              Faibles
            </div>
          </div>
        </div>
      </div>
    </Card>
  )
}

export default SERPSuggestions