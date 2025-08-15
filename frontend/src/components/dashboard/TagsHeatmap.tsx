import React, { useEffect, useMemo, useState } from 'react'
import { AnalysesAPI } from '../../services/analyses'

interface TagsHeatmapProps {
  projectId?: string
  days?: number
}

export const TagsHeatmap: React.FC<TagsHeatmapProps> = ({ projectId, days = 30 }) => {
  const [points, setPoints] = useState<Array<{ date: string; tag: string; count: number }>>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const load = async () => {
      try {
        if (!projectId) { setPoints([]); return }
        setLoading(true)
        setError(null)
        const dateTo = new Date()
        const dateFrom = new Date()
        dateFrom.setDate(dateTo.getDate() - days)
        const payload = await AnalysesAPI.getTagsHeatmap({
          project_id: projectId,
          date_from: dateFrom.toISOString().split('T')[0],
          date_to: dateTo.toISOString().split('T')[0]
        })
        setPoints(payload.points || [])
      } catch (e: any) {
        setError(e?.message || 'Erreur')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [projectId, days])

  const byDate = useMemo(() => {
    const map = new Map<string, Map<string, number>>()
    points.forEach(p => {
      if (!map.has(p.date)) map.set(p.date, new Map())
      map.get(p.date)!.set(p.tag, p.count)
    })
    return map
  }, [points])

  const dates = Array.from(byDate.keys()).sort()
  const tags = Array.from(new Set(points.map(p => p.tag))).sort()

  if (!projectId) return null
  if (loading) return <div className="card p-6">Chargement...</div>
  if (error) return <div className="card p-6 text-red-600">❌ {error}</div>

  return (
    <div className="card p-6">
      <h3 className="section-title mb-4">Heatmap Tags</h3>
      {points.length === 0 ? (
        <div className="muted">Aucune donnée de tags</div>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full text-xs">
            <thead>
              <tr>
                <th className="p-2 text-left">Tag \ Date</th>
                {dates.map(d => (
                  <th key={d} className="p-2 text-center whitespace-nowrap">{new Date(d).toLocaleDateString('fr-FR', { month: 'short', day: 'numeric' })}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {tags.map(tag => (
                <tr key={tag}>
                  <td className="p-2 font-medium text-gray-800 whitespace-nowrap">{tag}</td>
                  {dates.map(d => {
                    const cnt = byDate.get(d)?.get(tag) || 0
                    const intensity = Math.min(100, cnt * 15) // simple scale
                    return (
                      <td key={d} className="p-1">
                        <div className="w-8 h-6 rounded" style={{ backgroundColor: `rgba(59,130,246,${0.1 + intensity/120})` }} title={`${cnt} analyses`} />
                      </td>
                    )
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}


