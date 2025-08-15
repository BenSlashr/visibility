import React, { useState } from 'react'
import { Plus, Search, TrendingUp, BarChart3, DollarSign, Trash2, ExternalLink } from 'lucide-react'
import { ProjectCard } from '../components/ProjectCard'
import { Button, Input, Modal, Loading } from '../components/ui'
import { useProjects } from '../hooks/useProjects'
import { useCompetitors } from '../hooks/useCompetitors'
import { useCurrentProject } from '../contexts/ProjectContext'
import type { ProjectCreate, ProjectUpdate, ProjectSummary, CompetitorCreate } from '../types/project'

interface ProjectFormData {
  name: string
  main_website: string
  description: string
  keywords: string[]
  competitors: Array<{ name: string; website: string }>
}

export const ProjectsPage: React.FC = () => {
  const { projects, loading, error, createProject, updateProject, deleteProject, refresh } = useProjects()
  const { currentProject, setCurrentProject } = useCurrentProject()
  
  const [searchTerm, setSearchTerm] = useState('')
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)
  const [isEditModalOpen, setIsEditModalOpen] = useState(false)
  const [selectedProject, setSelectedProject] = useState<ProjectSummary | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  
  // Hook pour gérer les concurrents du projet sélectionné
  const { 
    competitors, 
    loading: competitorsLoading, 
    error: competitorsError, 
    addCompetitor: addCompetitorToProject, 
    removeCompetitor: removeCompetitorFromProject 
  } = useCompetitors(selectedProject?.id)
  
  // État du formulaire
  const [formData, setFormData] = useState<ProjectFormData>({
    name: '',
    main_website: '',
    description: '',
    keywords: [],
    competitors: []
  })
  
  // État pour les champs de saisie
  const [keywordInput, setKeywordInput] = useState('')
  const [newCompetitor, setNewCompetitor] = useState<CompetitorCreate>({
    name: '',
    website: ''
  })

  // Filtrage des projets
  const filteredProjects = projects.filter(project =>
    project.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (project.description || '').toLowerCase().includes(searchTerm.toLowerCase())
  )

  // Statistiques calculées
  const totalAnalyses = projects.reduce((sum, p) => sum + (p.analyses_count || 0), 0)
  const avgVisibility = projects.length > 0 ? 
    Math.round(projects.reduce((sum, p) => sum + (p.analyses_count || 0), 0) / projects.length) : 0

  const resetForm = () => {
    setFormData({
      name: '',
      main_website: '',
      description: '',
      keywords: [],
      competitors: []
    })
    setKeywordInput('')
    setNewCompetitor({ name: '', website: '' })
  }

  const handleCreateProject = () => {
    resetForm()
    setIsCreateModalOpen(true)
  }

  const handleEditProject = (project: ProjectSummary) => {
    setSelectedProject(project)
    setFormData({
      name: project.name,
      main_website: project.main_website || '',
      description: project.description || '',
      keywords: [], // Les keywords seront chargées séparément si nécessaire
      competitors: [] // Les competitors seront chargés séparément si nécessaire
    })
    setIsEditModalOpen(true)
  }

  const handleDeleteProject = async (project: ProjectSummary) => {
    if (window.confirm(`Êtes-vous sûr de vouloir supprimer le projet "${project.name}" ?\n\nCette action supprimera également tous les prompts et analyses associés.`)) {
      const success = await deleteProject(project.id)
      if (success && currentProject?.id === project.id) {
        setCurrentProject(null)
      }
    }
  }

  const handleSelectProject = (project: ProjectSummary) => {
    setCurrentProject(project)
    console.log('🏠 Projet sélectionné:', project.name)
  }

  const addKeyword = () => {
    if (keywordInput.trim() && !formData.keywords.includes(keywordInput.trim())) {
      setFormData(prev => ({
        ...prev,
        keywords: [...prev.keywords, keywordInput.trim()]
      }))
      setKeywordInput('')
    }
  }

  const removeKeyword = (index: number) => {
    setFormData(prev => ({
      ...prev,
      keywords: prev.keywords.filter((_, i) => i !== index)
    }))
  }

  const handleAddCompetitor = async () => {
    if (newCompetitor.name.trim() && newCompetitor.website.trim() && selectedProject) {
      const competitorData = {
        name: newCompetitor.name.trim(),
        website: newCompetitor.website.trim()
      }
      
      const result = await addCompetitorToProject(competitorData)
      if (result) {
        setNewCompetitor({ name: '', website: '' })
      }
    }
  }

  const handleRemoveCompetitor = async (competitorId: string) => {
    if (selectedProject) {
      await removeCompetitorFromProject(competitorId)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!formData.name.trim()) {
      alert('Le nom du projet est obligatoire')
      return
    }

    setIsSubmitting(true)
    
    try {
      const projectData: ProjectCreate | ProjectUpdate = {
        name: formData.name.trim(),
        main_website: formData.main_website.trim() || undefined,
        description: formData.description.trim() || undefined,
        keywords: formData.keywords
      }

      let result
      if (isEditModalOpen && selectedProject) {
        result = await updateProject(selectedProject.id, projectData)
      } else {
        result = await createProject(projectData as ProjectCreate)
      }

      if (result) {
        setIsCreateModalOpen(false)
        setIsEditModalOpen(false)
        resetForm()
        setSelectedProject(null)
        
        // Si c'est une création et qu'aucun projet n'est sélectionné, sélectionner le nouveau
        if (!isEditModalOpen && !currentProject) {
          // Convertir Project en ProjectSummary pour setCurrentProject
          const projectSummary: ProjectSummary = {
            id: result.id,
            name: result.name,
            main_website: result.main_website,
            description: result.description,
            created_at: result.created_at,
            updated_at: result.updated_at,
            keywords_count: result.keywords?.length || 0,
            competitors_count: result.competitors?.length || 0,
            analyses_count: 0
          }
          setCurrentProject(projectSummary)
        }
      }
    } catch (err) {
      console.error('Erreur lors de la soumission:', err)
    } finally {
      setIsSubmitting(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loading size="lg" text="Chargement des projets..." />
      </div>
    )
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center">
          <div className="text-red-600 text-xl mb-4">❌ Erreur</div>
          <p className="text-gray-600 mb-4">{error}</p>
          <Button onClick={refresh} variant="primary">
            Réessayer
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Mes Projets</h1>
          <p className="text-gray-600 mt-2">
            Gérez vos projets SEO et leurs analyses de visibilité
          </p>
        </div>
        <Button
          variant="primary"
          onClick={handleCreateProject}
          className="flex items-center space-x-2"
        >
          <Plus className="h-4 w-4" />
          <span>Nouveau Projet</span>
        </Button>
      </div>

      {/* Stats rapides */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
          <div className="flex items-center">
            <TrendingUp className="h-8 w-8 text-blue-600 mr-3" />
            <div>
              <div className="text-2xl font-bold text-gray-900">{projects.length}</div>
              <div className="text-gray-600 text-sm">Projets actifs</div>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
          <div className="flex items-center">
            <BarChart3 className="h-8 w-8 text-green-600 mr-3" />
            <div>
              <div className="text-2xl font-bold text-gray-900">{totalAnalyses}</div>
              <div className="text-gray-600 text-sm">Analyses totales</div>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
          <div className="flex items-center">
            <DollarSign className="h-8 w-8 text-purple-600 mr-3" />
            <div>
              <div className="text-2xl font-bold text-gray-900">{avgVisibility}%</div>
              <div className="text-gray-600 text-sm">Visibilité moyenne</div>
            </div>
          </div>
        </div>
      </div>

      {/* Barre de recherche */}
      {projects.length > 0 && (
        <div className="mb-6">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              placeholder="Rechercher des projets..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
        </div>
      )}

      {/* Liste des projets */}
      {filteredProjects.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredProjects.map((project) => (
            <div key={project.id} className="relative">
            <ProjectCard
                project={{
                  id: project.id as any, // Conversion temporaire pour compatibilité
                  name: project.name,
                  main_website: project.main_website || '',
                  description: project.description,
                  keywords: [], // Simplifié pour l'affichage
                  created_at: project.created_at,
                  updated_at: project.updated_at
                }}
                onEdit={() => handleEditProject(project)}
                onDelete={() => handleDeleteProject(project)}
                onAnalyze={() => handleSelectProject(project)}
              />
              {currentProject?.id === project.id && (
                <div className="absolute -top-2 -right-2">
                  <div className="bg-green-500 text-white text-xs px-2 py-1 rounded-full">
                    Actuel
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      ) : projects.length > 0 ? (
        <div className="text-center py-12">
          <div className="text-gray-400 text-lg mb-4">
            Aucun projet trouvé pour "{searchTerm}"
          </div>
          <Button variant="ghost" onClick={() => setSearchTerm('')}>
            Voir tous les projets
          </Button>
        </div>
      ) : (
        <div className="text-center py-12">
          <div className="text-gray-400 text-lg mb-4">
            Aucun projet créé pour le moment
          </div>
          <Button variant="primary" onClick={handleCreateProject}>
            Créer votre premier projet
          </Button>
        </div>
      )}

      {/* Modal de création */}
      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        title="Créer un nouveau projet"
      >
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Nom du projet *
            </label>
            <Input
              value={formData.name}
              onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
              placeholder="Mon Site E-commerce"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Site web principal
            </label>
            <Input
              value={formData.main_website}
              onChange={(e) => setFormData(prev => ({ ...prev, main_website: e.target.value }))}
              placeholder="https://monsite.com"
              type="url"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Description
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
              placeholder="Description du projet..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows={3}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Mots-clés cibles
            </label>
            <div className="flex space-x-2 mb-2">
              <Input
                value={keywordInput}
                onChange={(e) => setKeywordInput(e.target.value)}
                placeholder="Ajouter un mot-clé"
                onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addKeyword())}
              />
              <Button type="button" onClick={addKeyword} variant="outline">
                Ajouter
              </Button>
            </div>
            <div className="flex flex-wrap gap-2">
              {formData.keywords.map((keyword, index) => (
                <span
                  key={index}
                  className="inline-flex items-center bg-blue-100 text-blue-800 text-sm px-2 py-1 rounded"
                >
                  {keyword}
                  <button
                    type="button"
                    onClick={() => removeKeyword(index)}
                    className="ml-1 text-blue-600 hover:text-blue-800"
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          </div>



          <div className="flex justify-end space-x-3">
            <Button
              type="button"
              variant="ghost"
              onClick={() => setIsCreateModalOpen(false)}
            >
              Annuler
            </Button>
            <Button
              type="submit"
              variant="primary"
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Création...' : 'Créer le projet'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Modal d'édition */}
      <Modal
        isOpen={isEditModalOpen}
        onClose={() => setIsEditModalOpen(false)}
        title="Modifier le projet"
      >
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Nom du projet *
            </label>
            <Input
              value={formData.name}
              onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
              placeholder="Mon Site E-commerce"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Site web principal
            </label>
            <Input
              value={formData.main_website}
              onChange={(e) => setFormData(prev => ({ ...prev, main_website: e.target.value }))}
              placeholder="https://monsite.com"
              type="url"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Description
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
              placeholder="Description du projet..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows={3}
            />
          </div>

          {/* Section des concurrents */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Concurrents
            </label>
            
            {/* Liste des concurrents existants */}
            {competitorsLoading ? (
              <div className="text-sm text-gray-500">Chargement des concurrents...</div>
            ) : competitors.length > 0 ? (
              <div className="space-y-2 mb-4">
                {competitors.map((competitor) => (
                  <div
                    key={competitor.id}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border"
                  >
                    <div className="flex items-center space-x-3">
                      <div>
                        <div className="font-medium text-gray-900">{competitor.name}</div>
                        <div className="text-sm text-gray-500 flex items-center">
                          <ExternalLink className="h-3 w-3 mr-1" />
                          <a 
                            href={competitor.website} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="hover:text-blue-600"
                          >
                            {competitor.website}
                          </a>
                        </div>
                      </div>
                    </div>
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => handleRemoveCompetitor(competitor.id)}
                      className="text-red-600 hover:text-red-800"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-sm text-gray-500 mb-4">Aucun concurrent ajouté</div>
            )}

            {/* Formulaire d'ajout de concurrent */}
            <div className="space-y-3 p-4 bg-gray-50 rounded-lg border">
              <div className="text-sm font-medium text-gray-700">Ajouter un concurrent</div>
              <div className="grid grid-cols-2 gap-3">
                <Input
                  value={newCompetitor.name}
                  onChange={(e) => setNewCompetitor(prev => ({ ...prev, name: e.target.value }))}
                  placeholder="Nom du concurrent"
                />
                <Input
                  value={newCompetitor.website}
                  onChange={(e) => setNewCompetitor(prev => ({ ...prev, website: e.target.value }))}
                  placeholder="https://concurrent.com"
                  type="url"
                />
              </div>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={handleAddCompetitor}
                disabled={!newCompetitor.name.trim() || !newCompetitor.website.trim()}
                className="w-full"
              >
                <Plus className="h-4 w-4 mr-2" />
                Ajouter le concurrent
              </Button>
              {competitorsError && (
                <div className="text-sm text-red-600">{competitorsError}</div>
              )}
            </div>
          </div>

          <div className="flex justify-end space-x-3">
            <Button
              type="button"
              variant="ghost"
              onClick={() => setIsEditModalOpen(false)}
            >
              Annuler
            </Button>
            <Button
              type="submit"
              variant="primary"
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Modification...' : 'Modifier le projet'}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  )
} 