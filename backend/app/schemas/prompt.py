from typing import List, Optional, Dict, Any
from pydantic import Field
from datetime import datetime
from .base import BaseCreateSchema, BaseUpdateSchema, BaseReadSchema, BaseSchema

class PromptAIModelCreate(BaseCreateSchema):
    ai_model_id: str
    is_active: bool = True

class PromptAIModelRead(BaseSchema):
    prompt_id: str
    ai_model_id: str
    is_active: bool
    created_at: datetime
    # Relations optionnelles
    ai_model_name: Optional[str] = None
    ai_model_provider: Optional[str] = None

class PromptCreate(BaseCreateSchema):
    project_id: str = Field(..., description="ID du projet")
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    template: str = Field(..., min_length=1, description="Template du prompt avec variables")
    tags: List[str] = Field(default=[], description="Tags pour catégoriser le prompt")
    is_active: bool = Field(default=True)
    
    # Support multi-agents
    is_multi_agent: bool = Field(default=False, description="Prompt multi-agents ou modèle unique")
    ai_model_id: Optional[str] = Field(None, description="Modèle unique (si is_multi_agent=False)")
    ai_model_ids: List[str] = Field(default=[], description="Liste des modèles (si is_multi_agent=True)")

class PromptUpdate(BaseUpdateSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    template: Optional[str] = Field(None, min_length=1)
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None
    is_multi_agent: Optional[bool] = None
    ai_model_id: Optional[str] = None
    ai_model_ids: Optional[List[str]] = None

class PromptRead(BaseReadSchema):
    project_id: str
    name: str
    description: Optional[str]
    template: str
    is_active: bool
    is_multi_agent: bool
    ai_model_id: Optional[str]
    last_executed_at: Optional[datetime]
    execution_count: int
    
    # Relations
    tags: List[str] = Field(default=[])
    ai_models: List[PromptAIModelRead] = Field(default=[], description="Modèles IA associés (multi-agents)")
    
    # Champs calculés
    ai_model_name: Optional[str] = Field(None, description="Nom du modèle principal")
    ai_model_names: List[str] = Field(default=[], description="Noms de tous les modèles")

class BulkPromptItem(BaseCreateSchema):
    project_id: str
    name: str
    template: str
    description: Optional[str] = None
    tags: List[str] = Field(default=[])
    is_active: bool = True
    is_multi_agent: bool = False
    ai_model_id: Optional[str] = None
    ai_model_ids: List[str] = Field(default=[])
    # Nouveaux champs: acceptation par nom
    ai_model_name: Optional[str] = None
    ai_model_names: List[str] = Field(default=[])
    # Nouveaux champs: acceptation par identifiant API (model_identifier)
    ai_model_identifier: Optional[str] = None
    ai_model_identifiers: List[str] = Field(default=[])

class BulkPromptsRequest(BaseCreateSchema):
    validate_only: bool = Field(default=False)
    upsert_by: Optional[str] = Field(default=None, description="'name' pour upsert par nom")
    defaults: Dict[str, Any] = Field(default={})
    items: List[BulkPromptItem]

class BulkPromptResultItem(BaseSchema):
    index: int
    status: str  # created|updated|error|skipped
    id: Optional[str] = None
    errors: Optional[List[str]] = None

class BulkPromptsResponse(BaseSchema):
    success_count: int
    error_count: int
    results: List[BulkPromptResultItem]

class PromptExecuteRequest(BaseCreateSchema):
    """Requête d'exécution de prompt"""
    custom_variables: Optional[Dict[str, str]] = Field(default={})
    max_tokens: Optional[int] = Field(None, ge=1, le=8192)
    
    # Multi-agents
    ai_model_ids: Optional[List[str]] = Field(None, description="Modèles spécifiques à exécuter (optionnel)")
    compare_models: bool = Field(default=False, description="Exécuter sur tous les modèles pour comparaison")

class PromptExecuteResponse(BaseSchema):
    """Réponse d'exécution de prompt"""
    success: bool
    
    # Résultats uniques (pour compatibilité)
    analysis_id: Optional[str] = None
    prompt_executed: Optional[str] = None
    ai_response: Optional[str] = None
    variables_used: Optional[Dict[str, str]] = None
    brand_mentioned: Optional[bool] = None
    website_mentioned: Optional[bool] = None
    website_linked: Optional[bool] = None
    ranking_position: Optional[int] = None
    competitors_mentioned: Optional[int] = None
    visibility_score: Optional[float] = None
    analysis_summary: Optional[str] = None
    ai_model_used: Optional[str] = None
    tokens_used: Optional[int] = None
    processing_time_ms: Optional[int] = None
    cost_estimated: Optional[float] = None
    
    # Résultats multi-agents
    analyses: List[Dict[str, Any]] = Field(default=[], description="Résultats de tous les modèles")
    total_cost: Optional[float] = Field(None, description="Coût total pour tous les modèles")
    comparison_summary: Optional[Dict[str, Any]] = Field(None, description="Résumé de comparaison")
    
    error: Optional[str] = None

class PromptSummary(BaseReadSchema):
    """Version simplifiée pour les listes"""
    project_id: str
    name: str
    description: Optional[str]
    template: str  # Ajouté pour le frontend
    is_active: bool
    is_multi_agent: Optional[bool] = Field(default=False)
    ai_model_id: Optional[str] = None  # Pour les prompts mono-agent
    ai_model_name: Optional[str]
    ai_model_names: List[str] = Field(default=[])
    ai_models: List[PromptAIModelRead] = Field(default=[])  # Pour les prompts multi-agent
    tags: List[str] = Field(default=[])
    last_executed_at: Optional[datetime]
    execution_count: int

class PromptStats(BaseCreateSchema):
    """Statistiques d'un prompt"""
    prompt_id: str
    prompt_name: str
    total_analyses: int = 0
    avg_visibility_score: float = 0.0
    brand_mention_rate: float = 0.0
    website_link_rate: float = 0.0
    avg_cost: float = 0.0
    total_tokens: int = 0
    avg_processing_time: float = 0.0
    last_analysis: Optional[datetime] = None
    
    # Stats multi-agents
    models_used: List[str] = Field(default=[])
    best_performing_model: Optional[str] = None
    model_comparison: Dict[str, Dict[str, float]] = Field(default={})  # model_id -> metrics 