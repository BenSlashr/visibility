import React from 'react'
import { Card } from '../ui/Card'
import { Badge } from '../ui/Badge'
import { Button } from '../ui/Button'

interface SERPAssociation {
  prompt_id: string
  prompt_name: string
  keyword: string
  // Données SERP (Google SEO)
  serp_position: number
  volume?: number
  url?: string
  // Données de visibilité IA
  ai_visibility_percentage?: number
  ai_links_percentage?: number
  ai_average_position?: number
  // Métadonnées d'association
  matching_score?: number
  association_type: 'manual' | 'auto'
}

interface SERPComparisonTableProps {
  associations: SERPAssociation[]
  loading?: boolean
}

export const SERPComparisonTable: React.FC<SERPComparisonTableProps> = ({
  associations,
  loading = false
}) => {
  if (loading) {
    return (
      <Card>
        <div className="animate-pulse space-y-4">
          {[1, 2, 3].map(i => (
            <div key={i} className="h-16 bg-gray-200 dark:bg-gray-700 rounded"></div>
          ))}
        </div>
      </Card>
    )
  }

  if (!associations || associations.length === 0) {
    return (
      <Card>
        <div className="text-center py-8">
          <div className="w-16 h-16 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
            Aucune association trouvée
          </h3>
          <p className="text-gray-600 dark:text-gray-400">
            Utilisez l'association automatique ou créez des associations manuelles pour voir les comparaisons ici.
          </p>
        </div>
      </Card>
    )
  }

  const getPositionBadge = (position: number) => {
    if (position <= 3) return { variant: 'success' as const, label: `#${position}` }
    if (position <= 10) return { variant: 'warning' as const, label: `#${position}` }
    return { variant: 'error' as const, label: `#${position}` }
  }

  const getPercentageBadge = (percentage?: number) => {
    if (!percentage && percentage !== 0) return { variant: 'neutral' as const, label: '-' }
    if (percentage >= 70) return { variant: 'success' as const, label: `${percentage}%` }
    if (percentage >= 40) return { variant: 'warning' as const, label: `${percentage}%` }
    return { variant: 'error' as const, label: `${percentage}%` }
  }

  const formatVolume = (volume?: number) => {
    if (!volume) return '-'
    if (volume >= 1000) return `${(volume / 1000).toFixed(1)}k`
    return volume.toString()
  }

  return (
    <Card>
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
          Comparaison Prompt ↔ SERP
        </h3>
        <div className="text-sm text-gray-500 dark:text-gray-400">
          {associations.length} association{associations.length !== 1 ? 's' : ''}
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            {/* En-tête de groupe */}
            <tr className="border-b border-gray-300 dark:border-gray-600">
              <th className="text-left py-2 px-4 font-medium text-gray-900 dark:text-gray-100">
                Prompt
              </th>
              <th className="text-left py-2 px-4 font-medium text-gray-900 dark:text-gray-100">
                Mot-clé
              </th>
              <th colSpan={3} className="text-center py-2 px-4 font-bold text-blue-700 dark:text-blue-300 bg-blue-50 dark:bg-blue-900/20">
                📊 Google SEO (SERP)
              </th>
              <th colSpan={3} className="text-center py-2 px-4 font-bold text-purple-700 dark:text-purple-300 bg-purple-50 dark:bg-purple-900/20">
                🤖 Visibilité IA
              </th>
              <th className="text-center py-2 px-4 font-medium text-gray-900 dark:text-gray-100">
                Matching
              </th>
            </tr>
            {/* Sous-en-têtes détaillés */}
            <tr className="border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50">
              <th className="text-left py-3 px-4 text-sm font-medium text-gray-600 dark:text-gray-400">
                Nom
              </th>
              <th className="text-left py-3 px-4 text-sm font-medium text-gray-600 dark:text-gray-400">
                Requête
              </th>
              {/* Colonnes Google SEO */}
              <th className="text-center py-3 px-2 text-sm font-medium text-blue-700 dark:text-blue-300">
                Position
              </th>
              <th className="text-center py-3 px-2 text-sm font-medium text-blue-700 dark:text-blue-300">
                Volume
              </th>
              <th className="text-center py-3 px-2 text-sm font-medium text-blue-700 dark:text-blue-300">
                URL
              </th>
              {/* Colonnes Visibilité IA */}
              <th className="text-center py-3 px-2 text-sm font-medium text-purple-700 dark:text-purple-300">
                Visibilité %
              </th>
              <th className="text-center py-3 px-2 text-sm font-medium text-purple-700 dark:text-purple-300">
                Liens %
              </th>
              <th className="text-center py-3 px-2 text-sm font-medium text-purple-700 dark:text-purple-300">
                Pos. IA
              </th>
              {/* Matching */}
              <th className="text-center py-3 px-2 text-sm font-medium text-gray-600 dark:text-gray-400">
                Score
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
            {associations.map((association, index) => {
              const serpPositionBadge = getPositionBadge(association.serp_position)
              const visibilityBadge = getPercentageBadge(association.ai_visibility_percentage)
              const linksBadge = getPercentageBadge(association.ai_links_percentage)
              const aiPositionBadge = association.ai_average_position ? getPositionBadge(association.ai_average_position) : { variant: 'neutral' as const, label: '-' }
              
              return (
                <tr key={`${association.prompt_id}-${index}`} className="hover:bg-gray-50 dark:hover:bg-gray-800/50">
                  {/* Prompt */}
                  <td className="py-4 px-4">
                    <div className="flex flex-col max-w-xs">
                      <span className="font-medium text-gray-900 dark:text-gray-100 truncate">
                        {association.prompt_name}
                      </span>
                      <span className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                        ID: {association.prompt_id.slice(0, 8)}...
                      </span>
                    </div>
                  </td>
                  
                  {/* Mot-clé */}
                  <td className="py-4 px-4">
                    <div className="flex flex-col max-w-xs">
                      <span className="font-medium text-gray-900 dark:text-gray-100 truncate">
                        {association.keyword}
                      </span>
                    </div>
                  </td>
                  
                  {/* Google SEO - Position */}
                  <td className="py-4 px-2 text-center">
                    <Badge variant={serpPositionBadge.variant} size="sm">
                      {serpPositionBadge.label}
                    </Badge>
                  </td>
                  
                  {/* Google SEO - Volume */}
                  <td className="py-4 px-2 text-center">
                    <div className="flex flex-col items-center">
                      <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                        {formatVolume(association.volume)}
                      </span>
                      {association.volume && (
                        <span className="text-xs text-gray-500 dark:text-gray-400">
                          /mois
                        </span>
                      )}
                    </div>
                  </td>
                  
                  {/* Google SEO - URL */}
                  <td className="py-4 px-2 text-center">
                    {association.url ? (
                      <a 
                        href={association.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-blue-600 dark:text-blue-400 hover:underline truncate max-w-24 inline-block"
                        title={association.url}
                      >
                        🔗 Voir
                      </a>
                    ) : (
                      <span className="text-xs text-gray-400">-</span>
                    )}
                  </td>
                  
                  {/* IA - Visibilité % */}
                  <td className="py-4 px-2 text-center">
                    <Badge variant={visibilityBadge.variant} size="sm">
                      {visibilityBadge.label}
                    </Badge>
                  </td>
                  
                  {/* IA - Liens % */}
                  <td className="py-4 px-2 text-center">
                    <Badge variant={linksBadge.variant} size="sm">
                      {linksBadge.label}
                    </Badge>
                  </td>
                  
                  {/* IA - Position */}
                  <td className="py-4 px-2 text-center">
                    <Badge variant={aiPositionBadge.variant} size="sm">
                      {aiPositionBadge.label}
                    </Badge>
                  </td>
                  
                  {/* Matching Score */}
                  <td className="py-4 px-2 text-center">
                    {association.matching_score ? (
                      <div className="flex flex-col items-center">
                        <span className="text-xs font-medium text-gray-900 dark:text-gray-100">
                          {(association.matching_score * 100).toFixed(0)}%
                        </span>
                        <div className="w-8 bg-gray-200 dark:bg-gray-700 rounded-full h-1 mt-1">
                          <div
                            className="bg-green-500 h-1 rounded-full"
                            style={{ width: `${association.matching_score * 100}%` }}
                          />
                        </div>
                        <Badge 
                          variant={association.association_type === 'auto' ? 'success' : 'neutral'} 
                          size="sm"
                          className="mt-1"
                        >
                          {association.association_type === 'auto' ? 'A' : 'M'}
                        </Badge>
                      </div>
                    ) : (
                      <Badge variant="neutral" size="sm">
                        M
                      </Badge>
                    )}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {/* Statistiques comparatives */}
      <div className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
        <div className="grid grid-cols-2 md:grid-cols-6 gap-4 text-center">
          {/* Stats SERP */}
          <div className="bg-blue-50 dark:bg-blue-900/20 p-3 rounded-lg">
            <div className="text-lg font-semibold text-blue-600 dark:text-blue-400">
              {associations.filter(a => a.serp_position <= 3).length}
            </div>
            <div className="text-xs text-blue-700 dark:text-blue-300 font-medium">
              📊 SERP Top 3
            </div>
          </div>
          <div className="bg-blue-50 dark:bg-blue-900/20 p-3 rounded-lg">
            <div className="text-lg font-semibold text-blue-600 dark:text-blue-400">
              {associations.filter(a => a.serp_position <= 10).length}
            </div>
            <div className="text-xs text-blue-700 dark:text-blue-300 font-medium">
              📊 SERP Top 10
            </div>
          </div>
          
          {/* Stats IA */}
          <div className="bg-purple-50 dark:bg-purple-900/20 p-3 rounded-lg">
            <div className="text-lg font-semibold text-purple-600 dark:text-purple-400">
              {associations.filter(a => (a.ai_visibility_percentage || 0) >= 70).length}
            </div>
            <div className="text-xs text-purple-700 dark:text-purple-300 font-medium">
              🤖 IA Visible 70%+
            </div>
          </div>
          <div className="bg-purple-50 dark:bg-purple-900/20 p-3 rounded-lg">
            <div className="text-lg font-semibold text-purple-600 dark:text-purple-400">
              {associations.filter(a => (a.ai_average_position || Infinity) <= 10).length}
            </div>
            <div className="text-xs text-purple-700 dark:text-purple-300 font-medium">
              🤖 IA Top 10
            </div>
          </div>
          
          {/* Métadonnées */}
          <div className="bg-gray-50 dark:bg-gray-800 p-3 rounded-lg">
            <div className="text-lg font-semibold text-gray-600 dark:text-gray-400">
              {associations.filter(a => a.association_type === 'auto').length}
            </div>
            <div className="text-xs text-gray-700 dark:text-gray-300 font-medium">
              🔗 Auto-associés
            </div>
          </div>
          <div className="bg-gray-50 dark:bg-gray-800 p-3 rounded-lg">
            <div className="text-lg font-semibold text-gray-600 dark:text-gray-400">
              {associations.reduce((sum, a) => sum + (a.volume || 0), 0).toLocaleString()}
            </div>
            <div className="text-xs text-gray-700 dark:text-gray-300 font-medium">
              🔍 Volume total
            </div>
          </div>
        </div>
        
        {/* Message d'analyse comparative */}
        <div className="mt-4 p-4 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
          <div className="text-sm text-gray-700 dark:text-gray-300 text-center">
            <span className="font-medium">💡 Analyse comparative :</span> Ce tableau compare les performances Google SEO (positions SERP, volumes de recherche) avec la visibilité de vos prompts dans les IA (ChatGPT, Claude, etc.).
          </div>
        </div>
      </div>
    </Card>
  )
}

export default SERPComparisonTable