import React, { useState } from 'react'
import { Plus, Search, MessageSquare, AlertCircle, FolderOpen, Play, Edit2, Trash2, PlayCircle, Users, User, Upload } from 'lucide-react'
import { Button, Input, Modal, Loading, Badge, Table } from '../components/ui'
import { usePrompts } from '../hooks/usePrompts'
import { usePromptStats } from '../hooks/usePromptStats'
import { useCurrentProject } from '../contexts/ProjectContext'
import { AIModelsAPI } from '../services/aiModels'
import { PromptsAPI } from '../services/prompts'
import type { PromptCreate } from '../types/prompt'
import type { AIModel } from '../types/aiModel'
import { MultiSelect } from '../components/ui'

export const PromptsPage: React.FC = () => {
  const { currentProject } = useCurrentProject()
  const { prompts, loading, error, createPrompt, deletePrompt, executePrompt, refresh } = usePrompts()
  const { promptStats, loading: statsLoading } = usePromptStats(currentProject?.id)
  
  const [searchTerm, setSearchTerm] = useState('')
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)
  const [selectedPrompt, setSelectedPrompt] = useState<any>(null)
  const [isExecuting, setIsExecuting] = useState<string | null>(null)
  const [isCreating, setIsCreating] = useState(false)
  const [isExecutingAll, setIsExecutingAll] = useState(false)
  const [isImportOpen, setIsImportOpen] = useState(false)
  const [importText, setImportText] = useState('')
  const [importParsed, setImportParsed] = useState<any[] | null>(null)
  const [validateResult, setValidateResult] = useState<null | { success_count: number; error_count: number; results: Array<{ index: number; status: string; id?: string; errors?: string[] }> }>(null)
  const [isValidatingImport, setIsValidatingImport] = useState(false)
  const [isConfirmingImport, setIsConfirmingImport] = useState(false)
  const [upsertByName, setUpsertByName] = useState(true)
  const [importError, setImportError] = useState<string | null>(null)

  // Filtrage des prompts
  const filteredPrompts = prompts.filter(prompt =>
    prompt.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (prompt.description || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
    (prompt.tags || []).some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()))
  )

  const handleEdit = (prompt: any) => {
    setSelectedPrompt(prompt)
    setIsCreateModalOpen(true)
  }

  const handleDelete = async (promptId: string) => {
    if (window.confirm('Êtes-vous sûr de vouloir supprimer ce prompt ?')) {
      const success = await deletePrompt(promptId)
      if (success) {
        console.log('✅ Prompt supprimé avec succès')
      }
    }
  }

  const handleRun = async (prompt: any) => {
    if (!currentProject) {
      alert('Veuillez sélectionner un projet avant d\'exécuter un prompt')
      return
    }

    setIsExecuting(prompt.id)
    try {
      console.log('🚀 Exécution du prompt:', prompt.name)
      
      const result = await executePrompt(prompt.id, {
        custom_variables: {
          brand: currentProject.main_website || currentProject.name,
          sector: currentProject.description || 'secteur d\'activité',
          query: 'Recommandations générales'
        }
      })
      
      if (result?.success) {
        alert(`✅ Prompt exécuté avec succès !\nAnalyse créée : ${result.analysis_id}\nScore de visibilité : ${result.visibility_score}/100`)
      } else {
        alert('❌ Échec de l\'exécution du prompt. Vérifiez la console pour plus de détails.')
      }
    } catch (err) {
      console.error('❌ Erreur lors de l\'exécution:', err)
      alert('❌ Erreur lors de l\'exécution du prompt. Vérifiez la console pour plus de détails.')
    } finally {
      setIsExecuting(null)
    }
  }

  const handleRunAll = async () => {
    if (!currentProject) {
      alert('Veuillez sélectionner un projet avant d\'exécuter les prompts')
      return
    }

    const activePrompts = filteredPrompts.filter(prompt => prompt.is_active)
    
    if (activePrompts.length === 0) {
      alert('Aucun prompt actif à exécuter dans ce projet')
      return
    }

    const confirmMessage = `Êtes-vous sûr de vouloir exécuter tous les ${activePrompts.length} prompts actifs ?\n\nCela peut prendre plusieurs minutes et consommer des tokens IA.`
    if (!window.confirm(confirmMessage)) {
      return
    }

    setIsExecutingAll(true)
    let successCount = 0
    let errorCount = 0
    const results: string[] = []

    try {
      console.log(`🚀 Exécution en masse de ${activePrompts.length} prompts...`)
      
      for (const prompt of activePrompts) {
        try {
          console.log(`🔄 Exécution du prompt: ${prompt.name}`)
          
          const result = await executePrompt(prompt.id, {
            custom_variables: {
              brand: currentProject.main_website || currentProject.name,
              sector: currentProject.description || 'secteur d\'activité',
              query: 'Recommandations générales'
            }
          })
          
          if (result?.success) {
            successCount++
            results.push(`✅ ${prompt.name}: Score ${result.visibility_score || 'N/A'}/100`)
            console.log(`✅ ${prompt.name} exécuté avec succès`)
          } else {
            errorCount++
            results.push(`❌ ${prompt.name}: Échec`)
            console.error(`❌ Échec pour ${prompt.name}`)
          }
        } catch (err) {
          errorCount++
          results.push(`❌ ${prompt.name}: Erreur`)
          console.error(`❌ Erreur pour ${prompt.name}:`, err)
        }
        
        // Petit délai entre les exécutions pour éviter de surcharger l'API
        await new Promise(resolve => setTimeout(resolve, 1000))
      }

      // Afficher le résumé
      const summary = `🎯 Exécution terminée !\n\n✅ Réussis: ${successCount}\n❌ Échecs: ${errorCount}\n\n${results.join('\n')}`
      alert(summary)
      
    } catch (err) {
      console.error('❌ Erreur lors de l\'exécution en masse:', err)
      alert('❌ Erreur lors de l\'exécution en masse. Vérifiez la console pour plus de détails.')
    } finally {
      setIsExecutingAll(false)
    }
  }



  const handleCreatePrompt = async (formData: any) => {
    if (!currentProject) {
      alert('Veuillez sélectionner un projet avant de créer un prompt')
      return
    }

    setIsCreating(true)
    try {
      const promptData: PromptCreate = {
        name: formData.name,
        description: formData.description || '',
        template: formData.template || `Analysez {{query}} pour notre marque {{brand}}.`,
        tags: formData.tags || [],
        project_id: currentProject.id,
        is_active: true,
        // Mode détecté automatiquement
        is_multi_agent: formData.is_multi_agent,
        ai_model_id: formData.ai_model_id,
        ai_model_ids: formData.ai_model_ids
      }

      const newPrompt = await createPrompt(promptData)
      if (newPrompt) {
        setIsCreateModalOpen(false)
        setSelectedPrompt(null)
        console.log('✅ Prompt créé avec succès:', newPrompt.name)
        // Afficher un message selon le mode détecté
        if (formData.is_multi_agent) {
          alert(`✅ Prompt multi-agents créé avec succès !\nModèles sélectionnés : ${formData.ai_model_ids.length}`)
        } else {
          alert(`✅ Prompt créé avec succès !`)
        }
      }
    } catch (err) {
      console.error('❌ Erreur lors de la création:', err)
    } finally {
      setIsCreating(false)
    }
  }

  // Si aucun projet sélectionné
  if (!currentProject) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-8 text-center">
          <FolderOpen className="h-12 w-12 text-blue-600 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-blue-900 mb-2">
            Sélectionnez un projet pour voir vos prompts
          </h3>
          <p className="text-blue-700">
            Les prompts sont organisés par projet. Choisissez un projet dans le sélecteur en haut à droite.
          </p>
        </div>
      </div>
    )
  }

  // Enrichir les prompts avec les vraies statistiques
  const enrichedPrompts = filteredPrompts.map(prompt => {
    const stats = promptStats[prompt.id]
    return {
      ...prompt,
      visibility: stats?.avgVisibilityScore || 0,
      brandMentioned: stats?.lastAnalysis?.brand_mentioned || false,
      hasLink: stats?.lastAnalysis?.website_linked || false,
      competitors: stats?.avgCompetitorsMentioned || 0,
      aiModel: prompt.ai_model_name || 'N/A',
      totalAnalyses: stats?.totalAnalyses || 0,
      brandMentionRate: stats?.brandMentionRate || 0,
      websiteLinkRate: stats?.websiteLinkRate || 0
    }
  })

  const columns = [
    {
      key: 'name',
      label: 'Prompt',
      className: 'w-80 max-w-80',
      render: (prompt: any) => (
        <div className="flex items-center space-x-3">
          <MessageSquare className="h-4 w-4 text-gray-400 flex-shrink-0" />
          <div className="min-w-0 flex-1">
            <div 
              className="font-medium text-gray-900 truncate" 
              title={prompt.name}
            >
              {prompt.name}
            </div>
            {prompt.description && (
              <div 
                className="text-sm text-gray-500 truncate" 
                title={prompt.description}
              >
                {prompt.description}
              </div>
            )}
          </div>
        </div>
      )
    },
    {
      key: 'visibility',
      label: 'Visibilité',
      className: 'w-24 text-center',
      render: (prompt: any) => (
        <div className="text-center">
          {prompt.totalAnalyses > 0 ? (
            <>
              <div className="text-lg font-semibold text-gray-900">
                {prompt.visibility}%
              </div>
              <div className={`text-xs ${
                prompt.visibility >= 50 ? 'text-green-600' : 
                prompt.visibility >= 30 ? 'text-orange-600' : 'text-red-600'
              }`}>
                {prompt.visibility >= 50 ? 'Élevée' : 
                 prompt.visibility >= 30 ? 'Moyenne' : 'Faible'}
              </div>
            </>
          ) : (
            <>
              <div className="text-lg font-semibold text-gray-400">
                -
              </div>
              <div className="text-xs text-gray-400">
                Aucune analyse
              </div>
            </>
          )}
        </div>
      )
    },
    {
      key: 'brandMentioned',
      label: 'Marque',
      className: 'w-24 text-center',
      render: (prompt: any) => (
        <div className="flex items-center justify-center">
          {prompt.totalAnalyses > 0 ? (
            prompt.brandMentioned ? (
              <Badge variant="success" size="sm">✓ Citée</Badge>
            ) : (
              <Badge variant="error" size="sm">✗ Non citée</Badge>
            )
          ) : (
            <Badge variant="default" size="sm" className="text-gray-400">- N/A</Badge>
          )}
        </div>
      )
    },
    {
      key: 'hasLink',
      label: 'Lien',
      className: 'w-20 text-center',
      render: (prompt: any) => (
        <div className="flex items-center justify-center">
          {prompt.totalAnalyses > 0 ? (
            prompt.hasLink ? (
              <Badge variant="info" size="sm">🔗 Oui</Badge>
            ) : (
              <Badge variant="default" size="sm">- Non</Badge>
            )
          ) : (
            <Badge variant="default" size="sm" className="text-gray-400">- N/A</Badge>
          )}
        </div>
      )
    },
    {
      key: 'competitors',
      label: 'Concurrents',
      className: 'w-28 text-center',
      render: (prompt: any) => (
        <div className="flex items-center justify-center">
          {prompt.totalAnalyses > 0 ? (
            <Badge variant="default" size="sm">
              {prompt.competitors.toFixed(1)}
            </Badge>
          ) : (
            <Badge variant="default" size="sm" className="text-gray-400">
              - N/A
            </Badge>
          )}
        </div>
      )
    },
    {
      key: 'tags',
      label: 'Tags',
      className: 'w-32',
      render: (prompt: any) => (
        <div className="flex flex-wrap gap-1 max-w-32">
          {prompt.tags && prompt.tags.length > 0 ? (
            prompt.tags.slice(0, 2).map((tag: string, index: number) => (
              <Badge key={index} variant="info" size="sm" className="text-xs">
                {tag}
              </Badge>
            ))
          ) : (
            <span className="text-gray-400 text-sm">-</span>
          )}
          {prompt.tags && prompt.tags.length > 2 && (
            <Badge variant="default" size="sm" className="text-xs">
              +{prompt.tags.length - 2}
            </Badge>
          )}
        </div>
      )
    },
    {
      key: 'aiModel',
      label: 'Modèle',
      className: 'w-36',
      render: (prompt: any) => (
        <div title={prompt.aiModel}>
          <Badge variant="default" size="sm">
            <span className="truncate max-w-32">
              {prompt.aiModel}
            </span>
          </Badge>
        </div>
      )
    },
    {
      key: 'created',
      label: 'Créé',
      className: 'w-24',
      render: (prompt: any) => (
        <div className="text-sm text-gray-500">
          {new Date(prompt.created_at).toLocaleDateString('fr-FR')}
        </div>
      )
    },
    {
      key: 'actions',
      label: 'Actions',
      className: 'w-32',
      render: (prompt: any) => (
        <div className="flex items-center space-x-1">
          <Button
            variant="primary"
            size="sm"
            onClick={() => handleRun(prompt)}
            disabled={isExecuting === prompt.id}
            className="h-8 w-8 p-0"
            title="Exécuter le prompt"
          >
            {isExecuting === prompt.id ? (
              <div className="animate-spin h-3 w-3 border-2 border-white border-t-transparent rounded-full" />
            ) : (
              <Play className="h-3 w-3" />
            )}
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => handleEdit(prompt)}
            className="h-8 w-8 p-0"
            title="Modifier"
          >
            <Edit2 className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => handleDelete(prompt.id)}
            className="h-8 w-8 p-0 text-red-600 hover:text-red-700"
            title="Supprimer"
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      )
    }
  ]

  return (
    <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Prompts</h1>
          <p className="text-gray-600 mt-2">
            {currentProject 
              ? `Templates de prompts pour ${currentProject.name}`
              : 'Sélectionnez un projet pour voir vos prompts'
            }
          </p>
        </div>
        {currentProject && (
          <div className="flex items-center space-x-3">
            <Button
              variant="outline"
              onClick={() => setIsImportOpen(true)}
              className="flex items-center space-x-2"
            >
              <Upload className="h-4 w-4" />
              <span>Importer</span>
            </Button>
            <Button
              variant="outline"
              onClick={handleRunAll}
              disabled={isExecutingAll || filteredPrompts.filter(p => p.is_active).length === 0}
              className="flex items-center space-x-2"
            >
              {isExecutingAll ? (
                <>
                  <div className="animate-spin h-4 w-4 border-2 border-blue-600 border-t-transparent rounded-full" />
                  <span>Exécution...</span>
                </>
              ) : (
                <>
                  <PlayCircle className="h-4 w-4" />
                  <span>Exécuter tous ({filteredPrompts.filter(p => p.is_active).length})</span>
                </>
              )}
            </Button>
            <Button
              variant="primary"
              onClick={() => {
                setSelectedPrompt(null)
                setIsCreateModalOpen(true)
              }}
              className="flex items-center space-x-2"
            >
              <Plus className="h-4 w-4" />
              <span>Nouveau Prompt</span>
            </Button>
          </div>
        )}
      </div>

      {/* Erreur */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <div className="flex items-start space-x-3">
            <AlertCircle className="h-5 w-5 text-red-600 mt-0.5" />
            <div>
              <h4 className="font-medium text-red-900">Erreur de chargement</h4>
              <p className="text-red-700 text-sm mt-1">{error}</p>
              <Button variant="outline" size="sm" onClick={refresh} className="mt-2">
                Réessayer
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Barre de recherche et stats */}
      <div className="mb-6 space-y-4">
        <div className="flex items-center justify-between">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              placeholder="Rechercher des prompts..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
          <div className="text-sm text-gray-500">
            {filteredPrompts.length} de {prompts.length} prompts
          </div>
        </div>

        {/* Stats rapides */}
        <div className="flex items-center space-x-6 text-sm">
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
            <span className="text-gray-600">Actifs: {prompts.filter(p => p.is_active).length}</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-green-500 rounded-full"></div>
            <span className="text-gray-600">Exécutions: {prompts.reduce((sum, p) => sum + (p.execution_count || 0), 0)}</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
            <span className="text-gray-600">Tags: {[...new Set(prompts.flatMap(p => p.tags || []))].length}</span>
          </div>
        </div>
      </div>

      {/* Contenu principal */}
      {loading || statsLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loading size="lg" text={loading ? "Chargement des prompts..." : "Chargement des statistiques..."} />
        </div>
      ) : (
        <>
          {/* Tableau des prompts */}
          {filteredPrompts.length > 0 ? (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
              <div className="overflow-x-auto">
                <Table 
                  data={enrichedPrompts} 
                  columns={columns}
                  className="min-w-full"
                />
              </div>
            </div>
          ) : (
            /* État vide */
            <div className="text-center py-12">
              <MessageSquare className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                {searchTerm ? 'Aucun prompt trouvé' : 'Aucun prompt pour ce projet'}
              </h3>
              <p className="text-gray-600 mb-4">
                {searchTerm 
                  ? 'Aucun prompt ne correspond à votre recherche.' 
                  : 'Commencez par créer votre premier prompt pour ce projet.'
                }
              </p>
              {!searchTerm && (
                <Button
                  variant="primary"
                  onClick={() => setIsCreateModalOpen(true)}
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Créer un prompt
                </Button>
              )}
            </div>
          )}
        </>
      )}

      {/* Modal de création/édition */}
      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => {
          setIsCreateModalOpen(false)
          setSelectedPrompt(null)
        }}
        title={selectedPrompt ? 'Modifier le prompt' : 'Nouveau prompt'}
        size="lg"
      >
        <PromptForm
          prompt={selectedPrompt}
          onSubmit={handleCreatePrompt}
          onCancel={() => {
            setIsCreateModalOpen(false)
            setSelectedPrompt(null)
          }}
          isLoading={isCreating}
        />
      </Modal>

      {/* Modal d'import */}
      <Modal
        isOpen={isImportOpen}
        onClose={() => {
          setIsImportOpen(false)
          setImportText('')
          setImportParsed(null)
          setValidateResult(null)
          setImportError(null)
        }}
        title="Importer des prompts (JSON)"
        size="lg"
      >
        <div className="space-y-4">
          {!currentProject && (
            <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 rounded-lg p-3 text-sm">
              Sélectionnez un projet pour associer automatiquement les prompts importés.
            </div>
          )}

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="block text-sm font-medium text-gray-700">
                Collez un JSON d'items (array d'objets)
              </label>
              <label className="inline-flex items-center gap-2 text-sm text-gray-700">
                <input
                  type="checkbox"
                  className="rounded border-gray-300"
                  checked={upsertByName}
                  onChange={(e) => setUpsertByName(e.target.checked)}
                />
                Mettre à jour si même nom (upsert)
              </label>
            </div>
            <textarea
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
              rows={12}
              placeholder={`[
  {
    "name": "Audit SEO technique",
    "template": "Analyse {{query}} pour {{brand}}",
    "description": "Audit rapide",
    "tags": ["seo","audit"],
    "is_active": true,
    "ai_model_identifier": "gpt-5"
  }
]`}
              value={importText}
              onChange={(e) => {
                setImportText(e.target.value)
                setValidateResult(null)
                setImportParsed(null)
                setImportError(null)
              }}
            />
            <div className="text-xs text-gray-500">
              Champs supportés:
              name, template, description, tags, is_active, is_multi_agent,
              ai_model_identifier (préféré), ai_model_identifiers[], ai_model_name, ai_model_names[],
              ai_model_id, ai_model_ids. Le project_id actuel sera appliqué automatiquement si absent.
            </div>
          </div>

          {importError && (
            <div className="bg-red-50 border border-red-200 text-red-800 rounded-lg p-3 text-sm">
              {importError}
            </div>
          )}

          {importParsed && (
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 text-sm">
              <div className="flex items-center justify-between mb-2">
                <div className="font-medium text-gray-700">Prévisualisation</div>
                <div className="text-gray-600">{importParsed.length} items</div>
              </div>
              <div className="max-h-48 overflow-auto text-gray-700">
                <pre className="text-xs whitespace-pre-wrap">{JSON.stringify(importParsed.slice(0, 5), null, 2)}{importParsed.length > 5 ? '\n... (tronqué)' : ''}</pre>
              </div>
            </div>
          )}

          {validateResult && (
            <div className="bg-white border border-gray-200 rounded-lg p-3 text-sm">
              <div className="font-medium text-gray-800 mb-2">Validation</div>
              <div className="flex items-center gap-4 text-gray-700">
                <span>Valides: <span className="font-semibold text-green-600">{validateResult.success_count}</span></span>
                <span>Erreurs: <span className="font-semibold text-red-600">{validateResult.error_count}</span></span>
              </div>
              {validateResult.error_count > 0 && (
                <div className="mt-2 max-h-40 overflow-auto text-xs">
                  <ul className="list-disc pl-5 space-y-1">
                    {validateResult.results.filter(r => r.status === 'error').slice(0, 20).map((r, idx) => (
                      <li key={idx} className="text-red-700">
                        Item #{r.index + 1}: {(r.errors || []).join('; ')}
                      </li>
                    ))}
                    {validateResult.error_count > 20 && (
                      <li className="text-gray-500">... (plus d'erreurs non affichées)</li>
                    )}
                  </ul>
                </div>
              )}
            </div>
          )}

          <div className="flex justify-end gap-2 pt-2">
            <Button
              variant="secondary"
              onClick={() => {
                setIsImportOpen(false)
                setImportText('')
                setImportParsed(null)
                setValidateResult(null)
                setImportError(null)
              }}
            >
              Fermer
            </Button>
            <Button
              variant="outline"
              disabled={isValidatingImport}
              onClick={async () => {
                try {
                  setIsValidatingImport(true)
                  setValidateResult(null)
                  setImportError(null)

                  let data: any
                  try {
                    data = JSON.parse(importText)
                  } catch (e) {
                    throw new Error('JSON invalide')
                  }

                  const itemsArray: any[] = Array.isArray(data) ? data : (Array.isArray(data.items) ? data.items : [])
                  if (!Array.isArray(itemsArray) || itemsArray.length === 0) {
                    throw new Error('Le JSON doit être un tableau d\'items ou un objet avec une clé "items" non vide')
                  }

                  // Appliquer project_id et nettoyage minimal
                  const normalized = itemsArray.map((it) => ({
                    project_id: currentProject?.id || it.project_id,
                    name: it.name,
                    template: it.template,
                    description: it.description,
                    tags: it.tags,
                    is_active: it.is_active !== false,
                    is_multi_agent: it.is_multi_agent,
                    // Support IDs, names et identifiers
                    ai_model_id: it.ai_model_id,
                    ai_model_ids: it.ai_model_ids,
                    ai_model_name: it.ai_model_name,
                    ai_model_names: it.ai_model_names,
                    ai_model_identifier: it.ai_model_identifier,
                    ai_model_identifiers: it.ai_model_identifiers
                  }))
                  if (normalized.some(it => !it.project_id || !it.name || !it.template)) {
                    throw new Error('Chaque item doit contenir au moins project_id, name et template')
                  }

                  setImportParsed(normalized)
                  const res: any = await PromptsAPI.bulkImport({
                    validate_only: true,
                    upsert_by: upsertByName ? 'name' : null,
                    items: normalized
                  })
                  setValidateResult(res)
                } catch (err: any) {
                  setImportError(err?.message || 'Erreur lors de la validation')
                } finally {
                  setIsValidatingImport(false)
                }
              }}
            >
              {isValidatingImport ? 'Validation…' : 'Valider (dry‑run)'}
            </Button>
            <Button
              disabled={!validateResult || validateResult.error_count > 0 || isConfirmingImport}
              onClick={async () => {
                try {
                  if (!importParsed) return
                  setIsConfirmingImport(true)
                  const res: any = await PromptsAPI.bulkImport({
                    validate_only: false,
                    upsert_by: upsertByName ? 'name' : null,
                    items: importParsed
                  })
                  alert(`✅ Import terminé: ${res.success_count} succès, ${res.error_count} erreurs`)
                  setIsImportOpen(false)
                  setImportText('')
                  setImportParsed(null)
                  setValidateResult(null)
                  setImportError(null)
                  await refresh()
                } catch (err: any) {
                  setImportError(err?.message || 'Erreur lors de l\'import')
                } finally {
                  setIsConfirmingImport(false)
                }
              }}
            >
              {isConfirmingImport ? 'Import…' : 'Importer'}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}

// Composant formulaire pour créer/éditer un prompt (mode automatique selon sélection)
const PromptForm: React.FC<{
  prompt?: any
  onSubmit: (data: any) => void
  onCancel: () => void
  isLoading: boolean
}> = ({ prompt, onSubmit, onCancel, isLoading }) => {
  const [aiModels, setAiModels] = useState<AIModel[]>([])
  const [loadingModels, setLoadingModels] = useState(true)
  const [formData, setFormData] = useState({
    name: prompt?.name || '',
    description: prompt?.description || '',
    template: prompt?.template || 'Analysez {{query}} pour notre marque {{brand}}.',
    tags: prompt?.tags?.join(', ') || '',
    ai_model_ids: prompt?.ai_model_ids || []
  })

  // Charger les modèles IA disponibles
  React.useEffect(() => {
    const loadAiModels = async () => {
      try {
        setLoadingModels(true)
        const models = await AIModelsAPI.getActive()
        setAiModels(models)
        
        // Initialiser avec le premier modèle si aucune sélection
        if (!prompt && models.length > 0 && formData.ai_model_ids.length === 0) {
          setFormData(prev => ({ 
            ...prev, 
            ai_model_ids: [models[0].id]
          }))
        } else if (prompt) {
          // Charger les modèles existants pour un prompt en édition
          if (prompt.is_multi_agent && prompt.ai_models) {
            const activeModelIds = prompt.ai_models
              .filter((pm: any) => pm.is_active)
              .map((pm: any) => pm.ai_model_id)
            setFormData(prev => ({ 
              ...prev, 
              ai_model_ids: activeModelIds
            }))
          } else if (prompt.ai_model_id) {
            // Prompt mono-agent existant
            setFormData(prev => ({ 
              ...prev, 
              ai_model_ids: [prompt.ai_model_id]
            }))
          }
        }
      } catch (error) {
        console.error('❌ Erreur lors du chargement des modèles IA:', error)
      } finally {
        setLoadingModels(false)
      }
    }
    
    loadAiModels()
  }, [prompt])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    
    // Validation
    if (formData.ai_model_ids.length === 0) {
      alert('Veuillez sélectionner au moins un modèle IA')
      return
    }
    
    // Détection automatique du mode
    const isMultiAgent = formData.ai_model_ids.length > 1
    
    onSubmit({
      ...formData,
      is_multi_agent: isMultiAgent,
      ai_model_id: isMultiAgent ? undefined : formData.ai_model_ids[0],
      ai_model_ids: isMultiAgent ? formData.ai_model_ids : undefined,
      tags: formData.tags.split(',').map((tag: string) => tag.trim()).filter(Boolean)
    })
  }

  const aiModelOptions = aiModels.map(model => ({
    id: model.id,
    name: model.name,
    description: `${model.provider} - $${model.cost_per_1k_tokens}/1k tokens`
  }))

  const isMultiAgent = formData.ai_model_ids.length > 1

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <Input
        label="Nom du prompt"
        value={formData.name}
        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
        required
      />
      
      <Input
        label="Description (optionnel)"
        value={formData.description}
        onChange={(e) => setFormData({ ...formData, description: e.target.value })}
      />

      {/* Sélection des modèles IA */}
      {loadingModels ? (
        <div className="flex items-center space-x-2 p-4 border border-gray-300 rounded-lg">
          <Loading size="sm" />
          <span className="text-sm text-gray-500">Chargement des modèles...</span>
        </div>
      ) : (
        <div>
          <MultiSelect
            label="Modèles IA *"
            options={aiModelOptions}
            selectedIds={formData.ai_model_ids}
            onChange={(ids: string[]) => setFormData({ ...formData, ai_model_ids: ids })}
            placeholder="Sélectionner les modèles IA"
          />
          
          {/* Indication du mode détecté */}
          <div className="mt-2 text-sm text-gray-600">
            {isMultiAgent ? (
              <div className="flex items-center space-x-1">
                <Users className="h-4 w-4 text-purple-600" />
                <span>Mode multi-agents détecté ({formData.ai_model_ids.length} modèles)</span>
              </div>
            ) : (
              <div className="flex items-center space-x-1">
                <User className="h-4 w-4 text-green-600" />
                <span>Mode modèle unique</span>
              </div>
            )}
          </div>
        </div>
      )}
      
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Template du prompt
        </label>
        <textarea
          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
          rows={6}
          value={formData.template}
          onChange={(e) => setFormData({ ...formData, template: e.target.value })}
          placeholder="Utilisez {{variable}} pour les variables dynamiques"
          required
        />
      </div>
      
      <Input
        label="Tags (séparés par des virgules)"
        value={formData.tags}
        onChange={(e) => setFormData({ ...formData, tags: e.target.value })}
        placeholder="seo, analyse, recommandation"
      />

      <div className="flex justify-end space-x-3 pt-4">
        <Button 
          type="button" 
          variant="secondary" 
          onClick={onCancel}
          disabled={isLoading}
        >
          Annuler
        </Button>
        <Button 
          type="submit" 
          disabled={isLoading}
        >
          {isLoading ? 'Sauvegarde...' : 'Sauvegarder'}
        </Button>
      </div>
    </form>
  )
} 