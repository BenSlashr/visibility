import React, { useState } from 'react'
import { ChevronDown, X, Check } from 'lucide-react'

interface Option {
  id: string
  name: string
  description?: string
}

interface MultiSelectProps {
  options: Option[]
  selectedIds: string[]
  onChange: (selectedIds: string[]) => void
  placeholder?: string
  label?: string
  disabled?: boolean
  maxHeight?: string
}

export const MultiSelect: React.FC<MultiSelectProps> = ({
  options,
  selectedIds,
  onChange,
  placeholder = "Sélectionner des options",
  label,
  disabled = false,
  maxHeight = "200px"
}) => {
  const [isOpen, setIsOpen] = useState(false)

  const selectedOptions = options.filter(option => selectedIds.includes(option.id))

  const toggleOption = (optionId: string) => {
    if (selectedIds.includes(optionId)) {
      onChange(selectedIds.filter(id => id !== optionId))
    } else {
      onChange([...selectedIds, optionId])
    }
  }

  const removeOption = (optionId: string) => {
    onChange(selectedIds.filter(id => id !== optionId))
  }

  const clearAll = () => {
    onChange([])
  }

  return (
    <div className="relative">
      {label && (
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          {label}
        </label>
      )}
      
      {/* Selected items display */}
      {selectedOptions.length > 0 && (
        <div className="mb-2 flex flex-wrap gap-1">
          {selectedOptions.map(option => (
            <span
              key={option.id}
              className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-500/20 dark:text-blue-300"
            >
              {option.name}
              <button
                type="button"
                onClick={() => removeOption(option.id)}
                className="ml-1 inline-flex items-center justify-center w-4 h-4 rounded-full text-blue-400 hover:bg-blue-200 hover:text-blue-600"
                disabled={disabled}
              >
                <X className="w-3 h-3" />
              </button>
            </span>
          ))}
          {selectedOptions.length > 1 && (
            <button
              type="button"
              onClick={clearAll}
              className="text-xs text-gray-500 hover:text-gray-700 underline"
              disabled={disabled}
            >
              Tout supprimer
            </button>
          )}
        </div>
      )}

      {/* Dropdown trigger */}
      <div className="relative">
        <button
          type="button"
          onClick={() => setIsOpen(!isOpen)}
          disabled={disabled}
          className={`
            w-full px-3 py-2 text-left border rounded-lg bg-white dark:bg-gray-900/60 dark:border-gray-700 backdrop-blur
            ${disabled ? 'bg-gray-50 text-gray-400 cursor-not-allowed dark:bg-gray-800/50' : 'hover:border-gray-400 dark:hover:border-gray-500'}
            ${isOpen ? 'border-blue-500 ring-1 ring-blue-500' : 'border-gray-300 dark:border-gray-700'}
            flex items-center justify-between
          `}
        >
          <span className="text-sm">
            {selectedOptions.length === 0 
              ? placeholder 
              : `${selectedOptions.length} modèle${selectedOptions.length > 1 ? 's' : ''} sélectionné${selectedOptions.length > 1 ? 's' : ''}`
            }
          </span>
          <ChevronDown className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
        </button>

        {/* Dropdown menu */}
        {isOpen && (
          <>
            {/* Overlay */}
            <div
              className="fixed inset-0 z-10"
              onClick={() => setIsOpen(false)}
            />
            
            {/* Options */}
            <div 
              className="absolute z-20 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg overflow-hidden dark:bg-gray-900/80 dark:border-gray-700 backdrop-blur"
              style={{ maxHeight }}
            >
              <div className="max-h-48 overflow-y-auto py-1">
                {options.length === 0 ? (
                  <div className="px-3 py-2 text-sm text-gray-500">
                    Aucune option disponible
                  </div>
                ) : (
                  options.map(option => {
                    const isSelected = selectedIds.includes(option.id)
                    return (
                      <button
                        key={option.id}
                        type="button"
                        onClick={() => toggleOption(option.id)}
                        className={`
                          w-full px-3 py-2 text-left text-sm hover:bg-gray-50 dark:hover:bg-gray-800/60
                          flex items-center justify-between group
                          ${isSelected ? 'bg-blue-50 dark:bg-blue-500/10' : ''}
                        `}
                      >
                        <div className="flex-1">
                          <div className={`font-medium ${isSelected ? 'text-blue-900 dark:text-blue-300' : 'text-gray-900 dark:text-gray-100'}`}>
                            {option.name}
                          </div>
                          {option.description && (
                            <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                              {option.description}
                            </div>
                          )}
                        </div>
                        {isSelected && (
                          <Check className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                        )}
                      </button>
                    )
                  })
                )}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
} 