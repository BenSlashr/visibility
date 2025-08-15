import React, { useEffect, useState } from 'react'
import { AnalysesAPI } from '../../services/analyses'

interface ShareOfVoiceProps {
  projectId?: string
  days?: number
}

export const ShareOfVoice: React.FC<ShareOfVoiceProps> = ({ projectId, days = 30 }) => {
  const [items, setItems] = useState<Array<{ competitor: string; mentions: number }>>([])
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
        const payload = await AnalysesAPI.getCompetitorsSummary({
          project_id: projectId,
          date_from: dateFrom.toISOString().split('T')[0],
          date_to: dateTo.toISOString().split('T')[0]
        })
        setItems(payload.summary || [])
      } catch (e: any) {
        setError(e?.message || 'Erreur')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [projectId, days])

  if (!projectId) return null
  if (loading) return <div className="card p-6">Chargement...</div>
  if (error) return <div className="card p-6 text-red-600">❌ {error}</div>

  const total = items.reduce((s, i) => s + i.mentions, 0) || 1

  return (
    <div className="card p-6">
      <h3 className="section-title mb-4">Share of Voice</h3>
      {items.length === 0 ? (
        <div className="muted">Aucune donnée concurrent disponible</div>
      ) : (
        <div className="space-y-2">
          {items.map((i) => (
            <div key={i.competitor} className="flex items-center space-x-3">
              <div className="w-32 text-sm text-gray-700 truncate">{i.competitor}</div>
              <div className="flex-1 h-3 bg-gray-100 rounded">
                <div
                  className="h-3 bg-blue-500 rounded"
                  style={{ width: `${Math.round((i.mentions / total) * 100)}%` }}
                />
              </div>
              <div className="w-12 text-right text-sm text-gray-600">
                {Math.round((i.mentions / total) * 100)}%
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}


