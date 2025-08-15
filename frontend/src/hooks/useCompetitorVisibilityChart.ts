import { useState, useEffect } from 'react'
import { AnalysesAPI } from '../services/analyses'
import { ProjectsAPI } from '../services/projects'
// import type { AnalysisSummary } from '../types/analysis'
// import type { Competitor } from '../types/project'

interface ChartDataPoint {
  date: string
  mainSite: number
  [key: string]: number | string // Pour les données des concurrents dynamiques
}

interface CompetitorInfo {
  id: string
  name: string
  currentScore: number
  mentions: number
  mentionRate: number
  linkRate: number
}

interface CompetitorRankingItem {
  id: string
  name: string
  score: number
  mentions: number
  mentionRate: number
  linkRate: number
  isMainSite: boolean
}

interface CompetitorVisibilityChartData {
  chartData: ChartDataPoint[]
  mainSiteScore: number
  avgCompetitorScore: number
  mainSiteRanking: number
  avgGap: number
  totalAnalyses: number
  competitors: CompetitorInfo[]
  competitorRanking: CompetitorRankingItem[]
}

interface UseCompetitorVisibilityChartReturn {
  data: CompetitorVisibilityChartData | null
  loading: boolean
  error: string | null
  refresh: (timeFilter?: string, projectId?: string) => Promise<void>
}

export const useCompetitorVisibilityChart = (
  timeFilter: string = 'last7days', 
  projectId?: string
): UseCompetitorVisibilityChartReturn => {
  const [data, setData] = useState<CompetitorVisibilityChartData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadCompetitorVisibilityData = async (filter: string = timeFilter, currentProjectId?: string) => {
    try {
      setLoading(true)
      setError(null)

      console.log(`🔄 Chargement comparaison concurrents (${filter}) pour le projet:`, currentProjectId)

      if (!currentProjectId) {
        setData({
          chartData: [],
          mainSiteScore: 0,
          avgCompetitorScore: 0,
          mainSiteRanking: 1,
          avgGap: 0,
          totalAnalyses: 0,
          competitors: [],
          competitorRanking: []
        })
        setLoading(false)
        return
      }

      // Récupérer les concurrents du projet
      const competitors = await ProjectsAPI.getCompetitors(currentProjectId)
      console.log('✅ Concurrents chargés:', competitors.length)

      if (competitors.length === 0) {
        setData({
          chartData: [],
          mainSiteScore: 0,
          avgCompetitorScore: 0,
          mainSiteRanking: 1,
          avgGap: 0,
          totalAnalyses: 0,
          competitors: [],
          competitorRanking: []
        })
        setLoading(false)
        return
      }

      // Déterminer le nombre de jours selon le filtre
      const days = filter === 'last24h' ? 1 : 
                   filter === 'last7days' ? 7 : 
                   filter === 'last30days' ? 30 : 7

      // Récupérer les analyses du projet avec les données des concurrents
      const projectAnalyses = await AnalysesAPI.getAll({
        project_id: currentProjectId,
        limit: 1000
      })
      
      console.log('✅ Analyses chargées:', projectAnalyses.length)

      // Filtrer par période
      const cutoffDate = new Date()
      cutoffDate.setDate(cutoffDate.getDate() - days)
      
      const filteredAnalyses = projectAnalyses.filter(analysis => 
        new Date(analysis.created_at) >= cutoffDate
      )

      // Grouper par jour
      const dailyData = new Map<string, {
        mainSiteScores: number[]
        competitorData: Map<string, { scores: number[], mentions: number }>
      }>()

      // Traiter les analyses
      filteredAnalyses.forEach(analysis => {
        const date = new Date(analysis.created_at).toISOString().split('T')[0]
        
        if (!dailyData.has(date)) {
          dailyData.set(date, {
            mainSiteScores: [],
            competitorData: new Map()
          })
        }
        
        const dayData = dailyData.get(date)!
        
        // Score du site principal (calculé depuis brand_mentioned et website_linked)
        let mainSiteScore = 0
        if (analysis.brand_mentioned) mainSiteScore += 50
        if (analysis.website_linked) mainSiteScore += 50
        // Pas de visibility_score dans la base - on le calcule
        dayData.mainSiteScores.push(Math.min(mainSiteScore, 100))

        // Traiter les vraies données des concurrents depuis l'analyse
        if (analysis.competitors_analysis && analysis.competitors_analysis.length > 0) {
          analysis.competitors_analysis.forEach((competitorAnalysis: any) => {
            // Trouver le concurrent correspondant par nom
            const competitor = competitors.find(c => c.name === competitorAnalysis.competitor_name)
            if (!competitor) return
            
            if (!dayData.competitorData.has(competitor.id)) {
              dayData.competitorData.set(competitor.id, { scores: [], mentions: 0 })
            }
            
            const competitorData = dayData.competitorData.get(competitor.id)!
            
            // Calculer le score du concurrent basé sur les vraies données
            let competitorScore = 0
            if (competitorAnalysis.is_mentioned) {
              competitorScore += 50 // Base pour être mentionné
              competitorData.mentions += 1
            }
            
            // Bonus basé sur la position dans le classement
            if (competitorAnalysis.ranking_position) {
              const positionBonus = Math.max(0, 100 - (competitorAnalysis.ranking_position * 10))
              competitorScore += positionBonus
            }
            
            competitorData.scores.push(Math.min(competitorScore, 100))
          })
        }
        
        // Pour les concurrents qui ne sont pas mentionnés dans cette analyse, ajouter un score de 0
        competitors.forEach(competitor => {
          if (!dayData.competitorData.has(competitor.id)) {
            dayData.competitorData.set(competitor.id, { scores: [], mentions: 0 })
          }
          const competitorData = dayData.competitorData.get(competitor.id)!
          
          // Si le concurrent n'a pas de données pour cette analyse, ajouter 0
          const hasDataForThisAnalysis = analysis.competitors_analysis?.some((ca: any) => 
            competitors.find(c => c.name === ca.competitor_name)?.id === competitor.id
          )
          
          if (!hasDataForThisAnalysis) {
            competitorData.scores.push(0)
          }
        })
      })

      // Créer les données du graphique
      const chartData: ChartDataPoint[] = []
      const sortedDates = Array.from(dailyData.keys()).sort()

      sortedDates.forEach(date => {
        const dayData = dailyData.get(date)!
        
        const dataPoint: ChartDataPoint = {
          date: new Date(date).toLocaleDateString('fr-FR', { 
            month: 'short', 
            day: 'numeric' 
          }),
          mainSite: dayData.mainSiteScores.length > 0 ? 
            Math.round(dayData.mainSiteScores.reduce((sum, score) => sum + score, 0) / dayData.mainSiteScores.length) : 0
        }

        // Ajouter les scores des concurrents
        dayData.competitorData.forEach((competitorData, competitorId) => {
          const avgScore = competitorData.scores.length > 0 ? 
            Math.round(competitorData.scores.reduce((sum, score) => sum + score, 0) / competitorData.scores.length) : 0
          dataPoint[`competitor_${competitorId}`] = avgScore
        })

        chartData.push(dataPoint)
      })

      // Calculer les métriques globales
      const allMainSiteScores = Array.from(dailyData.values())
        .flatMap(day => day.mainSiteScores)
      const mainSiteScore = allMainSiteScores.length > 0 ? 
        Math.round(allMainSiteScores.reduce((sum, score) => sum + score, 0) / allMainSiteScores.length) : 0

      // Calculer les scores moyens des concurrents
      const competitorInfos: CompetitorInfo[] = competitors.map(competitor => {
        const competitorScores = Array.from(dailyData.values())
          .flatMap(day => day.competitorData.get(competitor.id)?.scores || [])
        const competitorMentions = Array.from(dailyData.values())
          .reduce((sum, day) => sum + (day.competitorData.get(competitor.id)?.mentions || 0), 0)
        const mentionRate = filteredAnalyses.length > 0 ?
          Math.round((competitorMentions / filteredAnalyses.length) * 100) : 0
        // Taux de liens: proportion d'analyses où le concurrent est mentionné ET website_linked=true (vers votre site)
        const analysesWithCompetitor = filteredAnalyses.filter(a => 
          (a.competitors_analysis || []).some((ca: any) => ca.competitor_name === competitor.name)
        )
        const linksWhenCompetitor = analysesWithCompetitor.filter(a => a.website_linked).length
        const linkRate = analysesWithCompetitor.length > 0 ? 
          Math.round((linksWhenCompetitor / analysesWithCompetitor.length) * 100) : 0
        
        const avgScore = competitorScores.length > 0 ? 
          Math.round(competitorScores.reduce((sum, score) => sum + score, 0) / competitorScores.length) : 0

        return {
          id: competitor.id,
          name: competitor.name,
          currentScore: avgScore,
          mentions: competitorMentions,
          mentionRate,
          linkRate
        }
      })

      const avgCompetitorScore = competitorInfos.length > 0 ? 
        Math.round(competitorInfos.reduce((sum, comp) => sum + comp.currentScore, 0) / competitorInfos.length) : 0

      // Créer le classement
      const mainMentions = filteredAnalyses.filter(a => a.brand_mentioned).length
      const mainMentionRate = filteredAnalyses.length > 0 ? Math.round((mainMentions / filteredAnalyses.length) * 100) : 0
      const allEntities = [
        { id: 'main', name: 'Votre site', score: mainSiteScore, mentions: mainMentions, mentionRate: mainMentionRate, linkRate: Math.round((filteredAnalyses.filter(a => a.website_linked).length / Math.max(1, filteredAnalyses.length)) * 100), isMainSite: true },
        ...competitorInfos.map(comp => ({ id: comp.id, name: comp.name, score: comp.currentScore, mentions: comp.mentions, mentionRate: comp.mentionRate, linkRate: comp.linkRate, isMainSite: false }))
      ]
      const competitorRanking = allEntities.sort((a, b) => b.score - a.score)

      const mainSiteRanking = competitorRanking.findIndex(item => item.isMainSite) + 1
      const avgGap = mainSiteScore - avgCompetitorScore

      const competitorVisibilityData: CompetitorVisibilityChartData = {
        chartData,
        mainSiteScore,
        avgCompetitorScore,
        mainSiteRanking,
        avgGap,
        totalAnalyses: filteredAnalyses.length,
        competitors: competitorInfos,
        competitorRanking
      }

      setData(competitorVisibilityData)
      console.log('✅ Données de comparaison traitées:', competitorVisibilityData)
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erreur inconnue'
      console.error('❌ Erreur lors du chargement de la comparaison:', err)
      setError(`Erreur lors du chargement: ${errorMessage}`)
    } finally {
      setLoading(false)
    }
  }

  const refresh = async (filter?: string, currentProjectId?: string) => {
    await loadCompetitorVisibilityData(filter || timeFilter, currentProjectId || projectId)
  }

  // Chargement initial et rechargement quand les paramètres changent
  useEffect(() => {
    loadCompetitorVisibilityData(timeFilter, projectId)
  }, [timeFilter, projectId])

  return {
    data,
    loading,
    error,
    refresh
  }
} 