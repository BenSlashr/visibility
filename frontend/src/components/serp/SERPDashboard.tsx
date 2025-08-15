import React from 'react'
import { Card } from '../ui/Card'
import { Badge } from '../ui/Badge'
import { Button } from '../ui/Button'
import { StatsCard } from '../dashboard/StatsCard'
import { useSERPProject, useSERPMetrics } from '../../hooks/useSERP'

interface SERPDashboardProps {
  projectId: string
  onUpload?: () => void
  onAutoMatch?: () => void
  onShowSuggestions?: () => void
}

export const SERPDashboard: React.FC<SERPDashboardProps> = ({
  projectId,
  onUpload,
  onAutoMatch,
  onShowSuggestions
}) => {
  const { summary, keywords, isLoading, error, refresh } = useSERPProject(projectId)
  const metrics = useSERPMetrics(keywords)

  if (isLoading) {
    return (
      <div className="space-y-6">
        {[1, 2, 3].map(i => (
          <div key={i} className="animate-pulse">
            <div className="h-32 bg-gray-200 dark:bg-gray-700 rounded-lg"></div>
          </div>
        ))}
      </div>
    )
  }

  if (error) {
    return (
      <Card>
        <div className="text-center py-8">
          <div className="w-16 h-16 bg-red-100 dark:bg-red-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
            Erreur de chargement
          </h3>
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            {error}
          </p>
          <Button onClick={refresh}>
            Réessayer
          </Button>
        </div>
      </Card>
    )
  }

  if (!summary?.has_serp_data) {
    return (
      <Card>
        <div className="text-center py-12">
          <div className="w-20 h-20 bg-blue-100 dark:bg-blue-900/30 rounded-full flex items-center justify-center mx-auto mb-6">
            <svg className="w-10 h-10 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          
          <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-3">
            Données SERP manquantes
          </h3>
          
          <p className="text-gray-600 dark:text-gray-400 mb-6 max-w-md mx-auto">
            Importez vos données de positionnement pour analyser les corrélations entre vos positions SERP et votre visibilité IA.
          </p>
          
          <div className="space-y-3">
            <Button onClick={onUpload} size="lg">
              <svg className="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              Importer un fichier CSV
            </Button>
            
            <div className="text-sm text-gray-500 dark:text-gray-400">
              Format attendu: keyword,volume,position,url
            </div>
          </div>
        </div>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* Statistiques principales */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatsCard
          title="Mots-clés importés"
          value={summary.import_info?.total_keywords || 0}
          icon="📊"
        />
        
        {summary.serp_stats && (
          <>
            <StatsCard
              title="Position moyenne"
              value={summary.serp_stats.average_position.toFixed(1)}
              icon="🎯"
              trend={summary.serp_stats.average_position <= 10 ? 'positive' : 'negative'}
            />
            
            <StatsCard
              title="Top 3"
              value={summary.serp_stats.top_3_keywords}
              icon="🏆"
              subtitle={`${((summary.serp_stats.top_3_keywords / (summary.import_info?.total_keywords || 1)) * 100).toFixed(1)}% des mots-clés`}
            />
            
            <StatsCard
              title="Top 10"
              value={summary.serp_stats.top_10_keywords}
              icon="⭐"
              subtitle={`${((summary.serp_stats.top_10_keywords / (summary.import_info?.total_keywords || 1)) * 100).toFixed(1)}% des mots-clés`}
            />
          </>
        )}
      </div>

      {/* Associations */}
      {summary.associations && (
        <Card>
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Associations Prompts ↔ SERP
            </h3>
            
            <div className="flex items-center space-x-3">
              <Badge variant={summary.associations.association_rate >= 80 ? 'success' : summary.associations.association_rate >= 50 ? 'warning' : 'error'}>
                {summary.associations.association_rate}% de couverture
              </Badge>
              
              <div className="flex items-center space-x-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={onAutoMatch}
                >
                  <svg className="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                  </svg>
                  Matching auto
                </Button>
                
                {summary.associations && summary.associations.unassociated_prompts > 0 && (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={onShowSuggestions}
                  >
                    <svg className="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
                    </svg>
                    Valider suggestions
                  </Button>
                )}
              </div>
            </div>
          </div>
          
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="text-center p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
              <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                {summary.associations.auto_associations}
              </div>
              <div className="text-sm text-green-700 dark:text-green-300">
                Associations automatiques
              </div>
            </div>
            
            <div className="text-center p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
              <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                {summary.associations.manual_associations}
              </div>
              <div className="text-sm text-blue-700 dark:text-blue-300">
                Associations manuelles
              </div>
            </div>
            
            <div className="text-center p-4 bg-orange-50 dark:bg-orange-900/20 rounded-lg">
              <div className="text-2xl font-bold text-orange-600 dark:text-orange-400">
                {summary.associations.unassociated_prompts}
              </div>
              <div className="text-sm text-orange-700 dark:text-orange-300">
                Prompts sans association
              </div>
            </div>
          </div>
        </Card>
      )}


      {/* Informations d'import */}
      {summary.import_info && (
        <Card>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
            Import actuel
          </h3>
          
          <div className="flex items-center justify-between">
            <div className="space-y-2">
              <div className="flex items-center space-x-2">
                <svg className="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  {summary.import_info.filename}
                </span>
              </div>
              
              <div className="flex items-center space-x-4 text-xs text-gray-500 dark:text-gray-400">
                <span>
                  Importé le {new Date(summary.import_info.import_date).toLocaleDateString('fr-FR')}
                </span>
                <span>
                  {summary.import_info.total_keywords} mots-clés
                </span>
              </div>
            </div>
            
            <Button
              size="sm"
              variant="outline"
              onClick={onUpload}
            >
              Nouvel import
            </Button>
          </div>
        </Card>
      )}
    </div>
  )
}

export default SERPDashboard