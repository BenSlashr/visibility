import React, { useState, useRef } from 'react'
import { clsx } from 'clsx'
import { Card } from '../ui/Card'
import { Button } from '../ui/Button'
import { Input } from '../ui/Input'
import { useSERPUpload, useCSVPreview } from '../../hooks/useSERP'
import type { SERPUploadFormData } from '../../types/serp'

interface SERPUploadProps {
  projectId: string
  onSuccess?: (result: any) => void
  onCancel?: () => void
}

export const SERPUpload: React.FC<SERPUploadProps> = ({
  projectId,
  onSuccess,
  onCancel
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [formData, setFormData] = useState<SERPUploadFormData>({
    file: null,
    notes: ''
  })
  
  const { isUploading, uploadProgress, error: uploadError, result, uploadCSV, reset } = useSERPUpload(projectId)
  const { preview, loading: previewLoading, error: previewError, previewFile, reset: resetPreview } = useCSVPreview()

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    setFormData(prev => ({ ...prev, file }))
    
    // Prévisualiser le fichier
    await previewFile(file)
  }

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    
    const result = await uploadCSV(formData)
    if (result && result.success && onSuccess) {
      onSuccess(result)
    }
  }

  const handleReset = () => {
    setFormData({ file: null, notes: '' })
    resetPreview()
    reset()
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const handleCancel = () => {
    handleReset()
    onCancel?.()
  }

  // Si upload réussi, afficher les résultats
  if (result && result.success) {
    return (
      <Card className="max-w-2xl mx-auto">
        <div className="text-center">
          <div className="w-16 h-16 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
            Import réussi !
          </h3>
          
          <div className="space-y-2 text-sm text-gray-600 dark:text-gray-400 mb-6">
            <p>{result.keywords_imported} mots-clés importés</p>
            {result.errors_count > 0 && (
              <p className="text-orange-600">{result.errors_count} erreurs détectées</p>
            )}
          </div>

          {result.errors.length > 0 && (
            <div className="bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-800 rounded-lg p-4 mb-6">
              <h4 className="text-sm font-medium text-orange-800 dark:text-orange-200 mb-2">
                Erreurs détectées :
              </h4>
              <ul className="text-xs text-orange-700 dark:text-orange-300 space-y-1">
                {result.errors.slice(0, 5).map((error, index) => (
                  <li key={index}>{error}</li>
                ))}
                {result.errors.length > 5 && (
                  <li>... et {result.errors.length - 5} autres erreurs</li>
                )}
              </ul>
            </div>
          )}

          <div className="flex gap-3 justify-center">
            <Button onClick={handleReset} variant="outline">
              Importer un autre fichier
            </Button>
            <Button onClick={() => onSuccess?.(result)}>
              Continuer
            </Button>
          </div>
        </div>
      </Card>
    )
  }

  return (
    <Card className="max-w-2xl mx-auto">
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* En-tête */}
        <div className="text-center">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
            Importer des données SERP
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Importez un fichier CSV avec vos positions de mots-clés
          </p>
        </div>

        {/* Format attendu */}
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
          <h4 className="text-sm font-medium text-blue-900 dark:text-blue-100 mb-2">
            Format CSV attendu :
          </h4>
          <code className="text-xs text-blue-800 dark:text-blue-200 bg-blue-100 dark:bg-blue-900/30 px-2 py-1 rounded">
            keyword,volume,position,url
          </code>
          <p className="text-xs text-blue-700 dark:text-blue-300 mt-2">
            Les colonnes <strong>keyword</strong> et <strong>position</strong> sont obligatoires.
          </p>
        </div>

        {/* Sélection de fichier */}
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Fichier CSV
            </label>
            <div className="relative">
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv"
                onChange={handleFileSelect}
                className="hidden"
              />
              
              <div
                onClick={() => fileInputRef.current?.click()}
                className={clsx(
                  'border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors',
                  formData.file
                    ? 'border-green-300 bg-green-50 dark:border-green-700 dark:bg-green-900/20'
                    : 'border-gray-300 hover:border-gray-400 dark:border-gray-700 dark:hover:border-gray-600'
                )}
              >
                {formData.file ? (
                  <div>
                    <div className="w-12 h-12 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center mx-auto mb-3">
                      <svg className="w-6 h-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </div>
                    <p className="text-sm text-green-700 dark:text-green-300 font-medium">
                      {formData.file.name}
                    </p>
                    <p className="text-xs text-green-600 dark:text-green-400">
                      {(formData.file.size / 1024).toFixed(1)} KB
                    </p>
                  </div>
                ) : (
                  <div>
                    <div className="w-12 h-12 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mx-auto mb-3">
                      <svg className="w-6 h-6 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                      </svg>
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Cliquez pour sélectionner un fichier CSV
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                      Maximum 10MB
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Prévisualisation */}
          {previewLoading && (
            <div className="text-center py-4">
              <div className="animate-spin w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full mx-auto mb-2"></div>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Lecture du fichier...
              </p>
            </div>
          )}

          {preview && (
            <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
              <div className="bg-gray-50 dark:bg-gray-800 px-4 py-2 border-b border-gray-200 dark:border-gray-700">
                <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  Aperçu des données (5 premières lignes)
                </h4>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full text-xs">
                  <thead className="bg-gray-50 dark:bg-gray-800">
                    <tr>
                      {preview.headers.map((header, index) => (
                        <th key={index} className="px-3 py-2 text-left font-medium text-gray-700 dark:text-gray-300">
                          {header}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                    {preview.rows.map((row, rowIndex) => (
                      <tr key={rowIndex} className="bg-white dark:bg-gray-900">
                        {row.map((cell, cellIndex) => (
                          <td key={cellIndex} className="px-3 py-2 text-gray-900 dark:text-gray-100">
                            {cell}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Notes */}
          <div>
            <label htmlFor="notes" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Notes (optionnel)
            </label>
            <Input
              id="notes"
              type="text"
              placeholder="Ex: Import du 15/01/2024 - SEMrush"
              value={formData.notes}
              onChange={(e) => setFormData(prev => ({ ...prev, notes: e.target.value }))}
            />
          </div>
        </div>

        {/* Erreurs */}
        {(uploadError || previewError) && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
            <div className="flex items-start">
              <svg className="w-5 h-5 text-red-400 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
              <div className="ml-3">
                <h4 className="text-sm font-medium text-red-800 dark:text-red-200">
                  Erreur
                </h4>
                <p className="text-sm text-red-700 dark:text-red-300 mt-1">
                  {uploadError || previewError}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Progress */}
        {isUploading && (
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600 dark:text-gray-400">Import en cours...</span>
              {uploadProgress && <span className="text-gray-600 dark:text-gray-400">{uploadProgress}%</span>}
            </div>
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
              <div 
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: uploadProgress ? `${uploadProgress}%` : '30%' }}
              />
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-3 justify-end pt-4">
          <Button
            type="button"
            variant="outline"
            onClick={handleCancel}
            disabled={isUploading}
          >
            Annuler
          </Button>
          <Button
            type="submit"
            disabled={!formData.file || isUploading || previewLoading}
            loading={isUploading}
          >
            {isUploading ? 'Import...' : 'Importer'}
          </Button>
        </div>
      </form>
    </Card>
  )
}

export default SERPUpload