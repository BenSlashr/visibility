// Types pour les fonctionnalités SERP

export interface SERPKeyword {
  id: string
  import_id: string
  project_id: string
  keyword: string
  keyword_normalized: string
  volume?: number
  position: number
  url?: string
  created_at: string
  updated_at: string
}

export interface SERPImport {
  id: string
  project_id: string
  filename: string
  import_date: string
  total_keywords: number
  is_active: boolean
  notes?: string
  created_at: string
  updated_at: string
  keywords?: SERPKeyword[]
}

export interface PromptSERPAssociation {
  prompt_id: string
  serp_keyword_id: string
  matching_score?: number
  association_type: 'manual' | 'auto' | 'suggested'
  created_at: string
  updated_at: string
  serp_keyword?: SERPKeyword
}

// Schémas pour les requêtes API

export interface SERPImportRequest {
  project_id: string
  filename: string
  notes?: string
}

export interface SERPKeywordCreateRequest {
  keyword: string
  position: number
  volume?: number
  url?: string
}

export interface PromptSERPAssociationRequest {
  serp_keyword_id?: string // null pour supprimer l'association
}

// Réponses API

export interface SERPImportResponse {
  success: boolean
  import_id?: string
  keywords_imported: number
  errors_count: number
  errors: string[]
}

export interface AutoMatchResponse {
  success: boolean
  auto_matches: number
  suggestions: number
  details: {
    auto_matches: AutoMatchAutomatic[]
    suggestions: MatchingSuggestion[]
  }
}

export interface AutoMatchAutomatic {
  prompt_id: string
  prompt_name: string
  keyword: string
  score: number
}

export interface MatchingSuggestion {
  prompt_id: string
  prompt_name: string
  keyword: string
  keyword_id: string
  score: number
  confidence_level: 'high' | 'medium' | 'low'
}

// Statistiques et résumés

export interface SERPStats {
  average_position: number
  top_3_keywords: number
  top_10_keywords: number
}

export interface AssociationStats {
  auto_associations: number
  manual_associations: number
  unassociated_prompts: number
  association_rate: number
}

export interface ImportInfo {
  filename: string
  import_date: string
  total_keywords: number
}

export interface SERPSummaryResponse {
  has_serp_data: boolean
  import_info?: ImportInfo
  serp_stats?: SERPStats
  associations?: AssociationStats
}

export interface SERPKeywordListResponse {
  keywords: Array<{
    id: string
    keyword: string
    position: number
    volume?: number
    url?: string
  }>
}

export interface PromptSERPAssociationResponse {
  has_association: boolean
  association?: {
    keyword_id: string
    keyword: string
    position: number
    volume?: number
    association_type: string
    matching_score?: number
  }
}

// Corrélations SERP vs IA

export interface SERPCorrelationData {
  analysis_id: string
  prompt_name: string
  serp_keyword?: string
  serp_position?: number
  serp_volume?: number
  ai_mentioned: boolean
  ai_ranking_position?: number
  correlation_score?: number
}

export interface ProjectSERPCorrelation {
  project_id: string
  project_name: string
  total_analyses: number
  analyses_with_serp: number
  correlation_analyses: SERPCorrelationData[]
  average_correlation?: number
  insights: Record<string, any>
}

// États de l'interface utilisateur

export interface SERPUploadState {
  isUploading: boolean
  uploadProgress?: number
  error?: string
  result?: SERPImportResponse
}

export interface SERPMatchingState {
  isMatching: boolean
  error?: string
  result?: AutoMatchResponse
}

export interface SERPDashboardData {
  summary?: SERPSummaryResponse
  keywords?: SERPKeyword[]
  correlations?: ProjectSERPCorrelation
  isLoading: boolean
  error?: string
}

// Formulaires et validation

export interface SERPUploadFormData {
  file: File | null
  notes: string
}

export interface SERPAssociationFormData {
  prompt_id: string
  serp_keyword_id: string | null
  association_type?: 'manual' | 'auto'
}

// Filtres et recherche

export interface SERPKeywordFilters {
  search?: string
  position_max?: number
  volume_min?: number
  association_status?: 'associated' | 'unassociated' | 'all'
}

export interface SERPAnalysisFilters {
  has_serp_data?: boolean
  correlation_threshold?: number
  position_range?: [number, number]
}

// Configuration et préférences

export interface SERPSettings {
  auto_match_threshold: number // Score minimum pour association automatique
  suggestion_threshold: number // Score minimum pour suggestions
  default_position_filter: number // Position max pour filtres par défaut
  enable_notifications: boolean // Notifications pour nouveaux imports
}

// Insights et métriques avancées

export interface SERPInsight {
  type: 'positive' | 'negative' | 'neutral'
  title: string
  description: string
  metric?: {
    value: number
    format: 'percentage' | 'number' | 'position'
    comparison?: {
      previous: number
      trend: 'up' | 'down' | 'stable'
    }
  }
}

export interface SERPPerformanceMetrics {
  visibility_correlation: number // Corrélation visibilité IA vs SERP
  top_performing_keywords: SERPKeyword[]
  underperforming_keywords: SERPKeyword[]
  coverage_rate: number // % de prompts avec association SERP
  insights: SERPInsight[]
}

// Export de tous les types
export type {
  // Types de base
  SERPKeyword as Keyword,
  SERPImport as Import,
  PromptSERPAssociation as Association,
  
  // Réponses API
  SERPImportResponse as ImportResponse,
  AutoMatchResponse as MatchResponse,
  SERPSummaryResponse as SummaryResponse,
  
  // États UI
  SERPUploadState as UploadState,
  SERPMatchingState as MatchingState,
  SERPDashboardData as DashboardData
}