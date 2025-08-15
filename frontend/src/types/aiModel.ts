// Types pour les modèles IA
export type AIProvider = 'openai' | 'anthropic' | 'google' | 'mistral'

export interface AIModel {
  id: string
  name: string
  provider: AIProvider
  model_identifier: string
  max_tokens: number
  cost_per_1k_tokens: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface AIModelCreate {
  name: string
  provider: AIProvider
  model_identifier: string
  max_tokens: number
  cost_per_1k_tokens: number
  is_active?: boolean
}

export interface AIModelUpdate {
  name?: string
  provider?: AIProvider
  model_identifier?: string
  max_tokens?: number
  cost_per_1k_tokens?: number
  is_active?: boolean
} 