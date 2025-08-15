import { useState, useEffect } from 'react'
import { PromptsAPI } from '../services/prompts'
import { useCurrentProject } from '../contexts/ProjectContext'
import type { 
  Prompt, 
  PromptSummary, 
  PromptCreate, 
  PromptUpdate, 
  PromptExecuteRequest,
  PromptExecuteResponse 
} from '../types/prompt'

interface UsePromptsReturn {
  prompts: PromptSummary[]
  loading: boolean
  error: string | null
  createPrompt: (prompt: PromptCreate) => Promise<Prompt | null>
  updatePrompt: (id: string, prompt: PromptUpdate) => Promise<Prompt | null>
  deletePrompt: (id: string) => Promise<boolean>
  executePrompt: (id: string, request?: PromptExecuteRequest) => Promise<PromptExecuteResponse | null>
  refresh: () => Promise<void>
}

export const usePrompts = (): UsePromptsReturn => {
  const { currentProject } = useCurrentProject()
  const [prompts, setPrompts] = useState<PromptSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchPrompts = async () => {
    try {
      setLoading(true)
      setError(null)

      if (!currentProject) {
        console.log('⚠️ Aucun projet sélectionné, pas de chargement de prompts')
        setPrompts([])
        return
      }

      console.log('🔄 Chargement des prompts pour le projet:', currentProject.name)
      
      // Récupérer les prompts du projet actuel
      const projectPrompts = await PromptsAPI.getAll({ 
        project_id: currentProject.id,
        active_only: false,
        limit: 100 
      })
      
      setPrompts(projectPrompts)
      console.log('✅ Prompts chargés:', projectPrompts.length)
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erreur inconnue'
      console.error('❌ Erreur lors du chargement des prompts:', err)
      setError(`Erreur lors du chargement des prompts: ${errorMessage}`)
    } finally {
      setLoading(false)
    }
  }

  const createPrompt = async (promptData: PromptCreate): Promise<Prompt | null> => {
    try {
      if (!currentProject) {
        throw new Error('Aucun projet sélectionné')
      }

      console.log('🔄 Création du prompt:', promptData.name)
      
      // Associer le prompt au projet actuel
      const promptWithProject = {
        ...promptData,
        project_id: currentProject.id
      }
      
      const newPrompt = await PromptsAPI.create(promptWithProject)
      
      // Recharger la liste des prompts
      await fetchPrompts()
      
      console.log('✅ Prompt créé:', newPrompt.name)
      return newPrompt
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erreur inconnue'
      console.error('❌ Erreur lors de la création du prompt:', err)
      setError(`Erreur lors de la création: ${errorMessage}`)
      return null
    }
  }

  const updatePrompt = async (id: string, promptData: PromptUpdate): Promise<Prompt | null> => {
    try {
      console.log('🔄 Mise à jour du prompt:', id)
      const updatedPrompt = await PromptsAPI.update(id, promptData)
      
      // Mettre à jour la liste locale
      setPrompts(prev => prev.map(p => 
        p.id === id ? { ...p, ...promptData } : p
      ))
      
      console.log('✅ Prompt mis à jour:', updatedPrompt.name)
      return updatedPrompt
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erreur inconnue'
      console.error('❌ Erreur lors de la mise à jour du prompt:', err)
      setError(`Erreur lors de la mise à jour: ${errorMessage}`)
      return null
    }
  }

  const deletePrompt = async (id: string): Promise<boolean> => {
    try {
      console.log('🔄 Suppression du prompt:', id)
      await PromptsAPI.delete(id)
      
      // Supprimer de la liste locale
      setPrompts(prev => prev.filter(p => p.id !== id))
      
      console.log('✅ Prompt supprimé:', id)
      return true
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erreur inconnue'
      console.error('❌ Erreur lors de la suppression du prompt:', err)
      setError(`Erreur lors de la suppression: ${errorMessage}`)
      return false
    }
  }

  const executePrompt = async (id: string, request?: PromptExecuteRequest): Promise<PromptExecuteResponse | null> => {
    try {
      if (!currentProject) {
        throw new Error('Aucun projet sélectionné')
      }

      console.log('🚀 Exécution du prompt:', id)
      setError(null)
      
      // Exécuter le prompt
      const result = await PromptsAPI.execute(id, request)
      
      if (result.success) {
        console.log('✅ Prompt exécuté avec succès, analyse créée:', result.analysis_id)
        
        // Optionnel : recharger les prompts pour mettre à jour les stats d'usage
        await fetchPrompts()
        
        return result
      } else {
        throw new Error(result.error || 'Erreur lors de l\'exécution')
      }
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erreur inconnue'
      console.error('❌ Erreur lors de l\'exécution du prompt:', err)
      setError(`Erreur lors de l'exécution: ${errorMessage}`)
      return null
    }
  }

  const refresh = async () => {
    await fetchPrompts()
  }

  // Chargement initial et rechargement si le projet change
  useEffect(() => {
    fetchPrompts()
  }, [currentProject?.id])

  // Écouter les changements de projet
  useEffect(() => {
    const handleProjectChange = () => {
      console.log('🔄 Projet changé, rechargement des prompts')
      fetchPrompts()
    }

    window.addEventListener('projectChanged', handleProjectChange)
    return () => window.removeEventListener('projectChanged', handleProjectChange)
  }, [])

  return {
    prompts,
    loading,
    error,
    createPrompt,
    updatePrompt,
    deletePrompt,
    executePrompt,
    refresh
  }
} 