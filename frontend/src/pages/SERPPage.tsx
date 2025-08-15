import React, { useState } from 'react'
import { useCurrentProject } from '../contexts/ProjectContext'
import { SERPDashboard, SERPUpload, SERPComparisonTable } from '../components/serp'
import SERPSuggestions from '../components/serp/SERPSuggestions'
import { useSERPMatching, useSERPSuggestions, useSERPAssociations } from '../hooks/useSERP'
import { Header } from '../components/Header'
import { Modal } from '../components/ui/Modal'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'

export const SERPPage: React.FC = () => {
  const { currentProject } = useCurrentProject()
  const [showUpload, setShowUpload] = useState(false)
  const [showAutoMatch, setShowAutoMatch] = useState(false)
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [refreshTrigger, setRefreshTrigger] = useState(0)

  const { isMatching, result: matchResult, error: matchError, autoMatch, reset: resetMatch } = useSERPMatching(currentProject?.id)
  const { suggestions, loading: suggestionsLoading, error: suggestionsError, stats: suggestionsStats, refresh: refreshSuggestions } = useSERPSuggestions(currentProject?.id, showSuggestions)
  const { associations, loading: associationsLoading, refresh: refreshAssociations } = useSERPAssociations(currentProject?.id)

  const handleUploadSuccess = (result: any) => {
    setShowUpload(false)
    setRefreshTrigger(prev => prev + 1)
    
    // Proposer le matching automatique après un import réussi
    if (result.success && result.keywords_imported > 0) {
      setShowAutoMatch(true)
    }
  }

  const handleAutoMatch = async () => {
    const result = await autoMatch()
    if (result && result.success) {
      setRefreshTrigger(prev => prev + 1)
      
      // Si il y a des suggestions, les afficher
      if (result.details.suggestions.length > 0) {
        setShowAutoMatch(false)
        setShowSuggestions(true)
      } else {
        setShowAutoMatch(false)
      }
    }
  }

  const handleSuggestionAccepted = (promptId: string, keywordId: string) => {
    setRefreshTrigger(prev => prev + 1)
    refreshAssociations() // Rafraîchir le tableau de comparaison
    // Ne pas refaire le calcul des suggestions ici pour éviter la lenteur
  }

  const handleSuggestionRejected = (promptId: string) => {
    // Pas besoin de rafraîchir pour un rejet
  }

  const handleAllSuggestionsProcessed = () => {
    setShowSuggestions(false)
    setRefreshTrigger(prev => prev + 1)
    // Les suggestions seront recalculées à la prochaine ouverture du modal
  }

  const handleCloseAutoMatch = () => {
    setShowAutoMatch(false)
    resetMatch()
  }

  if (!currentProject) {
    return (
      <div className="p-8">
        <Header title="SERP & Corrélations" />
        <div className="max-w-2xl mx-auto mt-8">
          <Card>
            <div className="text-center py-12">
              <div className="w-16 h-16 bg-orange-100 dark:bg-orange-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-orange-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
                Aucun projet sélectionné
              </h3>
              <p className="text-gray-600 dark:text-gray-400">
                Sélectionnez un projet pour voir ses données SERP et les corrélations avec l'IA.
              </p>
            </div>
          </Card>
        </div>
      </div>
    )
  }

  return (
    <div className="p-8">
      <Header 
        title="SERP & Corrélations" 
        subtitle={`Analysez les corrélations entre positions SERP et visibilité IA pour ${currentProject.name}`}
      />

      <div className="mt-8">
        <SERPDashboard
          key={refreshTrigger} // Force refresh
          projectId={currentProject.id}
          onUpload={() => setShowUpload(true)}
          onAutoMatch={() => setShowAutoMatch(true)}
          onShowSuggestions={() => setShowSuggestions(true)}
        />
      </div>

      {/* Tableau de comparaison des associations */}
      <div className="mt-8">
        <SERPComparisonTable
          associations={associations}
          loading={associationsLoading}
        />
      </div>

      {/* Modal Upload CSV */}
      <Modal
        isOpen={showUpload}
        onClose={() => setShowUpload(false)}
        title="Importer des données SERP"
        maxWidth="2xl"
      >
        <SERPUpload
          projectId={currentProject.id}
          onSuccess={handleUploadSuccess}
          onCancel={() => setShowUpload(false)}
        />
      </Modal>

      {/* Modal Auto-matching */}
      <Modal
        isOpen={showAutoMatch}
        onClose={handleCloseAutoMatch}
        title="Association automatique"
        maxWidth="xl"
      >
        <div className="space-y-6">
          <div className="text-center">
            <div className="w-16 h-16 bg-blue-100 dark:bg-blue-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
              </svg>
            </div>
            
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
              Association automatique
            </h3>
            
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              Associez automatiquement vos prompts aux mots-clés SERP basé sur la similarité de contenu.
            </p>
          </div>

          {/* Résultats du matching */}
          {matchResult && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="text-center p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
                  <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                    {matchResult.auto_matches}
                  </div>
                  <div className="text-sm text-green-700 dark:text-green-300">
                    Associations automatiques
                  </div>
                </div>
                
                <div className="text-center p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                  <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                    {matchResult.suggestions}
                  </div>
                  <div className="text-sm text-blue-700 dark:text-blue-300">
                    Suggestions à valider
                  </div>
                </div>
              </div>

              {matchResult.details.suggestions.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-3">
                    Suggestions à valider manuellement :
                  </h4>
                  <div className="space-y-2 max-h-48 overflow-y-auto">
                    {matchResult.details.suggestions.slice(0, 5).map((suggestion, index) => (
                      <div key={index} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                            {suggestion.prompt_name}
                          </p>
                          <p className="text-xs text-gray-500 dark:text-gray-400">
                            {suggestion.keyword} • Score: {(suggestion.score * 100).toFixed(0)}%
                          </p>
                        </div>
                        <div className={`px-2 py-1 rounded text-xs font-medium ${
                          suggestion.confidence_level === 'high' ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300' :
                          suggestion.confidence_level === 'medium' ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300' :
                          'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300'
                        }`}>
                          {suggestion.confidence_level}
                        </div>
                      </div>
                    ))}
                    {matchResult.details.suggestions.length > 5 && (
                      <p className="text-xs text-gray-500 dark:text-gray-400 text-center">
                        ... et {matchResult.details.suggestions.length - 5} autres suggestions
                      </p>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Erreur */}
          {matchError && (
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
              <div className="flex items-start">
                <svg className="w-5 h-5 text-red-400 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
                <div className="ml-3">
                  <h4 className="text-sm font-medium text-red-800 dark:text-red-200">
                    Erreur lors de l'association automatique
                  </h4>
                  <p className="text-sm text-red-700 dark:text-red-300 mt-1">
                    {matchError}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-3 justify-end">
            <Button
              variant="outline"
              onClick={handleCloseAutoMatch}
              disabled={isMatching}
            >
              {matchResult ? 'Fermer' : 'Annuler'}
            </Button>
            {!matchResult && (
              <Button
                onClick={handleAutoMatch}
                loading={isMatching}
                disabled={isMatching}
              >
                {isMatching ? 'Association...' : 'Démarrer l\'association'}
              </Button>
            )}
          </div>
        </div>
      </Modal>

      {/* Modal pour valider les suggestions */}
      <Modal
        isOpen={showSuggestions}
        onClose={() => {
          setShowSuggestions(false)
          // Rafraîchir le dashboard et les associations quand on ferme le modal
          setRefreshTrigger(prev => prev + 1)
          refreshAssociations()
        }}
        title="Valider les suggestions d'association"
        className="max-w-[90vw] w-full"
      >
        {suggestionsLoading ? (
          <div className="flex flex-col items-center justify-center py-8 space-y-4">
            <div className="animate-spin w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full"></div>
            <div className="text-center">
              <div className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
                Analyse des suggestions en cours...
              </div>
              {suggestionsStats && (
                <div className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
                  <div>
                    Analyse de {suggestionsStats.total_prompts_analyzed} prompts × {suggestionsStats.total_keywords_available} mots-clés
                  </div>
                  <div className="text-amber-600 dark:text-amber-400 font-medium">
                    ⏳ L'association peut prendre du temps si vous avez beaucoup de données
                  </div>
                  <div className="text-xs text-gray-500 mt-2">
                    {suggestionsStats.total_calculations?.toLocaleString()} calculs de similarité en cours...
                  </div>
                </div>
              )}
              {!suggestionsStats && (
                <div className="text-sm text-amber-600 dark:text-amber-400 font-medium">
                  ⏳ L'association peut prendre du temps si vous avez beaucoup de mots-clés
                </div>
              )}
            </div>
          </div>
        ) : suggestionsError ? (
          <div className="text-center py-8 text-red-600">
            Erreur: {suggestionsError}
          </div>
        ) : suggestions && suggestions.length > 0 ? (
          <SERPSuggestions
            suggestions={suggestions}
            onSuggestionAccepted={handleSuggestionAccepted}
            onSuggestionRejected={handleSuggestionRejected}
            onAllProcessed={handleAllSuggestionsProcessed}
          />
        ) : (
          <div className="text-center py-8 text-gray-500">
            Aucune suggestion disponible
          </div>
        )}
      </Modal>
    </div>
  )
}

export default SERPPage