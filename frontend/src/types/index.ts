// Export centralisé de tous les types
export * from './project'
export * from './aiModel'
export * from './prompt'
export * from './analysis'
export * from './serp'

// Types pour l'API Visibility Tracker (anciens types conservés pour compatibilité)
export interface Project {
  id: number
  name: string
  main_website: string
  description?: string
  keywords: string[]
  created_at: string
  updated_at: string
}

export interface Competitor {
  id: number
  project_id: number
  name: string
  website: string
  created_at: string
}

export interface AIModel {
  id: number
  name: string
  provider: string
  model_id: string
  max_tokens: number
  cost_per_token: number
  is_active: boolean
}

export interface Prompt {
  id: number
  name: string
  template: string
  ai_model_id: number
  tags: string[]
  variables: Record<string, string>
  created_at: string
  updated_at: string
}

export interface Analysis {
  id: number
  project_id: number
  prompt_id: number
  ai_model_id: number
  prompt_executed: string
  ai_response: string
  brand_mentioned: boolean
  website_mentioned: boolean
  brand_position?: number
  links_to_website: number
  tokens_used: number
  processing_time: number
  created_at: string
}

export interface CompetitorAnalysis {
  id: number
  analysis_id: number
  competitor_id: number
  mentioned: boolean
  position?: number
  created_at: string
}

// Types pour les formulaires
export interface CreateProjectRequest {
  name: string
  main_website: string
  description?: string
  keywords: string[]
}

export interface UpdateProjectRequest extends Partial<CreateProjectRequest> {
  id: number
}

export interface CreatePromptRequest {
  name: string
  template: string
  ai_model_id: number
  tags: string[]
  variables: Record<string, string>
}

export interface RunAnalysisRequest {
  project_id: number
  prompt_id: number
  custom_variables?: Record<string, string>
}

// Types pour les réponses API
export interface ApiResponse<T> {
  data: T
  message?: string
  success: boolean
}

export interface PaginatedResponse<T> {
  data: T[]
  total: number
  page: number
  per_page: number
  total_pages: number
}

// Types pour les états de l'interface
export interface LoadingState {
  isLoading: boolean
  error?: string
}

export interface AnalysisState extends LoadingState {
  current_analysis?: Analysis
  progress?: number
} 

// Sources aggregates
export interface SourceDomainSummary {
  id: string
  domain: string
  pages: number
  analyses: number
  me_mentions: number
  me_links: number
  competitor_mentions: number
  me_link_rate: number
  me_mention_rate: number
  first_seen?: string
  last_seen?: string
}