import { useState, useEffect, useCallback } from 'react'
import { AIModelsAPI } from '../services/aiModels'
import type { AIModel, AIModelCreate, AIModelUpdate } from '../types/aiModel'

interface UseAIModelsReturn {
  models: AIModel[]
  loading: boolean
  error: string | null
  createModel: (data: AIModelCreate) => Promise<AIModel | null>
  updateModel: (id: string, data: AIModelUpdate) => Promise<AIModel | null>
  deleteModel: (id: string) => Promise<boolean>
  toggleModel: (id: string) => Promise<AIModel | null>
  refresh: () => Promise<void>
}

export const useAIModels = (): UseAIModelsReturn => {
  const [models, setModels] = useState<AIModel[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchModels = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      console.log('🔄 Chargement des modèles IA...')
      
      const modelsData = await AIModelsAPI.getAll()
      setModels(modelsData)
      console.log('✅ Modèles IA chargés:', modelsData.length)
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erreur inconnue'
      console.error('❌ Erreur lors du chargement des modèles IA:', err)
      setError(`Erreur lors du chargement des modèles IA: ${errorMessage}`)
    } finally {
      setLoading(false)
    }
  }, [])

  const createModel = async (data: AIModelCreate): Promise<AIModel | null> => {
    try {
      console.log('🆕 Création d\'un nouveau modèle IA:', data.name)
      setError(null)
      
      const newModel = await AIModelsAPI.create(data)
      setModels(prev => [...prev, newModel])
      console.log('✅ Modèle IA créé:', newModel.id)
      
      return newModel
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erreur inconnue'
      console.error('❌ Erreur lors de la création du modèle IA:', err)
      setError(`Erreur lors de la création: ${errorMessage}`)
      return null
    }
  }

  const updateModel = async (id: string, data: AIModelUpdate): Promise<AIModel | null> => {
    try {
      console.log('📝 Mise à jour du modèle IA:', id)
      setError(null)
      
      const updatedModel = await AIModelsAPI.update(id, data)
      setModels(prev => prev.map(model => 
        model.id === id ? updatedModel : model
      ))
      console.log('✅ Modèle IA mis à jour:', id)
      
      return updatedModel
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erreur inconnue'
      console.error('❌ Erreur lors de la mise à jour du modèle IA:', err)
      setError(`Erreur lors de la mise à jour: ${errorMessage}`)
      return null
    }
  }

  const deleteModel = async (id: string): Promise<boolean> => {
    try {
      console.log('🗑️ Suppression du modèle IA:', id)
      setError(null)
      
      await AIModelsAPI.delete(id)
      setModels(prev => prev.filter(model => model.id !== id))
      console.log('✅ Modèle IA supprimé:', id)
      
      return true
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erreur inconnue'
      console.error('❌ Erreur lors de la suppression du modèle IA:', err)
      setError(`Erreur lors de la suppression: ${errorMessage}`)
      return false
    }
  }

  const toggleModel = async (id: string): Promise<AIModel | null> => {
    try {
      console.log('🔄 Basculement du statut du modèle IA:', id)
      setError(null)
      
      const toggledModel = await AIModelsAPI.toggle(id)
      setModels(prev => prev.map(model => 
        model.id === id ? toggledModel : model
      ))
      console.log('✅ Statut du modèle IA basculé:', id)
      
      return toggledModel
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erreur inconnue'
      console.error('❌ Erreur lors du basculement du statut:', err)
      setError(`Erreur lors du basculement: ${errorMessage}`)
      return null
    }
  }

  const refresh = useCallback(async () => {
    await fetchModels()
  }, [fetchModels])

  // Chargement initial
  useEffect(() => {
    fetchModels()
  }, [fetchModels])

  return {
    models,
    loading,
    error,
    createModel,
    updateModel,
    deleteModel,
    toggleModel,
    refresh
  }
} 