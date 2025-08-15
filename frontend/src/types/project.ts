// Types pour les projets
export interface Project {
  id: string
  name: string
  main_website?: string
  description?: string
  created_at: string
  updated_at: string
  keywords: ProjectKeyword[]
  competitors: Competitor[]
}

export interface ProjectCreate {
  name: string
  main_website?: string
  description?: string
  keywords?: string[]
}

export interface ProjectUpdate {
  name?: string
  main_website?: string
  description?: string
}

export interface ProjectSummary {
  id: string
  name: string
  main_website?: string
  description?: string
  created_at: string
  updated_at: string
  keywords_count: number
  competitors_count: number
  analyses_count: number
}

export interface Competitor {
  id: string
  project_id: string
  name: string
  website: string
  created_at: string
}

export interface CompetitorCreate {
  name: string
  website: string
}

export interface ProjectKeyword {
  project_id: string
  keyword: string
  created_at: string
} 