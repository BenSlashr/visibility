import { ApiClient, PaginationParams } from './api'
import type { 
  Analysis,
  AnalysisSummary,
  AnalysisCreate, 
  AnalysisUpdate,
  AnalysisStats,
  ProjectAnalysisStats,
  AnalysisFilters
} from '../types/analysis'

export class AnalysesAPI {
  // Récupérer toutes les analyses avec filtres avancés
  static async getAll(filters?: AnalysisFilters): Promise<AnalysisSummary[]> {
    try {
      return await ApiClient.get<AnalysisSummary[]>('/analyses/', filters)
    } catch (error) {
      console.error('❌ Erreur lors de la récupération des analyses:', error)
      throw error
    }
  }

  // Récupérer une analyse par ID avec toutes ses relations
  static async getById(id: string): Promise<Analysis> {
    try {
      return await ApiClient.get<Analysis>(`/analyses/${id}`)
    } catch (error) {
      console.error(`❌ Erreur lors de la récupération de l'analyse ${id}:`, error)
      throw error
    }
  }

  // Créer une nouvelle analyse
  static async create(analysis: AnalysisCreate): Promise<Analysis> {
    try {
      return await ApiClient.post<Analysis>('/analyses/', analysis)
    } catch (error) {
      console.error('❌ Erreur lors de la création de l\'analyse:', error)
      throw error
    }
  }

  // Mettre à jour une analyse
  static async update(id: string, analysis: AnalysisUpdate): Promise<Analysis> {
    try {
      return await ApiClient.put<Analysis>(`/analyses/${id}`, analysis)
    } catch (error) {
      console.error(`❌ Erreur lors de la mise à jour de l'analyse ${id}:`, error)
      throw error
    }
  }

  // Supprimer une analyse
  static async delete(id: string): Promise<void> {
    try {
      await ApiClient.delete(`/analyses/${id}`)
    } catch (error) {
      console.error(`❌ Erreur lors de la suppression de l'analyse ${id}:`, error)
      throw error
    }
  }

  // 📊 STATISTIQUES GLOBALES
  static async getGlobalStats(): Promise<AnalysisStats> {
    try {
      return await ApiClient.get<AnalysisStats>('/analyses/stats/global')
    } catch (error) {
      console.error('❌ Erreur lors de la récupération des statistiques globales:', error)
      throw error
    }
  }

  // 📊 STATISTIQUES PAR PROJET
  static async getProjectStats(projectId: string): Promise<ProjectAnalysisStats> {
    try {
      return await ApiClient.get<ProjectAnalysisStats>(`/analyses/stats/project/${projectId}`)
    } catch (error) {
      console.error(`❌ Erreur lors de la récupération des statistiques du projet ${projectId}:`, error)
      throw error
    }
  }

  // 🔬 Comparaison des modèles IA (sans coûts)
  static async getModelComparison(params: { project_id: string; date_from?: string; date_to?: string; metric?: string }): Promise<any> {
    return await ApiClient.get<any>('/analyses/models/comparison', params)
  }

  // 👥 Résumé des concurrents
  static async getCompetitorsSummary(params: { project_id: string; date_from?: string; date_to?: string }): Promise<any> {
    return await ApiClient.get<any>('/analyses/competitors/summary', params)
  }

  // 🧱 Heatmap Tags x Temps
  static async getTagsHeatmap(params: { project_id: string; date_from?: string; date_to?: string }): Promise<any> {
    return await ApiClient.get<any>('/analyses/tags/heatmap', params)
  }

  // 📊 ANALYSE DES COÛTS sur une période
  static async getCostAnalysis(days: number = 30): Promise<{
    total_cost: number
    daily_average: number
    cost_by_model: Record<string, number>
    cost_by_project: Record<string, number>
    cost_evolution: Array<{ date: string; cost: number }>
  }> {
    try {
      return await ApiClient.get<any>('/analyses/stats/costs', { days })
    } catch (error) {
      console.error(`❌ Erreur lors de l'analyse des coûts sur ${days} jours:`, error)
      throw error
    }
  }

  // 📅 ANALYSES RÉCENTES
  static async getRecent(days: number = 7, limit: number = 50): Promise<AnalysisSummary[]> {
    try {
      return await ApiClient.get<AnalysisSummary[]>(`/analyses/recent/${days}`, { limit })
    } catch (error) {
      console.error(`❌ Erreur lors de la récupération des analyses récentes (${days} jours):`, error)
      throw error
    }
  }

  // 🏆 MEILLEURES PERFORMANCES
  static async getBestPerforming(limit: number = 20): Promise<AnalysisSummary[]> {
    try {
      return await ApiClient.get<AnalysisSummary[]>(`/analyses/best-performing/${limit}`)
    } catch (error) {
      console.error(`❌ Erreur lors de la récupération des meilleures analyses (top ${limit}):`, error)
      throw error
    }
  }

  // Filtres spécialisés pour le dashboard
  static async getByProject(projectId: string, params?: PaginationParams): Promise<AnalysisSummary[]> {
    return this.getAll({ project_id: projectId, ...params })
  }

  static async getByPrompt(promptId: string, params?: PaginationParams): Promise<AnalysisSummary[]> {
    return this.getAll({ prompt_id: promptId, ...params })
  }

  static async getWithBrandMentions(params?: PaginationParams): Promise<AnalysisSummary[]> {
    return this.getAll({ brand_mentioned: true, ...params })
  }

  static async getWithRankings(params?: PaginationParams): Promise<AnalysisSummary[]> {
    return this.getAll({ has_ranking: true, ...params })
  }

  static async searchByResponse(searchTerm: string, params?: PaginationParams): Promise<AnalysisSummary[]> {
    return this.getAll({ search: searchTerm, ...params })
  }
} 