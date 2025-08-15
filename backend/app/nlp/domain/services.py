"""
Services du domaine NLP
Contiennent la logique métier pure
"""

import hashlib
import time
from typing import Dict, List, Optional, Any
from datetime import datetime

from .entities import NLPAnalysisResult, NLPProjectSummary, NLPGlobalStats
from .ports import (
    INLPAnalyzer,
    INLPResultRepository,
    INLPEventPublisher,
    INLPMetricsCollector,
    INLPCacheManager,
    ISectorDetector
)


class NLPAnalysisService:
    """Service principal pour l'analyse NLP"""
    
    def __init__(
        self,
        analyzer: INLPAnalyzer,
        result_repository: INLPResultRepository,
        event_publisher: INLPEventPublisher,
        metrics_collector: INLPMetricsCollector,
        cache_manager: Optional[INLPCacheManager] = None,
        sector_detector: Optional[ISectorDetector] = None
    ):
        self.analyzer = analyzer
        self.result_repository = result_repository
        self.event_publisher = event_publisher
        self.metrics_collector = metrics_collector
        self.cache_manager = cache_manager
        self.sector_detector = sector_detector
    
    def analyze_content(
        self, 
        analysis_id: str,
        prompt: str, 
        ai_response: str, 
        sector: Optional[str] = None,
        project_description: Optional[str] = None
    ) -> NLPAnalysisResult:
        """
        Analyse un contenu et sauvegarde le résultat
        
        Args:
            analysis_id: ID unique de l'analyse
            prompt: Prompt utilisé
            ai_response: Réponse de l'IA
            sector: Secteur (optionnel, auto-détecté si non fourni)
            project_description: Description du projet pour auto-détection
            
        Returns:
            Résultat de l'analyse NLP
        """
        start_time = time.time()
        
        try:
            # Auto-détection du secteur si nécessaire
            if not sector and self.sector_detector and project_description:
                sector = self.sector_detector.detect_sector(
                    project_description, 
                    [ai_response]
                )
            
            sector = sector or 'general'
            
            # Vérifier le cache si disponible
            if self.cache_manager:
                content_hash = self._generate_content_hash(prompt, ai_response, sector)
                cached_result = self.cache_manager.get_cached_result(content_hash)
                if cached_result:
                    # Mettre à jour l'analysis_id pour le cache hit
                    cached_result.analysis_id = analysis_id
                    self.result_repository.save_result(cached_result)
                    self.metrics_collector.record_analysis_duration(time.time() - start_time)
                    return cached_result
            
            # Effectuer l'analyse
            result = self.analyzer.analyze(prompt, ai_response, sector)
            result.analysis_id = analysis_id
            result.created_at = datetime.utcnow()
            
            # Sauvegarder le résultat
            success = self.result_repository.save_result(result)
            if not success:
                raise Exception("Échec de la sauvegarde du résultat NLP")
            
            # Mettre en cache si disponible
            if self.cache_manager:
                self.cache_manager.cache_result(content_hash, result)
            
            # Collecter les métriques
            duration = time.time() - start_time
            self.metrics_collector.record_analysis_duration(duration)
            self.metrics_collector.record_analysis_confidence(result.global_confidence)
            
            # Publier l'événement de succès
            self.event_publisher.publish_analysis_completed(result)
            
            return result
            
        except Exception as e:
            # Collecter l'erreur
            self.metrics_collector.record_error("analysis_failed", str(e))
            
            # Publier l'événement d'échec
            self.event_publisher.publish_analysis_failed(analysis_id, str(e))
            
            raise e
    
    def get_analysis_result(self, analysis_id: str) -> Optional[NLPAnalysisResult]:
        """Récupère le résultat d'une analyse"""
        return self.result_repository.get_result(analysis_id)
    
    def reanalyze_content(self, analysis_id: str, prompt: str, ai_response: str, sector: str) -> NLPAnalysisResult:
        """Re-analyse un contenu (force, ignore le cache)"""
        start_time = time.time()
        
        try:
            # Supprimer l'ancien résultat
            self.result_repository.delete_result(analysis_id)
            
            # Invalider le cache pour ce contenu
            if self.cache_manager:
                content_hash = self._generate_content_hash(prompt, ai_response, sector)
                self.cache_manager.invalidate_cache(content_hash)
            
            # Re-analyser
            result = self.analyzer.analyze(prompt, ai_response, sector)
            result.analysis_id = analysis_id
            result.created_at = datetime.utcnow()
            
            # Sauvegarder
            self.result_repository.save_result(result)
            
            # Métriques
            duration = time.time() - start_time
            self.metrics_collector.record_analysis_duration(duration)
            self.metrics_collector.record_analysis_confidence(result.global_confidence)
            
            # Événement
            self.event_publisher.publish_analysis_completed(result)
            
            return result
            
        except Exception as e:
            self.metrics_collector.record_error("reanalysis_failed", str(e))
            self.event_publisher.publish_analysis_failed(analysis_id, str(e))
            raise e
    
    def analyze_batch(self, analysis_requests: List[Dict[str, Any]]) -> List[NLPAnalysisResult]:
        """
        Analyse un batch de contenus
        
        Args:
            analysis_requests: Liste de requêtes avec les clés:
                - analysis_id
                - prompt
                - ai_response
                - sector (optionnel)
                
        Returns:
            Liste des résultats d'analyse
        """
        results = []
        errors = []
        
        for request in analysis_requests:
            try:
                result = self.analyze_content(
                    analysis_id=request['analysis_id'],
                    prompt=request['prompt'],
                    ai_response=request['ai_response'],
                    sector=request.get('sector'),
                    project_description=request.get('project_description')
                )
                results.append(result)
            except Exception as e:
                errors.append({
                    'analysis_id': request['analysis_id'],
                    'error': str(e)
                })
        
        # Publier l'événement de batch terminé
        if results:
            self.event_publisher.publish_batch_completed(results)
        
        return results
    
    def _generate_content_hash(self, prompt: str, ai_response: str, sector: str) -> str:
        """Génère un hash unique pour le contenu"""
        content = f"{prompt}||{ai_response}||{sector}||{self.analyzer.get_version()}"
        return hashlib.sha256(content.encode()).hexdigest()


class NLPStatsService:
    """Service pour les statistiques et résumés NLP"""
    
    def __init__(self, result_repository: INLPResultRepository):
        self.result_repository = result_repository
    
    def get_global_statistics(self) -> NLPGlobalStats:
        """Récupère les statistiques globales"""
        return self.result_repository.get_global_stats()
    
    def get_project_summary(self, project_id: str, limit: int = 100) -> NLPProjectSummary:
        """Récupère le résumé pour un projet"""
        return self.result_repository.get_project_summary(project_id, limit)
    
    def get_project_trends(self, project_id: str, days: int = 30) -> Dict[str, Any]:
        """
        Calcule les tendances pour un projet sur une période
        
        Args:
            project_id: ID du projet
            days: Nombre de jours à analyser
            
        Returns:
            Données de tendances
        """
        results = self.result_repository.get_results_for_project(project_id, limit=1000)
        
        # Filtrer par date si nécessaire
        # TODO: Implémenter le filtrage par date dans le repository
        
        # Grouper par période (jour/semaine selon la durée)
        if days <= 30:
            # Groupement par jour
            periods = self._group_by_day(results, days)
        else:
            # Groupement par semaine
            periods = self._group_by_week(results, days)
        
        return {
            'project_id': project_id,
            'periods': periods,
            'total_analyses': len(results),
            'period_type': 'day' if days <= 30 else 'week'
        }
    
    def _group_by_day(self, results: List[NLPAnalysisResult], days: int) -> List[Dict[str, Any]]:
        """Groupe les résultats par jour"""
        # TODO: Implémenter le groupement par jour
        return []
    
    def _group_by_week(self, results: List[NLPAnalysisResult], days: int) -> List[Dict[str, Any]]:
        """Groupe les résultats par semaine"""
        # TODO: Implémenter le groupement par semaine
        return []


class NLPQualityService:
    """Service pour l'évaluation de la qualité NLP"""
    
    def __init__(self, result_repository: INLPResultRepository):
        self.result_repository = result_repository
    
    def evaluate_analysis_quality(self, analysis_id: str) -> Dict[str, Any]:
        """Évalue la qualité d'une analyse"""
        result = self.result_repository.get_result(analysis_id)
        if not result:
            return {'error': 'Analysis not found'}
        
        quality_score = self._calculate_quality_score(result)
        
        return {
            'analysis_id': analysis_id,
            'quality_score': quality_score,
            'is_high_quality': result.is_high_quality(),
            'confidence_level': result.seo_intent.get_confidence_level().value,
            'issues': self._identify_quality_issues(result),
            'recommendations': self._generate_recommendations(result)
        }
    
    def _calculate_quality_score(self, result: NLPAnalysisResult) -> float:
        """Calcule un score de qualité pour l'analyse"""
        scores = []
        
        # Score de confiance globale (40%)
        scores.append(result.global_confidence * 0.4)
        
        # Score de confiance SEO (30%)
        scores.append(result.seo_intent.confidence * 0.3)
        
        # Score de richesse des topics (20%)
        topic_score = min(1.0, len(result.business_topics) / 5) * 0.2
        scores.append(topic_score)
        
        # Score des entités (10%)
        entity_count = sum(len(entities) for entities in result.sector_entities.values())
        entity_score = min(1.0, entity_count / 10) * 0.1
        scores.append(entity_score)
        
        return sum(scores)
    
    def _identify_quality_issues(self, result: NLPAnalysisResult) -> List[str]:
        """Identifie les problèmes de qualité"""
        issues = []
        
        if result.global_confidence < 0.5:
            issues.append("Confiance globale faible")
        
        if not result.business_topics:
            issues.append("Aucun topic business détecté")
        
        if not result.sector_entities:
            issues.append("Aucune entité sectorielle détectée")
        
        if len(result.semantic_keywords) < 3:
            issues.append("Peu de mots-clés sémantiques extraits")
        
        return issues
    
    def _generate_recommendations(self, result: NLPAnalysisResult) -> List[str]:
        """Génère des recommandations d'amélioration"""
        recommendations = []
        
        if result.global_confidence < 0.7:
            recommendations.append("Enrichir la configuration de mots-clés pour ce secteur")
        
        if not result.business_topics:
            recommendations.append("Ajouter des mots-clés business spécifiques au secteur")
        
        return recommendations