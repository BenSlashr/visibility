/**
 * Composant pour afficher les statistiques NLP d'un projet
 */

import React, { useState, useEffect } from 'react'
import { Brain, TrendingUp, Target, BarChart3, RefreshCw, Download } from 'lucide-react'
import { Card, Button, Badge, Loading } from '../ui'
import { NLPService, ProjectNLPSummary, NLPUtils } from '../../services/nlp'

interface ProjectNLPStatsProps {
  projectId: string
  projectName?: string
  limit?: number
  showExportButton?: boolean
}

export const ProjectNLPStats: React.FC<ProjectNLPStatsProps> = ({
  projectId,
  projectName,
  limit = 100,
  showExportButton = false
}) => {
  const [data, setData] = useState<ProjectNLPSummary | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchData = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const summary = await NLPService.getProjectNLPSummary(projectId, limit)
      setData(summary)
    } catch (err: any) {
      console.error('Erreur lors du chargement des stats NLP projet:', err)
      setError(err?.message || 'Erreur lors du chargement')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (projectId) {
      fetchData()
    }
  }, [projectId, limit])

  const handleExport = () => {
    if (!data) return
    
    // Créer un CSV simple des données
    const csvContent = [
      ['Métrique', 'Valeur'],
      ['Total analyses', data.summary.total_analyses],
      ['Confiance moyenne', data.summary.average_confidence.toFixed(2)],
      ['Analyses haute confiance', data.summary.high_confidence_count],
      ['Taux haute confiance', `${data.summary.high_confidence_rate}%`],
      ['Top intention SEO', data.summary.seo_intents.top_intent?.[0] || 'N/A'],
      ['Top type contenu', data.summary.content_types.top_type?.[0] || 'N/A'],
      ['Diversité marques', data.summary.sector_entities.brands_diversity],
      ['Diversité technologies', data.summary.sector_entities.technologies_diversity]
    ].map(row => row.join(',')).join('\n')
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)
    link.setAttribute('href', url)
    link.setAttribute('download', `nlp-stats-${projectId}.csv`)
    link.style.visibility = 'hidden'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  if (loading) {
    return (
      <Card className="p-6">
        <div className="flex items-center justify-center py-8">
          <Loading size="lg" text="Chargement des statistiques NLP..." />
        </div>
      </Card>
    )
  }

  if (error) {
    return (
      <Card className="p-6">
        <div className="text-center py-8">
          <div className="text-red-600 mb-4">{error}</div>
          <Button onClick={fetchData} variant="outline">
            <RefreshCw className="w-4 h-4 mr-2" />
            Réessayer
          </Button>
        </div>
      </Card>
    )
  }

  if (!data) {
    return null
  }

  const { summary } = data

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-purple-100 rounded-lg">
            <Brain className="w-5 h-5 text-purple-600" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              Statistiques NLP - {projectName || data.project_name}
            </h3>
            <p className="text-sm text-gray-600">
              Basé sur {summary.total_analyses} analyses (limite: {data.limit_applied})
            </p>
          </div>
        </div>
        
        <div className="flex gap-2">
          {showExportButton && (
            <Button variant="outline" size="sm" onClick={handleExport}>
              <Download className="w-4 h-4 mr-2" />
              Exporter
            </Button>
          )}
          <Button variant="ghost" size="sm" onClick={fetchData}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Actualiser
          </Button>
        </div>
      </div>

      {/* KPIs principaux */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-blue-50 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-blue-600 font-medium">Confiance moyenne</p>
              <p className="text-2xl font-bold text-blue-900">
                {NLPUtils.formatConfidence(summary.average_confidence)}
              </p>
            </div>
            <BarChart3 className="w-6 h-6 text-blue-600" />
          </div>
        </div>

        <div className="bg-green-50 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-green-600 font-medium">Haute confiance</p>
              <p className="text-2xl font-bold text-green-900">
                {summary.high_confidence_count}
              </p>
              <p className="text-xs text-green-600">
                {summary.high_confidence_rate}% du total
              </p>
            </div>
            <TrendingUp className="w-6 h-6 text-green-600" />
          </div>
        </div>

        <div className="bg-orange-50 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-orange-600 font-medium">Topics business</p>
              <p className="text-2xl font-bold text-orange-900">
                {summary.business_topics.total_topics}
              </p>
            </div>
            <Target className="w-6 h-6 text-orange-600" />
          </div>
        </div>

        <div className="bg-purple-50 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-purple-600 font-medium">Entités uniques</p>
              <p className="text-2xl font-bold text-purple-900">
                {summary.sector_entities.brands_diversity + summary.sector_entities.technologies_diversity}
              </p>
            </div>
            <Brain className="w-6 h-6 text-purple-600" />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Distribution des intentions SEO */}
        <div className="bg-gray-50 rounded-lg p-4">
          <h4 className="font-medium text-gray-900 mb-4">Intentions SEO</h4>
          
          {summary.seo_intents.top_intent && (
            <div className="mb-4 p-3 bg-white rounded-lg border border-blue-200">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span>{NLPUtils.getSEOIntentIcon(summary.seo_intents.top_intent[0])}</span>
                  <span className="font-medium">
                    {NLPUtils.translateSEOIntent(summary.seo_intents.top_intent[0])}
                  </span>
                  <Badge className="bg-blue-100 text-blue-800">Principal</Badge>
                </div>
                <span className="text-lg font-bold text-blue-900">
                  {summary.seo_intents.top_intent[1]}
                </span>
              </div>
            </div>
          )}
          
          <div className="space-y-2">
            {Object.entries(summary.seo_intents.distribution)
              .sort(([,a], [,b]) => b - a)
              .map(([intent, count]) => (
                <div key={intent} className="flex items-center justify-between">
                  <span className="text-sm text-gray-600 flex items-center gap-2">
                    <span>{NLPUtils.getSEOIntentIcon(intent)}</span>
                    {NLPUtils.translateSEOIntent(intent)}
                  </span>
                  <div className="flex items-center gap-2">
                    <div className="w-20 bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-blue-500 h-2 rounded-full"
                        style={{ width: `${(count / summary.total_analyses) * 100}%` }}
                      />
                    </div>
                    <span className="text-sm font-medium w-8">{count}</span>
                  </div>
                </div>
              ))}
          </div>
        </div>

        {/* Types de contenu */}
        <div className="bg-gray-50 rounded-lg p-4">
          <h4 className="font-medium text-gray-900 mb-4">Types de contenu</h4>
          
          {summary.content_types.top_type && (
            <div className="mb-4 p-3 bg-white rounded-lg border border-green-200">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="font-medium capitalize">
                    {summary.content_types.top_type[0]}
                  </span>
                  <Badge className="bg-green-100 text-green-800">Principal</Badge>
                </div>
                <span className="text-lg font-bold text-green-900">
                  {summary.content_types.top_type[1]}
                </span>
              </div>
            </div>
          )}
          
          <div className="space-y-2">
            {Object.entries(summary.content_types.distribution)
              .sort(([,a], [,b]) => b - a)
              .slice(0, 5)
              .map(([type, count]) => (
                <div key={type} className="flex items-center justify-between">
                  <span className="text-sm text-gray-600 capitalize">{type}</span>
                  <div className="flex items-center gap-2">
                    <div className="w-20 bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-green-500 h-2 rounded-full"
                        style={{ width: `${(count / summary.total_analyses) * 100}%` }}
                      />
                    </div>
                    <span className="text-sm font-medium w-8">{count}</span>
                  </div>
                </div>
              ))}
          </div>
        </div>

        {/* Top business topics */}
        <div className="bg-gray-50 rounded-lg p-4">
          <h4 className="font-medium text-gray-900 mb-4">Topics business populaires</h4>
          <div className="space-y-2">
            {Object.entries(summary.business_topics.top_topics)
              .sort(([,a], [,b]) => b - a)
              .slice(0, 6)
              .map(([topic, count]) => (
                <div key={topic} className="flex items-center justify-between">
                  <span className="text-sm text-gray-600 capitalize">{topic}</span>
                  <Badge className="bg-orange-100 text-orange-800">
                    {count}
                  </Badge>
                </div>
              ))}
          </div>
        </div>

        {/* Entités sectorielles */}
        <div className="bg-gray-50 rounded-lg p-4">
          <h4 className="font-medium text-gray-900 mb-4">Entités les plus mentionnées</h4>
          
          <div className="space-y-4">
            {Object.keys(summary.sector_entities.top_brands).length > 0 && (
              <div>
                <h5 className="text-sm font-medium text-gray-700 mb-2">Marques</h5>
                <div className="space-y-1">
                  {Object.entries(summary.sector_entities.top_brands)
                    .sort(([,a], [,b]) => b - a)
                    .slice(0, 5)
                    .map(([brand, count]) => (
                      <div key={brand} className="flex items-center justify-between">
                        <span className="text-sm text-gray-600">{brand}</span>
                        <Badge className="bg-purple-100 text-purple-800">{count}</Badge>
                      </div>
                    ))}
                </div>
              </div>
            )}
            
            {Object.keys(summary.sector_entities.top_technologies).length > 0 && (
              <div>
                <h5 className="text-sm font-medium text-gray-700 mb-2">Technologies</h5>
                <div className="space-y-1">
                  {Object.entries(summary.sector_entities.top_technologies)
                    .sort(([,a], [,b]) => b - a)
                    .slice(0, 5)
                    .map(([tech, count]) => (
                      <div key={tech} className="flex items-center justify-between">
                        <span className="text-sm text-gray-600">{tech}</span>
                        <Badge className="bg-indigo-100 text-indigo-800">{count}</Badge>
                      </div>
                    ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </Card>
  )
}