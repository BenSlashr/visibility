"""
Handlers pour les Commands et Queries
Orchestration des services et coordination des opérations
"""

import logging
import time
import asyncio
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from .commands import *
from .queries import *
from ..domain.services import NLPAnalysisService, NLPStatsService, NLPQualityService
from ..domain.entities import NLPAnalysisResult

logger = logging.getLogger(__name__)


class NLPCommandHandler:
    """Handler pour les commandes NLP"""
    
    def __init__(
        self,
        analysis_service: NLPAnalysisService,
        stats_service: NLPStatsService,
        quality_service: NLPQualityService
    ):
        self.analysis_service = analysis_service
        self.stats_service = stats_service
        self.quality_service = quality_service
    
    async def handle_analyze_content(self, command: AnalyzeContentCommand) -> AnalyzeContentResult:
        """Handle l'analyse de contenu"""
        start_time = time.time()
        cache_hit = False
        
        try:
            # Vérifier si re-analyse forcée
            if command.force_reanalysis and self.analysis_service.cache_manager:
                content_hash = self.analysis_service._generate_content_hash(
                    command.prompt, command.ai_response, command.sector or 'general'
                )
                self.analysis_service.cache_manager.invalidate_cache(content_hash)
            
            # Effectuer l'analyse
            result = self.analysis_service.analyze_content(
                analysis_id=command.analysis_id,
                prompt=command.prompt,
                ai_response=command.ai_response,
                sector=command.sector,
                project_description=command.project_description
            )
            
            processing_time = (time.time() - start_time) * 1000
            
            return AnalyzeContentResult(
                success=True,
                message="Analyse terminée avec succès",
                analysis_id=result.analysis_id,
                confidence=result.global_confidence,
                processing_time_ms=processing_time,
                cache_hit=cache_hit
            )
            
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            logger.error(f"Erreur analyse contenu {command.analysis_id}: {str(e)}")
            
            return AnalyzeContentResult(
                success=False,
                message=f"Échec de l'analyse: {str(e)}",
                analysis_id=command.analysis_id,
                confidence=0,
                processing_time_ms=processing_time,
                errors=[str(e)]
            )
    
    async def handle_reanalyze_content(self, command: ReanalyzeContentCommand) -> AnalyzeContentResult:
        """Handle la re-analyse de contenu"""
        start_time = time.time()
        
        try:
            result = self.analysis_service.reanalyze_content(
                analysis_id=command.analysis_id,
                prompt=command.prompt,
                ai_response=command.ai_response,
                sector=command.sector
            )
            
            processing_time = (time.time() - start_time) * 1000
            
            return AnalyzeContentResult(
                success=True,
                message="Re-analyse terminée avec succès",
                analysis_id=result.analysis_id,
                confidence=result.global_confidence,
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            logger.error(f"Erreur re-analyse contenu {command.analysis_id}: {str(e)}")
            
            return AnalyzeContentResult(
                success=False,
                message=f"Échec de la re-analyse: {str(e)}",
                analysis_id=command.analysis_id,
                confidence=0,
                processing_time_ms=processing_time,
                errors=[str(e)]
            )
    
    async def handle_batch_analyze(self, command: BatchAnalyzeCommand) -> BatchAnalyzeResult:
        """Handle l'analyse en batch"""
        start_time = time.time()
        
        try:
            if command.parallel_processing and len(command.analysis_requests) > 1:
                # Traitement parallèle
                results = await self._process_batch_parallel(
                    command.analysis_requests, 
                    command.max_workers
                )
            else:
                # Traitement séquentiel
                results = await self._process_batch_sequential(command.analysis_requests)
            
            # Calculer les statistiques
            successful_results = [r for r in results if r is not None]
            failed_count = len(command.analysis_requests) - len(successful_results)
            
            average_confidence = (
                sum(r.global_confidence for r in successful_results) / len(successful_results)
                if successful_results else 0
            )
            
            processing_time = (time.time() - start_time) * 1000
            
            return BatchAnalyzeResult(
                success=True,
                message=f"Batch traité: {len(successful_results)}/{len(command.analysis_requests)} réussis",
                total_requested=len(command.analysis_requests),
                successful_count=len(successful_results),
                failed_count=failed_count,
                average_confidence=average_confidence,
                total_processing_time_ms=processing_time,
                failed_analysis_ids=[]  # TODO: tracker les échecs
            )
            
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            logger.error(f"Erreur batch analyse: {str(e)}")
            
            return BatchAnalyzeResult(
                success=False,
                message=f"Échec du batch: {str(e)}",
                total_requested=len(command.analysis_requests),
                successful_count=0,
                failed_count=len(command.analysis_requests),
                average_confidence=0,
                total_processing_time_ms=processing_time,
                failed_analysis_ids=[],
                errors=[str(e)]
            )
    
    async def _process_batch_parallel(
        self, 
        requests: List[Dict[str, Any]], 
        max_workers: int
    ) -> List[Optional[NLPAnalysisResult]]:
        """Traitement parallèle du batch"""
        
        def process_single(request):
            try:
                return self.analysis_service.analyze_content(
                    analysis_id=request['analysis_id'],
                    prompt=request['prompt'],
                    ai_response=request['ai_response'],
                    sector=request.get('sector'),
                    project_description=request.get('project_description')
                )
            except Exception as e:
                logger.error(f"Erreur traitement {request['analysis_id']}: {str(e)}")
                return None
        
        # Utiliser ThreadPoolExecutor pour le parallélisme
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(process_single, req) for req in requests]
            results = []
            
            for future in as_completed(futures):
                try:
                    result = future.result(timeout=30)  # 30s timeout par analyse
                    results.append(result)
                except Exception as e:
                    logger.error(f"Erreur future: {str(e)}")
                    results.append(None)
        
        return results
    
    async def _process_batch_sequential(
        self, 
        requests: List[Dict[str, Any]]
    ) -> List[Optional[NLPAnalysisResult]]:
        """Traitement séquentiel du batch"""
        results = []
        
        for request in requests:
            try:
                result = self.analysis_service.analyze_content(
                    analysis_id=request['analysis_id'],
                    prompt=request['prompt'],
                    ai_response=request['ai_response'],
                    sector=request.get('sector'),
                    project_description=request.get('project_description')
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Erreur traitement {request['analysis_id']}: {str(e)}")
                results.append(None)
        
        return results
    
    async def handle_invalidate_cache(self, command: InvalidateCacheCommand) -> CommandResult:
        """Handle l'invalidation de cache"""
        try:
            if self.analysis_service.cache_manager:
                self.analysis_service.cache_manager.invalidate_cache(command.pattern)
                
                return CommandResult(
                    success=True,
                    message=f"Cache invalidé (pattern: {command.pattern}, raison: {command.reason})"
                )
            else:
                return CommandResult(
                    success=False,
                    message="Aucun gestionnaire de cache configuré"
                )
                
        except Exception as e:
            logger.error(f"Erreur invalidation cache: {str(e)}")
            return CommandResult(
                success=False,
                message=f"Échec invalidation cache: {str(e)}",
                errors=[str(e)]
            )


class NLPQueryHandler:
    """Handler pour les queries NLP"""
    
    def __init__(
        self,
        analysis_service: NLPAnalysisService,
        stats_service: NLPStatsService,
        quality_service: NLPQualityService
    ):
        self.analysis_service = analysis_service
        self.stats_service = stats_service
        self.quality_service = quality_service
    
    async def handle_get_analysis_result(self, query: GetAnalysisResultQuery) -> QueryResult:
        """Handle la récupération d'un résultat d'analyse"""
        start_time = time.time()
        
        try:
            result = self.analysis_service.get_analysis_result(query.analysis_id)
            execution_time = (time.time() - start_time) * 1000
            
            if result:
                return QueryResult(
                    success=True,
                    data=result,
                    execution_time_ms=execution_time
                )
            else:
                return QueryResult(
                    success=False,
                    message=f"Analyse {query.analysis_id} non trouvée",
                    execution_time_ms=execution_time
                )
                
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"Erreur récupération analyse {query.analysis_id}: {str(e)}")
            
            return QueryResult(
                success=False,
                message=f"Erreur récupération: {str(e)}",
                execution_time_ms=execution_time,
                errors=[str(e)]
            )
    
    async def handle_get_project_summary(self, query: GetProjectNLPSummaryQuery) -> QueryResult:
        """Handle la récupération du résumé projet"""
        start_time = time.time()
        
        try:
            summary = self.stats_service.get_project_summary(query.project_id, query.limit)
            execution_time = (time.time() - start_time) * 1000
            
            return QueryResult(
                success=True,
                data=summary,
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"Erreur résumé projet {query.project_id}: {str(e)}")
            
            return QueryResult(
                success=False,
                message=f"Erreur résumé projet: {str(e)}",
                execution_time_ms=execution_time,
                errors=[str(e)]
            )
    
    async def handle_get_global_stats(self, query: GetGlobalNLPStatsQuery) -> QueryResult:
        """Handle la récupération des stats globales"""
        start_time = time.time()
        
        try:
            stats = self.stats_service.get_global_statistics()
            execution_time = (time.time() - start_time) * 1000
            
            return QueryResult(
                success=True,
                data=stats,
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"Erreur stats globales: {str(e)}")
            
            return QueryResult(
                success=False,
                message=f"Erreur stats globales: {str(e)}",
                execution_time_ms=execution_time,
                errors=[str(e)]
            )
    
    async def handle_get_project_trends(self, query: GetProjectNLPTrendsQuery) -> QueryResult:
        """Handle la récupération des tendances projet"""
        start_time = time.time()
        
        try:
            trends = self.stats_service.get_project_trends(query.project_id, query.days)
            execution_time = (time.time() - start_time) * 1000
            
            return QueryResult(
                success=True,
                data=trends,
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"Erreur tendances projet {query.project_id}: {str(e)}")
            
            return QueryResult(
                success=False,
                message=f"Erreur tendances projet: {str(e)}",
                execution_time_ms=execution_time,
                errors=[str(e)]
            )
    
    async def handle_get_analysis_quality_report(self, query: GetAnalysisQualityReportQuery) -> QueryResult:
        """Handle la génération d'un rapport de qualité"""
        start_time = time.time()
        
        try:
            quality_data = self.quality_service.evaluate_analysis_quality(query.analysis_id)
            execution_time = (time.time() - start_time) * 1000
            
            if 'error' in quality_data:
                return QueryResult(
                    success=False,
                    message=quality_data['error'],
                    execution_time_ms=execution_time
                )
            
            # Construire le rapport
            report = QualityReport(
                analysis_id=query.analysis_id,
                overall_score=quality_data['quality_score'],
                confidence_level=quality_data['confidence_level'],
                quality_issues=quality_data['issues'],
                recommendations=quality_data['recommendations'] if query.include_recommendations else [],
                plugin_scores={},  # TODO: implémenter scores par plugin
                improvement_potential=1.0 - quality_data['quality_score']
            )
            
            return QueryResult(
                success=True,
                data=report,
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"Erreur rapport qualité {query.analysis_id}: {str(e)}")
            
            return QueryResult(
                success=False,
                message=f"Erreur rapport qualité: {str(e)}",
                execution_time_ms=execution_time,
                errors=[str(e)]
            )
    
    async def handle_get_cache_stats(self, query: GetCacheStatsQuery) -> QueryResult:
        """Handle la récupération des stats de cache"""
        start_time = time.time()
        
        try:
            if self.analysis_service.cache_manager:
                stats = self.analysis_service.cache_manager.get_cache_stats()
                execution_time = (time.time() - start_time) * 1000
                
                return QueryResult(
                    success=True,
                    data=stats,
                    execution_time_ms=execution_time
                )
            else:
                return QueryResult(
                    success=False,
                    message="Aucun gestionnaire de cache configuré"
                )
                
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"Erreur stats cache: {str(e)}")
            
            return QueryResult(
                success=False,
                message=f"Erreur stats cache: {str(e)}",
                execution_time_ms=execution_time,
                errors=[str(e)]
            )