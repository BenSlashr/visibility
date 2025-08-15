from typing import Optional
from pydantic import Field, ConfigDict
from enum import Enum

from .base import BaseSchema, TimestampSchema, BaseCreateSchema, BaseUpdateSchema, BaseReadSchema
from ..enums import AIProviderEnum

class AIModelCreate(BaseCreateSchema):
    """Schéma pour créer un modèle IA"""
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())
    
    name: str = Field(..., min_length=1, max_length=100, description="Nom d'affichage du modèle")
    provider: AIProviderEnum = Field(..., description="Fournisseur du modèle IA")
    model_identifier: str = Field(..., min_length=1, max_length=100, description="Identifiant technique du modèle")
    max_tokens: int = Field(..., gt=0, le=200000, description="Nombre maximum de tokens supportés")
    cost_per_1k_tokens: float = Field(..., ge=0, description="Coût par 1000 tokens en USD")
    is_active: bool = Field(default=True, description="Modèle actif ou non")

class AIModelUpdate(BaseUpdateSchema):
    """Schéma pour mettre à jour un modèle IA"""
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())
    
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    provider: Optional[AIProviderEnum] = None
    model_identifier: Optional[str] = Field(None, min_length=1, max_length=100)
    max_tokens: Optional[int] = Field(None, gt=0, le=200000)
    cost_per_1k_tokens: Optional[float] = Field(None, ge=0)
    is_active: Optional[bool] = None

class AIModelRead(BaseReadSchema):
    """Schéma pour lire un modèle IA complet"""
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())
    
    name: str
    provider: AIProviderEnum
    model_identifier: str
    max_tokens: int
    cost_per_1k_tokens: float
    is_active: bool

class AIModelSummary(TimestampSchema):
    """Schéma résumé pour les listes de modèles IA"""
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())
    
    id: str
    name: str
    provider: AIProviderEnum
    is_active: bool
    cost_per_1k_tokens: float 