"""
Pydantic schemas pour l'API NLP
Validation et sérialisation des requêtes/réponses
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, validator
from enum import Enum

from ..domain.entities import SEOIntentType, RelevanceLevel, ConfidenceLevel


# Enums API

class SEOIntentEnum(str, Enum):
    COMMERCIAL = "commercial"
    INFORMATIONAL = "informational"
    TRANSACTIONAL = "transactional"
    NAVIGATIONAL = "navigational"


class RelevanceLevelEnum(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ConfidenceLevelEnum(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# Request Schemas

class AnalyzeContentRequest(BaseModel):
    """Requête d'analyse de contenu"""
    analysis_id: str = Field(..., description="ID unique de l'analyse")
    prompt: str = Field(..., min_length=1, max_length=10000, description="Prompt utilisé")
    ai_response: str = Field(..., min_length=1, max_length=50000, description="Réponse de l'IA")
    sector: Optional[str] = Field(None, description="Secteur d'activité")
    project_description: Optional[str] = Field(None, max_length=1000, description="Description du projet")
    force_reanalysis: bool = Field(False, description="Forcer la re-analyse même si en cache")
    
    @validator('prompt')
    def validate_prompt(cls, v):
        if not v.strip():
            raise ValueError('Le prompt ne peut pas être vide')
        return v.strip()
    
    @validator('ai_response')
    def validate_ai_response(cls, v):
        if not v.strip():
            raise ValueError('La réponse IA ne peut pas être vide')
        return v.strip()


class BatchAnalyzeRequest(BaseModel):
    """Requête d'analyse en batch"""
    analyses: List[AnalyzeContentRequest] = Field(..., min_items=1, max_items=100)
    parallel_processing: bool = Field(True, description="Traitement parallèle")
    max_workers: int = Field(5, ge=1, le=10, description="Nombre max de workers")


class InvalidateCacheRequest(BaseModel):
    """Requête d'invalidation de cache"""
    pattern: str = Field("*", description="Pattern de clés à invalider")
    reason: str = Field("manual", description="Raison de l'invalidation")


# Response Schemas

class SEOIntentResponse(BaseModel):
    """Réponse intention SEO"""
    main_intent: SEOIntentEnum
    confidence: float = Field(..., ge=0, le=1)
    detailed_scores: Dict[str, float]


class ContentTypeResponse(BaseModel):
    """Réponse type de contenu"""
    main_type: str
    confidence: float = Field(..., ge=0, le=1)
    all_scores: Dict[str, float]


class BusinessTopicResponse(BaseModel):
    """Réponse topic business"""
    topic: str
    score: float
    raw_score: float
    weight: float
    relevance: RelevanceLevelEnum
    matches_count: int
    top_keywords: List[str]
    sample_contexts: List[str]


class SectorEntityResponse(BaseModel):
    """Réponse entité sectorielle"""
    name: str
    count: int
    contexts: List[str]
    entity_type: str


class NLPAnalysisResponse(BaseModel):
    """Réponse complète d'analyse NLP"""
    analysis_id: str
    seo_intent: SEOIntentResponse
    content_type: ContentTypeResponse
    business_topics: List[BusinessTopicResponse]
    sector_entities: Dict[str, List[SectorEntityResponse]]
    semantic_keywords: List[str]
    global_confidence: float = Field(..., ge=0, le=1)
    sector_context: str
    processing_version: str
    created_at: datetime


class ProjectNLPSummaryResponse(BaseModel):
    """Réponse résumé NLP projet"""
    project_id: str
    project_name: str
    total_analyses: int
    average_confidence: float
    high_confidence_count: int
    high_confidence_rate: float
    seo_intents_distribution: Dict[SEOIntentEnum, int]
    content_types_distribution: Dict[str, int]
    top_business_topics: Dict[str, int]
    top_entities: Dict[str, Dict[str, int]]
    analysis_period: str
    nlp_quality_score: float


class GlobalNLPStatsResponse(BaseModel):
    """Réponse statistiques globales NLP"""
    total_analyses: int
    analyzed_with_nlp: int
    nlp_coverage: float
    average_confidence: float
    seo_intents_distribution: Dict[SEOIntentEnum, int]
    content_types_distribution: Dict[str, int]
    top_business_topics: Dict[str, int]
    top_entities: Dict[str, Dict[str, int]]
    dominant_seo_intent: Optional[SEOIntentEnum]


class QualityReportResponse(BaseModel):
    """Réponse rapport de qualité"""
    analysis_id: str
    overall_score: float
    confidence_level: ConfidenceLevelEnum
    quality_issues: List[str]
    recommendations: List[str]
    plugin_scores: Dict[str, float]
    improvement_potential: float


class ProjectQualityScoreResponse(BaseModel):
    """Réponse score de qualité projet"""
    project_id: str
    project_name: str
    overall_score: float
    analysis_count: int
    high_quality_count: int
    average_confidence: float
    quality_distribution: Dict[str, int]
    improvement_areas: List[str]
    last_calculated: datetime


class CacheStatsResponse(BaseModel):
    """Réponse statistiques cache"""
    cache_type: str
    size: int
    hit_rate: float
    stats: Dict[str, Any]
    memory_usage_mb: Optional[float] = None
    additional_info: Optional[Dict[str, Any]] = None


class PerformanceMetricsResponse(BaseModel):
    """Réponse métriques de performance"""
    total_analyses: int
    average_processing_time_ms: float
    cache_hit_rate: float
    error_rate: float
    throughput_per_hour: float
    plugin_performance: Dict[str, Dict[str, Any]]
    system_health: str
    bottlenecks: List[str]


class TrendDataPointResponse(BaseModel):
    """Point de données de tendance"""
    period: str
    total_analyses: int
    average_confidence: float
    seo_intent_distribution: Dict[SEOIntentEnum, int]
    content_type_distribution: Dict[str, int]
    top_topics: List[str]


class TrendsDataResponse(BaseModel):
    """Données de tendances"""
    project_id: str
    project_name: str
    time_range_days: int
    data_points: List[TrendDataPointResponse]
    overall_trend: str
    insights: List[str]


class AnalysisSearchResultResponse(BaseModel):
    """Résultat de recherche d'analyses"""
    analysis_id: str
    project_name: str
    confidence: float
    main_topic: str
    seo_intent: SEOIntentEnum
    created_at: datetime
    relevance_score: float


# Command/Query Result Schemas

class CommandResultResponse(BaseModel):
    """Réponse générique de commande"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    errors: Optional[List[str]] = None
    execution_time_ms: Optional[float] = None


class AnalyzeContentResultResponse(CommandResultResponse):
    """Réponse d'analyse de contenu"""
    analysis_id: str
    confidence: float
    processing_time_ms: float
    cache_hit: bool = False


class BatchAnalyzeResultResponse(CommandResultResponse):
    """Réponse d'analyse en batch"""
    total_requested: int
    successful_count: int
    failed_count: int
    average_confidence: float
    total_processing_time_ms: float
    failed_analysis_ids: List[str]
    success_rate: float
    
    @validator('success_rate', always=True)
    def calculate_success_rate(cls, v, values):
        total = values.get('total_requested', 0)
        successful = values.get('successful_count', 0)
        return round(successful / total * 100, 2) if total > 0 else 0


class QueryResultResponse(BaseModel):
    """Réponse générique de query"""
    success: bool
    data: Optional[Any] = None
    message: Optional[str] = None
    errors: Optional[List[str]] = None
    execution_time_ms: Optional[float] = None
    cache_hit: bool = False


class PaginatedResponse(BaseModel):
    """Réponse paginée générique"""
    items: List[Any]
    total_count: int
    page: int
    page_size: int
    has_next: bool
    has_previous: bool
    total_pages: int
    
    @validator('total_pages', always=True)
    def calculate_total_pages(cls, v, values):
        total_count = values.get('total_count', 0)
        page_size = values.get('page_size', 1)
        return max(1, (total_count + page_size - 1) // page_size)


# Error Schemas

class ValidationErrorResponse(BaseModel):
    """Réponse d'erreur de validation"""
    message: str
    details: List[Dict[str, Any]]
    error_type: str = "validation_error"


class NLPErrorResponse(BaseModel):
    """Réponse d'erreur NLP générique"""
    message: str
    error_type: str
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime


# Health Check Schema

class HealthCheckResponse(BaseModel):
    """Réponse de health check"""
    status: str  # "healthy", "degraded", "unhealthy"
    version: str
    components: Dict[str, Dict[str, Any]]
    timestamp: datetime
    uptime_seconds: float