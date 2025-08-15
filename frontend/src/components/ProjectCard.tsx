import React from 'react'
import { Eye, Globe, Calendar } from 'lucide-react'
import { Button } from './ui/Button'

interface Project {
  id: string | number
  name: string
  main_website: string
  description?: string
  keywords: string[]
  created_at: string
  updated_at: string
}

interface ProjectCardProps {
  project: Project
  onEdit?: (project: Project) => void
  onDelete?: (project: Project) => void
  onAnalyze?: (project: Project) => void
}

export const ProjectCard: React.FC<ProjectCardProps> = ({
  project,
  onEdit,
  onDelete,
  onAnalyze
}) => {
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('fr-FR')
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-3">
          <Eye className="h-6 w-6 text-blue-600" />
          <h3 className="text-lg font-semibold text-gray-900">
            {project.name}
          </h3>
        </div>
        <div className="flex space-x-2">
          {onEdit && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onEdit(project)}
            >
              Modifier
            </Button>
          )}
          {onDelete && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onDelete(project)}
              className="text-red-600 hover:text-red-700"
            >
              Supprimer
            </Button>
          )}
        </div>
      </div>

      {/* Website */}
      <div className="flex items-center space-x-2 mb-3">
        <Globe className="h-4 w-4 text-gray-500" />
        <a
          href={project.main_website}
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-600 hover:text-blue-800 text-sm"
        >
          {project.main_website}
        </a>
      </div>

      {/* Description */}
      {project.description && (
        <p className="text-gray-600 text-sm mb-4 line-clamp-2">
          {project.description}
        </p>
      )}

      {/* Keywords */}
      {project.keywords.length > 0 && (
        <div className="mb-4">
          <div className="flex flex-wrap gap-1">
            {project.keywords.slice(0, 3).map((keyword, index) => (
              <span
                key={index}
                className="inline-block bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded"
              >
                {keyword}
              </span>
            ))}
            {project.keywords.length > 3 && (
              <span className="text-xs text-gray-500 px-2 py-1">
                +{project.keywords.length - 3} autres
              </span>
            )}
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between pt-4 border-t border-gray-200">
        <div className="flex items-center space-x-1 text-xs text-gray-500">
          <Calendar className="h-3 w-3" />
          <span>Créé le {formatDate(project.created_at)}</span>
        </div>
        
        {onAnalyze && (
          <Button
            variant="primary"
            size="sm"
            onClick={() => onAnalyze(project)}
          >
            Analyser
          </Button>
        )}
      </div>
    </div>
  )
} 