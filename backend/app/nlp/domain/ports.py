"""
Ports et interfaces pour le domaine NLP
Contrats que doivent respecter les implémentations
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from .entities import (
    NLPAnalysisResult, 
    NLPProjectSummary, 
    NLPGlobalStats,
    SEOIntentType
)


class INLPAnalyzer(ABC):
    """Interface pour les analyseurs NLP"""
    
    @abstractmethod
    def analyze(self, prompt: str, ai_response: str, sector: str) -> NLPAnalysisResult:
        """Analyse un texte et retourne les résultats NLP"""
        pass
    
    @abstractmethod
    def get_supported_sectors(self) -> List[str]:
        """Retourne la liste des secteurs supportés"""
        pass
    
    @abstractmethod
    def get_version(self) -> str:
        """Retourne la version de l'analyseur"""
        pass


class INLPConfigurationRepository(ABC):
    """Interface pour la gestion de la configuration NLP"""
    
    @abstractmethod
    def get_keywords_for_sector(self, sector: str) -> Dict[str, Any]:
        """Récupère les mots-clés pour un secteur"""
        pass
    
    @abstractmethod
    def get_seo_intent_keywords(self) -> Dict[SEOIntentType, Dict[str, Any]]:
        """Récupère les mots-clés pour les intentions SEO"""
        pass
    
    @abstractmethod
    def get_business_topic_keywords(self, sector: str) -> Dict[str, Any]:
        """Récupère les mots-clés pour les topics business"""
        pass
    
    @abstractmethod
    def update_configuration(self, sector: str, config: Dict[str, Any]) -> bool:
        """Met à jour la configuration pour un secteur"""
        pass
    
    @abstractmethod
    def get_configuration_version(self, sector: str) -> str:
        """Retourne la version de la configuration"""
        pass


class INLPResultRepository(ABC):
    """Interface pour la persistance des résultats NLP"""
    
    @abstractmethod
    def save_result(self, result: NLPAnalysisResult) -> bool:
        """Sauvegarde un résultat d'analyse"""
        pass
    
    @abstractmethod
    def get_result(self, analysis_id: str) -> Optional[NLPAnalysisResult]:
        """Récupère un résultat d'analyse"""
        pass
    
    @abstractmethod
    def get_results_for_project(self, project_id: str, limit: int = 100) -> List[NLPAnalysisResult]:
        """Récupère les résultats pour un projet"""
        pass
    
    @abstractmethod
    def delete_result(self, analysis_id: str) -> bool:
        """Supprime un résultat d'analyse"""
        pass
    
    @abstractmethod
    def get_global_stats(self) -> NLPGlobalStats:
        """Récupère les statistiques globales"""
        pass
    
    @abstractmethod
    def get_project_summary(self, project_id: str, limit: int = 100) -> NLPProjectSummary:
        """Récupère le résumé pour un projet"""
        pass


class INLPEventPublisher(ABC):
    """Interface pour la publication d'événements NLP"""
    
    @abstractmethod
    def publish_analysis_completed(self, result: NLPAnalysisResult) -> None:
        """Publie un événement d'analyse terminée"""
        pass
    
    @abstractmethod
    def publish_analysis_failed(self, analysis_id: str, error: str) -> None:
        """Publie un événement d'échec d'analyse"""
        pass
    
    @abstractmethod
    def publish_batch_completed(self, results: List[NLPAnalysisResult]) -> None:
        """Publie un événement de batch terminé"""
        pass


class INLPMetricsCollector(ABC):
    """Interface pour la collecte de métriques NLP"""
    
    @abstractmethod
    def record_analysis_duration(self, duration_ms: float) -> None:
        """Enregistre la durée d'une analyse"""
        pass
    
    @abstractmethod
    def record_analysis_confidence(self, confidence: float) -> None:
        """Enregistre le niveau de confiance"""
        pass
    
    @abstractmethod
    def record_error(self, error_type: str, error_message: str) -> None:
        """Enregistre une erreur"""
        pass
    
    @abstractmethod
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Récupère les métriques de performance"""
        pass


class ISectorDetector(ABC):
    """Interface pour la détection automatique de secteur"""
    
    @abstractmethod
    def detect_sector(self, project_description: str, analysis_samples: List[str]) -> str:
        """Détecte automatiquement le secteur d'un projet"""
        pass
    
    @abstractmethod
    def get_confidence_score(self, sector: str, text: str) -> float:
        """Calcule la confiance pour un secteur donné"""
        pass


class INLPCacheManager(ABC):
    """Interface pour la gestion du cache NLP"""
    
    @abstractmethod
    def get_cached_result(self, content_hash: str) -> Optional[NLPAnalysisResult]:
        """Récupère un résultat en cache"""
        pass
    
    @abstractmethod
    def cache_result(self, content_hash: str, result: NLPAnalysisResult, ttl_seconds: int = 3600) -> None:
        """Met en cache un résultat"""
        pass
    
    @abstractmethod
    def invalidate_cache(self, pattern: str = "*") -> None:
        """Invalide le cache selon un pattern"""
        pass
    
    @abstractmethod
    def get_cache_stats(self) -> Dict[str, Any]:
        """Récupère les statistiques du cache"""
        pass