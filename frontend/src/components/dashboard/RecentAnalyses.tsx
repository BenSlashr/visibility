import React from 'react'
import { Brain, Clock, CheckCircle, XCircle, ArrowRight } from 'lucide-react'
import { clsx } from 'clsx'
import { useRecentAnalyses } from '../../hooks/useAnalyses'
import { Loading } from '../ui'

interface RecentAnalysesProps {
  projectId?: string
}

export const RecentAnalyses: React.FC<RecentAnalysesProps> = ({ projectId }) => {
  const { recentAnalyses, loading, error } = useRecentAnalyses(7)

  // Filtrer les analyses par projet si un projet est sélectionné
  const filteredAnalyses = projectId 
    ? recentAnalyses.filter(analysis => analysis.project_id === projectId)
    : recentAnalyses

  const formatRelativeTime = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffInHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60))
    
    if (diffInHours < 1) return 'il y a moins d\'1h'
    if (diffInHours < 24) return `il y a ${diffInHours}h`
    const diffInDays = Math.floor(diffInHours / 24)
    if (diffInDays === 1) return 'hier'
    if (diffInDays < 7) return `il y a ${diffInDays} jours`
    return date.toLocaleDateString('fr-FR')
  }

  return (
    <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Analyses récentes</h3>
          <p className="text-sm text-gray-600">
            {projectId 
              ? `Dernières analyses pour ce projet (${filteredAnalyses.length})`
              : `Toutes les analyses récentes (${filteredAnalyses.length})`
            }
          </p>
        </div>
      </div>

      {loading ? (
        <div className="space-y-4">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="flex items-center space-x-3 p-3 rounded-lg border">
              <Loading size="sm" />
            </div>
          ))}
        </div>
      ) : error ? (
        <div className="text-center py-8 text-red-600">
          ❌ Erreur lors du chargement des analyses
        </div>
      ) : filteredAnalyses.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <Brain className="h-12 w-12 mx-auto mb-4 text-gray-400" />
          <p className="text-lg font-medium text-gray-900 mb-2">Aucune analyse récente</p>
          <p className="text-sm">
            {projectId 
              ? 'Aucune analyse trouvée pour ce projet cette semaine.'
              : 'Aucune analyse trouvée cette semaine.'}
          </p>
          <p className="text-sm mt-2 text-blue-600">
            Exécutez des prompts pour voir les résultats ici
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {filteredAnalyses.slice(0, 5).map((analysis) => (
            <div
              key={analysis.id}
              className="flex items-center justify-between p-3 rounded-lg border border-gray-100 hover:border-gray-200 hover:bg-gray-50 transition-colors"
            >
              <div className="flex items-center space-x-3 flex-1">
                <div className="flex-shrink-0">
                  {analysis.brand_mentioned ? (
                    <CheckCircle className="h-5 w-5 text-green-600" />
                  ) : (
                    <XCircle className="h-5 w-5 text-red-600" />
                  )}
                </div>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2 mb-1">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      Analyse {analysis.id.slice(0, 8)}
                    </p>
                    <span className={clsx(
                      'inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium',
                      analysis.brand_mentioned
                        ? 'bg-green-100 text-green-800'
                        : 'bg-red-100 text-red-800'
                    )}>
                      {analysis.brand_mentioned ? 'Mentionnée' : 'Non mentionnée'}
                    </span>
                  </div>
                  
                  <div className="flex items-center space-x-4 text-xs text-gray-500">
                    <div className="flex items-center space-x-1">
                      <Brain className="h-3 w-3" />
                      <span>{analysis.ai_model_used}</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <Clock className="h-3 w-3" />
                      <span>{formatRelativeTime(analysis.created_at)}</span>
                    </div>
                    {analysis.visibility_score !== undefined && (
                      <div className="flex items-center space-x-1">
                        <span>Score: {analysis.visibility_score}%</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              <div className="flex-shrink-0">
                <ArrowRight className="h-4 w-4 text-gray-400" />
              </div>
            </div>
          ))}

          {filteredAnalyses.length > 5 && (
            <div className="text-center pt-4 border-t border-gray-100">
              <button className="text-sm text-blue-600 hover:text-blue-700 font-medium">
                Voir toutes les analyses ({filteredAnalyses.length})
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
} 