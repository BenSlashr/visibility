import React, { useEffect, useState } from 'react'
import { AnalysesAPI } from '../../services/analyses'
import { useCurrentProject } from '../../contexts/ProjectContext'

interface ShareOfVoiceProps {
  projectId?: string
  days?: number
}

interface ShareOfVoiceItem {
  competitor: string
  mentions: number
  isMainSite?: boolean
}

export const ShareOfVoice: React.FC<ShareOfVoiceProps> = ({ projectId, days = 30 }) => {
  const { currentProject } = useCurrentProject()
  const [items, setItems] = useState<ShareOfVoiceItem[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const load = async () => {
      try {
        if (!projectId) { setItems([]); return }
        setLoading(true)
        setError(null)
        
        const dateTo = new Date()
        const dateFrom = new Date()
        dateFrom.setDate(dateTo.getDate() - days)
        
        // Récupérer les données des concurrents
        const competitorsPayload = await AnalysesAPI.getCompetitorsSummary({
          project_id: projectId,
          date_from: dateFrom.toISOString().split('T')[0],
          date_to: dateTo.toISOString().split('T')[0]
        })
        
        // Récupérer les statistiques du projet pour le site principal
        const projectStats = await AnalysesAPI.getProjectStats(projectId)
        
        const competitorItems: ShareOfVoiceItem[] = (competitorsPayload.summary || []).map((item: any) => ({
          competitor: item.competitor,
          mentions: item.mentions,
          isMainSite: false
        }))
        
        // Ajouter le site principal s'il existe
        const mainSiteItem: ShareOfVoiceItem[] = []
        if (currentProject?.main_website) {
          // Le nombre de mentions du site principal = analyses avec website_mentioned = true
          const mainSiteMentions = projectStats.website_mentions || 0
          if (mainSiteMentions > 0) {
            mainSiteItem.push({
              competitor: currentProject.main_website.replace(/^https?:\/\//, '').replace(/^www\./, ''),
              mentions: mainSiteMentions,
              isMainSite: true
            })
          }
        }
        
        // Combiner et trier par nombre de mentions
        const allItems = [...mainSiteItem, ...competitorItems]
        allItems.sort((a, b) => b.mentions - a.mentions)
        
        setItems(allItems)
      } catch (e: any) {
        setError(e?.message || 'Erreur')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [projectId, days, currentProject])

  if (!projectId) return null
  if (loading) return <div className="card p-6">Chargement...</div>
  if (error) return <div className="card p-6 text-red-600">❌ {error}</div>

  const total = items.reduce((s, i) => s + i.mentions, 0) || 1

  return (
    <div className="card p-6">
      <h3 className="section-title mb-4">Share of Voice</h3>
      {items.length === 0 ? (
        <div className="muted">Aucune donnée de visibilité disponible</div>
      ) : (
        <div className="space-y-3">
          {items.map((item, index) => (
            <div key={item.competitor} className="flex items-center space-x-3">
              <div className="w-32 text-sm font-medium truncate flex items-center gap-2">
                {item.isMainSite && (
                  <div className="w-2 h-2 bg-green-500 rounded-full flex-shrink-0" title="Votre site"></div>
                )}
                <span className={item.isMainSite ? 'text-green-700' : 'text-gray-700'}>
                  {item.competitor}
                </span>
              </div>
              <div className="flex-1 h-3 bg-gray-100 rounded">
                <div
                  className={`h-3 rounded transition-all duration-300 ${
                    item.isMainSite 
                      ? 'bg-gradient-to-r from-green-500 to-green-600' 
                      : index === 0 && !item.isMainSite
                        ? 'bg-gradient-to-r from-blue-500 to-blue-600'
                        : 'bg-gray-400'
                  }`}
                  style={{ width: `${Math.round((item.mentions / total) * 100)}%` }}
                />
              </div>
              <div className="w-16 text-right">
                <div className={`text-sm font-semibold ${item.isMainSite ? 'text-green-700' : 'text-gray-700'}`}>
                  {Math.round((item.mentions / total) * 100)}%
                </div>
                <div className="text-xs text-gray-500">
                  {item.mentions} mentions
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
      {items.length > 0 && (
        <div className="mt-4 pt-3 border-t border-gray-100">
          <div className="text-xs text-gray-500">
            Total des mentions sur {days} jours : {total}
          </div>
        </div>
      )}
    </div>
  )
}


