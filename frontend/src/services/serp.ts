import { ApiClient } from './api'
import type {
  SERPImportResponse,
  AutoMatchResponse,
  SERPSummaryResponse,
  SERPKeywordListResponse,
  PromptSERPAssociationResponse,
  ProjectSERPCorrelation,
  PromptSERPAssociationRequest,
  SERPUploadFormData
} from '../types/serp'

/**
 * Service pour les opérations SERP
 * Centralise tous les appels API liés aux données SERP
 */
export class SERPService {
  
  /**
   * Importe un fichier CSV de positionnement SERP
   */
  static async importCSV(projectId: string, formData: FormData): Promise<SERPImportResponse> {
    const endpoint = `/serp/projects/${projectId}/serp/import`
    
    // Utiliser fetch directement pour FormData
    const API_BASE_URL = import.meta.env?.VITE_API_URL || 'http://localhost:8021'
    const response = await fetch(`${API_BASE_URL}/api/v1${endpoint}`, {
      method: 'POST',
      body: formData
    })
    
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Erreur lors de l\'import')
    }
    
    return response.json()
  }
  
  /**
   * Lance l'association automatique des prompts aux mots-clés SERP
   */
  static async autoMatchPrompts(projectId: string): Promise<AutoMatchResponse> {
    return ApiClient.post<AutoMatchResponse>(`/serp/projects/${projectId}/serp/auto-match`)
  }
  
  /**
   * Récupère les suggestions de matching pour un projet
   */
  static async getMatchingSuggestions(projectId: string) {
    return ApiClient.get(`/serp/projects/${projectId}/serp/suggestions`)
  }
  
  /**
   * Récupère toutes les associations d'un projet
   */
  static async getProjectAssociations(projectId: string) {
    return ApiClient.get(`/serp/projects/${projectId}/serp/associations`)
  }
  
  /**
   * Définit manuellement l'association entre un prompt et un mot-clé SERP
   */
  static async setPromptAssociation(
    promptId: string, 
    data: PromptSERPAssociationRequest
  ): Promise<{ success: boolean }> {
    return ApiClient.put<{ success: boolean }>(`/serp/prompts/${promptId}/serp/association`, data)
  }
  
  /**
   * Récupère le résumé des données SERP d'un projet
   */
  static async getProjectSummary(projectId: string): Promise<SERPSummaryResponse> {
    return ApiClient.get<SERPSummaryResponse>(`/serp/projects/${projectId}/serp/summary`)
  }
  
  /**
   * Récupère la liste des mots-clés SERP d'un projet
   */
  static async getProjectKeywords(projectId: string): Promise<SERPKeywordListResponse> {
    return ApiClient.get<SERPKeywordListResponse>(`/serp/projects/${projectId}/serp/keywords`)
  }
  
  /**
   * Récupère l'association SERP d'un prompt
   */
  static async getPromptAssociation(promptId: string): Promise<PromptSERPAssociationResponse> {
    return ApiClient.get<PromptSERPAssociationResponse>(`/serp/prompts/${promptId}/serp/association`)
  }
  
  /**
   * Supprime l'association SERP d'un prompt
   */
  static async removePromptAssociation(promptId: string): Promise<{ success: boolean }> {
    return ApiClient.put<{ success: boolean }>(`/serp/prompts/${promptId}/serp/association`, {
      serp_keyword_id: null
    })
  }
  
  /**
   * Récupère les corrélations SERP vs IA pour un projet
   */
  static async getProjectCorrelations(projectId: string): Promise<ProjectSERPCorrelation> {
    return ApiClient.get<ProjectSERPCorrelation>(`/serp/projects/${projectId}/correlations`)
  }
  
  /**
   * Valide un fichier CSV avant l'upload
   */
  static validateCSVFile(file: File): { isValid: boolean; error?: string } {
    // Vérifier l'extension
    if (!file.name.toLowerCase().endsWith('.csv')) {
      return { isValid: false, error: 'Le fichier doit être au format CSV' }
    }
    
    // Vérifier la taille (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
      return { isValid: false, error: 'Le fichier ne peut pas dépasser 10MB' }
    }
    
    return { isValid: true }
  }
  
  /**
   * Parse un fichier CSV pour prévisualiser les données
   */
  static async previewCSV(file: File): Promise<{ headers: string[]; rows: string[][] }> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      
      reader.onload = (e) => {
        try {
          const text = e.target?.result as string
          const lines = text.split('\n').filter(line => line.trim())
          
          if (lines.length < 2) {
            reject(new Error('Le fichier doit contenir au moins un en-tête et une ligne de données'))
            return
          }
          
          const headers = lines[0].split(',').map(h => h.trim())
          const rows = lines.slice(1, 6).map(line => // Première 5 lignes pour preview
            line.split(',').map(cell => cell.trim())
          )
          
          resolve({ headers, rows })
        } catch (error) {
          reject(new Error('Erreur lors de la lecture du fichier CSV'))
        }
      }
      
      reader.onerror = () => reject(new Error('Erreur lors de la lecture du fichier'))
      reader.readAsText(file)
    })
  }
  
  /**
   * Crée un FormData à partir des données d'upload
   */
  static createFormData(uploadData: SERPUploadFormData): FormData {
    const formData = new FormData()
    
    if (uploadData.file) {
      formData.append('file', uploadData.file)
    }
    
    if (uploadData.notes) {
      formData.append('notes', uploadData.notes)
    }
    
    return formData
  }
  
  /**
   * Calcule les métriques de performance SERP
   */
  static calculatePerformanceMetrics(
    keywords: Array<{ keyword: string; position: number; volume?: number }>,
    correlations?: ProjectSERPCorrelation
  ) {
    const total = keywords.length
    if (total === 0) return null
    
    const top3 = keywords.filter(k => k.position <= 3).length
    const top10 = keywords.filter(k => k.position <= 10).length
    const avgPosition = keywords.reduce((sum, k) => sum + k.position, 0) / total
    
    const totalVolume = keywords.reduce((sum, k) => sum + (k.volume || 0), 0)
    const top3Volume = keywords
      .filter(k => k.position <= 3)
      .reduce((sum, k) => sum + (k.volume || 0), 0)
    
    return {
      total_keywords: total,
      top_3_count: top3,
      top_10_count: top10,
      top_3_rate: (top3 / total) * 100,
      top_10_rate: (top10 / total) * 100,
      average_position: Math.round(avgPosition * 10) / 10,
      total_volume: totalVolume,
      top_3_volume: top3Volume,
      volume_visibility: totalVolume > 0 ? (top3Volume / totalVolume) * 100 : 0,
      correlation_score: correlations?.average_correlation || null
    }
  }
  
  /**
   * Génère des insights basés sur les données SERP
   */
  static generateInsights(
    summary: SERPSummaryResponse,
    keywords?: Array<{ keyword: string; position: number; volume?: number }>
  ) {
    const insights: Array<{
      type: 'positive' | 'negative' | 'neutral'
      title: string
      description: string
    }> = []
    
    if (!summary.has_serp_data) {
      insights.push({
        type: 'neutral',
        title: 'Données SERP manquantes',
        description: 'Importez vos données de positionnement pour débloquer les corrélations IA vs SERP.'
      })
      return insights
    }
    
    const stats = summary.serp_stats
    const associations = summary.associations
    
    if (stats) {
      // Insight position moyenne
      if (stats.average_position <= 5) {
        insights.push({
          type: 'positive',
          title: 'Excellente visibilité SERP',
          description: `Position moyenne de ${stats.average_position.toFixed(1)} - votre site est très visible.`
        })
      } else if (stats.average_position >= 15) {
        insights.push({
          type: 'negative',
          title: 'Visibilité SERP à améliorer',
          description: `Position moyenne de ${stats.average_position.toFixed(1)} - opportunités d'optimisation SEO.`
        })
      }
      
      // Insight top 3
      if (stats.top_3_keywords > 0) {
        insights.push({
          type: 'positive',
          title: `${stats.top_3_keywords} mots-clés en top 3`,
          description: 'Excellentes positions pour capturer du trafic qualifié.'
        })
      }
    }
    
    if (associations) {
      // Insight taux d'association
      if (associations.association_rate >= 80) {
        insights.push({
          type: 'positive',
          title: 'Couverture SERP excellente',
          description: `${associations.association_rate}% des prompts ont une correspondance SERP.`
        })
      } else if (associations.association_rate < 50) {
        insights.push({
          type: 'negative',
          title: 'Couverture SERP incomplète',
          description: `Seulement ${associations.association_rate}% des prompts ont une correspondance SERP.`
        })
      }
      
      // Insight prompts non associés
      if (associations.unassociated_prompts > 5) {
        insights.push({
          type: 'neutral',
          title: `${associations.unassociated_prompts} prompts sans SERP`,
          description: 'Utilisez le matching automatique ou associez manuellement.'
        })
      }
    }
    
    return insights
  }
}

export default SERPService