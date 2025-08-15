/**
 * Page dédiée aux insights et statistiques NLP
 */

import React, { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { 
  Brain, 
  BarChart3, 
  TrendingUp, 
  Target, 
  Tags, 
  Download, 
  RefreshCw,
  Calendar,
  Filter,
  Search,
  Users
} from 'lucide-react'
import { Button, Input, Loading } from '../components/ui'
import { ProjectNLPStats } from '../components/nlp/ProjectNLPStats'
import { useCurrentProject } from '../contexts/ProjectContext'
import { useProjects } from '../hooks/useProjects'
import { NLPService, GlobalNLPStats, ProjectNLPTrends } from '../services/nlp'

export const NLPInsightsPage: React.FC = () => {
  const { currentProject } = useCurrentProject()
  const { projects } = useProjects()
  const [searchParams, setSearchParams] = useSearchParams()
  
  // États pour les filtres
  const [selectedProject, setSelectedProject] = useState<string>(currentProject?.id || 'all')
  const [timeRange, setTimeRange] = useState<number>(30) // derniers 30 jours
  const [limit, setLimit] = useState<number>(100)
  
  // États pour les données
  const [globalStats, setGlobalStats] = useState<GlobalNLPStats | null>(null)
  const [projectTrends, setProjectTrends] = useState<ProjectNLPTrends | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  // Paramètres URL
  useEffect(() => {
    const projectId = searchParams.get('project_id')
    const range = searchParams.get('range')
    if (projectId) setSelectedProject(projectId)
    if (range) setTimeRange(parseInt(range))
  }, [searchParams])

  // Chargement des données
  const fetchData = async () => {
    try {
      setLoading(true)
      setError(null)
      
      // Charger les stats globales
      const statsPromise = NLPService.getGlobalNLPStats()
      
      // Charger les tendances du projet si un projet est sélectionné
      let trendsPromise = null
      if (selectedProject !== 'all') {
        trendsPromise = NLPService.getProjectNLPTrends(selectedProject, timeRange)
      }
      
      const [stats, trends] = await Promise.all([
        statsPromise,
        trendsPromise
      ])
      
      setGlobalStats(stats)
      setProjectTrends(trends)
      
    } catch (err: any) {
      console.error('Erreur lors du chargement des données NLP:', err)
      setError(err?.message || 'Erreur lors du chargement')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [selectedProject, timeRange])

  // Mise à jour des paramètres URL
  const updateFilters = (newProject: string, newRange: number) => {
    const params = new URLSearchParams()
    if (newProject !== 'all') params.set('project_id', newProject)
    if (newRange !== 30) params.set('range', newRange.toString())
    setSearchParams(params)
    setSelectedProject(newProject)
    setTimeRange(newRange)
  }

  const handleExportGlobalStats = () => {
    if (!globalStats) return
    
    const csvContent = [
      ['Métrique', 'Valeur'],
      ['Total analyses', globalStats.total_analyses],
      ['Analyses avec NLP', globalStats.analyzed_with_nlp],
      ['Couverture NLP', `${globalStats.nlp_coverage}%`],
      ['Confiance moyenne', globalStats.average_confidence.toFixed(2)],
      ...Object.entries(globalStats.seo_intents_distribution).map(([intent, count]) => 
        [`SEO ${intent}`, count]
      ),
      ...Object.entries(globalStats.content_types_distribution).map(([type, count]) => 
        [`Type ${type}`, count]
      )
    ].map(row => row.join(',')).join('\n')
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)
    link.setAttribute('href', url)
    link.setAttribute('download', 'nlp-global-stats.csv')
    link.style.visibility = 'hidden'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  return (
    <div className="bg-gray-50 min-h-screen">
      {/* Header */}
      <div className="bg-white shadow-sm border-b sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 rounded-lg">
                <Brain className="w-6 h-6 text-purple-600" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">NLP Insights</h1>
                <p className="text-sm text-gray-600">
                  Analyse sémantique et intelligence des contenus
                </p>
              </div>
            </div>
            
            <div className="flex items-center space-x-2">
              <Button 
                variant="ghost" 
                onClick={fetchData} 
                disabled={loading}
              >
                <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                Actualiser
              </Button>
              <Button variant="outline" onClick={handleExportGlobalStats}>
                <Download className="h-4 w-4 mr-2" />
                Exporter
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Filtres */}
        <div className="bg-white p-4 rounded-lg border border-gray-200 mb-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Projet
              </label>
              <select
                value={selectedProject}
                onChange={(e) => updateFilters(e.target.value, timeRange)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
              >
                <option value="all">Tous les projets</option>
                {projects.map(project => (
                  <option key={project.id} value={project.id}>{project.name}</option>
                ))}
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Période d'analyse
              </label>
              <select
                value={timeRange}
                onChange={(e) => updateFilters(selectedProject, parseInt(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
              >
                <option value={7}>7 derniers jours</option>
                <option value={30}>30 derniers jours</option>
                <option value={90}>90 derniers jours</option>
                <option value={365}>12 derniers mois</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Limite d'analyses
              </label>
              <select
                value={limit}
                onChange={(e) => setLimit(parseInt(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
              >
                <option value={50}>50 analyses</option>
                <option value={100}>100 analyses</option>
                <option value={250}>250 analyses</option>
                <option value={500}>500 analyses</option>
              </select>
            </div>
          </div>
        </div>

        {loading && (
          <div className="flex items-center justify-center py-12">
            <Loading size="lg" text="Chargement des statistiques NLP..." />
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 mb-8">
            <div className="text-red-800 font-medium">Erreur de chargement</div>
            <div className="text-red-600 text-sm mt-1">{error}</div>
            <Button variant="outline" size="sm" className="mt-3" onClick={fetchData}>
              <RefreshCw className="w-4 h-4 mr-2" />
              Réessayer
            </Button>
          </div>
        )}

        {/* Statistiques globales */}
        {globalStats && (
          <div className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-6">Vue d'ensemble globale</h2>
            
            {/* KPIs principaux */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
              <div className="bg-white rounded-lg border border-gray-200 p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600 font-medium">Total analyses</p>
                    <p className="text-3xl font-bold text-gray-900">{globalStats.total_analyses}</p>
                  </div>
                  <BarChart3 className="w-8 h-8 text-blue-600" />
                </div>
              </div>

              <div className="bg-white rounded-lg border border-gray-200 p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-green-600 font-medium">Couverture NLP</p>
                    <p className="text-3xl font-bold text-green-900">{globalStats.nlp_coverage}%</p>
                    <p className="text-xs text-green-600">{globalStats.analyzed_with_nlp} analysées</p>
                  </div>
                  <TrendingUp className="w-8 h-8 text-green-600" />
                </div>
              </div>

              <div className="bg-white rounded-lg border border-gray-200 p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-purple-600 font-medium">Confiance moyenne</p>
                    <p className="text-3xl font-bold text-purple-900">
                      {Math.round(globalStats.average_confidence * 100)}%
                    </p>
                  </div>
                  <Brain className="w-8 h-8 text-purple-600" />
                </div>
              </div>

              <div className="bg-white rounded-lg border border-gray-200 p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-orange-600 font-medium">Types de contenu</p>
                    <p className="text-3xl font-bold text-orange-900">
                      {Object.keys(globalStats.content_types_distribution).length}
                    </p>
                  </div>
                  <Tags className="w-8 h-8 text-orange-600" />
                </div>
              </div>
            </div>

            {/* Distributions */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Distribution des intentions SEO */}
              <div className="bg-white rounded-lg border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Distribution des intentions SEO
                </h3>
                <div className="space-y-3">
                  {Object.entries(globalStats.seo_intents_distribution)
                    .sort(([,a], [,b]) => b - a)
                    .map(([intent, count]) => {
                      const percentage = Math.round((count / globalStats.total_analyses) * 100)
                      return (
                        <div key={intent} className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <span className="text-lg">
                              {intent === 'commercial' && '💰'}
                              {intent === 'informational' && '📚'}
                              {intent === 'transactional' && '⚡'}
                              {intent === 'navigational' && '🧭'}
                            </span>
                            <span className="font-medium capitalize">{intent}</span>
                          </div>
                          <div className="flex items-center gap-3">
                            <div className="w-24 bg-gray-200 rounded-full h-2">
                              <div 
                                className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                                style={{ width: `${percentage}%` }}
                              />
                            </div>
                            <span className="text-sm font-medium w-12 text-right">
                              {count} ({percentage}%)
                            </span>
                          </div>
                        </div>
                      )
                    })}
                </div>
              </div>

              {/* Distribution des types de contenu */}
              <div className="bg-white rounded-lg border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Types de contenu populaires
                </h3>
                <div className="space-y-3">
                  {Object.entries(globalStats.content_types_distribution)
                    .sort(([,a], [,b]) => b - a)
                    .slice(0, 8)
                    .map(([type, count]) => {
                      const percentage = Math.round((count / globalStats.total_analyses) * 100)
                      return (
                        <div key={type} className="flex items-center justify-between">
                          <span className="font-medium capitalize text-gray-700">{type}</span>
                          <div className="flex items-center gap-3">
                            <div className="w-24 bg-gray-200 rounded-full h-2">
                              <div 
                                className="bg-green-500 h-2 rounded-full transition-all duration-300"
                                style={{ width: `${percentage}%` }}
                              />
                            </div>
                            <span className="text-sm font-medium w-12 text-right">
                              {count} ({percentage}%)
                            </span>
                          </div>
                        </div>
                      )
                    })}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Statistiques par projet */}
        {selectedProject !== 'all' && (
          <div className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-6">
              Statistiques du projet
            </h2>
            <ProjectNLPStats
              projectId={selectedProject}
              projectName={projects.find(p => p.id === selectedProject)?.name}
              limit={limit}
              showExportButton={true}
            />
          </div>
        )}

        {/* Tendances temporelles */}
        {projectTrends && (
          <div className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-6">
              Évolution temporelle - {projectTrends.project_name}
            </h2>
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <div className="mb-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-medium text-gray-900">
                    Tendances sur {timeRange} jours
                  </h3>
                  <div className="text-sm text-gray-600">
                    {projectTrends.trends_data.total_analyses} analyses • 
                    {projectTrends.trends_data.period_size} périodes
                  </div>
                </div>
              </div>
              
              {projectTrends.trends_data.trends.length > 0 ? (
                <div className="space-y-4">
                  {projectTrends.trends_data.trends.map((trend, index) => (
                    <div key={index} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-3">
                        <h4 className="font-medium text-gray-900">{trend.period}</h4>
                        <div className="text-sm text-gray-600">
                          {Object.values(trend.metrics).reduce((sum, val) => sum + val, 0)} analyses
                        </div>
                      </div>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        {Object.entries(trend.metrics).map(([metric, value]) => (
                          <div key={metric} className="text-center">
                            <div className="text-lg font-bold text-gray-900">{value}</div>
                            <div className="text-xs text-gray-600 capitalize">{metric}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  Aucune donnée de tendance disponible pour cette période
                </div>
              )}
            </div>
          </div>
        )}

        {/* Section projet vide */}
        {selectedProject === 'all' && (
          <div className="bg-white rounded-lg border border-gray-200 p-8 text-center">
            <Users className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              Sélectionnez un projet pour plus de détails
            </h3>
            <p className="text-gray-600 mb-4">
              Choisissez un projet spécifique pour voir les statistiques détaillées et les tendances.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}