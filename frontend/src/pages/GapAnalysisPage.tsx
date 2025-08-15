import React, { useState, useMemo } from 'react'
import { useCurrentProject } from '../contexts/ProjectContext'
import { Search, Filter, TrendingUp, AlertTriangle, Target, FileText, RefreshCw, Play, Eye } from 'lucide-react'
import { Button, Input, Select, Badge, Card, Loading } from '../components/ui'
import { useGapAnalysis } from '../hooks/useGapAnalysis'
import { useNavigate } from 'react-router-dom'

// Types pour le Gap Analysis
interface GapAnalysisItem {
  id: string
  query: string
  prompt_id: string
  competitor_name: string
  competitor_mentions: number
  competitor_rate: number
  our_mentions: number
  our_rate: number
  gap_score: number
  frequency_estimate: number
  last_seen: string
  gap_type: 'critical' | 'medium' | 'low'
  business_relevance: 'high' | 'medium' | 'low'
  suggested_action: string
  content_exists: boolean
}

export const GapAnalysisPage: React.FC = () => {
  const { currentProject } = useCurrentProject()
  const navigate = useNavigate()
  const [searchTerm, setSearchTerm] = useState('')
  const [priorityFilter, setPriorityFilter] = useState<string>('')
  const [competitorFilter, setCompetitorFilter] = useState<string>('')
  const [relevanceFilter, setRelevanceFilter] = useState<string>('')
  const [sortBy, setSortBy] = useState<'gap_score' | 'frequency' | 'relevance'>('gap_score')
  const [dateRange, setDateRange] = useState<string>('30')

  // Calcul des dates
  const dateTo = new Date().toISOString().split('T')[0]
  const dateFrom = new Date(Date.now() - parseInt(dateRange) * 24 * 60 * 60 * 1000).toISOString().split('T')[0]

  // Hook pour charger les données
  const { data, loading, error, refresh } = useGapAnalysis({
    project_id: currentProject?.id,
    date_from: dateFrom,
    date_to: dateTo,
    competitor_filter: competitorFilter || undefined,
    priority_filter: priorityFilter || undefined
  })

  // Calculs des KPIs (depuis les vraies données ou fallback)
  const totalGaps = data?.stats.total_gaps || 0
  const criticalGaps = data?.stats.critical_gaps || 0
  const mediumGaps = data?.stats.medium_gaps || 0
  const lowGaps = data?.stats.low_gaps || 0
  const averageGapScore = data?.stats.average_gap_score || 0
  const potentialVisibility = data?.stats.potential_monthly_mentions || 0

  // Filtrage et tri des données
  const filteredGaps = useMemo(() => {
    if (!data) return []
    
    let filtered = data.gaps.filter(gap => {
      const matchesSearch = gap.query.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           gap.competitor_name.toLowerCase().includes(searchTerm.toLowerCase())
      const matchesRelevance = !relevanceFilter || gap.business_relevance === relevanceFilter
      
      return matchesSearch && matchesRelevance
    })

    // Tri
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'gap_score':
          return b.gap_score - a.gap_score
        case 'frequency':
          return b.frequency_estimate - a.frequency_estimate
        case 'relevance':
          const relevanceOrder = { high: 3, medium: 2, low: 1 }
          return relevanceOrder[b.business_relevance] - relevanceOrder[a.business_relevance]
        default:
          return 0
      }
    })

    return filtered
  }, [data, searchTerm, relevanceFilter, sortBy])

  // Extraire la liste unique des concurrents pour le filtre
  const availableCompetitors = useMemo(() => {
    if (!data) return []
    const competitors = new Set(data.gaps.map(g => g.competitor_name))
    return Array.from(competitors).sort()
  }, [data])

  const getGapColor = (gapType: string) => {
    switch (gapType) {
      case 'critical': return 'text-red-600 bg-red-50 border-red-200'
      case 'medium': return 'text-amber-600 bg-amber-50 border-amber-200'
      case 'low': return 'text-green-600 bg-green-50 border-green-200'
      default: return 'text-gray-600 bg-gray-50 border-gray-200'
    }
  }

  const getGapIcon = (gapType: string) => {
    switch (gapType) {
      case 'critical': return <AlertTriangle className="w-4 h-4" />
      case 'medium': return <TrendingUp className="w-4 h-4" />
      case 'low': return <Target className="w-4 h-4" />
      default: return null
    }
  }

  // Actions pour les boutons
  const handleAnalyze = (gap: GapAnalysisItem) => {
    // Créer une nouvelle analyse basée sur cette requête
    const analysisParams = new URLSearchParams({
      prompt: gap.query,
      competitor: gap.competitor_name,
      project_id: currentProject?.id || '',
      gap_id: gap.id
    });
    navigate(`/analyses/new?${analysisParams.toString()}`);
  }

  const handleViewAnalyses = (gap: GapAnalysisItem) => {
    // Aller à la page des analyses filtrées par le prompt_id exact
    const searchParams = new URLSearchParams({
      prompt_id: gap.prompt_id,
      project_id: currentProject?.id || '',
      gap_context: 'true' // Indicateur que c'est depuis gap analysis
    });
    navigate(`/analyses?${searchParams.toString()}`);
  }


  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Gap Analysis</h1>
              {currentProject ? (
                <p className="text-sm text-gray-600">Projet • {currentProject.name}</p>
              ) : (
                <p className="text-sm text-gray-600">Aucun projet sélectionné</p>
              )}
              {data && (
                <p className="text-xs text-gray-500 mt-1">
                  {data.stats.total_analyses_analyzed} analyses sur {dateRange} jours
                </p>
              )}
            </div>
            <div className="flex items-center gap-2">
              <Button 
                variant="ghost" 
                onClick={refresh}
                disabled={loading}
              >
                <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                Actualiser
              </Button>
              <Button className="bg-blue-600 hover:bg-blue-700">
                <FileText className="w-4 h-4 mr-2" />
                Exporter rapport
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* Loading State */}
        {loading && (
          <div className="flex items-center justify-center py-12">
            <Loading size="lg" text="Analyse des gaps en cours..." />
          </div>
        )}

        {/* Error State */}
        {error && !loading && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-center">
              <AlertTriangle className="w-5 h-5 text-red-600 mr-2" />
              <span className="text-red-800 font-medium">Erreur lors du chargement</span>
            </div>
            <p className="text-red-700 text-sm mt-1">{error}</p>
            <Button 
              size="sm" 
              variant="outline" 
              className="mt-3"
              onClick={refresh}
            >
              Réessayer
            </Button>
          </div>
        )}

        {/* Content - Only show when not loading and no error */}
        {!loading && !error && data && (
          <>
            {/* KPIs Header */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Gaps totaux</p>
                <p className="text-2xl font-bold text-gray-900">{totalGaps}</p>
              </div>
              <div className="text-blue-600">
                <Search className="w-6 h-6" />
              </div>
            </div>
          </Card>

          <Card className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Gaps critiques</p>
                <p className="text-2xl font-bold text-red-600">{criticalGaps}</p>
              </div>
              <div className="text-red-600">
                <AlertTriangle className="w-6 h-6" />
              </div>
            </div>
          </Card>

          <Card className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Score gap moyen</p>
                <p className="text-2xl font-bold text-amber-600">{averageGapScore}%</p>
              </div>
              <div className="text-amber-600">
                <TrendingUp className="w-6 h-6" />
              </div>
            </div>
          </Card>

          <Card className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Potentiel mensuel</p>
                <p className="text-2xl font-bold text-green-600">+{potentialVisibility}</p>
                <p className="text-xs text-gray-500">mentions</p>
              </div>
              <div className="text-green-600">
                <Target className="w-6 h-6" />
              </div>
            </div>
          </Card>
        </div>

        {/* Filtres redesignés */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm">
          <div className="p-6">
            <div className="flex items-center gap-2 mb-4">
              <Filter className="w-5 h-5 text-slate-600" />
              <h3 className="text-lg font-semibold text-slate-900">Filtres</h3>
            </div>
            
            <div className="space-y-6">
              {/* Recherche principale */}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Recherche
                </label>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
                  <input
                    type="text"
                    placeholder="Rechercher par requête ou concurrent..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-10 pr-4 py-3 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
                  />
                </div>
              </div>

              {/* Filtres en grille */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {/* Période */}
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Période
                  </label>
                  <select
                    value={dateRange}
                    onChange={(e) => setDateRange(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white"
                  >
                    <option value="7">7 derniers jours</option>
                    <option value="30">30 derniers jours</option>
                    <option value="90">90 derniers jours</option>
                  </select>
                </div>

                {/* Priorité */}
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Priorité
                  </label>
                  <select
                    value={priorityFilter}
                    onChange={(e) => setPriorityFilter(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white"
                  >
                    <option value="">Toutes les priorités</option>
                    <option value="critical">Critiques uniquement</option>
                    <option value="medium">Moyennes uniquement</option>
                    <option value="low">Faibles uniquement</option>
                  </select>
                </div>

                {/* Concurrent */}
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Concurrent
                  </label>
                  <select
                    value={competitorFilter}
                    onChange={(e) => setCompetitorFilter(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white"
                  >
                    <option value="">Tous les concurrents</option>
                    {availableCompetitors.map(comp => (
                      <option key={comp} value={comp}>{comp}</option>
                    ))}
                  </select>
                </div>

                {/* Pertinence métier */}
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Pertinence métier
                  </label>
                  <select
                    value={relevanceFilter}
                    onChange={(e) => setRelevanceFilter(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white"
                  >
                    <option value="">Toute pertinence</option>
                    <option value="high">Haute pertinence</option>
                    <option value="medium">Pertinence moyenne</option>
                    <option value="low">Faible pertinence</option>
                  </select>
                </div>
              </div>

              {/* Tri et actions */}
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pt-4 border-t border-slate-100">
                <div className="flex items-center gap-2">
                  <label className="text-sm font-medium text-slate-700">
                    Trier par :
                  </label>
                  <select
                    value={sortBy}
                    onChange={(e) => setSortBy(e.target.value as any)}
                    className="px-3 py-1 border border-slate-200 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white text-sm"
                  >
                    <option value="gap_score">Score de gap</option>
                    <option value="frequency">Fréquence</option>
                    <option value="relevance">Pertinence</option>
                  </select>
                </div>
                
                <div className="text-sm text-slate-600">
                  {filteredGaps.length} résultat{filteredGaps.length !== 1 ? 's' : ''} trouvé{filteredGaps.length !== 1 ? 's' : ''}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Tableau des gaps */}
        <Card>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Requête
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Concurrent leader
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Votre position
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Gap Score
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Fréquence
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredGaps.map((gap) => (
                  <tr key={gap.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <div className="flex items-start">
                        <div>
                          <div className="text-sm font-medium text-gray-900 max-w-xs">
                            {gap.query}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm">
                        <div className="font-medium text-gray-900">{gap.competitor_name}</div>
                        <div className="text-gray-500">{gap.competitor_rate}% ({gap.competitor_mentions}/10)</div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm">
                        <div className="font-medium text-gray-900">{gap.our_rate}%</div>
                        <div className="text-gray-500">({gap.our_mentions}/10 mentions)</div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className={`inline-flex items-center gap-2 px-2 py-1 rounded-md border ${getGapColor(gap.gap_type)}`}>
                        {getGapIcon(gap.gap_type)}
                        <span className="text-sm font-medium">{gap.gap_score}%</span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-gray-900">{gap.frequency_estimate}/mois</div>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className="flex items-center justify-end gap-1">
                        <div className="group relative">
                          <Button 
                            size="sm" 
                            variant="ghost" 
                            className="text-blue-600 hover:text-blue-700 hover:bg-blue-50 p-2"
                            onClick={() => handleAnalyze(gap)}
                          >
                            <Play className="w-4 h-4" />
                          </Button>
                          <div className="absolute bottom-full right-0 mb-2 px-2 py-1 text-xs text-white bg-gray-900 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none z-10">
                            Lancer une nouvelle analyse pour cette requête
                          </div>
                        </div>
                        <div className="group relative">
                          <Button 
                            size="sm" 
                            variant="ghost" 
                            className="text-slate-600 hover:text-slate-700 hover:bg-slate-50 p-2"
                            onClick={() => handleViewAnalyses(gap)}
                          >
                            <Eye className="w-4 h-4" />
                          </Button>
                          <div className="absolute bottom-full right-0 mb-2 px-2 py-1 text-xs text-white bg-gray-900 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none z-10">
                            Voir toutes les analyses existantes
                          </div>
                        </div>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            
            {filteredGaps.length === 0 && (
              <div className="p-6 text-center text-gray-500">
                Aucun gap trouvé avec les filtres actuels
              </div>
            )}
          </div>
        </Card>

        {/* Résumé des actions */}
        {filteredGaps.length > 0 && (
          <Card className="p-4 bg-blue-50 border-blue-200">
            <div className="flex items-start gap-3">
              <div className="text-blue-600">
                <Target className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-medium text-blue-900">Résumé des opportunités</h3>
                <p className="text-sm text-blue-700 mt-1">
                  {criticalGaps} gaps critiques nécessitent une action immédiate. 
                  Potentiel d'amélioration estimé : <strong>+{potentialVisibility} mentions/mois</strong>.
                </p>
                <div className="mt-3 flex gap-2">
                  <Button size="sm" className="bg-blue-600 hover:bg-blue-700">
                    Créer plan d'action
                  </Button>
                  <Button size="sm" variant="outline">
                    Programmer suivi
                  </Button>
                </div>
              </div>
            </div>
          </Card>
        )}

        {/* Message quand pas de données du tout */}
        {totalGaps === 0 && (
          <Card className="p-6 text-center">
            <Target className="w-12 h-12 text-gray-400 mx-auto mb-3" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">Aucune donnée d'analyse</h3>
            <p className="text-gray-600">
              Aucune analyse avec des concurrents trouvée pour ce projet sur la période sélectionnée.
              Assurez-vous d'avoir des analyses avec des données de concurrents.
            </p>
          </Card>
        )}
        </>
        )}

        {/* State quand pas de projet */}
        {!currentProject && !loading && (
          <Card className="p-6 text-center">
            <AlertTriangle className="w-12 h-12 text-gray-400 mx-auto mb-3" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">Aucun projet sélectionné</h3>
            <p className="text-gray-600">
              Sélectionnez un projet pour voir l'analyse des gaps de visibilité.
            </p>
          </Card>
        )}
      </div>
    </div>
  )
}