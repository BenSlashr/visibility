"""
Commands pour la couche application NLP
Pattern CQRS - Commands pour les opérations d'écriture
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod


@dataclass
class Command(ABC):
    """Commande de base"""
    pass


@dataclass
class AnalyzeContentCommand(Command):
    """Commande pour analyser un contenu"""
    analysis_id: str
    prompt: str
    ai_response: str
    sector: Optional[str] = None
    project_description: Optional[str] = None
    force_reanalysis: bool = False


@dataclass
class ReanalyzeContentCommand(Command):
    """Commande pour re-analyser un contenu"""
    analysis_id: str
    prompt: str
    ai_response: str
    sector: str
    invalidate_cache: bool = True


@dataclass
class BatchAnalyzeCommand(Command):
    """Commande pour analyser un batch de contenus"""
    analysis_requests: List[Dict[str, Any]]
    parallel_processing: bool = True
    max_workers: int = 5


@dataclass
class UpdateNLPConfigurationCommand(Command):
    """Commande pour mettre à jour la configuration NLP"""
    sector: str
    configuration: Dict[str, Any]
    version: str
    auto_invalidate_cache: bool = True


@dataclass
class InvalidateCacheCommand(Command):
    """Commande pour invalider le cache"""
    pattern: str = "*"
    reason: str = "manual"


@dataclass
class EnablePluginCommand(Command):
    """Commande pour activer/désactiver un plugin"""
    plugin_name: str
    enabled: bool


@dataclass
class OptimizeAnalysisQualityCommand(Command):
    """Commande pour optimiser la qualité d'analyse d'un projet"""
    project_id: str
    target_confidence: float = 0.8
    max_analyses_to_reprocess: int = 100


# Command Results

@dataclass
class CommandResult:
    """Résultat d'une commande"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    errors: Optional[List[str]] = None


@dataclass
class AnalyzeContentResult(CommandResult):
    """Résultat d'analyse de contenu"""
    analysis_id: str
    confidence: float
    processing_time_ms: float
    cache_hit: bool = False


@dataclass
class BatchAnalyzeResult(CommandResult):
    """Résultat d'analyse en batch"""
    total_requested: int
    successful_count: int
    failed_count: int
    average_confidence: float
    total_processing_time_ms: float
    failed_analysis_ids: List[str]


@dataclass
class QualityOptimizationResult(CommandResult):
    """Résultat d'optimisation de qualité"""
    project_id: str
    analyses_reprocessed: int
    quality_improvement: float
    before_average_confidence: float
    after_average_confidence: float