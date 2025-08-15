/**
 * Service API pour les fonctionnalités NLP
 * Interface avec les endpoints backend /api/v1/analyses/[id]/nlp
 */

import { ApiClient } from './api'

// Types pour les réponses NLP
export interface SEOIntent {
  main_intent: 'commercial' | 'informational' | 'transactional' | 'navigational'
  confidence: number
  detailed_scores: Record<string, number>
}

export interface ContentType {
  main_type: string
  confidence: number
  all_scores: Record<string, number>
}

export interface BusinessTopic {
  topic: string
  score: number
  raw_score: number
  weight: number
  relevance: 'high' | 'medium' | 'low'
  matches_count: number
  top_keywords: string[]
  sample_contexts: string[]
}

export interface SectorEntity {
  name: string
  count: number
  contexts: string[]
}

export interface NLPResults {
  seo_intent: SEOIntent
  business_topics: BusinessTopic[]
  content_type: ContentType
  sector_entities: Record<string, SectorEntity[]>
  semantic_keywords: string[]
  global_confidence: number
  sector_context: string
  processing_version: string
  created_at?: string
}

export interface AnalysisNLPResponse {
  analysis_id: string
  nlp_results: NLPResults
}

export interface ProjectNLPSummary {
  project_id: string
  project_name: string
  summary: {
    total_analyses: number
    average_confidence: number
    high_confidence_count: number
    high_confidence_rate: number
    seo_intents: {
      distribution: Record<string, number>
      top_intent: [string, number] | null
    }
    content_types: {
      distribution: Record<string, number>
      top_type: [string, number] | null
    }
    business_topics: {
      top_topics: Record<string, number>
      total_topics: number
    }
    sector_entities: {
      top_brands: Record<string, number>
      top_technologies: Record<string, number>
      brands_diversity: number
      technologies_diversity: number
    }
  }
  limit_applied: number
}

export interface ProjectNLPTrends {
  project_id: string
  project_name: string
  trends_data: {
    trends: Array<{
      period: string
      metrics: Record<string, number>
    }>
    period_days: number
    period_size: number
    total_analyses: number
  }
}

export interface BatchNLPResult {
  total_requested: number
  success_count: number
  failure_count: number
  results: Record<string, boolean>
  success_rate: number
}

export interface GlobalNLPStats {
  total_analyses: number
  analyzed_with_nlp: number
  nlp_coverage: number
  average_confidence: number
  seo_intents_distribution: Record<string, number>
  content_types_distribution: Record<string, number>
}

export class NLPService {
  /**
   * Récupère l'analyse NLP d'une analyse spécifique
   */
  static async getAnalysisNLP(analysisId: string): Promise<AnalysisNLPResponse> {
    try {
      return await ApiClient.get<AnalysisNLPResponse>(`/analyses/${analysisId}/nlp`)
    } catch (error) {
      console.error('❌ Erreur lors de la récupération de l\'analyse NLP:', error)
      throw error
    }
  }

  /**
   * Force la re-analyse NLP d'une analyse
   */
  static async reanalyzeAnalysisNLP(analysisId: string): Promise<{ success: boolean; message: string }> {
    try {
      return await ApiClient.post<{ success: boolean; message: string }>(`/analyses/${analysisId}/nlp/reanalyze`)
    } catch (error) {
      console.error('❌ Erreur lors de la re-analyse NLP:', error)
      throw error
    }
  }

  /**
   * Récupère le résumé NLP d'un projet
   */
  static async getProjectNLPSummary(projectId: string, limit: number = 100): Promise<ProjectNLPSummary> {
    try {
      const params = { limit: limit.toString() }
      return await ApiClient.get<ProjectNLPSummary>(`/analyses/nlp/project-summary/${projectId}`, params)
    } catch (error) {
      console.error('❌ Erreur lors de la récupération du résumé NLP projet:', error)
      throw error
    }
  }

  /**
   * Récupère les tendances NLP d'un projet
   */
  static async getProjectNLPTrends(projectId: string, days: number = 30): Promise<ProjectNLPTrends> {
    try {
      const params = { days: days.toString() }
      return await ApiClient.get<ProjectNLPTrends>(`/analyses/nlp/project-trends/${projectId}`, params)
    } catch (error) {
      console.error('❌ Erreur lors de la récupération des tendances NLP:', error)
      throw error
    }
  }

  /**
   * Analyse NLP en lot
   */
  static async batchAnalyzeNLP(analysisIds: string[]): Promise<BatchNLPResult> {
    try {
      return await ApiClient.post<BatchNLPResult>('/analyses/nlp/batch-analyze', analysisIds)
    } catch (error) {
      console.error('❌ Erreur lors de l\'analyse NLP en lot:', error)
      throw error
    }
  }

  /**
   * Re-analyse complète d'un projet
   */
  static async reanalyzeProjectNLP(projectId: string): Promise<{
    project_id: string
    project_name: string
    success: boolean
    total_analyses: number
    success_count: number
    failure_count: number
    message?: string
  }> {
    try {
      return await ApiClient.post(`/analyses/nlp/project-reanalyze/${projectId}`)
    } catch (error) {
      console.error('❌ Erreur lors de la re-analyse projet NLP:', error)
      throw error
    }
  }

  /**
   * Récupère les secteurs disponibles
   */
  static async getAvailableSectors(): Promise<string[]> {
    try {
      return await ApiClient.get<string[]>('/analyses/nlp/available-sectors')
    } catch (error) {
      console.error('❌ Erreur lors de la récupération des secteurs:', error)
      throw error
    }
  }

  /**
   * Récupère les statistiques globales NLP
   */
  static async getGlobalNLPStats(): Promise<GlobalNLPStats> {
    try {
      return await ApiClient.get<GlobalNLPStats>('/analyses/nlp/stats/global')
    } catch (error) {
      console.error('❌ Erreur lors de la récupération des stats globales NLP:', error)
      throw error
    }
  }
}

// Utilitaires pour l'interface
export const NLPUtils = {
  /**
   * Traduit les intentions SEO en français
   */
  translateSEOIntent(intent: string): string {
    const translations: Record<string, string> = {
      'commercial': 'Commercial',
      'informational': 'Informationnel', 
      'transactional': 'Transactionnel',
      'navigational': 'Navigationnel'
    }
    return translations[intent] || intent
  },

  /**
   * Retourne la couleur associée à un niveau de confiance
   */
  getConfidenceColor(confidence: number): string {
    if (confidence >= 0.7) return 'text-green-600 bg-green-50 border-green-200'
    if (confidence >= 0.4) return 'text-amber-600 bg-amber-50 border-amber-200'
    return 'text-red-600 bg-red-50 border-red-200'
  },

  /**
   * Retourne l'icône associée à une intention SEO
   */
  getSEOIntentIcon(intent: string): string {
    const icons: Record<string, string> = {
      'commercial': '💰',
      'informational': '📚',
      'transactional': '⚡',
      'navigational': '🧭'
    }
    return icons[intent] || '📊'
  },

  /**
   * Retourne la couleur associée à une pertinence de topic
   */
  getRelevanceColor(relevance: string): string {
    const colors: Record<string, string> = {
      'high': 'text-red-600 bg-red-50 border-red-200',
      'medium': 'text-amber-600 bg-amber-50 border-amber-200',
      'low': 'text-green-600 bg-green-50 border-green-200'
    }
    return colors[relevance] || 'text-gray-600 bg-gray-50 border-gray-200'
  },

  /**
   * Formate un score de confiance pour l'affichage
   */
  formatConfidence(confidence: number): string {
    return `${Math.round(confidence * 100)}%`
  },

  /**
   * Retourne le niveau de confiance textuel
   */
  getConfidenceLevel(confidence: number): string {
    if (confidence >= 0.7) return 'Élevée'
    if (confidence >= 0.4) return 'Moyenne'
    return 'Faible'
  }
}