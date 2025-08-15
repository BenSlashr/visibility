import React from 'react'
import { Target, Zap, Eye, CheckCircle } from 'lucide-react'
import { clsx } from 'clsx'

interface ProjectInsightsProps {
  projectId?: string
}

interface Insight {
  id: string
  type: 'success' | 'warning' | 'info'
  icon: React.ReactNode
  title: string
  description: string
  value?: string
}

export const ProjectInsights: React.FC<ProjectInsightsProps> = ({ projectId }) => {
  // Simuler des insights basés sur le projet
  const insights: Insight[] = projectId ? [
    {
      id: '1',
      type: 'success',
      icon: <CheckCircle className="h-5 w-5" />,
      title: 'Taux de mention élevé',
      description: 'Votre marque est mentionnée dans 75% des analyses',
      value: '75%'
    },
    {
      id: '2',
      type: 'info',
      icon: <Eye className="h-5 w-5" />,
      title: 'Score de visibilité stable',
      description: 'Maintien d\'un score constant sur les 7 derniers jours',
      value: '68%'
    },
    {
      id: '3',
      type: 'warning',
      icon: <Target className="h-5 w-5" />,
      title: 'Opportunité d\'amélioration',
      description: 'Augmentez le nombre de liens obtenus dans les réponses',
      value: '45%'
    },
    {
      id: '4',
      type: 'info',
      icon: <Zap className="h-5 w-5" />,
      title: 'Modèle IA performant',
      description: 'GPT-4 génère les meilleurs résultats pour ce projet'
    }
  ] : []

  const getInsightColor = (type: string) => {
    switch (type) {
      case 'success':
        return 'text-green-600 bg-green-100'
      case 'warning':
        return 'text-orange-600 bg-orange-100'
      case 'info':
        return 'text-blue-600 bg-blue-100'
      default:
        return 'text-gray-600 bg-gray-100'
    }
  }

  return (
    <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center space-x-2">
          <span>💡</span>
          <span>Insights du projet</span>
        </h3>
        <p className="text-sm text-gray-600 mt-1">
          {projectId 
            ? 'Analyses et recommandations pour ce projet'
            : 'Sélectionnez un projet pour voir les insights'
          }
        </p>
      </div>

      {!projectId ? (
        <div className="text-center py-8 text-gray-500">
          <Target className="h-12 w-12 mx-auto mb-4 text-gray-400" />
          <p className="text-lg font-medium text-gray-900 mb-2">Aucun projet sélectionné</p>
          <p className="text-sm">
            Sélectionnez un projet pour voir les insights et recommandations personnalisées.
          </p>
        </div>
      ) : insights.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <Zap className="h-12 w-12 mx-auto mb-4 text-gray-400" />
          <p className="text-lg font-medium text-gray-900 mb-2">Insights en cours de génération</p>
          <p className="text-sm">
            Exécutez quelques analyses pour obtenir des insights personnalisés.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {insights.map((insight) => (
            <div
              key={insight.id}
              className="flex items-start space-x-3 p-4 rounded-lg border border-gray-100 hover:border-gray-200 transition-colors"
            >
              <div className={clsx(
                'flex-shrink-0 p-2 rounded-full',
                getInsightColor(insight.type)
              )}>
                {insight.icon}
              </div>
              
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between mb-1">
                  <h4 className="text-sm font-medium text-gray-900">
                    {insight.title}
                  </h4>
                  {insight.value && (
                    <span className="text-sm font-semibold text-gray-900">
                      {insight.value}
                    </span>
                  )}
                </div>
                <p className="text-sm text-gray-600">
                  {insight.description}
                </p>
              </div>
            </div>
          ))}

          <div className="mt-6 pt-4 border-t border-gray-100">
            <div className="flex items-center justify-between">
              <p className="text-xs text-gray-500">
                Insights mis à jour en temps réel
              </p>
              <button className="text-xs text-blue-600 hover:text-blue-800 font-medium">
                Voir tous les insights →
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
} 