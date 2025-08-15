// Types pour les analyses
export interface AnalysisSource {
  id: string
  analysis_id: string
  url: string
  domain?: string
  title?: string
  snippet?: string
  citation_label?: string
  position?: number
  is_valid?: boolean
  http_status?: number
  content_type?: string
  confidence?: number
  metadata?: Record<string, any>
  created_at: string
  updated_at: string
}

export interface Analysis {
  id: string
  prompt_id: string
  project_id: string
  ai_model_id: string
  prompt_executed: string
  ai_response: string
  brand_mentioned: boolean
  website_mentioned: boolean
  website_linked: boolean
  ranking_position?: number
  visibility_score: number
  analysis_summary?: string
  ai_model_used: string
  tokens_used: number
  processing_time_ms: number
  cost_estimated: number
  web_search_used?: boolean
  created_at: string
  updated_at: string
  competitors_analysis?: CompetitorAnalysis[]
  sources?: AnalysisSource[]
}

export interface AnalysisCreate {
  prompt_id: string
  project_id: string
  ai_model_id: string
  prompt_executed: string
  ai_response: string
  brand_mentioned: boolean
  website_mentioned: boolean
  website_linked: boolean
  ranking_position?: number
  visibility_score: number
  analysis_summary?: string
  ai_model_used: string
  tokens_used: number
  processing_time_ms: number
  cost_estimated: number
  competitors_analysis?: CompetitorAnalysisCreate[]
}

export interface AnalysisUpdate {
  brand_mentioned?: boolean
  website_mentioned?: boolean
  website_linked?: boolean
  ranking_position?: number
  visibility_score?: number
  analysis_summary?: string
}

export interface AnalysisSummary {
  id: string
  prompt_id: string
  project_id: string
  brand_mentioned: boolean
  website_mentioned: boolean
  website_linked: boolean
  ranking_position?: number
  ai_model_used: string
  tokens_used: number
  cost_estimated: number
  visibility_score: number
  created_at: string
  updated_at: string
  // Données des concurrents
  competitors_analysis?: CompetitorAnalysis[]
  has_sources?: boolean
  web_search_used?: boolean
}

export interface CompetitorAnalysis {
  id: string
  analysis_id: string
  competitor_id: string
  competitor_name: string
  is_mentioned: boolean
  mention_context?: string
  ranking_position?: number
  created_at: string
}

export interface CompetitorAnalysisCreate {
  competitor_id: string
  competitor_name: string
  is_mentioned: boolean
  mention_context?: string
  ranking_position?: number
}

export interface AnalysisStats {
  total_analyses: number
  total_cost: number
  average_tokens: number
  brand_mention_rate: number
  website_mention_rate: number
  average_visibility_score: number
  best_ranking_position?: number
  most_active_model: string
  total_processing_time_ms: number
}

export interface ProjectAnalysisStats extends AnalysisStats {
  project_id: string
  project_name: string
  analyses_last_30_days: number
  cost_last_30_days: number
  average_score_last_30_days: number
}

export interface AnalysisFilters {
  project_id?: string
  prompt_id?: string
  brand_mentioned?: boolean
  has_ranking?: boolean
  search?: string
  skip?: number
  limit?: number
  model_id?: string
  date_from?: string
  date_to?: string
  tag?: string
  has_sources?: boolean
} 