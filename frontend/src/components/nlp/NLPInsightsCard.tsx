/**
 * Composant principal pour afficher les insights NLP d'une analyse
 */

import React from 'react'
import { Brain, TrendingUp, Target, Tags, RefreshCw } from 'lucide-react'
import { Card, Button, Badge, Loading } from '../ui'
import { NLPResults, NLPUtils } from '../../services/nlp'

interface NLPInsightsCardProps {
  nlpData: NLPResults
  loading?: boolean
  onReanalyze?: () => Promise<void>
  showReanalyzeButton?: boolean
}

export const NLPInsightsCard: React.FC<NLPInsightsCardProps> = ({
  nlpData,
  loading = false,
  onReanalyze,
  showReanalyzeButton = true
}) => {
  const [reanalyzing, setReanalyzing] = React.useState(false)

  const handleReanalyze = async () => {
    if (!onReanalyze) return
    
    try {
      setReanalyzing(true)
      await onReanalyze()
    } finally {
      setReanalyzing(false)
    }
  }

  if (loading) {
    return (
      <Card className="p-6">
        <div className="flex items-center justify-center py-8">
          <Loading size="lg" text="Analyse NLP en cours..." />
        </div>
      </Card>
    )
  }

  // Vérification de sécurité
  if (!nlpData || !nlpData.seo_intent || !nlpData.content_type) {
    return (
      <Card className="p-6">
        <div className="text-center py-8">
          <div className="text-red-600 mb-4">⚠️ Données NLP incomplètes</div>
          <p className="text-gray-600">Les données NLP ne semblent pas être complètes.</p>
        </div>
      </Card>
    )
  }

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-purple-100 rounded-lg">
            <Brain className="w-5 h-5 text-purple-600" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Insights NLP</h3>
            <p className="text-sm text-gray-600">
              Confiance globale: {NLPUtils.formatConfidence(nlpData.global_confidence || 0)}
              <span className={`ml-2 px-2 py-1 rounded-md text-xs ${NLPUtils.getConfidenceColor(nlpData.global_confidence || 0)}`}>
                {NLPUtils.getConfidenceLevel(nlpData.global_confidence || 0)}
              </span>
            </p>
          </div>
        </div>
        
        {showReanalyzeButton && onReanalyze && (
          <Button
            variant="ghost"
            size="sm"
            onClick={handleReanalyze}
            disabled={reanalyzing}
            className="text-gray-600 hover:text-gray-800"
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${reanalyzing ? 'animate-spin' : ''}`} />
            {reanalyzing ? 'Re-analyse...' : 'Re-analyser'}
          </Button>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Intention SEO */}
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <Target className="w-4 h-4 text-blue-600" />
            <h4 className="font-medium text-gray-900">Intention SEO</h4>
          </div>
          
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <span className="text-xl">
                  {NLPUtils.getSEOIntentIcon(nlpData.seo_intent.main_intent || 'informational')}
                </span>
                <span className="font-medium">
                  {NLPUtils.translateSEOIntent(nlpData.seo_intent.main_intent || 'informational')}
                </span>
              </div>
              <Badge className={NLPUtils.getConfidenceColor(nlpData.seo_intent.confidence || 0)}>
                {NLPUtils.formatConfidence(nlpData.seo_intent.confidence || 0)}
              </Badge>
            </div>
            
            {/* Scores détaillés */}
            {nlpData.seo_intent.detailed_scores && (
              <div className="space-y-2">
                {Object.entries(nlpData.seo_intent.detailed_scores)
                  .sort(([,a], [,b]) => b - a)
                  .slice(0, 3)
                  .map(([intent, score]) => (
                    <div key={intent} className="flex items-center justify-between text-sm">
                      <span className="text-gray-600">
                        {NLPUtils.translateSEOIntent(intent)}
                      </span>
                      <div className="flex items-center gap-2">
                        <div className="w-16 bg-gray-200 rounded-full h-1.5">
                          <div 
                            className="bg-blue-500 h-1.5 rounded-full transition-all duration-300"
                            style={{ width: `${Math.min(100, score * 5)}%` }}
                          />
                        </div>
                        <span className="w-8 text-xs text-gray-500">
                          {score.toFixed(1)}
                        </span>
                      </div>
                    </div>
                  ))}
              </div>
            )}
          </div>
        </div>

        {/* Type de contenu */}
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-green-600" />
            <h4 className="font-medium text-gray-900">Type de contenu</h4>
          </div>
          
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <span className="font-medium capitalize">
                {nlpData.content_type.main_type || 'Inconnu'}
              </span>
              <Badge className={NLPUtils.getConfidenceColor(nlpData.content_type.confidence || 0)}>
                {NLPUtils.formatConfidence(nlpData.content_type.confidence || 0)}
              </Badge>
            </div>
            
            {/* Autres types détectés */}
            {nlpData.content_type.all_scores && Object.entries(nlpData.content_type.all_scores)
              .filter(([type, score]) => type !== nlpData.content_type.main_type && score > 0)
              .sort(([,a], [,b]) => b - a)
              .slice(0, 2)
              .map(([type, score]) => (
                <div key={type} className="text-sm text-gray-600 mb-1">
                  {type}: {score}
                </div>
              ))}
          </div>
        </div>

        {/* Business Topics */}
        {nlpData.business_topics && nlpData.business_topics.length > 0 && (
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <Tags className="w-4 h-4 text-orange-600" />
              <h4 className="font-medium text-gray-900">Topics Business</h4>
            </div>
            
            <div className="space-y-2">
              {nlpData.business_topics.slice(0, 5).map((topic, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium capitalize">{topic.topic}</span>
                      <Badge className={NLPUtils.getRelevanceColor(topic.relevance)}>
                        {topic.relevance}
                      </Badge>
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      {topic.top_keywords.slice(0, 3).join(', ')}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-medium text-gray-900">
                      {topic.score.toFixed(1)}
                    </div>
                    <div className="text-xs text-gray-500">
                      {topic.matches_count} matches
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Entités sectorielles */}
        {nlpData.sector_entities && Object.keys(nlpData.sector_entities).length > 0 && (
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <Target className="w-4 h-4 text-indigo-600" />
              <h4 className="font-medium text-gray-900">Entités détectées</h4>
            </div>
            
            <div className="space-y-3">
              {Object.entries(nlpData.sector_entities).map(([entityType, entities]) => (
                <div key={entityType} className="bg-gray-50 rounded-lg p-3">
                  <div className="font-medium text-sm text-gray-700 mb-2 capitalize">
                    {entityType}
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {entities && entities.slice(0, 6).map((entity, index) => (
                      <Badge 
                        key={index}
                        className="bg-white border border-gray-200 text-gray-700 hover:bg-gray-100"
                      >
                        {entity.name}
                        {entity.count > 1 && (
                          <span className="ml-1 text-xs text-gray-500">
                            ×{entity.count}
                          </span>
                        )}
                      </Badge>
                    ))}
                    {entities && entities.length > 6 && (
                      <Badge className="bg-gray-200 text-gray-600">
                        +{entities.length - 6} autres
                      </Badge>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Mots-clés sémantiques */}
      {nlpData.semantic_keywords && nlpData.semantic_keywords.length > 0 && (
        <div className="mt-6 pt-4 border-t border-gray-200">
          <h4 className="font-medium text-gray-900 mb-3">Mots-clés sémantiques</h4>
          <div className="flex flex-wrap gap-2">
            {nlpData.semantic_keywords.slice(0, 15).map((keyword, index) => (
              <Badge 
                key={index}
                className="bg-blue-50 border border-blue-200 text-blue-700"
              >
                {keyword}
              </Badge>
            ))}
            {nlpData.semantic_keywords.length > 15 && (
              <Badge className="bg-gray-100 text-gray-600">
                +{nlpData.semantic_keywords.length - 15} autres
              </Badge>
            )}
          </div>
        </div>
      )}

      {/* Métadonnées */}
      <div className="mt-4 pt-4 border-t border-gray-200">
        <div className="flex items-center justify-between text-xs text-gray-500">
          <span>Secteur: {nlpData.sector_context || 'Non défini'}</span>
          <span>Version: {nlpData.processing_version || '1.0'}</span>
          {nlpData.created_at && (
            <span>Analysé: {new Date(nlpData.created_at).toLocaleString()}</span>
          )}
        </div>
      </div>
    </Card>
  )
}