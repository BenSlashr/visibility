import React from 'react'
import { X } from 'lucide-react'
import { useSearchParams } from 'react-router-dom'

export const FilterChips: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams()
  const chips: Array<{ key: string; label: string; value: string }> = []

  const tag = searchParams.get('tag')
  const modelId = searchParams.get('model_id')
  const date = searchParams.get('date')
  if (tag) chips.push({ key: 'tag', label: 'Tag', value: tag })
  if (modelId) chips.push({ key: 'model_id', label: 'Modèle', value: modelId })
  if (date) chips.push({ key: 'date', label: 'Date', value: date })

  if (chips.length === 0) return null

  const clearChip = (key: string) => {
    const next = new URLSearchParams(searchParams)
    next.delete(key)
    setSearchParams(next, { replace: true })
  }

  const clearAll = () => {
    const next = new URLSearchParams(searchParams)
    ;['tag', 'model_id', 'date'].forEach(k => next.delete(k))
    setSearchParams(next, { replace: true })
  }

  return (
    <div className="flex items-center gap-2">
      {chips.map(chip => (
        <span
          key={chip.key}
          className="inline-flex items-center gap-1 px-2 py-1 rounded-full bg-primary-50 text-primary-700 text-xs border border-primary-100"
        >
          <span className="font-medium">{chip.label}:</span>
          <span className="truncate max-w-[120px]" title={chip.value}>{chip.value}</span>
          <button
            className="ml-1 hover:text-primary-900"
            onClick={() => clearChip(chip.key)}
            aria-label={`Retirer ${chip.label}`}
          >
            <X className="h-3 w-3" />
          </button>
        </span>
      ))}
      <button
        onClick={clearAll}
        className="text-xs text-gray-500 hover:text-gray-700 underline"
      >
        Effacer tout
      </button>
    </div>
  )
}


