import React, { useState } from 'react'
import { clsx } from 'clsx'
import { Button } from '../ui/Button'
import { Select } from '../ui/Select'
import { Badge } from '../ui/Badge'
import { useSERPAssociation } from '../../hooks/useSERP'
import type { SERPKeyword } from '../../types/serp'

interface SERPAssociationProps {
  promptId: string
  promptName: string
  availableKeywords: SERPKeyword[]
  onUpdate?: () => void
}

export const SERPAssociation: React.FC<SERPAssociationProps> = ({
  promptId,
  promptName,
  availableKeywords,
  onUpdate
}) => {
  const { association, loading, error, setAssociation, removeAssociation } = useSERPAssociation(promptId)
  const [isEditing, setIsEditing] = useState(false)
  const [selectedKeywordId, setSelectedKeywordId] = useState<string>('')

  const handleSave = async () => {
    if (!selectedKeywordId) return

    const success = await setAssociation({
      serp_keyword_id: selectedKeywordId
    })

    if (success) {
      setIsEditing(false)
      onUpdate?.()
    }
  }

  const handleRemove = async () => {
    const success = await removeAssociation()
    if (success) {
      onUpdate?.()
    }
  }

  const handleCancel = () => {
    setIsEditing(false)
    setSelectedKeywordId('')
  }

  const keywordOptions = availableKeywords.map(keyword => ({
    value: keyword.id,
    label: `${keyword.keyword} (pos. ${keyword.position}${keyword.volume ? `, ${keyword.volume.toLocaleString()} vol.` : ''})`
  }))

  if (loading) {
    return (
      <div className="flex items-center space-x-2">
        <div className="animate-spin w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full"></div>
        <span className="text-sm text-gray-500">Chargement...</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-sm text-red-600 dark:text-red-400">
        Erreur: {error}
      </div>
    )
  }

  if (isEditing) {
    return (
      <div className="space-y-3">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Associer à un mot-clé SERP :
          </label>
          <Select
            value={selectedKeywordId}
            onChange={(value) => setSelectedKeywordId(value)}
            options={keywordOptions}
            placeholder="Sélectionner un mot-clé..."
          />
        </div>
        
        <div className="flex gap-2">
          <Button
            size="sm"
            onClick={handleSave}
            disabled={!selectedKeywordId}
          >
            Associer
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={handleCancel}
          >
            Annuler
          </Button>
        </div>
      </div>
    )
  }

  if (!association?.has_association) {
    return (
      <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 bg-gray-200 dark:bg-gray-700 rounded-full flex items-center justify-center">
            <svg className="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
            </svg>
          </div>
          <div>
            <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
              Aucune association SERP
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Ce prompt n'est pas lié à un mot-clé SERP
            </p>
          </div>
        </div>
        
        <Button
          size="sm"
          variant="outline"
          onClick={() => setIsEditing(true)}
          disabled={availableKeywords.length === 0}
        >
          Associer
        </Button>
      </div>
    )
  }

  const assoc = association.association!

  return (
    <div className="flex items-center justify-between p-3 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800">
      <div className="flex items-center space-x-3">
        <div className="w-8 h-8 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center">
          <svg className="w-4 h-4 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
          </svg>
        </div>
        
        <div className="flex-1 min-w-0">
          <div className="flex items-center space-x-2">
            <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
              {assoc.keyword}
            </p>
            <Badge
              variant={assoc.association_type === 'auto' ? 'success' : 'info'}
              size="sm"
            >
              {assoc.association_type === 'auto' ? 'Auto' : 'Manuel'}
            </Badge>
          </div>
          
          <div className="flex items-center space-x-4 mt-1">
            <span className="text-xs text-gray-500 dark:text-gray-400">
              Position: <span className="font-medium text-gray-700 dark:text-gray-300">#{assoc.position}</span>
            </span>
            
            {assoc.volume && (
              <span className="text-xs text-gray-500 dark:text-gray-400">
                Volume: <span className="font-medium text-gray-700 dark:text-gray-300">{assoc.volume.toLocaleString()}</span>
              </span>
            )}
            
            {assoc.matching_score && (
              <span className="text-xs text-gray-500 dark:text-gray-400">
                Score: <span className="font-medium text-gray-700 dark:text-gray-300">{(assoc.matching_score * 100).toFixed(0)}%</span>
              </span>
            )}
          </div>
        </div>
      </div>
      
      <div className="flex items-center space-x-2 ml-4">
        <Button
          size="sm"
          variant="outline"
          onClick={() => setIsEditing(true)}
        >
          Modifier
        </Button>
        <Button
          size="sm"
          variant="outline"
          onClick={handleRemove}
          className="text-red-600 hover:text-red-700 hover:bg-red-50 dark:text-red-400 dark:hover:text-red-300 dark:hover:bg-red-900/20"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </Button>
      </div>
    </div>
  )
}