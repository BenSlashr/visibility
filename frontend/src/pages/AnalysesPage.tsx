import React, { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Search, Filter, Download, TrendingUp, TrendingDown, BarChart3, RefreshCw, MessageSquare, Bot } from 'lucide-react'
import { AnalysisCard } from '../components/AnalysisCard'
import { Button, Input, Modal, Loading } from '../components/ui'
import { useAnalyses } from '../hooks/useAnalyses'
import { useCurrentProject } from '../contexts/ProjectContext'
import { useProjects } from '../hooks/useProjects'
import { AnalysesAPI } from '../services/analyses'
import type { AnalysisFilters, AnalysisSummary, Analysis } from '../types/analysis'

export const AnalysesPage: React.FC = () => {
  const { currentProject } = useCurrentProject()
  const { projects } = useProjects()
  const [searchParams] = useSearchParams()
  
  // État pour les filtres
  const [filters, setFilters] = useState<AnalysisFilters>({
    project_id: currentProject?.id,
    limit: 50
  })
  
  const { analyses, loading, error, fetchAnalyses, refresh } = useAnalyses(filters)
  
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedProject, setSelectedProject] = useState<string>(currentProject?.id || 'all')
  const [selectedModel, setSelectedModel] = useState<string>('all')
  const [brandMentionFilter, setBrandMentionFilter] = useState<string>('all')
  const [withSourcesOnly, setWithSourcesOnly] = useState<boolean>(false)
  // Pré-remplir depuis l'URL si présent (drill-down)
  useEffect(() => {
    const pid = searchParams.get('project_id')
    // const date = searchParams.get('date')
    // const tag = searchParams.get('tag')
    // const modelId = searchParams.get('model_id')
    if (pid) setSelectedProject(pid)
    // On peut exploiter date/tag/modelId pour un futur filtrage avancé
  }, [searchParams])

  const [selectedAnalysis, setSelectedAnalysis] = useState<AnalysisSummary | null>(null)
  const [selectedAnalysisDetails, setSelectedAnalysisDetails] = useState<Analysis | null>(null)
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false)
  const [isLoadingDetails, setIsLoadingDetails] = useState(false)

  // Mise à jour des filtres quand le projet actuel change
  useEffect(() => {
    if (currentProject?.id !== selectedProject && currentProject?.id) {
      setSelectedProject(currentProject.id)
    }
  }, [currentProject?.id])

  // Application des filtres
  useEffect(() => {
    const newFilters: AnalysisFilters = {
      limit: 50
    }

    if (selectedProject !== 'all') {
      newFilters.project_id = selectedProject
    }

    if (brandMentionFilter === 'mentioned') {
      newFilters.brand_mentioned = true
    } else if (brandMentionFilter === 'not_mentioned') {
      newFilters.brand_mentioned = false
    }

    if (searchTerm.trim()) {
      newFilters.search = searchTerm.trim()
    }

    // Appliquer les filtres URL si présents
    const dateParam = searchParams.get('date')
    const tag = searchParams.get('tag')
    const modelId = searchParams.get('model_id')
    if (modelId) (newFilters as any).model_id = modelId
    if (dateParam) {
      // Filtrer du jour 'date' à 'date'
      (newFilters as any)['date_from'] = dateParam as string
      (newFilters as any)['date_to'] = dateParam as string
    }
    if (tag) (newFilters as any).tag = tag
    if (withSourcesOnly) (newFilters as any).has_sources = true

    setFilters(newFilters)
  }, [selectedProject, brandMentionFilter, searchTerm, searchParams, withSourcesOnly])

  // Refetch quand les filtres changent (mais pas trop souvent)
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      fetchAnalyses(filters)
    }, 300) // Debounce de 300ms pour éviter les requêtes trop fréquentes

    return () => clearTimeout(timeoutId)
  }, [filters, fetchAnalyses])

  // Calculs des statistiques sur les analyses filtrées
  const totalAnalyses = analyses.length
  const mentionedCount = analyses.filter(a => a.brand_mentioned).length
  const totalCost = analyses.reduce((sum, a) => sum + (a.cost_estimated || 0), 0)
  const avgTokens = totalAnalyses > 0 ? 
    Math.round(analyses.reduce((sum, a) => sum + (a.tokens_used || 0), 0) / totalAnalyses) : 0
  const visibilityRate = totalAnalyses > 0 ? Math.round((mentionedCount / totalAnalyses) * 100) : 0
  const avgVisibilityScore = totalAnalyses > 0 ?
    Math.round(analyses.reduce((sum, a) => sum + (a.visibility_score || 0), 0) / totalAnalyses) : 0

  // Modèles uniques dans les analyses
  const uniqueModels = [...new Set(analyses.map(a => a.ai_model_used).filter(Boolean))]

  const handleViewDetails = async (analysis: AnalysisSummary) => {
    setSelectedAnalysis(analysis)
    setSelectedAnalysisDetails(null)
    setIsDetailModalOpen(true)
    setIsLoadingDetails(true)
    
    try {
      const fullAnalysis = await AnalysesAPI.getById(analysis.id)
      setSelectedAnalysisDetails(fullAnalysis)
    } catch (error) {
      console.error('❌ Erreur lors du chargement des détails:', error)
    } finally {
      setIsLoadingDetails(false)
    }
  }

  const handleRerun = (analysis: AnalysisSummary) => {
    console.log('🔄 Relancer analyse:', analysis.id)
    // TODO: Implémenter la relance d'analyse
  }

  const handleExport = () => {
    console.log('📊 Export des analyses:', analyses.length)
    // TODO: Implémenter l'export
  }

  const resetFilters = () => {
    setSearchTerm('')
    setSelectedProject(currentProject?.id || 'all')
    setSelectedModel('all')
    setBrandMentionFilter('all')
  }

  if (loading && analyses.length === 0) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loading size="lg" text="Chargement des analyses..." />
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-gray-50 min-h-screen">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center">
            <div className="text-red-600 text-xl mb-4">❌ Erreur</div>
            <p className="text-gray-600 mb-4">{error}</p>
            <Button onClick={refresh} variant="primary">
              <RefreshCw className="h-4 w-4 mr-2" />
              Réessayer
            </Button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-gray-50 min-h-screen">
      {/* Header */}
      <div className="bg-white shadow-sm border-b sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Analyses</h1>
              <p className="text-sm text-gray-600">
                Historique et résultats de vos exécutions
                {currentProject && (
                  <span className="ml-2 text-blue-600">• {currentProject.name}</span>
                )}
              </p>
            </div>
            
            <div className="flex items-center space-x-2">
              <Button 
                variant="ghost" 
                onClick={refresh} 
                disabled={loading}
              >
                <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                Actualiser
              </Button>
              <Button variant="outline" onClick={handleExport}>
              <Download className="h-4 w-4 mr-2" />
              Exporter
            </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Contenu principal */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats rapides */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-8">
          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <div className="text-2xl font-bold text-gray-900">{totalAnalyses}</div>
            <div className="text-sm text-gray-600">Analyses</div>
          </div>
          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <div className="flex items-center space-x-1">
              <div className="text-2xl font-bold text-green-600">{visibilityRate}%</div>
              {visibilityRate >= 50 ? (
                <TrendingUp className="h-4 w-4 text-green-600" />
              ) : (
                <TrendingDown className="h-4 w-4 text-red-600" />
              )}
            </div>
            <div className="text-sm text-gray-600">Taux mention</div>
          </div>
          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <div className="text-2xl font-bold text-blue-600">{avgVisibilityScore}</div>
            <div className="text-sm text-gray-600">Score moyen</div>
          </div>
          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <div className="text-2xl font-bold text-purple-600">${totalCost.toFixed(3)}</div>
            <div className="text-sm text-gray-600">Coût total</div>
          </div>
          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <div className="text-2xl font-bold text-orange-600">{avgTokens}</div>
            <div className="text-sm text-gray-600">Tokens moy.</div>
          </div>
        </div>

        {/* Filtres */}
        <div className="bg-white p-4 rounded-lg border border-gray-200 mb-8">
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                type="text"
                placeholder="Rechercher..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            
            <select
              value={selectedProject}
              onChange={(e) => setSelectedProject(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">Tous les projets</option>
              {projects.map(project => (
                <option key={project.id} value={project.id}>{project.name}</option>
              ))}
            </select>
            
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">Tous les modèles</option>
              {uniqueModels.map(model => (
                <option key={model} value={model}>{model}</option>
              ))}
            </select>
            
            <select
              value={brandMentionFilter}
              onChange={(e) => setBrandMentionFilter(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">Toutes mentions</option>
              <option value="mentioned">Marque citée</option>
              <option value="not_mentioned">Marque non citée</option>
            </select>

            <label className="inline-flex items-center text-sm text-gray-700">
              <input
                type="checkbox"
                className="mr-2"
                checked={withSourcesOnly}
                onChange={(e) => setWithSourcesOnly(e.target.checked)}
              />
              Avec sources
            </label>
            
            <Button variant="outline" onClick={resetFilters}>
              <Filter className="h-4 w-4 mr-2" />
              Réinitialiser
            </Button>
          </div>
        </div>

        {/* Indicateur de chargement pour les filtres */}
        {loading && analyses.length > 0 && (
          <div className="text-center py-2 mb-4">
            <div className="inline-flex items-center text-sm text-gray-600">
              <RefreshCw className="h-4 w-4 animate-spin mr-2" />
              Mise à jour des résultats...
            </div>
          </div>
        )}

        {/* Liste des analyses */}
        {analyses.length > 0 ? (
        <div className="space-y-4">
            {analyses.map((analysis) => (
            <AnalysisCard
              key={analysis.id}
                analysis={{
                  id: analysis.id as any, // Conversion pour compatibilité
                  project_name: projects.find(p => p.id === analysis.project_id)?.name || 'Projet inconnu',
                  prompt_name: `Analyse ${analysis.id.slice(0, 8)}`, // Nom temporaire
                  ai_model: analysis.ai_model_used,
                  prompt_executed: '', // chargé au détail
                  ai_response: '', // chargé au détail
                  brand_mentioned: analysis.brand_mentioned,
                  website_mentioned: analysis.website_mentioned,
                  brand_position: analysis.ranking_position,
                  links_to_website: analysis.website_linked ? 1 : 0,
                  tokens_used: analysis.tokens_used,
                  processing_time: 0, // Non disponible dans le summary
                  cost: analysis.cost_estimated,
                  web_search_used: Boolean((analysis as any).web_search_used),
                  created_at: analysis.created_at
                }}
                onViewDetails={() => handleViewDetails(analysis)}
                onRerun={() => handleRerun(analysis)}
            />
          ))}
        </div>
        ) : (
          <div className="text-center py-12">
            <BarChart3 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              {searchTerm || selectedProject !== 'all' || brandMentionFilter !== 'all'
                ? 'Aucune analyse trouvée'
                : 'Aucune analyse disponible'}
            </h3>
            <p className="text-gray-600 mb-4">
              {searchTerm || selectedProject !== 'all' || brandMentionFilter !== 'all'
                ? 'Aucune analyse ne correspond à vos filtres.'
                : currentProject 
                  ? `Vous n'avez pas encore d'analyses pour le projet "${currentProject.name}".`
                : 'Vous n\'avez pas encore d\'analyses.'}
            </p>
            {(searchTerm || selectedProject !== 'all' || brandMentionFilter !== 'all') && (
              <Button variant="outline" onClick={resetFilters}>
                Réinitialiser les filtres
              </Button>
            )}
            {!currentProject && analyses.length === 0 && (
              <p className="text-sm text-gray-500 mt-2">
                Sélectionnez un projet et exécutez des prompts pour voir vos analyses ici.
              </p>
            )}
          </div>
        )}
      </div>

      {/* Modal de détail */}
      <Modal
        isOpen={isDetailModalOpen}
        onClose={() => setIsDetailModalOpen(false)}
        title="Détail de l'analyse"
        size="xl"
      >
        {selectedAnalysis && (
          <div className="space-y-6">
            {/* Info générale */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <h4 className="font-medium text-gray-900 mb-2">Projet</h4>
                <p className="text-sm text-gray-600">
                  {projects.find(p => p.id === selectedAnalysis.project_id)?.name || 'Projet inconnu'}
                </p>
              </div>
              <div>
                <h4 className="font-medium text-gray-900 mb-2">Modèle IA</h4>
                <p className="text-sm text-gray-600">{selectedAnalysis.ai_model_used}</p>
              </div>
            </div>

            {/* Métriques de visibilité */}
            <div>
              <h4 className="font-medium text-gray-900 mb-3">Métriques de visibilité</h4>
              <div className="grid grid-cols-2 gap-4">
                <div className="flex items-center space-x-2">
                  <div className={`w-3 h-3 rounded-full ${selectedAnalysis.brand_mentioned ? 'bg-green-500' : 'bg-red-500'}`}></div>
                  <span className="text-sm">
                    Marque {selectedAnalysis.brand_mentioned ? 'mentionnée' : 'non mentionnée'}
                  </span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className={`w-3 h-3 rounded-full ${selectedAnalysis.website_linked ? 'bg-blue-500' : 'bg-gray-400'}`}></div>
                  <span className="text-sm">
                    Lien {selectedAnalysis.website_linked ? 'présent' : 'absent'}
                  </span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 rounded-full bg-purple-500"></div>
                  <span className="text-sm">
                    Score de visibilité: {selectedAnalysis.visibility_score}/100
                  </span>
                </div>
                {selectedAnalysis.ranking_position && (
                  <div className="flex items-center space-x-2">
                    <div className="w-3 h-3 rounded-full bg-orange-500"></div>
                    <span className="text-sm">
                      Position: #{selectedAnalysis.ranking_position}
                    </span>
                  </div>
                )}
              </div>
            </div>

            {/* Prompt exécuté et réponse IA */}
            {isLoadingDetails ? (
              <div className="flex items-center justify-center py-8">
                <Loading size="lg" />
                <span className="ml-3 text-gray-600">Chargement des détails...</span>
              </div>
            ) : selectedAnalysisDetails ? (
              <div className="space-y-4">
                                 {/* Prompt exécuté */}
                 <div>
                   <h4 className="font-medium text-gray-900 mb-2 flex items-center">
                     <MessageSquare className="h-4 w-4 mr-2 text-gray-500" />
                     Prompt exécuté
                   </h4>
                  <div className="bg-gray-50 p-4 rounded-lg border">
                    <pre className="text-sm text-gray-700 whitespace-pre-wrap font-mono">
                      {selectedAnalysisDetails.prompt_executed}
                    </pre>
              </div>
            </div>

            {/* Réponse IA */}
            <div>
                   <h4 className="font-medium text-gray-900 mb-2 flex items-center">
                     <Bot className="h-4 w-4 mr-2 text-blue-500" />
                     Réponse de l'IA
                   </h4>
              <div className="bg-blue-50 p-4 rounded-lg border border-blue-200 max-h-96 overflow-y-auto">
                    <div className="text-sm text-gray-800 whitespace-pre-wrap">
                      {selectedAnalysisDetails.ai_response}
                    </div>
                  </div>
                </div>

            {/* Sources */}
            {selectedAnalysisDetails.sources && selectedAnalysisDetails.sources.length > 0 && (
              <div>
                <h4 className="font-medium text-gray-900 mb-2">Sources</h4>
                <div className="bg-white p-4 rounded-lg border border-gray-200 space-y-2">
                  {selectedAnalysisDetails.sources.map((s) => (
                    <div key={s.id} className="flex items-start justify-between">
                      <div className="min-w-0">
                        <a href={s.url} target="_blank" rel="noreferrer" className="text-blue-600 hover:underline break-all">
                          {s.title || s.url}
                        </a>
                        <div className="text-xs text-gray-500">
                          {s.domain} {s.citation_label ? `• ${s.citation_label}` : ''}
                        </div>
                        {s.snippet && (
                          <div className="text-xs text-gray-600 mt-1 line-clamp-2">
                            {s.snippet}
                          </div>
                        )}
                      </div>
                      <div className="text-xs text-gray-500 ml-4 whitespace-nowrap">
                        {s.is_valid === false && <span className="text-red-600">invalide</span>}
                        {s.is_valid === true && <span className="text-green-600">valide</span>}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
              </div>
            ) : (
              <div className="bg-yellow-50 p-3 rounded text-sm text-yellow-800">
                ⚠️ Impossible de charger les détails de l'analyse.
            </div>
            )}

            {/* Métriques techniques */}
            <div className="grid grid-cols-3 gap-4 pt-4 border-t">
              <div className="text-center">
                <div className="text-lg font-bold text-gray-900">
                  {selectedAnalysis.tokens_used}
                </div>
                <div className="text-sm text-gray-600">Tokens utilisés</div>
              </div>
              <div className="text-center">
                <div className="text-lg font-bold text-gray-900">
                  ${selectedAnalysis.cost_estimated.toFixed(4)}
                </div>
                <div className="text-sm text-gray-600">Coût estimé</div>
              </div>
              <div className="text-center">
                <div className="text-lg font-bold text-gray-900">
                  {new Date(selectedAnalysis.created_at).toLocaleDateString('fr-FR')}
                </div>
                <div className="text-sm text-gray-600">Date d'analyse</div>
              </div>
            </div>


          </div>
        )}
      </Modal>
    </div>
  )
} 