import { apiClient } from './api'
import type { AIModel, AIModelCreate, AIModelUpdate } from '../types/aiModel'

export const AIModelsAPI = {
  // Récupérer tous les modèles IA
  getAll: async (params?: {
    skip?: number
    limit?: number
    provider?: string
    active_only?: boolean
  }): Promise<AIModel[]> => {
    const response = await apiClient.get('/ai-models/', { params })
    return response.data
  },

  // Récupérer les modèles actifs uniquement
  getActive: async (): Promise<AIModel[]> => {
    const response = await apiClient.get('/ai-models/active')
    return response.data
  },

  // Récupérer un modèle par ID
  getById: async (id: string): Promise<AIModel> => {
    const response = await apiClient.get(`/ai-models/${id}`)
    return response.data
  },

  // Créer un nouveau modèle
  create: async (data: AIModelCreate): Promise<AIModel> => {
    const response = await apiClient.post('/ai-models/', data)
    return response.data
  },

  // Mettre à jour un modèle
  update: async (id: string, data: AIModelUpdate): Promise<AIModel> => {
    const response = await apiClient.put(`/ai-models/${id}`, data)
    return response.data
  },

  // Supprimer un modèle
  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/ai-models/${id}`)
  },

  // Activer/désactiver un modèle
  toggle: async (id: string): Promise<AIModel> => {
    const response = await apiClient.post(`/ai-models/${id}/toggle`)
    return response.data
  },

  // Récupérer les modèles par fournisseur
  getByProvider: async (provider: string, activeOnly: boolean = true): Promise<AIModel[]> => {
    const response = await apiClient.get(`/ai-models/provider/${provider}`, {
      params: { active_only: activeOnly }
    })
    return response.data
  }
} 