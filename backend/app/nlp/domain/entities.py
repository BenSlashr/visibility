"""
Entités du domaine NLP
Règles métier pures, sans dépendances externes
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


class SEOIntentType(str, Enum):
    """Types d'intentions SEO"""
    COMMERCIAL = "commercial"
    INFORMATIONAL = "informational"
    TRANSACTIONAL = "transactional"
    NAVIGATIONAL = "navigational"


class ConfidenceLevel(str, Enum):
    """Niveaux de confiance"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RelevanceLevel(str, Enum):
    """Niveaux de pertinence"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class SEOIntent:
    """Intention SEO détectée"""
    main_intent: SEOIntentType
    confidence: float
    detailed_scores: Dict[str, float]
    
    def is_high_confidence(self) -> bool:
        return self.confidence >= 0.7
    
    def get_confidence_level(self) -> ConfidenceLevel:
        if self.confidence >= 0.7:
            return ConfidenceLevel.HIGH
        elif self.confidence >= 0.4:
            return ConfidenceLevel.MEDIUM
        return ConfidenceLevel.LOW


@dataclass
class ContentType:
    """Type de contenu détecté"""
    main_type: str
    confidence: float
    all_scores: Dict[str, float]
    
    def is_high_confidence(self) -> bool:
        return self.confidence >= 0.7


@dataclass
class BusinessTopic:
    """Topic business détecté"""
    topic: str
    score: float
    raw_score: float
    weight: float
    relevance: RelevanceLevel
    matches_count: int
    top_keywords: List[str]
    sample_contexts: List[str]
    
    def is_relevant(self) -> bool:
        return self.relevance in [RelevanceLevel.HIGH, RelevanceLevel.MEDIUM]


@dataclass
class SectorEntity:
    """Entité sectorielle détectée"""
    name: str
    count: int
    contexts: List[str]
    entity_type: str  # 'brand', 'technology', 'product', etc.
    
    def is_significant(self) -> bool:
        return self.count > 1


@dataclass
class NLPAnalysisResult:
    """Résultat complet d'une analyse NLP"""
    analysis_id: str
    seo_intent: SEOIntent
    content_type: ContentType
    business_topics: List[BusinessTopic]
    sector_entities: Dict[str, List[SectorEntity]]
    semantic_keywords: List[str]
    global_confidence: float
    sector_context: str
    processing_version: str
    created_at: datetime
    
    def is_high_quality(self) -> bool:
        """Détermine si l'analyse est de haute qualité"""
        return (
            self.global_confidence >= 0.7 and
            self.seo_intent.is_high_confidence() and
            len(self.business_topics) > 0
        )
    
    def get_primary_business_topic(self) -> Optional[BusinessTopic]:
        """Retourne le topic business principal"""
        relevant_topics = [t for t in self.business_topics if t.is_relevant()]
        return relevant_topics[0] if relevant_topics else None
    
    def get_significant_entities(self) -> Dict[str, List[SectorEntity]]:
        """Retourne uniquement les entités significatives"""
        return {
            entity_type: [e for e in entities if e.is_significant()]
            for entity_type, entities in self.sector_entities.items()
        }


@dataclass
class NLPProjectSummary:
    """Résumé NLP pour un projet"""
    project_id: str
    project_name: str
    total_analyses: int
    average_confidence: float
    high_confidence_count: int
    seo_intents_distribution: Dict[SEOIntentType, int]
    content_types_distribution: Dict[str, int]
    top_business_topics: Dict[str, int]
    top_entities: Dict[str, Dict[str, int]]
    analysis_period: str
    
    @property
    def high_confidence_rate(self) -> float:
        if self.total_analyses == 0:
            return 0
        return round((self.high_confidence_count / self.total_analyses) * 100, 1)
    
    @property
    def nlp_quality_score(self) -> float:
        """Score de qualité global du NLP pour ce projet"""
        if self.total_analyses == 0:
            return 0
        
        # Facteurs de qualité
        confidence_factor = self.average_confidence
        coverage_factor = min(1.0, self.high_confidence_count / max(1, self.total_analyses))
        diversity_factor = min(1.0, len(self.content_types_distribution) / 5)
        
        return round((confidence_factor + coverage_factor + diversity_factor) / 3, 2)


@dataclass
class NLPGlobalStats:
    """Statistiques globales NLP"""
    total_analyses: int
    analyzed_with_nlp: int
    average_confidence: float
    seo_intents_distribution: Dict[SEOIntentType, int]
    content_types_distribution: Dict[str, int]
    top_business_topics: Dict[str, int]
    top_entities: Dict[str, Dict[str, int]]
    
    @property
    def nlp_coverage(self) -> float:
        if self.total_analyses == 0:
            return 0
        return round((self.analyzed_with_nlp / self.total_analyses) * 100, 1)
    
    @property
    def dominant_seo_intent(self) -> Optional[SEOIntentType]:
        if not self.seo_intents_distribution:
            return None
        return max(self.seo_intents_distribution.items(), key=lambda x: x[1])[0]