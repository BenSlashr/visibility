import React from 'react'
import { Tooltip } from '../ui'
import { TrendingUp, TrendingDown } from 'lucide-react'
import { clsx } from 'clsx'

interface StatsCardProps {
  title: string
  value: string
  change: string
  changeLabel: string
  icon: React.ReactNode
  trend: 'up' | 'down'
}

export const StatsCard: React.FC<StatsCardProps> = ({
  title,
  value,
  change,
  changeLabel,
  icon,
  trend
}) => {
  return (
    <div className="bg-white dark:bg-gray-900/60 rounded-lg shadow-sm dark:shadow-none p-6 border border-gray-200 dark:border-gray-800/80 backdrop-blur">
      {/* Header avec icône et titre */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          {icon}
          <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400">
            <Tooltip text={title}><span>{title}</span></Tooltip>
          </h3>
        </div>
      </div>

      {/* Valeur principale */}
      <div className="mb-3">
        <p className="text-3xl font-bold text-gray-900 dark:text-gray-100">{value}</p>
      </div>

      {/* Évolution */}
      <div className="flex items-center space-x-2">
        <div className={clsx(
          'flex items-center space-x-1 text-sm font-medium',
          trend === 'up' ? 'text-green-600' : 'text-red-600'
        )}>
          {trend === 'up' ? (
            <TrendingUp className="h-4 w-4" />
          ) : (
            <TrendingDown className="h-4 w-4" />
          )}
          <span>{change}</span>
        </div>
        <span className="text-sm text-gray-500 dark:text-gray-400">{changeLabel}</span>
      </div>
    </div>
  )
} 