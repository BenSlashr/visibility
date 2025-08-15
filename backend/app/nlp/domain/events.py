"""
Système d'événements pour le domaine NLP
Pattern Event Sourcing/CQRS pour découpler les composants
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
from enum import Enum

from .entities import NLPAnalysisResult


class EventType(str, Enum):
    """Types d'événements NLP"""
    ANALYSIS_STARTED = "nlp.analysis.started"
    ANALYSIS_COMPLETED = "nlp.analysis.completed"
    ANALYSIS_FAILED = "nlp.analysis.failed"
    BATCH_STARTED = "nlp.batch.started"
    BATCH_COMPLETED = "nlp.batch.completed"
    CONFIGURATION_UPDATED = "nlp.configuration.updated"
    CACHE_INVALIDATED = "nlp.cache.invalidated"
    QUALITY_THRESHOLD_BREACHED = "nlp.quality.threshold_breached"


@dataclass
class DomainEvent(ABC):
    """Événement de domaine de base"""
    event_id: str
    aggregate_id: str
    occurred_at: datetime
    event_type: EventType
    version: int = field(default=1)
    metadata: Optional[Dict[str, Any]] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.metadata:
            self.metadata = {}


@dataclass
class AnalysisStartedEvent(DomainEvent):
    """Événement d'analyse démarrée"""
    prompt: str = field(default="")
    sector: str = field(default="")
    event_type: EventType = field(default=EventType.ANALYSIS_STARTED)
    
    def __post_init__(self):
        super().__post_init__()
        self.metadata.update({
            'prompt_length': len(self.prompt),
            'sector': self.sector
        })


@dataclass
class AnalysisCompletedEvent(DomainEvent):
    """Événement d'analyse terminée"""
    result: Optional[NLPAnalysisResult] = field(default=None)
    processing_duration_ms: float = field(default=0)
    event_type: EventType = field(default=EventType.ANALYSIS_COMPLETED)
    
    def __post_init__(self):
        super().__post_init__()
        if self.result:
            self.metadata.update({
                'confidence': self.result.global_confidence,
                'seo_intent': self.result.seo_intent.main_intent.value,
                'content_type': self.result.content_type.main_type,
                'topics_count': len(self.result.business_topics),
                'entities_count': sum(len(entities) for entities in self.result.sector_entities.values()),
                'processing_duration_ms': self.processing_duration_ms
            })


@dataclass
class AnalysisFailedEvent(DomainEvent):
    """Événement d'échec d'analyse"""
    error_message: str = field(default="")
    error_type: str = field(default="")
    event_type: EventType = field(default=EventType.ANALYSIS_FAILED)
    
    def __post_init__(self):
        super().__post_init__()
        self.metadata.update({
            'error_message': self.error_message,
            'error_type': self.error_type
        })


@dataclass
class BatchCompletedEvent(DomainEvent):
    """Événement de batch terminé"""
    results: Optional[List[NLPAnalysisResult]] = field(default=None)
    total_count: int = field(default=0)
    success_count: int = field(default=0)
    failure_count: int = field(default=0)
    event_type: EventType = field(default=EventType.BATCH_COMPLETED)
    
    def __post_init__(self):
        super().__post_init__()
        self.metadata.update({
            'total_count': self.total_count,
            'success_count': self.success_count,
            'failure_count': self.failure_count,
            'success_rate': self.success_count / max(1, self.total_count)
        })


@dataclass
class ConfigurationUpdatedEvent(DomainEvent):
    """Événement de mise à jour de configuration"""
    sector: str = field(default="")
    configuration_version: str = field(default="")
    changed_fields: Optional[List[str]] = field(default=None)
    event_type: EventType = field(default=EventType.CONFIGURATION_UPDATED)
    
    def __post_init__(self):
        super().__post_init__()
        self.metadata.update({
            'sector': self.sector,
            'configuration_version': self.configuration_version,
            'changed_fields': self.changed_fields or []
        })


@dataclass
class QualityThresholdBreachedEvent(DomainEvent):
    """Événement de seuil de qualité franchi"""
    quality_score: float = field(default=0)
    threshold: float = field(default=0)
    quality_issues: Optional[List[str]] = field(default=None)
    event_type: EventType = field(default=EventType.QUALITY_THRESHOLD_BREACHED)
    
    def __post_init__(self):
        super().__post_init__()
        self.metadata.update({
            'quality_score': self.quality_score,
            'threshold': self.threshold,
            'quality_issues': self.quality_issues or []
        })


class IEventHandler(ABC):
    """Interface pour les gestionnaires d'événements"""
    
    @abstractmethod
    def can_handle(self, event: DomainEvent) -> bool:
        """Détermine si ce handler peut traiter l'événement"""
        pass
    
    @abstractmethod
    async def handle(self, event: DomainEvent) -> None:
        """Traite l'événement"""
        pass


class IEventBus(ABC):
    """Interface pour le bus d'événements"""
    
    @abstractmethod
    def publish(self, event: DomainEvent) -> None:
        """Publie un événement"""
        pass
    
    @abstractmethod
    def subscribe(self, event_type: EventType, handler: IEventHandler) -> None:
        """S'abonne à un type d'événement"""
        pass
    
    @abstractmethod
    def unsubscribe(self, event_type: EventType, handler: IEventHandler) -> None:
        """Se désabonne d'un type d'événement"""
        pass


class IEventStore(ABC):
    """Interface pour le stockage d'événements"""
    
    @abstractmethod
    def append(self, event: DomainEvent) -> None:
        """Ajoute un événement au store"""
        pass
    
    @abstractmethod
    def get_events(self, aggregate_id: str, from_version: int = 0) -> List[DomainEvent]:
        """Récupère les événements pour un agrégat"""
        pass
    
    @abstractmethod
    def get_events_by_type(self, event_type: EventType, limit: int = 100) -> List[DomainEvent]:
        """Récupère les événements par type"""
        pass


# Event Handlers predéfinis

class AnalysisMetricsHandler(IEventHandler):
    """Handler pour collecter les métriques d'analyse"""
    
    def __init__(self, metrics_collector):
        self.metrics_collector = metrics_collector
    
    def can_handle(self, event: DomainEvent) -> bool:
        return event.event_type in [
            EventType.ANALYSIS_COMPLETED,
            EventType.ANALYSIS_FAILED
        ]
    
    async def handle(self, event: DomainEvent) -> None:
        if isinstance(event, AnalysisCompletedEvent):
            self.metrics_collector.record_analysis_duration(
                event.metadata.get('processing_duration_ms', 0)
            )
            self.metrics_collector.record_analysis_confidence(
                event.metadata.get('confidence', 0)
            )
        elif isinstance(event, AnalysisFailedEvent):
            self.metrics_collector.record_error(
                event.error_type,
                event.error_message
            )


class CacheInvalidationHandler(IEventHandler):
    """Handler pour invalider le cache lors des mises à jour de configuration"""
    
    def __init__(self, cache_manager):
        self.cache_manager = cache_manager
    
    def can_handle(self, event: DomainEvent) -> bool:
        return event.event_type == EventType.CONFIGURATION_UPDATED
    
    async def handle(self, event: DomainEvent) -> None:
        if isinstance(event, ConfigurationUpdatedEvent):
            # Invalider le cache pour ce secteur
            pattern = f"*{event.sector}*"
            self.cache_manager.invalidate_cache(pattern)


class QualityMonitoringHandler(IEventHandler):
    """Handler pour surveiller la qualité des analyses"""
    
    def __init__(self, quality_threshold: float = 0.6):
        self.quality_threshold = quality_threshold
    
    def can_handle(self, event: DomainEvent) -> bool:
        return event.event_type == EventType.ANALYSIS_COMPLETED
    
    async def handle(self, event: DomainEvent) -> None:
        if isinstance(event, AnalysisCompletedEvent):
            confidence = event.metadata.get('confidence', 0)
            if confidence < self.quality_threshold:
                # Publier un événement de seuil franchi
                quality_event = QualityThresholdBreachedEvent(
                    event_id=f"quality_{event.aggregate_id}",
                    aggregate_id=event.aggregate_id,
                    occurred_at=datetime.utcnow(),
                    quality_score=confidence,
                    threshold=self.quality_threshold,
                    quality_issues=["Confiance faible"]
                )
                # TODO: Publier via le bus d'événements