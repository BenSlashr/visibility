from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator

from .base import BaseSchema

class SERPKeywordBase(BaseModel):
    """Base pour les mots-clés SERP"""
    keyword: str = Field(..., min_length=1, max_length=500, description="Mot-clé de recherche")
    position: int = Field(..., ge=1, le=200, description="Position dans les résultats SERP")
    volume: Optional[int] = Field(None, ge=0, description="Volume de recherche mensuel")
    url: Optional[str] = Field(None, max_length=2000, description="URL de la page positionnée")

class SERPKeywordCreate(SERPKeywordBase):
    """Schéma pour créer un mot-clé SERP"""
    pass

class SERPKeywordUpdate(BaseModel):
    """Schéma pour modifier un mot-clé SERP"""
    keyword: Optional[str] = Field(None, min_length=1, max_length=500)
    position: Optional[int] = Field(None, ge=1, le=200)
    volume: Optional[int] = Field(None, ge=0)
    url: Optional[str] = Field(None, max_length=2000)

class SERPKeyword(SERPKeywordBase, BaseSchema):
    """Schéma complet pour un mot-clé SERP"""
    import_id: str
    project_id: str
    keyword_normalized: str
    
    class Config:
        from_attributes = True

class SERPImportBase(BaseModel):
    """Base pour les imports SERP"""
    filename: str = Field(..., min_length=1, max_length=255, description="Nom du fichier importé")
    notes: Optional[str] = Field(None, max_length=1000, description="Notes sur l'import")

class SERPImportCreate(SERPImportBase):
    """Schéma pour créer un import SERP"""
    project_id: str = Field(..., description="ID du projet")

class SERPImport(SERPImportBase, BaseSchema):
    """Schéma complet pour un import SERP"""
    project_id: str
    import_date: datetime
    total_keywords: int = 0
    is_active: bool = True
    
    # Relations optionnelles
    keywords: Optional[List[SERPKeyword]] = None
    
    class Config:
        from_attributes = True

class PromptSERPAssociationBase(BaseModel):
    """Base pour les associations prompt-SERP"""
    association_type: str = Field("manual", pattern="^(manual|auto|suggested)$")
    matching_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Score de confiance du matching")

class PromptSERPAssociationCreate(PromptSERPAssociationBase):
    """Schéma pour créer une association"""
    prompt_id: str
    serp_keyword_id: str

class PromptSERPAssociationUpdate(BaseModel):
    """Schéma pour modifier une association"""
    serp_keyword_id: Optional[str] = None  # None pour supprimer l'association
    association_type: Optional[str] = Field(None, pattern="^(manual|auto|suggested)$")

class PromptSERPAssociation(PromptSERPAssociationBase):
    """Schéma complet pour une association"""
    prompt_id: str
    serp_keyword_id: str
    created_at: datetime
    updated_at: datetime
    
    # Relations optionnelles
    serp_keyword: Optional[SERPKeyword] = None
    
    class Config:
        from_attributes = True

# Schémas pour les réponses d'API

class SERPImportResponse(BaseModel):
    """Réponse après import CSV"""
    success: bool
    import_id: Optional[str] = None
    keywords_imported: int = 0
    errors_count: int = 0
    errors: List[str] = []

class AutoMatchResponse(BaseModel):
    """Réponse après matching automatique"""
    success: bool
    auto_matches: int = 0
    suggestions: int = 0
    details: Dict[str, Any] = {}

class SERPStats(BaseModel):
    """Statistiques SERP d'un projet"""
    average_position: float
    top_3_keywords: int
    top_10_keywords: int

class AssociationStats(BaseModel):
    """Statistiques des associations"""
    auto_associations: int
    manual_associations: int
    unassociated_prompts: int
    association_rate: float

class SERPSummaryResponse(BaseModel):
    """Résumé complet des données SERP d'un projet"""
    has_serp_data: bool
    import_info: Optional[Dict[str, Any]] = None
    serp_stats: Optional[SERPStats] = None
    associations: Optional[AssociationStats] = None

class SERPKeywordListResponse(BaseModel):
    """Liste des mots-clés SERP"""
    keywords: List[Dict[str, Any]]

class PromptSERPAssociationResponse(BaseModel):
    """Association SERP d'un prompt"""
    has_association: bool
    association: Optional[Dict[str, Any]] = None

# Schémas pour les suggestions de matching

class MatchingSuggestion(BaseModel):
    """Suggestion de matching prompt-keyword"""
    prompt_id: str
    prompt_name: str
    keyword: str
    keyword_id: str
    score: float = Field(..., ge=0.0, le=1.0)
    confidence_level: str = Field(..., pattern="^(high|medium|low)$")
    
    @validator('confidence_level', pre=True, always=True)
    def set_confidence_level(cls, v, values):
        score = values.get('score', 0)
        if score >= 0.7:
            return 'high'
        elif score >= 0.4:
            return 'medium'
        else:
            return 'low'

class AutoMatchAutomatic(BaseModel):
    """Match automatique avec haute confiance"""
    prompt_id: str
    prompt_name: str
    keyword: str
    score: float

class AutoMatchDetails(BaseModel):
    """Détails complets du matching automatique"""
    auto_matches: List[AutoMatchAutomatic]
    suggestions: List[MatchingSuggestion]

# Schémas pour les corrélations SERP vs IA

class SERPCorrelationData(BaseModel):
    """Données de corrélation pour une analyse"""
    analysis_id: str
    prompt_name: str
    serp_keyword: Optional[str] = None
    serp_position: Optional[int] = None
    serp_volume: Optional[int] = None
    ai_mentioned: bool
    ai_ranking_position: Optional[int] = None
    correlation_score: Optional[float] = Field(None, ge=-1.0, le=1.0)
    
class ProjectSERPCorrelation(BaseModel):
    """Corrélation SERP vs IA pour un projet complet"""
    project_id: str
    project_name: str
    total_analyses: int
    analyses_with_serp: int
    correlation_analyses: List[SERPCorrelationData]
    average_correlation: Optional[float] = Field(None, ge=-1.0, le=1.0)
    insights: Dict[str, Any] = {}

# Validation personnalisée

class CSVUpload(BaseModel):
    """Validation pour l'upload de fichier CSV"""
    filename: str = Field(..., pattern=r'^.*\.csv$')
    content: str = Field(..., min_length=10)
    
    @validator('content')
    def validate_csv_structure(cls, v):
        """Valide que le CSV contient au minimum les colonnes requises"""
        lines = v.strip().split('\n')
        if len(lines) < 2:
            raise ValueError("Le fichier CSV doit contenir au moins un en-tête et une ligne de données")
        
        header = lines[0].lower()
        required_columns = ['keyword', 'position']
        
        for col in required_columns:
            if col not in header:
                raise ValueError(f"La colonne '{col}' est requise dans le CSV")
        
        return v