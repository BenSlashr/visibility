import React, { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Calendar, Tag, Brain } from 'lucide-react'
import { PromptsAPI } from '../../services/prompts'
import { AIModelsAPI } from '../../services/aiModels'
import { Select } from '../ui'

type TimeFilter = 'last24h' | 'last7days' | 'last30days' | 'custom'

interface DashboardFiltersProps {
  projectId?: string
  timeFilter: TimeFilter
  onChange: (filters: { timeFilter: TimeFilter; tag?: string; modelId?: string }) => void
}

export const DashboardFilters: React.FC<DashboardFiltersProps> = ({ projectId, timeFilter, onChange }) => {
  const [searchParams, setSearchParams] = useSearchParams()
  const [tags, setTags] = useState<string[]>([])
  const [models, setModels] = useState<{ id: string; name: string }[]>([])
  const [tag, setTag] = useState<string>(searchParams.get('tag') || '')
  const [modelId, setModelId] = useState<string>(searchParams.get('model_id') || '')

  const timeFilterOptions = useMemo(() => ([
    { value: 'last24h' as TimeFilter, label: 'Dernières 24h' },
    { value: 'last7days' as TimeFilter, label: '7 derniers jours' },
    { value: 'last30days' as TimeFilter, label: '30 derniers jours' },
  ]), [])

  // Charger tags et modèles disponibles selon projet
  useEffect(() => {
    const loadOptions = async () => {
      try {
        if (!projectId) {
          setTags([])
          setModels([])
          return
        }
        const prompts = await PromptsAPI.getAll({ project_id: projectId, limit: 1000 })
        const tagSet = new Set<string>()
        prompts.forEach(p => p.tags?.forEach((t: string) => tagSet.add(t)))
        setTags(Array.from(tagSet).sort())

        const activeModels = await AIModelsAPI.getActive()
        setModels(activeModels.map(m => ({ id: (m as any).id, name: (m as any).name })))
      } catch (e) {
        // no-op UI
      }
    }
    loadOptions()
  }, [projectId])

  // Sync URL query params
  useEffect(() => {
    const next = new URLSearchParams(searchParams)
    if (tag) next.set('tag', tag); else next.delete('tag')
    if (modelId) next.set('model_id', modelId); else next.delete('model_id')
    setSearchParams(next, { replace: true })
    onChange({ timeFilter, tag, modelId })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tag, modelId])

  return (
    <div className="flex items-center space-x-4">
      {/* Période */}
      <div className="flex items-center space-x-2">
        <Calendar className="h-4 w-4 text-gray-500" />
        <select
          value={timeFilter}
          onChange={(e) => onChange({ timeFilter: e.target.value as TimeFilter, tag, modelId })}
          className="text-sm border border-gray-300 rounded-md px-3 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {timeFilterOptions.map(option => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>

      {/* Tag */}
      <div className="flex items-center space-x-2">
        <Tag className="h-4 w-4 text-gray-500" />
        <Select
          value={tag || undefined}
          onChange={(v) => setTag(v || '')}
          options={tags.map(t => ({ value: t, label: t }))}
          placeholder="Tous les tags"
        />
      </div>

      {/* Modèle IA */}
      <div className="flex items-center space-x-2">
        <Brain className="h-4 w-4 text-gray-500" />
        <Select
          value={modelId || undefined}
          onChange={(v) => setModelId(v || '')}
          options={models.map(m => ({ value: m.id, label: m.name }))}
          placeholder="Tous les modèles"
        />
      </div>
    </div>
  )
}


