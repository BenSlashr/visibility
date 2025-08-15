import React, { useState } from 'react'
import { ThemeToggle } from '../components/ui'
import { VisibilityChart } from '../components/dashboard/VisibilityChart'
import { AIModelComparisonChart } from '../components/dashboard/AIModelComparisonChart'
import { ShareOfVoice } from '../components/dashboard/ShareOfVoice'
import { TagsHeatmap } from '../components/dashboard/TagsHeatmap'
import { RecentAnalyses } from '../components/dashboard/RecentAnalyses'
import { DashboardFilters } from '../components/dashboard/DashboardFilters'
import { useCurrentProject } from '../contexts/ProjectContext'
import { useCompetitorVisibilityChart } from '../hooks/useCompetitorVisibilityChart'

type TimeFilter = 'last24h' | 'last7days' | 'last30days' | 'custom'

export const DashboardV2Page: React.FC = () => {
  const { currentProject } = useCurrentProject()
  const [timeFilter, setTimeFilter] = useState<TimeFilter>('last30days')
  const { data: competitorData, loading: competitorLoading } = useCompetitorVisibilityChart(timeFilter, currentProject?.id)

  return (
    <div className="aurora-bg min-h-screen">
      <header className="sticky top-0 z-10 backdrop-blur-md bg-white/60 dark:bg-gray-900/40 border-b border-gray-200/70 dark:border-gray-800/60">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold text-gray-900 dark:text-gray-100">Dashboard V2</h1>
            {currentProject && (
              <div className="text-xs text-gray-500 dark:text-gray-400">{currentProject.name}</div>
            )}
          </div>
          <div className="flex items-center gap-3">
            <DashboardFilters 
              projectId={currentProject?.id}
              timeFilter={timeFilter}
              onChange={({ timeFilter: tf }) => setTimeFilter(tf)}
            />
            <ThemeToggle />
          </div>
        </div>
      </header>

      <main className="relative z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
          {/* Bloc principal: graphique à gauche + ranking à droite */}
          <section className="grid grid-cols-1 xl:grid-cols-3 gap-8">
            <div className="xl:col-span-2 glass p-0">
              <div className="panel-header">
                <h3 className="panel-title">Visibility score</h3>
                <p className="panel-subtitle">Pourcentage de réponses IA qui mentionnent votre marque/site</p>
              </div>
              <div className="p-6">
                <VisibilityChart timeFilter={timeFilter} projectId={currentProject?.id} />
              </div>
            </div>
            <aside className="glass p-0">
              <div className="panel-header">
                <h3 className="panel-title">Classement des marques</h3>
                <p className="panel-subtitle">Rang actuel et score moyen</p>
              </div>
              <div className="p-2 sm:p-4">
                {!currentProject ? (
                  <div className="h-80 flex items-center justify-center text-gray-400 text-sm">Sélectionnez un projet</div>
                ) : competitorLoading ? (
                  <div className="h-80 flex items-center justify-center text-gray-400 text-sm">Chargement…</div>
                ) : !competitorData || competitorData.competitorRanking.length === 0 ? (
                  <div className="h-80 flex items-center justify-center text-gray-400 text-sm">Aucune donnée de classement</div>
                ) : (
                  <ul className="divide-y divide-gray-800/60">
                    {competitorData.competitorRanking.slice(0, 6).map((item, index) => (
                      <li key={item.id} className="ranking-item">
                        <div className="flex items-center gap-3">
                          <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold text-white ${
                            index === 0 ? 'bg-emerald-600' : index === 1 ? 'bg-sky-600' : index === 2 ? 'bg-violet-600' : 'bg-gray-700'
                          }`}>{index + 1}</div>
                          <span className={`text-sm ${item.isMainSite ? 'text-emerald-400' : 'text-gray-200'}`}>{item.isMainSite ? 'Vous' : item.name}</span>
                        </div>
                        <div className="text-sm font-semibold text-gray-100">{item.score}%</div>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </aside>
          </section>

          {/* Comparaison modèles IA */}
          <div className="glass p-0">
            <div className="p-6 border-b border-gray-800/60">
              <h3 className="text-sm font-medium text-gray-100">Comparaison des modèles IA</h3>
            </div>
            <div className="p-6">
              <AIModelComparisonChart timeFilter={timeFilter} projectId={currentProject?.id} />
            </div>
          </div>

          {/* Bas de page: analyses récentes + SOV + heatmap */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div className="glass p-6">
              <RecentAnalyses projectId={currentProject?.id} />
            </div>
            <div className="space-y-8">
              <div className="glass p-6">
                <ShareOfVoice projectId={currentProject?.id} />
              </div>
              <div className="glass p-6">
                <TagsHeatmap projectId={currentProject?.id} />
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

export default DashboardV2Page


