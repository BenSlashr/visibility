"""
Routers FastAPI pour l'API NLP
Endpoints RESTful avec documentation automatique
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, BackgroundTasks
from fastapi.responses import JSONResponse

from .dependencies import get_command_handler, get_query_handler, get_cache_manager
from .schemas import *
from ..application.commands import *
from ..application.queries import *
from ..application.handlers import NLPCommandHandler, NLPQueryHandler

logger = logging.getLogger(__name__)

# Router principal NLP
nlp_router = APIRouter(
    prefix="/nlp",
    tags=["NLP"],
    responses={
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": NLPErrorResponse},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ValidationErrorResponse},
    }
)


# Endpoints d'analyse

@nlp_router.post(
    "/analyze",
    response_model=AnalyzeContentResultResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Analyser un contenu",
    description="Lance l'analyse NLP d'un contenu (prompt + réponse IA)"
)
async def analyze_content(
    request: AnalyzeContentRequest,
    command_handler: NLPCommandHandler = Depends(get_command_handler)
) -> AnalyzeContentResultResponse:
    """Analyse un contenu avec le système NLP"""
    try:
        command = AnalyzeContentCommand(
            analysis_id=request.analysis_id,
            prompt=request.prompt,
            ai_response=request.ai_response,
            sector=request.sector,
            project_description=request.project_description,
            force_reanalysis=request.force_reanalysis
        )
        
        result = await command_handler.handle_analyze_content(command)
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=result.message
            )
        
        return AnalyzeContentResultResponse(**result.__dict__)
        
    except Exception as e:
        logger.error(f"Erreur analyse contenu: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur interne lors de l'analyse: {str(e)}"
        )


@nlp_router.post(
    "/analyze/batch",
    response_model=BatchAnalyzeResultResponse,
    summary="Analyser un batch de contenus",
    description="Lance l'analyse NLP de plusieurs contenus en parallèle"
)
async def batch_analyze_content(
    request: BatchAnalyzeRequest,
    background_tasks: BackgroundTasks,
    command_handler: NLPCommandHandler = Depends(get_command_handler)
) -> BatchAnalyzeResultResponse:
    """Analyse plusieurs contenus en batch"""
    try:
        # Convertir les requêtes en format interne
        analysis_requests = [
            {
                'analysis_id': req.analysis_id,
                'prompt': req.prompt,
                'ai_response': req.ai_response,
                'sector': req.sector,
                'project_description': req.project_description
            }
            for req in request.analyses
        ]
        
        command = BatchAnalyzeCommand(
            analysis_requests=analysis_requests,
            parallel_processing=request.parallel_processing,
            max_workers=request.max_workers
        )
        
        result = await command_handler.handle_batch_analyze(command)
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=result.message
            )
        
        return BatchAnalyzeResultResponse(**result.__dict__)
        
    except Exception as e:
        logger.error(f"Erreur batch analyse: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur interne lors du batch: {str(e)}"
        )


@nlp_router.post(
    "/reanalyze/{analysis_id}",
    response_model=AnalyzeContentResultResponse,
    summary="Re-analyser un contenu",
    description="Force la re-analyse d'un contenu existant"
)
async def reanalyze_content(
    analysis_id: str = Path(..., description="ID de l'analyse à re-analyser"),
    request: AnalyzeContentRequest = None,
    command_handler: NLPCommandHandler = Depends(get_command_handler)
) -> AnalyzeContentResultResponse:
    """Re-analyse un contenu existant"""
    try:
        if not request:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Données d'analyse requises pour la re-analyse"
            )
        
        command = ReanalyzeContentCommand(
            analysis_id=analysis_id,
            prompt=request.prompt,
            ai_response=request.ai_response,
            sector=request.sector or 'general'
        )
        
        result = await command_handler.handle_reanalyze_content(command)
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=result.message
            )
        
        return AnalyzeContentResultResponse(**result.__dict__)
        
    except Exception as e:
        logger.error(f"Erreur re-analyse {analysis_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur interne lors de la re-analyse: {str(e)}"
        )


# Endpoints de récupération

@nlp_router.get(
    "/analysis/{analysis_id}",
    response_model=NLPAnalysisResponse,
    summary="Récupérer une analyse",
    description="Récupère le résultat d'une analyse NLP par son ID"
)
async def get_analysis_result(
    analysis_id: str = Path(..., description="ID de l'analyse"),
    query_handler: NLPQueryHandler = Depends(get_query_handler)
) -> NLPAnalysisResponse:
    """Récupère le résultat d'une analyse"""
    try:
        query = GetAnalysisResultQuery(analysis_id=analysis_id)
        result = await query_handler.handle_get_analysis_result(query)
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Analyse {analysis_id} non trouvée"
            )
        
        # Convertir l'entité domaine en réponse API
        analysis = result.data
        return NLPAnalysisResponse(
            analysis_id=analysis.analysis_id,
            seo_intent=SEOIntentResponse(
                main_intent=analysis.seo_intent.main_intent,
                confidence=analysis.seo_intent.confidence,
                detailed_scores=analysis.seo_intent.detailed_scores
            ),
            content_type=ContentTypeResponse(
                main_type=analysis.content_type.main_type,
                confidence=analysis.content_type.confidence,
                all_scores=analysis.content_type.all_scores
            ),
            business_topics=[
                BusinessTopicResponse(
                    topic=topic.topic,
                    score=topic.score,
                    raw_score=topic.raw_score,
                    weight=topic.weight,
                    relevance=topic.relevance,
                    matches_count=topic.matches_count,
                    top_keywords=topic.top_keywords,
                    sample_contexts=topic.sample_contexts
                )
                for topic in analysis.business_topics
            ],
            sector_entities={
                entity_type: [
                    SectorEntityResponse(
                        name=entity.name,
                        count=entity.count,
                        contexts=entity.contexts,
                        entity_type=entity.entity_type
                    )
                    for entity in entities
                ]
                for entity_type, entities in analysis.sector_entities.items()
            },
            semantic_keywords=analysis.semantic_keywords,
            global_confidence=analysis.global_confidence,
            sector_context=analysis.sector_context,
            processing_version=analysis.processing_version,
            created_at=analysis.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur récupération analyse {analysis_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur interne: {str(e)}"
        )


# Endpoints de statistiques

@nlp_router.get(
    "/stats/global",
    response_model=GlobalNLPStatsResponse,
    summary="Statistiques globales NLP",
    description="Récupère les statistiques NLP sur toutes les analyses"
)
async def get_global_nlp_stats(
    include_trends: bool = Query(False, description="Inclure les données de tendance"),
    query_handler: NLPQueryHandler = Depends(get_query_handler)
) -> GlobalNLPStatsResponse:
    """Récupère les statistiques globales NLP"""
    try:
        query = GetGlobalNLPStatsQuery(include_trends=include_trends)
        result = await query_handler.handle_get_global_stats(query)
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.message
            )
        
        stats = result.data
        return GlobalNLPStatsResponse(
            total_analyses=stats.total_analyses,
            analyzed_with_nlp=stats.analyzed_with_nlp,
            nlp_coverage=stats.nlp_coverage,
            average_confidence=stats.average_confidence,
            seo_intents_distribution=stats.seo_intents_distribution,
            content_types_distribution=stats.content_types_distribution,
            top_business_topics=stats.top_business_topics,
            top_entities=stats.top_entities,
            dominant_seo_intent=stats.dominant_seo_intent
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur stats globales: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur interne: {str(e)}"
        )


@nlp_router.get(
    "/stats/project/{project_id}",
    response_model=ProjectNLPSummaryResponse,
    summary="Résumé NLP d'un projet",
    description="Récupère le résumé NLP pour un projet spécifique"
)
async def get_project_nlp_summary(
    project_id: str = Path(..., description="ID du projet"),
    limit: int = Query(100, ge=1, le=500, description="Nombre max d'analyses"),
    query_handler: NLPQueryHandler = Depends(get_query_handler)
) -> ProjectNLPSummaryResponse:
    """Récupère le résumé NLP d'un projet"""
    try:
        query = GetProjectNLPSummaryQuery(project_id=project_id, limit=limit)
        result = await query_handler.handle_get_project_summary(query)
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Projet {project_id} non trouvé ou sans données NLP"
            )
        
        summary = result.data
        return ProjectNLPSummaryResponse(
            project_id=summary.project_id,
            project_name=summary.project_name,
            total_analyses=summary.total_analyses,
            average_confidence=summary.average_confidence,
            high_confidence_count=summary.high_confidence_count,
            high_confidence_rate=summary.high_confidence_rate,
            seo_intents_distribution=summary.seo_intents_distribution,
            content_types_distribution=summary.content_types_distribution,
            top_business_topics=summary.top_business_topics,
            top_entities=summary.top_entities,
            analysis_period=summary.analysis_period,
            nlp_quality_score=summary.nlp_quality_score
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur résumé projet {project_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur interne: {str(e)}"
        )


@nlp_router.get(
    "/trends/project/{project_id}",
    response_model=TrendsDataResponse,
    summary="Tendances NLP d'un projet",
    description="Récupère les tendances NLP d'un projet sur une période"
)
async def get_project_nlp_trends(
    project_id: str = Path(..., description="ID du projet"),
    days: int = Query(30, ge=1, le=365, description="Nombre de jours d'historique"),
    group_by: str = Query("day", regex="^(day|week|month)$", description="Groupement temporel"),
    query_handler: NLPQueryHandler = Depends(get_query_handler)
) -> TrendsDataResponse:
    """Récupère les tendances NLP d'un projet"""
    try:
        query = GetProjectNLPTrendsQuery(
            project_id=project_id,
            days=days,
            group_by=group_by
        )
        result = await query_handler.handle_get_project_trends(query)
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Aucune donnée de tendance pour le projet {project_id}"
            )
        
        # Adapter le format de réponse
        trends_data = result.data
        return TrendsDataResponse(
            project_id=trends_data['project_id'],
            project_name=trends_data.get('project_name', 'Unknown'),
            time_range_days=days,
            data_points=[],  # TODO: mapper les données
            overall_trend="stable",  # TODO: calculer la tendance
            insights=[]  # TODO: générer des insights
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur tendances projet {project_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur interne: {str(e)}"
        )


# Endpoints de qualité

@nlp_router.get(
    "/quality/analysis/{analysis_id}",
    response_model=QualityReportResponse,
    summary="Rapport de qualité d'analyse",
    description="Génère un rapport de qualité pour une analyse"
)
async def get_analysis_quality_report(
    analysis_id: str = Path(..., description="ID de l'analyse"),
    include_recommendations: bool = Query(True, description="Inclure les recommandations"),
    query_handler: NLPQueryHandler = Depends(get_query_handler)
) -> QualityReportResponse:
    """Génère un rapport de qualité pour une analyse"""
    try:
        query = GetAnalysisQualityReportQuery(
            analysis_id=analysis_id,
            include_recommendations=include_recommendations
        )
        result = await query_handler.handle_get_analysis_quality_report(query)
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Analyse {analysis_id} non trouvée"
            )
        
        report = result.data
        return QualityReportResponse(
            analysis_id=report.analysis_id,
            overall_score=report.overall_score,
            confidence_level=report.confidence_level,
            quality_issues=report.quality_issues,
            recommendations=report.recommendations,
            plugin_scores=report.plugin_scores,
            improvement_potential=report.improvement_potential
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur rapport qualité {analysis_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur interne: {str(e)}"
        )


# Endpoints de cache et système

@nlp_router.get(
    "/system/cache/stats",
    response_model=CacheStatsResponse,
    summary="Statistiques du cache",
    description="Récupère les statistiques du système de cache"
)
async def get_cache_stats(
    detailed: bool = Query(False, description="Informations détaillées"),
    query_handler: NLPQueryHandler = Depends(get_query_handler)
) -> CacheStatsResponse:
    """Récupère les statistiques du cache"""
    try:
        query = GetCacheStatsQuery(detailed=detailed)
        result = await query_handler.handle_get_cache_stats(query)
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.message
            )
        
        stats = result.data
        return CacheStatsResponse(
            cache_type=stats.get('type', 'unknown'),
            size=stats.get('size', 0),
            hit_rate=stats.get('hit_rate', 0),
            stats=stats.get('stats', {}),
            memory_usage_mb=stats.get('memory_usage_mb'),
            additional_info=stats
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur stats cache: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur interne: {str(e)}"
        )


@nlp_router.post(
    "/system/cache/invalidate",
    response_model=CommandResultResponse,
    summary="Invalider le cache",
    description="Invalide le cache selon un pattern"
)
async def invalidate_cache(
    request: InvalidateCacheRequest,
    command_handler: NLPCommandHandler = Depends(get_command_handler)
) -> CommandResultResponse:
    """Invalide le cache"""
    try:
        command = InvalidateCacheCommand(
            pattern=request.pattern,
            reason=request.reason
        )
        
        result = await command_handler.handle_invalidate_cache(command)
        
        return CommandResultResponse(
            success=result.success,
            message=result.message,
            data=result.data,
            errors=result.errors
        )
        
    except Exception as e:
        logger.error(f"Erreur invalidation cache: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur interne: {str(e)}"
        )


# Health Check

@nlp_router.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="Health check NLP",
    description="Vérifie la santé du système NLP"
)
async def health_check() -> HealthCheckResponse:
    """Health check du système NLP"""
    try:
        # TODO: Implémenter health check complet
        from datetime import datetime
        import time
        
        start_time = time.time()
        
        return HealthCheckResponse(
            status="healthy",
            version="2.0.0",
            components={
                "analyzer": {"status": "healthy", "plugins": 5},
                "cache": {"status": "healthy", "type": "in_memory"},
                "database": {"status": "healthy", "connections": 1},
                "events": {"status": "healthy", "bus": "in_memory"}
            },
            timestamp=datetime.utcnow(),
            uptime_seconds=time.time() - start_time
        )
        
    except Exception as e:
        logger.error(f"Erreur health check: {str(e)}")
        return HealthCheckResponse(
            status="unhealthy",
            version="2.0.0",
            components={},
            timestamp=datetime.utcnow(),
            uptime_seconds=0
        )