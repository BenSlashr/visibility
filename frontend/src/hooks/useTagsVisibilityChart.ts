import { useState, useEffect } from 'react'
import { AnalysesAPI } from '../services/analyses'
import { PromptsAPI } from '../services/prompts'

interface ChartDataPoint {
  date: string
  [key: string]: number | string
}

interface TagRankingItem {
  tag: string
  score: number
  mentionRate: number
  linkRate: number
  trend: number[]
}

interface TagsVisibilityData {
  chartData: ChartDataPoint[]
  totalAnalyses: number
  ranking: TagRankingItem[]
}

export const useTagsVisibilityChart = (projectId?: string, days: number = 30) => {
  const [data, setData] = useState<TagsVisibilityData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true)
        setError(null)
        if (!projectId) {
          setData({ chartData: [], totalAnalyses: 0, ranking: [] })
          setLoading(false)
          return
        }
        const prompts = await PromptsAPI.getAll({ project_id: projectId })
        const allTags = Array.from(new Set((prompts as any[]).flatMap(p => p.tags || [])))
        const analyses = await AnalysesAPI.getAll({ project_id: projectId, limit: 1000 })

        const cutoff = new Date()
        cutoff.setDate(cutoff.getDate() - days)
        const filtered = analyses.filter(a => new Date(a.created_at) >= cutoff)

        // Map prompt_id -> tags
        const promptIdToTags: Record<string, string[]> = {}
        ;(prompts as any[]).forEach(p => { promptIdToTags[p.id] = p.tags || [] })

        // Grouper par jour et par tag
        const daily: Map<string, Map<string, number[]>> = new Map()
        filtered.forEach(a => {
          const day = new Date(a.created_at).toISOString().split('T')[0]
          const tags = promptIdToTags[a.prompt_id] || []
          if (!daily.has(day)) daily.set(day, new Map())
          tags.forEach(tag => {
            const m = daily.get(day)!
            if (!m.has(tag)) m.set(tag, [])
            let score = 0
            if (a.brand_mentioned) score += 50
            if (a.website_linked) score += 50
            m.get(tag)!.push(Math.min(score, 100))
          })
        })

        const sortedDays = Array.from(daily.keys()).sort()
        const chartData: ChartDataPoint[] = sortedDays.map(d => {
          const row: ChartDataPoint = { date: new Date(d).toLocaleDateString('fr-FR', { month: 'short', day: 'numeric' }) }
          const byTag = daily.get(d)!
          allTags.forEach(tag => {
            const arr = byTag.get(tag) || []
            if (arr.length > 0) row[tag] = Math.round(arr.reduce((s, v) => s + v, 0) / arr.length)
          })
          return row
        })

        // Classement des tags (sur la période)
        const ranking: TagRankingItem[] = allTags.map(tag => {
          const tagAnalyses = filtered.filter(a => (promptIdToTags[a.prompt_id] || []).includes(tag))
          const mentionRate = tagAnalyses.length > 0 ? Math.round((tagAnalyses.filter(a => a.brand_mentioned).length / tagAnalyses.length) * 100) : 0
          const linkRate = tagAnalyses.length > 0 ? Math.round((tagAnalyses.filter(a => a.website_linked).length / tagAnalyses.length) * 100) : 0
          const scores: number[] = []
          const trend: number[] = []
          sortedDays.forEach(d => {
            const m = daily.get(d)!
            const arr = m.get(tag) || []
            if (arr.length > 0) scores.push(Math.round(arr.reduce((s, v) => s + v, 0) / arr.length))
            trend.push(arr.length > 0 ? Math.round(arr.reduce((s, v) => s + v, 0) / arr.length) : 0)
          })
          const score = scores.length > 0 ? Math.round(scores.reduce((s, v) => s + v, 0) / scores.length) : 0
          // Garder seulement les 10 derniers points pour le sparkline
          const trimmedTrend = trend.slice(-10)
          return { tag, score, mentionRate, linkRate, trend: trimmedTrend }
        }).sort((a, b) => b.score - a.score)

        setData({ chartData, totalAnalyses: filtered.length, ranking })
      } catch (e: any) {
        setError(e?.message || 'Erreur inconnue')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [projectId, days])

  return { data, loading, error }
}


