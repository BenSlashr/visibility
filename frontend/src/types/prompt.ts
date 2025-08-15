// Types pour les prompts
export interface PromptAIModel {
  prompt_id: string
  ai_model_id: string
  is_active: boolean
  created_at: string
  ai_model_name?: string
  ai_model_provider?: string
}

export interface Prompt {
  id: string
  project_id: string
  ai_model_id?: string  // Nullable pour les prompts multi-agents
  name: string
  template: string
  description?: string
  is_active: boolean
  is_multi_agent: boolean  // Nouveau champ
  execution_count: number
  last_executed_at?: string
  created_at: string
  updated_at: string
  tags: string[]  // Simplifié
  ai_models: PromptAIModel[]  // Relations multi-agents
  ai_model_name?: string  // Nom du modèle principal
  ai_model_names: string[]  // Noms de tous les modèles
  ai_model?: {
    id: string
    name: string
    provider: string
  }
}

export interface PromptCreate {
  project_id: string
  name: string
  template: string
  description?: string
  tags?: string[]
  is_active?: boolean
  // Support multi-agents
  is_multi_agent?: boolean
  ai_model_id?: string  // Pour les prompts à modèle unique
  ai_model_ids?: string[]  // Pour les prompts multi-agents
}

export interface PromptUpdate {
  name?: string
  template?: string
  description?: string
  is_active?: boolean
  is_multi_agent?: boolean
  ai_model_id?: string
  ai_model_ids?: string[]
}

export interface PromptSummary {
  id: string
  project_id: string
  name: string
  description?: string
  template?: string
  is_active: boolean
  is_multi_agent?: boolean  // Nouveau champ
  execution_count: number
  last_executed_at?: string
  ai_model_name?: string
  ai_model_names?: string[]  // Nouveau champ
  tags?: string[]
  created_at: string
  updated_at: string
}

export interface PromptTag {
  prompt_id: string
  tag: string
  created_at: string
}

export interface PromptExecuteRequest {
  custom_variables?: Record<string, string>
  max_tokens?: number
  // Multi-agents
  ai_model_ids?: string[]  // Modèles spécifiques à exécuter
  compare_models?: boolean  // Exécuter sur tous les modèles pour comparaison
}

export interface PromptExecuteResponse {
  success: boolean
  analysis_id?: string
  prompt_executed?: string
  ai_response?: string
  variables_used?: Record<string, string>
  brand_mentioned?: boolean
  website_mentioned?: boolean
  website_linked?: boolean
  ranking_position?: number
  competitors_mentioned?: number
  visibility_score?: number
  analysis_summary?: string
  ai_model_used?: string
  tokens_used?: number
  processing_time_ms?: number
  cost_estimated?: number
  error?: string
  // Multi-agents
  results?: Array<{
    ai_model_id: string
    ai_model_name: string
    analysis_id: string
    ai_response: string
    visibility_score: number
    cost_estimated: number
    tokens_used: number
    processing_time_ms: number
  }>
} 