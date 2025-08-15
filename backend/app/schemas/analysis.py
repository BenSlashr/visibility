from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from .base import BaseCreateSchema, BaseUpdateSchema, BaseReadSchema, BaseSchema

class AnalysisCompetitorCreate(BaseCreateSchema):
    competitor_name: str
    is_mentioned: bool = False
    ranking_position: Optional[int] = None
    mention_context: Optional[str] = Field(None, max_length=500)

class AnalysisCompetitorRead(BaseModel):  # BaseModel simple sans héritage
    analysis_id: str
    competitor_name: str
    is_mentioned: bool
    ranking_position: Optional[int]
    mention_context: Optional[str]
    created_at: datetime

class AnalysisCreate(BaseCreateSchema):
    prompt_id: str = Field(..., description="ID du prompt exécuté")
    project_id: str = Field(..., description="ID du projet (dénormalisé)")
    prompt_executed: str = Field(..., description="Prompt final exécuté")
    ai_response: str = Field(..., description="Réponse complète de l'IA")
    variables_used: Dict[str, Any] = Field(default={}, description="Variables utilisées")
    
    # Métriques de visibilité
    brand_mentioned: bool = Field(default=False, description="Marque mentionnée")
    website_mentioned: bool = Field(default=False, description="Site web mentionné")
    website_linked: bool = Field(default=False, description="Lien vers le site")
    ranking_position: Optional[int] = Field(None, ge=1, description="Position dans un classement")
    
    # Métadonnées techniques
    ai_model_used: str = Field(..., description="Modèle IA utilisé")
    tokens_used: int = Field(default=0, ge=0, description="Tokens consommés")
    processing_time_ms: int = Field(default=0, ge=0, description="Temps de traitement en ms")
    cost_estimated: float = Field(default=0.0, ge=0, description="Coût estimé")
    web_search_used: bool = Field(default=False, description="Indique si la web search a été utilisée (OpenAI)")
    
    # Analyses des concurrents
    competitor_analyses: List[AnalysisCompetitorCreate] = Field(default=[], description="Mentions des concurrents")

class AnalysisUpdate(BaseUpdateSchema):
    # Seules les métriques peuvent être mises à jour (après analyse manuelle)
    brand_mentioned: Optional[bool] = None
    website_mentioned: Optional[bool] = None
    website_linked: Optional[bool] = None
    ranking_position: Optional[int] = Field(None, ge=1)

class AnalysisSourceCreate(BaseCreateSchema):
    analysis_id: Optional[str] = None
    url: str
    domain: Optional[str] = None
    title: Optional[str] = None
    snippet: Optional[str] = None
    citation_label: Optional[str] = None
    position: Optional[int] = None
    is_valid: Optional[bool] = None
    http_status: Optional[int] = None
    content_type: Optional[str] = None
    confidence: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class AnalysisSourceRead(BaseReadSchema):
    analysis_id: str
    url: str
    domain: Optional[str] = None
    title: Optional[str] = None
    snippet: Optional[str] = None
    citation_label: Optional[str] = None
    position: Optional[int] = None
    is_valid: Optional[bool] = None
    http_status: Optional[int] = None
    content_type: Optional[str] = None
    confidence: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class AnalysisRead(BaseReadSchema):
    prompt_id: str
    project_id: str
    prompt_executed: str
    ai_response: str
    variables_used: Dict[str, Any]
    
    # Métriques de visibilité
    brand_mentioned: bool
    website_mentioned: bool
    website_linked: bool
    ranking_position: Optional[int]
    
    # Métadonnées techniques
    ai_model_used: str
    tokens_used: int
    processing_time_ms: int
    cost_estimated: float
    web_search_used: bool = False
    
    # Relations
    competitor_analyses: List[AnalysisCompetitorRead] = []
    sources: List[AnalysisSourceRead] = []
    
    # Propriétés calculées
    @property
    def visibility_score(self) -> float:
        """Score de visibilité calculé"""
        score = 0
        if self.brand_mentioned:
            score += 40
        if self.website_mentioned:
            score += 30
        if self.website_linked:
            score += 20
        if self.ranking_position:
            if self.ranking_position <= 3:
                score += 10
            elif self.ranking_position <= 5:
                score += 5
        return min(score, 100)

class AnalysisSummary(BaseReadSchema):
    """Version simplifiée pour les listes"""
    prompt_id: str
    project_id: str
    brand_mentioned: bool
    website_mentioned: bool
    website_linked: bool
    ranking_position: Optional[int]
    ai_model_used: str
    tokens_used: int
    cost_estimated: float
    visibility_score: float = 0
    project_name: Optional[str] = None
    prompt_name: Optional[str] = None
    # Données des concurrents
    competitors_analysis: List[AnalysisCompetitorRead] = Field(default=[], description="Analyses des concurrents")
    has_sources: Optional[bool] = None
    web_search_used: Optional[bool] = None


 

class AnalysisStats(BaseCreateSchema):
    """Statistiques d'analyses"""
    total_analyses: int = 0
    brand_mentions: int = 0
    website_mentions: int = 0
    website_links: int = 0
    average_visibility_score: float = 0.0
    total_cost: float = 0.0
    total_tokens: int = 0
    average_processing_time: float = 0.0
    top_ranking_position: Optional[int] = None
    
class ProjectAnalysisStats(AnalysisStats):
    """Statistiques par projet"""
    project_id: str
    project_name: str
    brand_mention_rate: float = 0.0
    website_mention_rate: float = 0.0
    website_link_rate: float = 0.0
    analyses_last_7_days: int = 0
    analyses_last_30_days: int = 0
    cost_last_7_days: float = 0.0
    cost_last_30_days: float = 0.0
    last_analysis: Optional[datetime] = None
    
class CompetitorAnalysisStats(BaseCreateSchema):
    """Statistiques des concurrents"""
    competitor_id: str
    competitor_name: str
    competitor_website: str
    total_mentions: int = 0
    mention_rate: float = 0.0  # Pourcentage de mentions
    average_position: float = 0.0
    best_position: Optional[int] = None 