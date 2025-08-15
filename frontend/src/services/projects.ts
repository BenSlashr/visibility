import { apiClient } from './api'
import type { 
  Project, 
  ProjectCreate, 
  ProjectUpdate, 
  ProjectSummary,
  Competitor,
  CompetitorCreate
} from '../types/project'

export const ProjectsAPI = {
  // Projets
  async getAll(params?: { limit?: number; skip?: number; search?: string }): Promise<ProjectSummary[]> {
    const response = await apiClient.get('/projects/', { params })
    return response.data
  },

  async getById(id: string): Promise<Project> {
    const response = await apiClient.get(`/projects/${id}`)
    return response.data
  },

  async create(project: ProjectCreate): Promise<Project> {
    const response = await apiClient.post('/projects/', project)
    return response.data
  },

  async update(id: string, project: ProjectUpdate): Promise<Project> {
    const response = await apiClient.put(`/projects/${id}`, project)
    return response.data
  },

  async delete(id: string): Promise<void> {
    await apiClient.delete(`/projects/${id}`)
  },

  async updateKeywords(id: string, keywords: string[]): Promise<Project> {
    const response = await apiClient.put(`/projects/${id}/keywords`, { keywords })
    return response.data
  },

  // Concurrents
  async getCompetitors(projectId: string): Promise<Competitor[]> {
    const response = await apiClient.get(`/projects/${projectId}/competitors`)
    return response.data
  },

  async addCompetitor(projectId: string, competitor: CompetitorCreate): Promise<Competitor> {
    const response = await apiClient.post(`/projects/${projectId}/competitors`, competitor)
    return response.data
  },

  async removeCompetitor(projectId: string, competitorId: string): Promise<void> {
    await apiClient.delete(`/projects/${projectId}/competitors/${competitorId}`)
  }
} 