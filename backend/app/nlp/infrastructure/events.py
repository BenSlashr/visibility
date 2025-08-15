"""
Implémentations de l'infrastructure événementielle
Event Bus, Event Store et Event Handlers
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Set, Any, Optional
from collections import defaultdict
from dataclasses import asdict

from ..domain.events import (
    DomainEvent, 
    EventType, 
    IEventHandler, 
    IEventBus, 
    IEventStore,
    AnalysisStartedEvent,
    AnalysisCompletedEvent,
    AnalysisFailedEvent,
    BatchCompletedEvent,
    ConfigurationUpdatedEvent
)
from ..domain.ports import INLPEventPublisher

logger = logging.getLogger(__name__)


class InMemoryEventBus(IEventBus):
    """Bus d'événements en mémoire pour développement/test"""
    
    def __init__(self):
        self._handlers: Dict[EventType, Set[IEventHandler]] = defaultdict(set)
        self._event_store: Optional[IEventStore] = None
    
    def set_event_store(self, event_store: IEventStore) -> None:
        """Configure le store d'événements"""
        self._event_store = event_store
    
    def publish(self, event: DomainEvent) -> None:
        """Publie un événement de manière synchrone"""
        try:
            # Stocker l'événement si store configuré
            if self._event_store:
                self._event_store.append(event)
            
            # Traiter les handlers
            handlers = self._handlers.get(event.event_type, set())
            for handler in handlers:
                try:
                    if handler.can_handle(event):
                        # Exécuter de manière asynchrone si possible
                        if asyncio.iscoroutinefunction(handler.handle):
                            asyncio.create_task(handler.handle(event))
                        else:
                            handler.handle(event)
                except Exception as e:
                    logger.error(f"Erreur handler {handler.__class__.__name__} pour {event.event_type}: {str(e)}")
            
            logger.debug(f"Événement publié: {event.event_type} pour {event.aggregate_id}")
            
        except Exception as e:
            logger.error(f"Erreur publication événement {event.event_type}: {str(e)}")
    
    def subscribe(self, event_type: EventType, handler: IEventHandler) -> None:
        """S'abonne à un type d'événement"""
        self._handlers[event_type].add(handler)
        logger.debug(f"Handler {handler.__class__.__name__} abonné à {event_type}")
    
    def unsubscribe(self, event_type: EventType, handler: IEventHandler) -> None:
        """Se désabonne d'un type d'événement"""
        self._handlers[event_type].discard(handler)
        logger.debug(f"Handler {handler.__class__.__name__} désabonné de {event_type}")
    
    def get_subscribers_count(self, event_type: EventType) -> int:
        """Retourne le nombre de souscripteurs pour un type d'événement"""
        return len(self._handlers.get(event_type, set()))


class FileEventStore(IEventStore):
    """Store d'événements basé sur fichiers (pour développement)"""
    
    def __init__(self, storage_path: str = "data/events"):
        self.storage_path = storage_path
        self._ensure_storage_exists()
    
    def _ensure_storage_exists(self) -> None:
        """S'assure que le répertoire de stockage existe"""
        import os
        os.makedirs(self.storage_path, exist_ok=True)
    
    def append(self, event: DomainEvent) -> None:
        """Ajoute un événement au store"""
        try:
            event_data = {
                'event_id': event.event_id,
                'event_type': event.event_type.value,
                'aggregate_id': event.aggregate_id,
                'occurred_at': event.occurred_at.isoformat(),
                'version': event.version,
                'metadata': event.metadata,
                'event_class': event.__class__.__name__,
                'data': asdict(event)
            }
            
            # Fichier par agrégat
            file_path = f"{self.storage_path}/{event.aggregate_id}.jsonl"
            with open(file_path, 'a') as f:
                f.write(json.dumps(event_data) + '\n')
                
        except Exception as e:
            logger.error(f"Erreur sauvegarde événement {event.event_id}: {str(e)}")
    
    def get_events(self, aggregate_id: str, from_version: int = 0) -> List[DomainEvent]:
        """Récupère les événements pour un agrégat"""
        try:
            file_path = f"{self.storage_path}/{aggregate_id}.jsonl"
            events = []
            
            with open(file_path, 'r') as f:
                for line in f:
                    event_data = json.loads(line.strip())
                    if event_data['version'] >= from_version:
                        # Reconstruction minimale de l'événement
                        events.append(self._reconstruct_event(event_data))
            
            return events
            
        except FileNotFoundError:
            return []
        except Exception as e:
            logger.error(f"Erreur lecture événements {aggregate_id}: {str(e)}")
            return []
    
    def get_events_by_type(self, event_type: EventType, limit: int = 100) -> List[DomainEvent]:
        """Récupère les événements par type"""
        # TODO: Implémenter une recherche plus efficace
        return []
    
    def _reconstruct_event(self, event_data: Dict[str, Any]) -> DomainEvent:
        """Reconstruit un événement depuis les données"""
        # Reconstruction basique - à améliorer selon les besoins
        class GenericEvent(DomainEvent):
            pass
        
        return GenericEvent(
            event_id=event_data['event_id'],
            event_type=EventType(event_data['event_type']),
            aggregate_id=event_data['aggregate_id'],
            occurred_at=datetime.fromisoformat(event_data['occurred_at']),
            version=event_data['version'],
            metadata=event_data['metadata']
        )


class DatabaseEventStore(IEventStore):
    """Store d'événements en base de données (production)"""
    
    def __init__(self, db_session_factory):
        self.db_session_factory = db_session_factory
    
    def append(self, event: DomainEvent) -> None:
        """Ajoute un événement au store"""
        # TODO: Implémenter avec table events en DB
        pass
    
    def get_events(self, aggregate_id: str, from_version: int = 0) -> List[DomainEvent]:
        """Récupère les événements pour un agrégat"""
        # TODO: Implémenter la lecture depuis DB
        return []
    
    def get_events_by_type(self, event_type: EventType, limit: int = 100) -> List[DomainEvent]:
        """Récupère les événements par type"""
        # TODO: Implémenter la recherche par type
        return []


class NLPEventPublisher(INLPEventPublisher):
    """Publisher d'événements NLP utilisant le bus d'événements"""
    
    def __init__(self, event_bus: IEventBus):
        self.event_bus = event_bus
    
    def publish_analysis_completed(self, result) -> None:
        """Publie un événement d'analyse terminée"""
        event = AnalysisCompletedEvent(
            event_id=f"analysis_completed_{uuid.uuid4()}",
            aggregate_id=result.analysis_id,
            occurred_at=datetime.utcnow(),
            result=result
        )
        self.event_bus.publish(event)
    
    def publish_analysis_failed(self, analysis_id: str, error: str) -> None:
        """Publie un événement d'échec d'analyse"""
        event = AnalysisFailedEvent(
            event_id=f"analysis_failed_{uuid.uuid4()}",
            aggregate_id=analysis_id,
            occurred_at=datetime.utcnow(),
            error_message=error,
            error_type="processing_error"
        )
        self.event_bus.publish(event)
    
    def publish_batch_completed(self, results) -> None:
        """Publie un événement de batch terminé"""
        event = BatchCompletedEvent(
            event_id=f"batch_completed_{uuid.uuid4()}",
            aggregate_id=f"batch_{datetime.utcnow().timestamp()}",
            occurred_at=datetime.utcnow(),
            results=results,
            total_count=len(results),
            success_count=len(results),
            failure_count=0
        )
        self.event_bus.publish(event)


# Event Handlers Infrastructure

class LoggingEventHandler(IEventHandler):
    """Handler pour logger tous les événements"""
    
    def can_handle(self, event: DomainEvent) -> bool:
        return True
    
    async def handle(self, event: DomainEvent) -> None:
        logger.info(
            f"Événement: {event.event_type.value} | "
            f"Agrégat: {event.aggregate_id} | "
            f"Timestamp: {event.occurred_at} | "
            f"Metadata: {event.metadata}"
        )


class MetricsEventHandler(IEventHandler):
    """Handler pour collecter des métriques depuis les événements"""
    
    def __init__(self):
        self.metrics = {
            'events_processed': 0,
            'analyses_completed': 0,
            'analyses_failed': 0,
            'average_confidence': 0,
            'confidence_samples': []
        }
    
    def can_handle(self, event: DomainEvent) -> bool:
        return event.event_type in [
            EventType.ANALYSIS_COMPLETED,
            EventType.ANALYSIS_FAILED,
            EventType.BATCH_COMPLETED
        ]
    
    async def handle(self, event: DomainEvent) -> None:
        self.metrics['events_processed'] += 1
        
        if event.event_type == EventType.ANALYSIS_COMPLETED:
            self.metrics['analyses_completed'] += 1
            confidence = event.metadata.get('confidence', 0)
            self.metrics['confidence_samples'].append(confidence)
            
            # Calculer la confiance moyenne
            if self.metrics['confidence_samples']:
                self.metrics['average_confidence'] = sum(self.metrics['confidence_samples']) / len(self.metrics['confidence_samples'])
        
        elif event.event_type == EventType.ANALYSIS_FAILED:
            self.metrics['analyses_failed'] += 1
        
        elif event.event_type == EventType.BATCH_COMPLETED:
            success_count = event.metadata.get('success_count', 0)
            failure_count = event.metadata.get('failure_count', 0)
            self.metrics['analyses_completed'] += success_count
            self.metrics['analyses_failed'] += failure_count
    
    def get_metrics(self) -> Dict[str, Any]:
        """Retourne les métriques collectées"""
        return self.metrics.copy()


class CacheInvalidationEventHandler(IEventHandler):
    """Handler pour invalider le cache lors de certains événements"""
    
    def __init__(self, cache_manager):
        self.cache_manager = cache_manager
    
    def can_handle(self, event: DomainEvent) -> bool:
        return event.event_type in [
            EventType.CONFIGURATION_UPDATED,
            EventType.ANALYSIS_COMPLETED  # Invalider stats après nouvelle analyse
        ]
    
    async def handle(self, event: DomainEvent) -> None:
        if event.event_type == EventType.CONFIGURATION_UPDATED:
            # Invalider tout le cache pour ce secteur
            sector = event.metadata.get('sector', '')
            if sector:
                self.cache_manager.invalidate_cache(f"*{sector}*")
        
        elif event.event_type == EventType.ANALYSIS_COMPLETED:
            # Invalider les caches de statistiques
            self.cache_manager.invalidate_cache("stats:*")
            self.cache_manager.invalidate_cache("summary:*")


# Factory pour créer l'infrastructure événementielle

class EventInfrastructureFactory:
    """Factory pour créer l'infrastructure événementielle"""
    
    @staticmethod
    def create_development_setup() -> tuple[IEventBus, IEventStore, INLPEventPublisher]:
        """Crée une configuration pour le développement"""
        event_store = FileEventStore()
        event_bus = InMemoryEventBus()
        event_bus.set_event_store(event_store)
        
        # Configurer des handlers par défaut
        logging_handler = LoggingEventHandler()
        metrics_handler = MetricsEventHandler()
        
        for event_type in EventType:
            event_bus.subscribe(event_type, logging_handler)
            if metrics_handler.can_handle_type(event_type):
                event_bus.subscribe(event_type, metrics_handler)
        
        event_publisher = NLPEventPublisher(event_bus)
        
        return event_bus, event_store, event_publisher
    
    @staticmethod
    def create_production_setup(db_session_factory, cache_manager) -> tuple[IEventBus, IEventStore, INLPEventPublisher]:
        """Crée une configuration pour la production"""
        event_store = DatabaseEventStore(db_session_factory)
        event_bus = InMemoryEventBus()  # ou RedisEventBus pour la scalabilité
        event_bus.set_event_store(event_store)
        
        # Handlers production
        logging_handler = LoggingEventHandler()
        metrics_handler = MetricsEventHandler()
        cache_handler = CacheInvalidationEventHandler(cache_manager)
        
        for event_type in EventType:
            event_bus.subscribe(event_type, logging_handler)
            if metrics_handler.can_handle_type(event_type):
                event_bus.subscribe(event_type, metrics_handler)
            if cache_handler.can_handle_type(event_type):
                event_bus.subscribe(event_type, cache_handler)
        
        event_publisher = NLPEventPublisher(event_bus)
        
        return event_bus, event_store, event_publisher