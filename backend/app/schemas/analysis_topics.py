"""
Schémas Pydantic pour les AnalysisTopics (NLP)
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class AnalysisTopicsBase(BaseModel):
    """Schéma de base pour AnalysisTopics"""
    seo_intent: str = Field(..., description="Intention SEO principale")
    seo_confidence: float = Field(..., ge=0, le=1, description="Confiance de l'intention SEO")
    content_type: Optional[str] = Field(None, description="Type de contenu détecté")
    content_confidence: Optional[float] = Field(None, ge=0, le=1, description="Confiance du type de contenu")
    global_confidence: float = Field(..., ge=0, le=1, description="Score de confiance global")
    sector_context: Optional[str] = Field(None, description="Secteur utilisé pour l'analyse")


class AnalysisTopicsCreate(AnalysisTopicsBase):
    """Schéma pour créer une AnalysisTopics"""
    analysis_id: str = Field(..., description="ID de l'analyse associée")
    seo_detailed_scores: Optional[Dict[str, float]] = Field(None, description="Scores détaillés par intention")
    business_topics: Optional[List[Dict[str, Any]]] = Field(None, description="Topics business détectés")
    sector_entities: Optional[Dict[str, List[Any]]] = Field(None, description="Entités sectorielles")
    semantic_keywords: Optional[List[str]] = Field(None, description="Mots-clés sémantiques")
    processing_version: Optional[str] = Field("1.0", description="Version de l'algorithme")


class AnalysisTopicsUpdate(BaseModel):
    """Schéma pour mettre à jour une AnalysisTopics"""
    seo_intent: Optional[str] = None
    seo_confidence: Optional[float] = Field(None, ge=0, le=1)
    content_type: Optional[str] = None
    content_confidence: Optional[float] = Field(None, ge=0, le=1)
    global_confidence: Optional[float] = Field(None, ge=0, le=1)
    sector_context: Optional[str] = None
    seo_detailed_scores: Optional[Dict[str, float]] = None
    business_topics: Optional[List[Dict[str, Any]]] = None
    sector_entities: Optional[Dict[str, List[Any]]] = None
    semantic_keywords: Optional[List[str]] = None


class AnalysisTopicsRead(AnalysisTopicsBase):
    """Schéma pour lire une AnalysisTopics"""
    id: str
    analysis_id: str
    seo_detailed_scores: Optional[Dict[str, float]]
    business_topics: Optional[List[Dict[str, Any]]]
    sector_entities: Optional[Dict[str, List[Any]]]
    semantic_keywords: Optional[List[str]]
    processing_version: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AnalysisTopicsSummary(BaseModel):
    """Schéma résumé pour AnalysisTopics"""
    analysis_id: str
    seo_intent: str
    seo_confidence: float
    content_type: Optional[str]
    primary_topic: Optional[str] = Field(None, description="Topic business principal")
    global_confidence: float
    brands_detected: int = Field(0, description="Nombre de marques détectées")
    technologies_detected: int = Field(0, description="Nombre de technologies détectées")
    created_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class NLPAnalysisResult(BaseModel):
    """Schéma pour le résultat complet d'une analyse NLP"""
    analysis_id: str
    nlp_results: Dict[str, Any] = Field(..., description="Résultats détaillés de l'analyse NLP")
    
    class Config:
        from_attributes = True


class ProjectNLPSummary(BaseModel):
    """Schéma pour le résumé NLP d'un projet"""
    project_id: str
    project_name: str
    summary: Dict[str, Any] = Field(..., description="Résumé agrégé des analyses NLP")
    limit_applied: int
    
    class Config:
        from_attributes = True


class ProjectNLPTrends(BaseModel):
    """Schéma pour les tendances NLP d'un projet"""
    project_id: str
    project_name: str
    trends_data: Dict[str, Any] = Field(..., description="Données de tendances NLP")
    
    class Config:
        from_attributes = True


class BatchNLPAnalysisResult(BaseModel):
    """Schéma pour le résultat d'une analyse NLP en lot"""
    total_requested: int
    success_count: int
    failure_count: int
    results: Dict[str, bool] = Field(..., description="Résultats par analyse_id")
    success_rate: float
    
    class Config:
        from_attributes = True


class GlobalNLPStats(BaseModel):
    """Schéma pour les statistiques globales NLP"""
    total_analyses: int
    analyzed_with_nlp: int
    nlp_coverage: float = Field(..., description="Pourcentage d'analyses avec NLP")
    average_confidence: float
    seo_intents_distribution: Dict[str, int]
    content_types_distribution: Dict[str, int]
    
    class Config:
        from_attributes = True


class ProjectReanalysisResult(BaseModel):
    """Schéma pour le résultat d'une re-analyse de projet"""
    project_id: str
    project_name: str
    success: bool
    total_analyses: int
    success_count: int
    failure_count: int
    message: Optional[str] = None
    
    class Config:
        from_attributes = True


class SEOIntentDetails(BaseModel):
    """Schéma détaillé pour une intention SEO"""
    main_intent: str
    confidence: float
    detailed_scores: Dict[str, float]
    
    class Config:
        from_attributes = True


class ContentTypeDetails(BaseModel):
    """Schéma détaillé pour un type de contenu"""
    main_type: str
    confidence: float
    all_scores: Dict[str, float]
    
    class Config:
        from_attributes = True


class BusinessTopic(BaseModel):
    """Schéma pour un topic business"""
    topic: str
    score: float
    raw_score: int
    weight: float
    relevance: str
    matches_count: int
    top_keywords: List[str]
    sample_contexts: List[str]
    
    class Config:
        from_attributes = True


class SectorEntity(BaseModel):
    """Schéma pour une entité sectorielle"""
    name: str
    count: int
    contexts: List[str]
    
    class Config:
        from_attributes = True