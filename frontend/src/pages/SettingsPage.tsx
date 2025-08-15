import React, { useState } from 'react'
import { Key, Save, Eye, EyeOff, AlertCircle, CheckCircle, RefreshCw, Plus, Trash2 } from 'lucide-react'
import { Button, Input, Card, Badge, Loading, Modal } from '../components/ui'
import { useAIModels } from '../hooks/useAIModels'
import type { AIModelCreate, AIModelUpdate } from '../types/aiModel'

export const SettingsPage: React.FC = () => {
  const { models, loading, error, createModel, updateModel, deleteModel, toggleModel, refresh } = useAIModels()
  
  const [showKeys, setShowKeys] = useState<{[key: string]: boolean}>({})
  const [isAddingModel, setIsAddingModel] = useState(false)
  const [isEditingModel, setIsEditingModel] = useState<string | null>(null)
  const [saved, setSaved] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  
  // Formulaire pour nouveau modèle
  const [newModel, setNewModel] = useState<AIModelCreate>({
    name: '',
    provider: 'openai',
    model_identifier: '',
    max_tokens: 4096,
    cost_per_1k_tokens: 0.03,
    is_active: true
  })

  // Formulaire pour édition
  const [editModel, setEditModel] = useState<AIModelUpdate>({})

  const toggleKeyVisibility = (modelId: string) => {
    setShowKeys(prev => ({ ...prev, [modelId]: !prev[modelId] }))
  }

  const handleToggleStatus = async (modelId: string) => {
    const result = await toggleModel(modelId)
    if (result) {
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    }
  }

  const handleAddModel = async () => {
    if (!newModel.name || !newModel.model_identifier) return

    setSubmitting(true)
    try {
      const result = await createModel(newModel)
      if (result) {
        setNewModel({
          name: '',
          provider: 'openai',
          model_identifier: '',
          max_tokens: 4096,
          cost_per_1k_tokens: 0.03,
          is_active: true
        })
        setIsAddingModel(false)
        setSaved(true)
        setTimeout(() => setSaved(false), 2000)
      }
    } finally {
      setSubmitting(false)
    }
  }

  const handleEditModel = async (modelId: string) => {
    if (!editModel || Object.keys(editModel).length === 0) return

    setSubmitting(true)
    try {
      const result = await updateModel(modelId, editModel)
      if (result) {
        setEditModel({})
        setIsEditingModel(null)
        setSaved(true)
        setTimeout(() => setSaved(false), 2000)
      }
    } finally {
      setSubmitting(false)
    }
  }

  const handleDeleteModel = async (modelId: string, modelName: string) => {
    if (!confirm(`Êtes-vous sûr de vouloir supprimer le modèle "${modelName}" ?\n\nCette action est irréversible et supprimera toutes les analyses associées.`)) {
      return
    }

    const result = await deleteModel(modelId)
    if (result) {
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    }
  }

  const startEditModel = (modelId: string) => {
    const model = models.find(m => m.id === modelId)
    if (model) {
      setEditModel({
        name: model.name,
        model_identifier: model.model_identifier,
        max_tokens: model.max_tokens,
        cost_per_1k_tokens: model.cost_per_1k_tokens,
        is_active: model.is_active
      })
      setIsEditingModel(modelId)
    }
  }

  const cancelEdit = () => {
    setEditModel({})
    setIsEditingModel(null)
  }

  const cancelAdd = () => {
    setNewModel({
      name: '',
      provider: 'openai',
      model_identifier: '',
      max_tokens: 4096,
      cost_per_1k_tokens: 0.03,
      is_active: true
    })
    setIsAddingModel(false)
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('fr-FR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const maskKey = (key: string) => {
    if (key.length <= 12) return key
    return key.substring(0, 8) + '...' + key.substring(key.length - 4)
  }

  const getProviderIcon = (provider: string) => {
    switch (provider.toLowerCase()) {
      case 'openai': return '🤖'
      case 'anthropic': return '🧠'
      case 'google': return '💎'
      case 'mistral': return '🌪️'
      default: return '🔮'
    }
  }

  const getProviderColor = (provider: string) => {
    switch (provider.toLowerCase()) {
      case 'openai': return 'bg-green-100 text-green-800'
      case 'anthropic': return 'bg-orange-100 text-orange-800'
      case 'google': return 'bg-blue-100 text-blue-800'
      case 'mistral': return 'bg-purple-100 text-purple-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  if (loading && models.length === 0) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loading size="lg" text="Chargement des paramètres..." />
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-gray-50 min-h-screen">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center">
            <div className="text-red-600 text-xl mb-4">❌ Erreur</div>
            <p className="text-gray-600 mb-4">{error}</p>
            <Button onClick={refresh} variant="primary">
              <RefreshCw className="h-4 w-4 mr-2" />
              Réessayer
            </Button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-gray-50 min-h-screen">
      {/* Header */}
      <div className="bg-white shadow-sm border-b sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Paramètres</h1>
              <p className="text-sm text-gray-600">Configuration des modèles IA et paramètres</p>
            </div>
            
            <div className="flex items-center space-x-2">
              <Button
                variant="ghost"
                onClick={refresh}
                disabled={loading}
              >
                <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                Actualiser
              </Button>
              
              <Button
                variant={saved ? "primary" : "primary"}
                disabled={submitting}
                className={saved ? "bg-green-600 hover:bg-green-700" : ""}
              >
                {saved ? (
                  <>
                    <CheckCircle className="h-4 w-4 mr-2" />
                    Sauvegardé
                  </>
                ) : (
                  <>
                    <Save className="h-4 w-4 mr-2" />
                    Auto-sauvegarde
                  </>
                )}
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Contenu principal */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Section Modèles IA */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-lg font-semibold text-gray-900 flex items-center space-x-2">
                <Key className="h-5 w-5" />
                <span>Modèles IA</span>
              </h2>
              <p className="text-sm text-gray-600 mt-1">
                Gérez vos modèles IA et leurs configurations
              </p>
            </div>
            
            <Button
              variant="primary"
              onClick={() => setIsAddingModel(true)}
              disabled={submitting}
            >
              <Plus className="h-4 w-4 mr-2" />
              Ajouter un modèle
            </Button>
          </div>

          {/* Statistiques rapides */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="bg-white p-4 rounded-lg border border-gray-200">
              <div className="text-2xl font-bold text-gray-900">{models.length}</div>
              <div className="text-sm text-gray-600">Modèles configurés</div>
            </div>
            <div className="bg-white p-4 rounded-lg border border-gray-200">
              <div className="text-2xl font-bold text-green-600">
                {models.filter(m => m.is_active).length}
              </div>
              <div className="text-sm text-gray-600">Modèles actifs</div>
            </div>
            <div className="bg-white p-4 rounded-lg border border-gray-200">
              <div className="text-2xl font-bold text-blue-600">
                {[...new Set(models.map(m => m.provider))].length}
              </div>
              <div className="text-sm text-gray-600">Fournisseurs</div>
            </div>
          </div>

          {/* Liste des modèles IA */}
          <div className="space-y-4">
            {models.map((model) => (
              <Card key={model.id} className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-3">
                    <div className="text-2xl">{getProviderIcon(model.provider)}</div>
                    <div className={`w-3 h-3 rounded-full ${
                      model.is_active ? 'bg-green-500' : 'bg-gray-400'
                    }`} />
                    <div>
                      <h3 className="font-medium text-gray-900">{model.name}</h3>
                      <div className="flex items-center space-x-2 mt-1">
                        <Badge variant="default" size="sm" className={getProviderColor(model.provider)}>
                          {model.provider}
                        </Badge>
                        <Badge variant={model.is_active ? 'success' : 'default'} size="sm">
                          {model.is_active ? 'Actif' : 'Inactif'}
                        </Badge>
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => toggleKeyVisibility(model.id)}
                    >
                      {showKeys[model.id] ? (
                        <EyeOff className="h-4 w-4" />
                      ) : (
                        <Eye className="h-4 w-4" />
                      )}
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => startEditModel(model.id)}
                      disabled={submitting}
                    >
                      Modifier
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleToggleStatus(model.id)}
                      disabled={submitting}
                    >
                      {model.is_active ? 'Désactiver' : 'Activer'}
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDeleteModel(model.id, model.name)}
                      className="text-red-600 hover:text-red-700"
                      disabled={submitting}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>

                {/* Identifiant du modèle */}
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Identifiant du modèle
                  </label>
                  <div className="font-mono text-sm bg-gray-50 p-2 rounded border">
                    {showKeys[model.id] ? model.model_identifier : maskKey(model.model_identifier)}
                  </div>
                </div>

                {/* Informations techniques */}
                <div className="grid grid-cols-3 gap-4 pt-4 border-t border-gray-200">
                  <div className="text-center">
                    <div className="text-lg font-bold text-gray-900">
                      {model.max_tokens.toLocaleString()}
                    </div>
                    <div className="text-xs text-gray-600">Tokens max</div>
                  </div>
                  <div className="text-center">
                    <div className="text-lg font-bold text-gray-900">
                      ${model.cost_per_1k_tokens.toFixed(4)}
                    </div>
                    <div className="text-xs text-gray-600">Coût/1k tokens</div>
                  </div>
                  <div className="text-center">
                    <div className="text-sm text-gray-900">
                      {formatDate(model.updated_at)}
                    </div>
                    <div className="text-xs text-gray-600">Dernière MAJ</div>
                  </div>
                </div>
              </Card>
            ))}
          </div>

          {models.length === 0 && (
            <div className="text-center py-12">
              <Key className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                Aucun modèle IA configuré
              </h3>
              <p className="text-gray-600 mb-4">
                Ajoutez votre premier modèle IA pour commencer à utiliser l'application.
              </p>
              <Button
                variant="primary"
                onClick={() => setIsAddingModel(true)}
              >
                <Plus className="h-4 w-4 mr-2" />
                Ajouter un modèle
              </Button>
            </div>
          )}
        </div>

        {/* Avertissement de sécurité */}
        <Card className="p-4 bg-yellow-50 border-yellow-200">
          <div className="flex items-start space-x-3">
            <AlertCircle className="h-5 w-5 text-yellow-600 mt-0.5" />
            <div>
              <h3 className="font-medium text-yellow-800">Configuration des modèles IA</h3>
              <p className="text-sm text-yellow-700 mt-1">
                Les modèles IA sont stockés de manière sécurisée en base de données. 
                Assurez-vous que les identifiants et coûts sont corrects avant d'activer un modèle.
                Les modèles inactifs ne seront pas disponibles pour les analyses.
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* Modal d'ajout de modèle */}
      <Modal
        isOpen={isAddingModel}
        onClose={cancelAdd}
        title="Ajouter un nouveau modèle IA"
        size="lg"
      >
        <div className="space-y-4">
          <Input
            label="Nom du modèle"
            placeholder="Ex: GPT-4 Turbo"
            value={newModel.name}
            onChange={(e) => setNewModel(prev => ({ ...prev, name: e.target.value }))}
          />
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Fournisseur
            </label>
                         <select
               value={newModel.provider}
               onChange={(e) => setNewModel(prev => ({ ...prev, provider: e.target.value as any }))}
               className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
             >
               <option value="openai">OpenAI</option>
               <option value="anthropic">Anthropic (Claude)</option>
               <option value="google">Google (Gemini)</option>
               <option value="mistral">Mistral AI</option>
             </select>
          </div>
          
          <Input
            label="Identifiant du modèle"
            placeholder="Ex: gpt-4-turbo-preview"
            value={newModel.model_identifier}
            onChange={(e) => setNewModel(prev => ({ ...prev, model_identifier: e.target.value }))}
          />

          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Tokens maximum"
              type="number"
              value={newModel.max_tokens.toString()}
              onChange={(e) => setNewModel(prev => ({ ...prev, max_tokens: parseInt(e.target.value) || 4096 }))}
            />
            
            <Input
              label="Coût par 1000 tokens ($)"
              type="number"
              step="0.0001"
              value={newModel.cost_per_1k_tokens.toString()}
              onChange={(e) => setNewModel(prev => ({ ...prev, cost_per_1k_tokens: parseFloat(e.target.value) || 0.03 }))}
            />
          </div>

          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              id="is_active"
              checked={newModel.is_active}
              onChange={(e) => setNewModel(prev => ({ ...prev, is_active: e.target.checked }))}
              className="h-4 w-4 text-blue-600 rounded border-gray-300"
            />
            <label htmlFor="is_active" className="text-sm text-gray-700">
              Activer ce modèle immédiatement
            </label>
          </div>
          
          <div className="flex space-x-3 pt-4">
            <Button
              variant="primary"
              onClick={handleAddModel}
              disabled={!newModel.name || !newModel.model_identifier || submitting}
            >
              {submitting ? 'Ajout...' : 'Ajouter'}
            </Button>
            <Button
              variant="outline"
              onClick={cancelAdd}
              disabled={submitting}
            >
              Annuler
            </Button>
          </div>
        </div>
      </Modal>

      {/* Modal d'édition de modèle */}
      <Modal
        isOpen={isEditingModel !== null}
        onClose={cancelEdit}
        title="Modifier le modèle IA"
        size="lg"
      >
        {isEditingModel && (
          <div className="space-y-4">
            <Input
              label="Nom du modèle"
              value={editModel.name || ''}
              onChange={(e) => setEditModel(prev => ({ ...prev, name: e.target.value }))}
            />
            
            <Input
              label="Identifiant du modèle"
              value={editModel.model_identifier || ''}
              onChange={(e) => setEditModel(prev => ({ ...prev, model_identifier: e.target.value }))}
            />

            <div className="grid grid-cols-2 gap-4">
              <Input
                label="Tokens maximum"
                type="number"
                value={editModel.max_tokens?.toString() || ''}
                onChange={(e) => setEditModel(prev => ({ ...prev, max_tokens: parseInt(e.target.value) || undefined }))}
              />
              
              <Input
                label="Coût par 1000 tokens ($)"
                type="number"
                step="0.0001"
                value={editModel.cost_per_1k_tokens?.toString() || ''}
                onChange={(e) => setEditModel(prev => ({ ...prev, cost_per_1k_tokens: parseFloat(e.target.value) || undefined }))}
              />
            </div>

            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="edit_is_active"
                checked={editModel.is_active || false}
                onChange={(e) => setEditModel(prev => ({ ...prev, is_active: e.target.checked }))}
                className="h-4 w-4 text-blue-600 rounded border-gray-300"
              />
              <label htmlFor="edit_is_active" className="text-sm text-gray-700">
                Modèle actif
              </label>
            </div>
            
            <div className="flex space-x-3 pt-4">
              <Button
                variant="primary"
                onClick={() => handleEditModel(isEditingModel)}
                disabled={submitting}
              >
                {submitting ? 'Mise à jour...' : 'Mettre à jour'}
              </Button>
              <Button
                variant="outline"
                onClick={cancelEdit}
                disabled={submitting}
              >
                Annuler
              </Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
} 