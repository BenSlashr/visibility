import { ApiClient, PaginationParams } from './api'
import type { 
  Prompt,
  PromptSummary,
  PromptCreate, 
  PromptUpdate,
  PromptExecuteRequest,
  PromptExecuteResponse
} from '../types/prompt'

export class PromptsAPI {
  // Récupérer tous les prompts avec filtres
  static async getAll(params?: PaginationParams & {
    project_id?: string
    tag?: string
    active_only?: boolean
    search?: string
  }): Promise<PromptSummary[]> {
    try {
      return await ApiClient.get<PromptSummary[]>('/prompts/', params)
    } catch (error) {
      console.error('❌ Erreur lors de la récupération des prompts:', error)
      throw error
    }
  }

  // Récupérer un prompt par ID avec toutes ses relations
  static async getById(id: string): Promise<Prompt> {
    try {
      return await ApiClient.get<Prompt>(`/prompts/${id}`)
    } catch (error) {
      console.error(`❌ Erreur lors de la récupération du prompt ${id}:`, error)
      throw error
    }
  }

  // Créer un nouveau prompt
  static async create(prompt: PromptCreate): Promise<Prompt> {
    try {
      return await ApiClient.post<Prompt>('/prompts/', prompt)
    } catch (error) {
      console.error('❌ Erreur lors de la création du prompt:', error)
      throw error
    }
  }

  // Mettre à jour un prompt
  static async update(id: string, prompt: PromptUpdate): Promise<Prompt> {
    try {
      return await ApiClient.put<Prompt>(`/prompts/${id}`, prompt)
    } catch (error) {
      console.error(`❌ Erreur lors de la mise à jour du prompt ${id}:`, error)
      throw error
    }
  }

  // Supprimer un prompt
  static async delete(id: string): Promise<void> {
    try {
      await ApiClient.delete(`/prompts/${id}`)
    } catch (error) {
      console.error(`❌ Erreur lors de la suppression du prompt ${id}:`, error)
      throw error
    }
  }

  // Activer/désactiver un prompt
  static async toggleStatus(id: string): Promise<Prompt> {
    try {
      return await ApiClient.post<Prompt>(`/prompts/${id}/toggle`)
    } catch (error) {
      console.error(`❌ Erreur lors du changement de statut du prompt ${id}:`, error)
      throw error
    }
  }

  // Mettre à jour les tags d'un prompt
  static async updateTags(id: string, tags: string[]): Promise<Prompt> {
    try {
      return await ApiClient.put<Prompt>(`/prompts/${id}/tags`, tags)
    } catch (error) {
      console.error(`❌ Erreur lors de la mise à jour des tags du prompt ${id}:`, error)
      throw error
    }
  }

  // 🎯 EXÉCUTER UN PROMPT (endpoint principal)
  static async execute(id: string, request?: PromptExecuteRequest): Promise<PromptExecuteResponse> {
    try {
      return await ApiClient.post<PromptExecuteResponse>(`/prompts/${id}/execute`, request || {})
    } catch (error) {
      console.error(`❌ Erreur lors de l'exécution du prompt ${id}:`, error)
      throw error
    }
  }

  // Prévisualiser un prompt avec substitution des variables
  static async getPreview(id: string, customVariables?: Record<string, string>): Promise<{
    prompt_executed: string
    variables_used: Record<string, string>
    missing_variables: string[]
  }> {
    try {
      return await ApiClient.get<any>(`/prompts/${id}/preview`, { custom_variables: customVariables })
    } catch (error) {
      console.error(`❌ Erreur lors de la prévisualisation du prompt ${id}:`, error)
      throw error
    }
  }

  // Valider qu'un prompt peut être exécuté
  static async validate(id: string): Promise<{
    is_valid: boolean
    errors: string[]
    warnings: string[]
    can_execute: boolean
  }> {
    try {
      return await ApiClient.get<any>(`/prompts/${id}/validate`)
    } catch (error) {
      console.error(`❌ Erreur lors de la validation du prompt ${id}:`, error)
      throw error
    }
  }

  // Récupérer les prompts les plus utilisés
  static async getMostUsed(limit: number = 10): Promise<PromptSummary[]> {
    try {
      return await ApiClient.get<PromptSummary[]>('/prompts/stats/most-used', { limit })
    } catch (error) {
      console.error('❌ Erreur lors de la récupération des prompts les plus utilisés:', error)
      throw error
    }
  }

  // Récupérer les prompts récemment exécutés
  static async getRecentlyExecuted(limit: number = 10): Promise<PromptSummary[]> {
    try {
      return await ApiClient.get<PromptSummary[]>('/prompts/stats/recently-executed', { limit })
    } catch (error) {
      console.error('❌ Erreur lors de la récupération des prompts récemment exécutés:', error)
      throw error
    }
  }

  // Import en masse (JSON)
  static async bulkImport(payload: {
    validate_only?: boolean
    upsert_by?: 'name' | null
    defaults?: Record<string, any>
    items: Array<{
      project_id: string
      name: string
      template: string
      description?: string
      tags?: string[]
      is_active?: boolean
      is_multi_agent?: boolean
      ai_model_id?: string
      ai_model_ids?: string[]
    }>
  }): Promise<{
    success_count: number
    error_count: number
    results: Array<{ index: number; status: string; id?: string; errors?: string[] }>
  }> {
    return await ApiClient.post('/prompts/bulk', payload)
  }
} 