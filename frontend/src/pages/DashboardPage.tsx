import React, { useState } from 'react'
import { RefreshCw } from 'lucide-react'
import { StatsGrid } from '../components/dashboard/StatsGrid'
import { VisibilityChart } from '../components/dashboard/VisibilityChart'
import { DashboardFilters } from '../components/dashboard/DashboardFilters'
import { FilterChips } from '../components/dashboard/FilterChips'
import { CompetitorVisibilityChart } from '../components/dashboard/CompetitorVisibilityChart'
import { AIModelComparisonChart } from '../components/dashboard/AIModelComparisonChart'
import { ProjectInsights } from '../components/dashboard/CompetitorRanking'
import { ShareOfVoice } from '../components/dashboard/ShareOfVoice'
import { TagsHeatmap } from '../components/dashboard/TagsHeatmap'
import { TagsVisibilityBlock } from '../components/dashboard/TagsVisibilityBlock'
import { RecentAnalyses } from '../components/dashboard/RecentAnalyses'
import { Button, Loading, ThemeToggle } from '../components/ui'
import { ProjectSelector } from '../components/ProjectSelector'
import { useCurrentProject } from '../contexts/ProjectContext'
import { useDashboardStats } from '../hooks/useDashboardStats'
import { useNavigate, useSearchParams } from 'react-router-dom'

type TimeFilter = 'last24h' | 'last7days' | 'last30days' | 'custom'

export const DashboardPage: React.FC = () => {
  const [timeFilter, setTimeFilter] = useState<TimeFilter>('last30days')
  const [tagFilter] = useState<string>('')
  const [modelId] = useState<string>('')
  const { currentProject } = useCurrentProject()
  const { stats, loading, error, refresh } = useDashboardStats(currentProject?.id)
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()

  // no local options here; handled by DashboardFilters

  // Gestion des erreurs
  if (error) {
    return (
      <div className="bg-gray-50 min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-600 text-xl mb-4">❌ Erreur de chargement</div>
          <p className="text-gray-600 mb-4">{error}</p>
          <Button onClick={refresh} variant="secondary">
            <RefreshCw className="h-4 w-4 mr-2" />
            Réessayer
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-gray-50">
      {/* Header avec filtres temporels */}
      <div className="bg-white/80 backdrop-blur shadow-sm border-b sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <h1 className="text-xl font-semibold text-gray-900">Dashboard</h1>
              {currentProject && (
                <div className="text-sm text-gray-600">
                  {currentProject.name}
                </div>
              )}
            </div>

            <div className="flex items-center space-x-4">
              <DashboardFilters 
                projectId={currentProject?.id}
                timeFilter={timeFilter}
                onChange={({ timeFilter: tf }) => {
                  setTimeFilter(tf)
                  // synchronized via props into chart
                }}
              />

              <ThemeToggle />
              <Button onClick={refresh} variant="secondary" size="sm">
                <RefreshCw className="h-4 w-4 mr-2" />
                Actualiser
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Contenu principal */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 pb-16">
        {/* Message explicatif si aucun projet sélectionné */}
        {!currentProject ? (
          <div className="text-center py-12">
            <div className="bg-white rounded-lg shadow-sm p-8 border border-gray-200">
              <div className="text-4xl mb-4">📊</div>
              <h2 className="text-xl font-semibold text-gray-900 mb-2">
                Sélectionnez un projet
              </h2>
              <p className="text-gray-600 mb-6">
                Pour voir le dashboard personnalisé avec les métriques, graphiques et analyses 
                spécifiques à votre projet, veuillez d'abord sélectionner un projet.
              </p>
              <ProjectSelector />
            </div>
          </div>
        ) : (
          <>
            {/* Filtres actifs (chips) */}
            <div className="mb-4">
              <FilterChips />
            </div>
            {loading ? (
              <div className="flex items-center justify-center py-12">
                <Loading size="lg" text="Chargement des données du projet..." />
              </div>
            ) : (
              <>
                {/* Grid des métriques principales */}
                <div className="mb-8">
                  <StatsGrid stats={stats} />
                </div>

                {/* Graphique principal full-width */}
                <div className="mb-8">
                  <VisibilityChart 
                    timeFilter={timeFilter} 
                    projectId={currentProject.id}
                    tagFilter={tagFilter}
                    modelId={modelId}
                    onPointClick={({ date }) => {
                      // Drill-down vers /analyses avec les filtres encodés
                      const params = new URLSearchParams()
                      params.set('project_id', currentProject.id)
                      params.set('date', date)
                      const tag = searchParams.get('tag')
                      const mid = searchParams.get('model_id')
                      if (tag) params.set('tag', tag)
                      if (mid) params.set('model_id', mid)
                      navigate({ pathname: '/analyses', search: params.toString() })
                    }}
                  />
                </div>

                {/* Graphique de comparaison avec les concurrents */}
                <div className="mb-8">
                  <CompetitorVisibilityChart 
                    timeFilter={timeFilter} 
                    projectId={currentProject.id}
                  />
                </div>

                {/* Graphique de comparaison des modèles IA */}
                <div className="mb-8">
                  <AIModelComparisonChart 
                    timeFilter={timeFilter} 
                    projectId={currentProject.id}
                  />
                </div>

                {/* Visibilité par tags (graph + classement) */}
                <div className="mb-8">
                  <TagsVisibilityBlock projectId={currentProject.id} />
                </div>

                {/* Grid 2 colonnes - Insights + Analyses récentes */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                  <ProjectInsights projectId={currentProject.id} />
                  <RecentAnalyses projectId={currentProject.id} />
                </div>

                {/* Share of Voice + Heatmap Tags */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mt-8">
                  <ShareOfVoice projectId={currentProject.id} />
                  <TagsHeatmap projectId={currentProject.id} />
                </div>
              </>
            )}
          </>
        )}
      </div>
    </div>
  )
} 