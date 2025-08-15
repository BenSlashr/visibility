"""
Queries pour la couche application NLP
Pattern CQRS - Queries pour les opérations de lecture
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime
from abc import ABC


@dataclass
class Query(ABC):
    """Query de base"""
    pass


@dataclass
class GetAnalysisResultQuery(Query):
    """Query pour récupérer un résultat d'analyse"""
    analysis_id: str


@dataclass
class GetProjectNLPSummaryQuery(Query):
    """Query pour récupérer le résumé NLP d'un projet"""
    project_id: str
    limit: int = 100
    include_low_confidence: bool = True


@dataclass
class GetGlobalNLPStatsQuery(Query):
    """Query pour récupérer les statistiques globales"""
    include_trends: bool = False


@dataclass
class GetProjectNLPTrendsQuery(Query):
    """Query pour récupérer les tendances d'un projet"""
    project_id: str
    days: int = 30
    group_by: str = "day"  # "day", "week", "month"


@dataclass
class SearchAnalysesByTopicQuery(Query):
    """Query pour rechercher des analyses par topic"""
    topic: str
    project_id: Optional[str] = None
    min_confidence: float = 0.5
    limit: int = 50


@dataclass
class GetAnalysesWithLowQualityQuery(Query):
    """Query pour récupérer les analyses de faible qualité"""
    project_id: Optional[str] = None
    max_confidence: float = 0.4
    limit: int = 100


@dataclass
class GetNLPPerformanceMetricsQuery(Query):
    """Query pour récupérer les métriques de performance"""
    time_range_hours: int = 24
    include_plugin_metrics: bool = True


@dataclass
class GetCacheStatsQuery(Query):
    """Query pour récupérer les statistiques du cache"""
    detailed: bool = False


@dataclass
class GetSectorAnalysisDistributionQuery(Query):
    """Query pour la distribution des analyses par secteur"""
    project_id: Optional[str] = None
    limit: int = 10


@dataclass
class GetTopEntitiesByTypeQuery(Query):
    """Query pour récupérer les top entités par type"""
    entity_type: str  # 'brands', 'technologies', etc.
    project_id: Optional[str] = None
    sector: Optional[str] = None
    limit: int = 20


@dataclass
class GetAnalysisQualityReportQuery(Query):
    """Query pour un rapport de qualité d'analyse"""
    analysis_id: str
    include_recommendations: bool = True


@dataclass
class GetProjectQualityScoreQuery(Query):
    """Query pour le score de qualité d'un projet"""
    project_id: str
    recalculate: bool = False


# Query Results

@dataclass
class QueryResult:
    """Résultat d'une query"""
    success: bool
    data: Optional[Any] = None
    message: Optional[str] = None
    errors: Optional[List[str]] = None
    execution_time_ms: Optional[float] = None
    cache_hit: bool = False


@dataclass
class PaginatedQueryResult(QueryResult):
    """Résultat paginé"""
    total_count: int
    page: int
    page_size: int
    has_next: bool
    has_previous: bool


@dataclass
class AnalysisSearchResult:
    """Résultat de recherche d'analyses"""
    analysis_id: str
    project_name: str
    confidence: float
    main_topic: str
    seo_intent: str
    created_at: datetime
    relevance_score: float


@dataclass
class QualityReport:
    """Rapport de qualité d'analyse"""
    analysis_id: str
    overall_score: float
    confidence_level: str
    quality_issues: List[str]
    recommendations: List[str]
    plugin_scores: Dict[str, float]
    improvement_potential: float


@dataclass
class ProjectQualityScore:
    """Score de qualité d'un projet"""
    project_id: str
    project_name: str
    overall_score: float
    analysis_count: int
    high_quality_count: int
    average_confidence: float
    quality_distribution: Dict[str, int]
    improvement_areas: List[str]
    last_calculated: datetime


@dataclass
class PerformanceMetrics:
    """Métriques de performance NLP"""
    total_analyses: int
    average_processing_time_ms: float
    cache_hit_rate: float
    error_rate: float
    throughput_per_hour: float
    plugin_performance: Dict[str, Dict[str, Any]]
    system_health: str  # "healthy", "warning", "critical"
    bottlenecks: List[str]


@dataclass
class TrendDataPoint:
    """Point de données de tendance"""
    period: str
    total_analyses: int
    average_confidence: float
    seo_intent_distribution: Dict[str, int]
    content_type_distribution: Dict[str, int]
    top_topics: List[str]


@dataclass
class TrendsData:
    """Données de tendances"""
    project_id: str
    project_name: str
    time_range_days: int
    data_points: List[TrendDataPoint]
    overall_trend: str  # "improving", "stable", "declining"
    insights: List[str]