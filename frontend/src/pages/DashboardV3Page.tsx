import React, { useState } from 'react'
import { ThemeToggle, Card } from '../components/ui'
import { useCurrentProject } from '../contexts/ProjectContext'
import { DashboardFilters } from '../components/dashboard/DashboardFilters'
import { VisibilityChart } from '../components/dashboard/VisibilityChart'
import { useCompetitorVisibilityChart } from '../hooks/useCompetitorVisibilityChart'

type TimeFilter = 'last24h' | 'last7days' | 'last30days' | 'custom'

const PanelHeader: React.FC<{ title: string; subtitle?: string; right?: React.ReactNode }>=({ title, subtitle, right }) => (
  <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-800">
    <div>
      <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100">{title}</h3>
      {subtitle && <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">{subtitle}</p>}
    </div>
    {right}
  </div>
)

export const DashboardV3Page: React.FC = () => {
  const { currentProject } = useCurrentProject()
  const [timeFilter, setTimeFilter] = useState<TimeFilter>('last30days')
  const { data: competitorData } = useCompetitorVisibilityChart(timeFilter, currentProject?.id)

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-[#0b1220]">
      {/* Header */}
      <header className="sticky top-0 z-10 backdrop-blur bg-white/70 dark:bg-gray-900/50 border-b border-gray-200 dark:border-gray-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold text-gray-900 dark:text-gray-100">Dashboard V3</h1>
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

      {/* Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Top: Brand visibility + Ranking */}
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
          {/* Brand visibility */}
          <Card className="xl:col-span-2 p-0">
            <PanelHeader 
              title="Visibility score"
              subtitle="Pourcentage de réponses IA qui mentionnent votre marque/site"
            />
            <div className="p-6">
              <VisibilityChart timeFilter={timeFilter} projectId={currentProject?.id} variant="embedded" />
            </div>
          </Card>

          {/* Ranking */}
          <Card className="p-0">
            <PanelHeader title="Classement des marques" subtitle="Rang actuel et score moyen" />
            <div className="p-2 sm:p-4">
              {!competitorData || competitorData.competitorRanking.length === 0 ? (
                <div className="h-80 flex items-center justify-center text-gray-500 text-sm">Aucune donnée de classement</div>
              ) : (
                <ul className="divide-y divide-gray-200 dark:divide-gray-800">
                  {competitorData.competitorRanking.slice(0, 6).map((item, index) => (
                    <li key={item.id} className="flex items-center justify-between py-3 px-2">
                      <div className="flex items-center gap-3">
                        <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold text-white ${
                          index === 0 ? 'bg-emerald-600' : index === 1 ? 'bg-sky-600' : index === 2 ? 'bg-violet-600' : 'bg-gray-600'
                        }`}>{index + 1}</div>
                        <span className={`text-sm ${item.isMainSite ? 'text-emerald-600 dark:text-emerald-400' : 'text-gray-900 dark:text-gray-200'}`}>{item.isMainSite ? 'Vous' : item.name}</span>
                      </div>
                      <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">{item.score}%</div>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </Card>
        </div>

        {/* Below: Placeholder sections to extend later */}
        <Card className="p-0">
          <PanelHeader title="Comparaison des modèles IA" />
          <div className="p-6">
            {/* On réutilise le composant existant pour rester productif */}
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">Comparaison à venir (réutilisation composant existant possible).</p>
          </div>
        </Card>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <Card className="p-0">
            <PanelHeader title="Analyses récentes" />
            <div className="p-6 text-sm text-gray-600 dark:text-gray-400">Section à brancher.</div>
          </Card>
          <Card className="p-0">
            <PanelHeader title="Share of Voice / Tags" />
            <div className="p-6 text-sm text-gray-600 dark:text-gray-400">Section à brancher.</div>
          </Card>
        </div>
      </main>
    </div>
  )
}

export default DashboardV3Page



