import React from 'react'
import { StatsCard } from './StatsCard'
import { BarChart3, Eye, CheckCircle, Link } from 'lucide-react'
import { Loading } from '../ui'

interface DashboardStats {
  totalAnalyses: number
  totalCost: number
  averageVisibilityScore: number
  brandMentionRate: number
  websiteLinkRate: number
  averageTokens: number
  analysesThisWeek: number
  analysesChange: number
  costChange: number
}

interface StatsGridProps {
  stats: DashboardStats | null
}

export const StatsGrid: React.FC<StatsGridProps> = ({ stats }) => {
  if (!stats) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="card p-4 animate-pulse">
            <Loading size="sm" />
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
      <StatsCard
        title="Analyses totales"
        value={stats.totalAnalyses.toString()}
        change={stats.analysesChange >= 0 ? `+${stats.analysesChange}` : stats.analysesChange.toString()}
        changeLabel="cette semaine"
        icon={<BarChart3 className="h-5 w-5 text-blue-600" />}
        trend={stats.analysesChange >= 0 ? "up" : "down"}
      />
      
      <StatsCard
        title="Score visibilité"
        value={`${stats.averageVisibilityScore}%`}
        change=""
        changeLabel="score moyen"
        icon={<Eye className="h-5 w-5 text-purple-600" />}
        trend="up"
      />
      
      <StatsCard
        title="Taux mention"
        value={`${stats.brandMentionRate}%`}
        change=""
        changeLabel="marque citée"
        icon={<CheckCircle className="h-5 w-5 text-green-600" />}
        trend="up"
      />
      
      <StatsCard
        title="Taux de liens"
        value={`${stats.websiteLinkRate}%`}
        change=""
        changeLabel="liens obtenus"
        icon={<Link className="h-5 w-5 text-indigo-600" />}
        trend="up"
      />
    </div>
  )
} 