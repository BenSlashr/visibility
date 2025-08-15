"""
Dependency Injection Container pour l'architecture NLP
Configuration et assembly des composants
"""

import logging
import time
from typing import Optional
from functools import lru_cache
from sqlalchemy.orm import Session

from ..domain.services import NLPAnalysisService, NLPStatsService, NLPQualityService
from ..domain.ports import (
    INLPAnalyzer, 
    INLPResultRepository, 
    INLPConfigurationRepository,
    INLPEventPublisher,
    INLPMetricsCollector,
    INLPCacheManager,
    ISectorDetector
)
from ..infrastructure.repositories import SQLNLPResultRepository, FileNLPConfigurationRepository
from ..infrastructure.legacy_config import SafeLegacyConfigurationRepository
from ..infrastructure.analyzers import CompositeNLPAnalyzer
from ..infrastructure.events import EventInfrastructureFactory, NLPEventPublisher
from ..infrastructure.cache import CacheFactory
from ..application.handlers import NLPCommandHandler, NLPQueryHandler
from ...core.database import get_db

logger = logging.getLogger(__name__)


class NLPContainer:
    """Container DI pour les services NLP"""
    
    def __init__(self):
        self._instances = {}
        self._initialized = False
    
    def initialize(self, environment: str = "development"):
        """Initialise le container selon l'environnement"""
        if self._initialized:
            return
        
        logger.info(f"Initialisation du container NLP pour l'environnement: {environment}")
        
        try:
            # Configuration selon l'environnement
            if environment == "production":
                self._setup_production()
            elif environment == "test":
                self._setup_test()
            else:
                self._setup_development()
            
            self._initialized = True
            logger.info("Container NLP initialisé avec succès")
            
        except Exception as e:
            logger.error(f"Erreur initialisation container NLP: {str(e)}")
            raise
    
    def _setup_development(self):
        """Configuration pour développement"""
        # Repositories
        config_repo = SafeLegacyConfigurationRepository()
        result_repo = SQLNLPResultRepository(lambda: next(get_db()))
        
        # Cache
        cache_manager = CacheFactory.create_development_cache()
        
        # Events
        event_bus, event_store, event_publisher = EventInfrastructureFactory.create_development_setup()
        
        # Metrics (stub pour développement)
        metrics_collector = DevelopmentMetricsCollector()
        
        # Analyzer
        analyzer = CompositeNLPAnalyzer(config_repo)
        
        # Services domaine
        analysis_service = NLPAnalysisService(
            analyzer=analyzer,
            result_repository=result_repo,
            event_publisher=event_publisher,
            metrics_collector=metrics_collector,
            cache_manager=cache_manager
        )
        
        stats_service = NLPStatsService(result_repo)
        quality_service = NLPQualityService(result_repo)
        
        # Handlers application
        command_handler = NLPCommandHandler(analysis_service, stats_service, quality_service)
        query_handler = NLPQueryHandler(analysis_service, stats_service, quality_service)
        
        # Stocker les instances
        self._instances.update({
            'config_repository': config_repo,
            'result_repository': result_repo,
            'cache_manager': cache_manager,
            'event_bus': event_bus,
            'event_store': event_store,
            'event_publisher': event_publisher,
            'metrics_collector': metrics_collector,
            'analyzer': analyzer,
            'analysis_service': analysis_service,
            'stats_service': stats_service,
            'quality_service': quality_service,
            'command_handler': command_handler,
            'query_handler': query_handler
        })
    
    def _setup_production(self):
        """Configuration pour production"""
        # TODO: Configuration Redis, monitoring, etc.
        self._setup_development()  # Temporaire
    
    def _setup_test(self):
        """Configuration pour tests"""
        # TODO: Mocks et test doubles
        self._setup_development()  # Temporaire
    
    def get(self, service_name: str):
        """Récupère un service du container"""
        if not self._initialized:
            raise RuntimeError("Container non initialisé")
        
        if service_name not in self._instances:
            raise KeyError(f"Service '{service_name}' non trouvé dans le container")
        
        return self._instances[service_name]
    
    def get_command_handler(self) -> NLPCommandHandler:
        """Récupère le command handler"""
        return self.get('command_handler')
    
    def get_query_handler(self) -> NLPQueryHandler:
        """Récupère le query handler"""
        return self.get('query_handler')


class DevelopmentMetricsCollector(INLPMetricsCollector):
    """Collecteur de métriques pour développement"""
    
    def __init__(self):
        self._metrics = {
            'analysis_durations': [],
            'confidence_scores': [],
            'errors': []
        }
    
    def record_analysis_duration(self, duration_ms: float) -> None:
        self._metrics['analysis_durations'].append(duration_ms)
    
    def record_analysis_confidence(self, confidence: float) -> None:
        self._metrics['confidence_scores'].append(confidence)
    
    def record_error(self, error_type: str, error_message: str) -> None:
        self._metrics['errors'].append({
            'type': error_type,
            'message': error_message,
            'timestamp': time.time()
        })
    
    def get_performance_metrics(self) -> dict:
        durations = self._metrics['analysis_durations']
        confidences = self._metrics['confidence_scores']
        
        return {
            'total_analyses': len(durations),
            'avg_duration_ms': sum(durations) / len(durations) if durations else 0,
            'avg_confidence': sum(confidences) / len(confidences) if confidences else 0,
            'error_count': len(self._metrics['errors'])
        }


# Instance globale du container
_container: Optional[NLPContainer] = None


def get_container() -> NLPContainer:
    """Factory pour récupérer le container global"""
    global _container
    
    if _container is None:
        _container = NLPContainer()
        # Initialiser selon variable d'environnement
        import os
        environment = os.getenv('ENVIRONMENT', 'development')
        _container.initialize(environment)
    
    return _container


# Dependencies FastAPI

def get_command_handler() -> NLPCommandHandler:
    """Dependency pour récupérer le command handler"""
    return get_container().get_command_handler()


def get_query_handler() -> NLPQueryHandler:
    """Dependency pour récupérer le query handler"""
    return get_container().get_query_handler()


def get_nlp_analyzer() -> INLPAnalyzer:
    """Dependency pour récupérer l'analyzer"""
    return get_container().get('analyzer')


def get_cache_manager() -> INLPCacheManager:
    """Dependency pour récupérer le cache manager"""
    return get_container().get('cache_manager')


def get_analysis_service() -> NLPAnalysisService:
    """Dependency pour récupérer le service d'analyse"""
    return get_container().get('analysis_service')


def get_stats_service() -> NLPStatsService:
    """Dependency pour récupérer le service de stats"""
    return get_container().get('stats_service')


def get_quality_service() -> NLPQualityService:
    """Dependency pour récupérer le service de qualité"""
    return get_container().get('quality_service')