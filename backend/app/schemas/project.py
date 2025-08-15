from typing import List, Optional
from pydantic import HttpUrl, Field
from .base import BaseCreateSchema, BaseUpdateSchema, BaseReadSchema

# Schémas pour les mots-clés
class KeywordCreate(BaseCreateSchema):
    keyword: str = Field(..., min_length=1, max_length=100)

class KeywordRead(BaseCreateSchema):
    keyword: str

# Schémas pour les concurrents
class CompetitorCreate(BaseCreateSchema):
    name: str = Field(..., min_length=1, max_length=200)
    website: str = Field(..., min_length=1, max_length=500)

class CompetitorUpdate(BaseUpdateSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    website: Optional[str] = Field(None, min_length=1, max_length=500)

class CompetitorRead(BaseReadSchema):
    project_id: str
    name: str
    website: str

# Schémas pour les projets
class ProjectCreate(BaseCreateSchema):
    name: str = Field(..., min_length=1, max_length=200, description="Nom du projet")
    main_website: Optional[str] = Field(None, max_length=500, description="Site web principal")
    description: Optional[str] = Field(None, max_length=1000, description="Description du projet")
    keywords: List[str] = Field(default=[], description="Liste des mots-clés cibles")

class ProjectUpdate(BaseUpdateSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    main_website: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = Field(None, max_length=1000)
    keywords: Optional[List[str]] = Field(None, description="Liste des mots-clés cibles")

class ProjectRead(BaseReadSchema):
    name: str
    main_website: Optional[str]
    description: Optional[str]
    keywords: List[KeywordRead] = []
    competitors: List[CompetitorRead] = []

class ProjectSummary(BaseReadSchema):
    """Version simplifiée pour les listes"""
    name: str
    main_website: Optional[str]
    description: Optional[str]
    keywords_count: int = 0
    competitors_count: int = 0
    analyses_count: int = 0 