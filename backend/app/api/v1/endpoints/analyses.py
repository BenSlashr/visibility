from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from datetime import datetime, timedelta
from sqlalchemy.orm import joinedload
from sqlalchemy import and_
from app.models.prompt import Prompt, PromptTag
from app.models.analysis import Analysis
from sqlalchemy.orm import Session

from app.core.deps import get_database_session
from app.crud.analysis import crud_analysis
from app.crud.project import crud_project
from app.crud.prompt import crud_prompt
from app.schemas.analysis import (
    AnalysisCreate, AnalysisUpdate, AnalysisRead, AnalysisSummary,
    AnalysisStats, ProjectAnalysisStats, AnalysisCompetitorRead,
    AnalysisSourceRead
)
from app.crud.analysis_source import crud_analysis_source

router = APIRouter()

@router.get("/", response_model=List[AnalysisSummary])
def get_analyses(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre maximum d'éléments à retourner"),
    project_id: Optional[str] = Query(None, description="Filtrer par projet"),
    prompt_id: Optional[str] = Query(None, description="Filtrer par prompt"),
    brand_mentioned: Optional[bool] = Query(None, description="Filtrer par mention de marque"),
    has_ranking: Optional[bool] = Query(None, description="Filtrer par présence de classement"),
    search: Optional[str] = Query(None, description="Recherche dans les réponses IA"),
    model_id: Optional[str] = Query(None, description="Filtrer par modèle IA"),
    date_from: Optional[str] = Query(None, description="Date de début (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Date de fin (YYYY-MM-DD)"),
    tag: Optional[str] = Query(None, description="Filtrer par tag de prompt"),
    has_sources: Optional[bool] = Query(None, description="Filtrer les analyses ayant des sources"),
    db: Session = Depends(get_database_session)
):
    """
    Récupère la liste des analyses avec filtres avancés
    """
    base_query = db.query(Analysis)
    if project_id:
        base_query = base_query.filter(Analysis.project_id == project_id)
    if prompt_id:
        base_query = base_query.filter(Analysis.prompt_id == prompt_id)
    if model_id:
        base_query = base_query.filter(Analysis.ai_model_id == model_id)
    # Dates
    if date_from:
        try:
            start_dt = datetime.fromisoformat(date_from)
            base_query = base_query.filter(Analysis.created_at >= start_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Paramètre date_from invalide (ISO attendu)")
    if date_to:
        try:
            end_dt = datetime.fromisoformat(date_to)
            # Inclure toute la journée de date_to en filtrant strictement avant le jour suivant
            end_next = end_dt + timedelta(days=1)
            base_query = base_query.filter(Analysis.created_at < end_next)
        except ValueError:
            raise HTTPException(status_code=400, detail="Paramètre date_to invalide (ISO attendu)")

    if brand_mentioned is not None:
        if brand_mentioned:
            base_query = base_query.filter(Analysis.brand_mentioned == True)
        else:
            base_query = base_query.filter(Analysis.brand_mentioned == False)
    elif has_ranking is not None:
        if has_ranking:
            base_query = base_query.filter(Analysis.ranking_position.isnot(None))
        else:
            base_query = base_query.filter(Analysis.ranking_position.is_(None))
    elif search:
        base_query = base_query.filter(Analysis.ai_response.contains(search))

    # Filtre has_sources (nécessite jointure légère ou post-filtrage)
    if has_sources is not None:
        if has_sources:
            base_query = base_query.filter(Analysis.sources.any())
        else:
            base_query = base_query.filter(~Analysis.sources.any())

    # Ordonner par défaut du plus récent au plus ancien
    analyses = base_query.order_by(Analysis.created_at.desc()).offset(skip).limit(limit).all()
    # Filtre par tag (si fourni)
    if tag:
        prompt_ids = {a.prompt_id for a in analyses}
        if prompt_ids:
            prompt_tags = db.query(PromptTag).filter(PromptTag.prompt_id.in_(prompt_ids)).all()
            prompt_id_to_tags: Dict[str, List[str]] = {}
            for pt in prompt_tags:
                prompt_id_to_tags.setdefault(pt.prompt_id, []).append(pt.tag_name)
            analyses = [a for a in analyses if tag in (prompt_id_to_tags.get(a.prompt_id, []))]
    
    # Convertir en AnalysisSummary (score centralisé via propriété modèle)
    result = []
    for analysis in analyses:
        # Construire les données des concurrents
        competitors_analysis = []
        for competitor in analysis.competitors:
            competitors_analysis.append(AnalysisCompetitorRead(
                analysis_id=competitor.analysis_id,
                competitor_name=competitor.competitor_name,
                is_mentioned=competitor.is_mentioned,
                mention_context=competitor.mention_context,
                ranking_position=competitor.ranking_position,
                created_at=competitor.created_at
            ))
        
        derived_web = getattr(analysis, 'web_search_used', False)
        try:
            if not derived_web and analysis.ai_response:
                # euristique simple: présence d'urls marquées openai
                if 'utm_source=openai' in analysis.ai_response:
                    derived_web = True
        except Exception:
            pass
        analysis_summary = AnalysisSummary(
            id=analysis.id,
            prompt_id=analysis.prompt_id,
            project_id=analysis.project_id,
            brand_mentioned=analysis.brand_mentioned,
            website_mentioned=analysis.website_mentioned,
            website_linked=analysis.website_linked,
            ranking_position=analysis.ranking_position,
            ai_model_used=analysis.ai_model_used,
            tokens_used=analysis.tokens_used,
            cost_estimated=analysis.cost_estimated,
            visibility_score=analysis.visibility_score,
            web_search_used=derived_web,
            competitors_analysis=competitors_analysis,
            created_at=analysis.created_at,
            updated_at=analysis.updated_at,
            has_sources=bool(getattr(analysis, 'sources', []))
        )
        result.append(analysis_summary)
    
    return result

@router.post("/", response_model=AnalysisRead, status_code=status.HTTP_201_CREATED)
def create_analysis(
    analysis_in: AnalysisCreate,
    db: Session = Depends(get_database_session)
):
    """Crée une nouvelle analyse avec les données des concurrents"""
    # Vérifier que le prompt existe
    crud_prompt.get_or_404(db, analysis_in.prompt_id)
    
    # Vérifier que le projet existe
    crud_project.get_or_404(db, analysis_in.project_id)
    
    analysis = crud_analysis.create_with_competitors(db, obj_in=analysis_in)
    return crud_analysis.get_with_relations(db, analysis.id)

@router.get("/{analysis_id}", response_model=AnalysisRead)
def get_analysis(
    analysis_id: str,
    db: Session = Depends(get_database_session)
):
    """Récupère une analyse par ID avec toutes ses relations"""
    analysis = crud_analysis.get_with_relations(db, analysis_id)
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analyse non trouvée"
        )
    
    # Construire manuellement les competitor_analyses pour Pydantic
    competitor_analyses = []
    for competitor in analysis.competitors:
        competitor_analyses.append(AnalysisCompetitorRead(
            analysis_id=competitor.analysis_id,
            competitor_name=competitor.competitor_name,
            is_mentioned=competitor.is_mentioned,
            mention_context=competitor.mention_context,
            ranking_position=competitor.ranking_position,
            created_at=competitor.created_at
        ))
    
    # Récupérer les sources
    sources = crud_analysis_source.get_by_analysis(db, analysis.id)
    sources_read = []
    for s in sources:
        sources_read.append(AnalysisSourceRead(
            id=s.id,
            created_at=s.created_at,
            updated_at=s.updated_at,
            analysis_id=s.analysis_id,
            url=s.url,
            domain=s.domain,
            title=s.title,
            snippet=s.snippet,
            citation_label=s.citation_label,
            position=s.position,
            is_valid=s.is_valid,
            http_status=s.http_status,
            content_type=s.content_type,
            confidence=s.confidence,
            metadata=getattr(s, 'metadata_json', None),
        ))

    # Créer l'objet AnalysisRead avec les données des concurrents et sources
    analysis_dict = {
        "id": analysis.id,
        "prompt_id": analysis.prompt_id,
        "project_id": analysis.project_id,
        "prompt_executed": analysis.prompt_executed,
        "ai_response": analysis.ai_response,
        "variables_used": analysis.variables_used or {},
        "brand_mentioned": analysis.brand_mentioned,
        "website_mentioned": analysis.website_mentioned,
        "website_linked": analysis.website_linked,
        "ranking_position": analysis.ranking_position,
        "ai_model_used": analysis.ai_model_used,
        "tokens_used": analysis.tokens_used,
        "processing_time_ms": analysis.processing_time_ms,
        "cost_estimated": analysis.cost_estimated,
        "competitor_analyses": competitor_analyses,
        "sources": sources_read,
        "created_at": analysis.created_at,
        "updated_at": analysis.updated_at
    }
    
    return AnalysisRead(**analysis_dict)

@router.put("/{analysis_id}", response_model=AnalysisRead)
def update_analysis(
    analysis_id: str,
    analysis_in: AnalysisUpdate,
    db: Session = Depends(get_database_session)
):
    """Met à jour une analyse"""
    analysis = crud_analysis.get_or_404(db, analysis_id)
    analysis = crud_analysis.update(db, db_obj=analysis, obj_in=analysis_in)
    return crud_analysis.get_with_relations(db, analysis.id)

@router.delete("/{analysis_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_analysis(
    analysis_id: str,
    db: Session = Depends(get_database_session)
):
    """Supprime une analyse"""
    analysis = crud_analysis.get_or_404(db, analysis_id)
    crud_analysis.remove(db, id=analysis_id)

# Endpoints statistiques
@router.get("/stats/global", response_model=AnalysisStats)
def get_global_analysis_stats(
    db: Session = Depends(get_database_session)
):
    """Récupère les statistiques globales de toutes les analyses"""
    return crud_analysis.get_global_stats(db)

@router.get("/stats/project/{project_id}", response_model=ProjectAnalysisStats)
def get_project_analysis_stats(
    project_id: str,
    db: Session = Depends(get_database_session)
):
    """Récupère les statistiques d'analyses pour un projet spécifique"""
    project = crud_project.get_or_404(db, project_id)
    
    stats = crud_analysis.get_stats_by_project(db, project_id)
    stats.project_name = project.name
    return stats

@router.get("/stats/costs", response_model=Dict[str, Any])
def get_cost_analysis(
    days: int = Query(30, ge=1, le=365, description="Période en jours"),
    db: Session = Depends(get_database_session)
):
    """Analyse des coûts sur une période donnée"""
    return crud_analysis.get_cost_summary_by_period(db, days)

@router.get("/recent/{days}", response_model=List[AnalysisSummary])
def get_recent_analyses(
    days: int = Path(..., ge=1, le=90, description="Nombre de jours"),
    limit: int = Query(50, ge=1, le=200, description="Nombre maximum d'analyses"),
    db: Session = Depends(get_database_session)
):
    """Récupère les analyses récentes"""
    analyses = crud_analysis.get_recent(db, days=days, limit=limit)
    
    result = []
    for analysis in analyses:
        analysis_summary = AnalysisSummary(
            id=analysis.id,
            prompt_id=analysis.prompt_id,
            project_id=analysis.project_id,
            brand_mentioned=analysis.brand_mentioned,
            website_mentioned=analysis.website_mentioned,
            website_linked=analysis.website_linked,
            ranking_position=analysis.ranking_position,
            ai_model_used=analysis.ai_model_used,
            tokens_used=analysis.tokens_used,
            cost_estimated=analysis.cost_estimated,
            visibility_score=analysis.visibility_score,
            created_at=analysis.created_at,
            updated_at=analysis.updated_at
        )
        result.append(analysis_summary)
    
    return result

@router.get("/best-performing/{limit}", response_model=List[AnalysisSummary])
def get_best_performing_analyses(
    limit: int = Path(..., ge=1, le=50, description="Nombre d'analyses à retourner"),
    db: Session = Depends(get_database_session)
):
    """Récupère les analyses avec les meilleurs scores de visibilité"""
    analyses = crud_analysis.get_best_performing(db, limit=limit)
    
    result = []
    for analysis in analyses:
        analysis_summary = AnalysisSummary(
            id=analysis.id,
            prompt_id=analysis.prompt_id,
            project_id=analysis.project_id,
            brand_mentioned=analysis.brand_mentioned,
            website_mentioned=analysis.website_mentioned,
            website_linked=analysis.website_linked,
            ranking_position=analysis.ranking_position,
            ai_model_used=analysis.ai_model_used,
            tokens_used=analysis.tokens_used,
            cost_estimated=analysis.cost_estimated,
            visibility_score=analysis.visibility_score,
            created_at=analysis.created_at,
            updated_at=analysis.updated_at
        )
        result.append(analysis_summary)
    
    return result 

# --- Timeseries agrégées pour le dashboard ---
@router.get("/timeseries", response_model=Dict[str, Any])
def get_timeseries(
    project_id: str = Query(..., description="ID du projet"),
    date_from: Optional[str] = Query(None, description="Date de début ISO (inclus)"),
    date_to: Optional[str] = Query(None, description="Date de fin ISO (inclus)"),
    tag: Optional[str] = Query(None, description="Filtrer par tag de prompt"),
    model_id: Optional[str] = Query(None, description="Filtrer par modèle IA"),
    db: Session = Depends(get_database_session)
):
    """
    Retourne une série temporelle agrégée par jour pour un projet, avec filtres optionnels.
    Réponse: {
      "points": [{ date: "YYYY-MM-DD", avg_visibility_score: float, brand_mention_rate: float, website_link_rate: float, count: int }],
      "total_analyses": int
    }
    """
    # Construire le filtre de base
    query = db.query(Analysis).options(joinedload(Analysis.prompt)).filter(Analysis.project_id == project_id)
    
    # Filtre période
    if date_from:
        try:
            start_dt = datetime.fromisoformat(date_from)
            query = query.filter(Analysis.created_at >= start_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Paramètre date_from invalide (ISO attendu)")
    if date_to:
        try:
            # Inclure toute la journée de date_to: < (date_to + 1 jour)
            end_dt = datetime.fromisoformat(date_to)
            end_next = end_dt + timedelta(days=1)
            query = query.filter(Analysis.created_at < end_next)
        except ValueError:
            raise HTTPException(status_code=400, detail="Paramètre date_to invalide (ISO attendu)")
    
    # Filtre modèle IA
    if model_id:
        query = query.filter(Analysis.ai_model_id == model_id)
    
    analyses = query.all()
    
    # Filtre tag (si fourni): requiert mapping prompt -> tags
    if tag:
        # Charger les tags des prompts impliqués
        prompt_ids = {a.prompt_id for a in analyses}
        if prompt_ids:
            prompt_tags = db.query(PromptTag).filter(PromptTag.prompt_id.in_(prompt_ids)).all()
            prompt_id_to_tags: Dict[str, List[str]] = {}
            for pt in prompt_tags:
                prompt_id_to_tags.setdefault(pt.prompt_id, []).append(pt.tag_name)
            analyses = [a for a in analyses if tag in (prompt_id_to_tags.get(a.prompt_id, []))]
        else:
            analyses = []
    
    # Agrégation par jour
    from collections import defaultdict
    daily = defaultdict(lambda: {"scores": [], "brand": 0, "link": 0, "total": 0})
    for a in analyses:
        day = a.created_at.strftime("%Y-%m-%d")
        daily[day]["scores"].append(a.visibility_score or 0)
        daily[day]["brand"] += 1 if a.brand_mentioned else 0
        daily[day]["link"] += 1 if a.website_linked else 0
        daily[day]["total"] += 1
    
    points = []
    for day in sorted(daily.keys()):
        bucket = daily[day]
        avg_score = round(sum(bucket["scores"]) / len(bucket["scores"]) , 2) if bucket["scores"] else 0.0
        brand_rate = round((bucket["brand"] / bucket["total"]) * 100, 2) if bucket["total"] else 0.0
        link_rate = round((bucket["link"] / bucket["total"]) * 100, 2) if bucket["total"] else 0.0
        points.append({
            "date": day,
            "avg_visibility_score": avg_score,
            "brand_mention_rate": brand_rate,
            "website_link_rate": link_rate,
            "count": bucket["total"]
        })
    
    return {
        "points": points,
        "total_analyses": len(analyses),
        "period_analyses_count": len(analyses)
    }

# Alias stable pour éviter les collisions avec /{analysis_id}
@router.get("/stats/timeseries", response_model=Dict[str, Any])
def get_timeseries_alias(
    project_id: str = Query(..., description="ID du projet"),
    date_from: Optional[str] = Query(None, description="Date de début ISO (inclus)"),
    date_to: Optional[str] = Query(None, description="Date de fin ISO (inclus)"),
    tag: Optional[str] = Query(None, description="Filtrer par tag de prompt"),
    model_id: Optional[str] = Query(None, description="Filtrer par modèle IA"),
    db: Session = Depends(get_database_session)
):
    # Reutilise la même logique que get_timeseries
    query = db.query(Analysis).options(joinedload(Analysis.prompt)).filter(Analysis.project_id == project_id)
    if date_from:
        try:
            start_dt = datetime.fromisoformat(date_from)
            query = query.filter(Analysis.created_at >= start_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Paramètre date_from invalide (ISO attendu)")
    if date_to:
        try:
            end_dt = datetime.fromisoformat(date_to)
            end_next = end_dt + timedelta(days=1)
            query = query.filter(Analysis.created_at < end_next)
        except ValueError:
            raise HTTPException(status_code=400, detail="Paramètre date_to invalide (ISO attendu)")
    if model_id:
        query = query.filter(Analysis.ai_model_id == model_id)
    analyses = query.all()
    if tag:
        prompt_ids = {a.prompt_id for a in analyses}
        if prompt_ids:
            prompt_tags = db.query(PromptTag).filter(PromptTag.prompt_id.in_(prompt_ids)).all()
            prompt_id_to_tags: Dict[str, List[str]] = {}
            for pt in prompt_tags:
                prompt_id_to_tags.setdefault(pt.prompt_id, []).append(pt.tag_name)
            analyses = [a for a in analyses if tag in (prompt_id_to_tags.get(a.prompt_id, []))]
        else:
            analyses = []
    from collections import defaultdict
    daily = defaultdict(lambda: {"scores": [], "brand": 0, "link": 0, "total": 0})
    for a in analyses:
        day = a.created_at.strftime("%Y-%m-%d")
        daily[day]["scores"].append(a.visibility_score or 0)
        daily[day]["brand"] += 1 if a.brand_mentioned else 0
        daily[day]["link"] += 1 if a.website_linked else 0
        daily[day]["total"] += 1
    points = []
    for day in sorted(daily.keys()):
        bucket = daily[day]
        avg_score = round(sum(bucket["scores"]) / len(bucket["scores"]) , 2) if bucket["scores"] else 0.0
        brand_rate = round((bucket["brand"] / bucket["total"]) * 100, 2) if bucket["total"] else 0.0
        link_rate = round((bucket["link"] / bucket["total"]) * 100, 2) if bucket["total"] else 0.0
        points.append({
            "date": day,
            "avg_visibility_score": avg_score,
            "brand_mention_rate": brand_rate,
            "website_link_rate": link_rate,
            "count": bucket["total"]
        })
    return {
        "points": points,
        "total_analyses": len(analyses),
        "period_analyses_count": len(analyses)
    }

# --- Comparaison des modèles IA (sans coûts) ---
@router.get("/models/comparison", response_model=Dict[str, Any])
def get_models_comparison(
    project_id: str = Query(...),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    metric: Optional[str] = Query("visibility"),
    db: Session = Depends(get_database_session)
):
    """
    Retourne une comparaison des modèles IA pour un projet, agrégée par jour.
    Métriques retournées (sans coûts): score de visibilité moyen, taux de mention, taux de liens, total analyses.
    """
    query = db.query(Analysis).filter(Analysis.project_id == project_id)
    if date_from:
        try:
            start_dt = datetime.fromisoformat(date_from)
            query = query.filter(Analysis.created_at >= start_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Paramètre date_from invalide (ISO attendu)")
    if date_to:
        try:
            end_dt = datetime.fromisoformat(date_to)
            end_next = end_dt + timedelta(days=1)
            query = query.filter(Analysis.created_at < end_next)
        except ValueError:
            raise HTTPException(status_code=400, detail="Paramètre date_to invalide (ISO attendu)")

    analyses = query.all()
    
    # Grouper par modèle et jour
    from collections import defaultdict
    model_daily_scores = defaultdict(lambda: defaultdict(list))  # model_name -> day -> [scores]
    model_daily_counts = defaultdict(lambda: defaultdict(lambda: {"total": 0, "brand": 0, "link": 0}))
    model_totals = defaultdict(lambda: {"count": 0, "brand": 0, "link": 0})
    all_days = set()
    for a in analyses:
        model_name = a.ai_model_used
        day = a.created_at.strftime("%Y-%m-%d")
        all_days.add(day)
        model_daily_scores[model_name][day].append(a.visibility_score or 0)
        model_daily_counts[model_name][day]["total"] += 1
        model_daily_counts[model_name][day]["brand"] += 1 if a.brand_mentioned else 0
        model_daily_counts[model_name][day]["link"] += 1 if a.website_linked else 0
        model_totals[model_name]["count"] += 1
        model_totals[model_name]["brand"] += 1 if a.brand_mentioned else 0
        model_totals[model_name]["link"] += 1 if a.website_linked else 0

    # Construire les séries (clés stables par modèle)
    def _slugify(value: str) -> str:
        import re
        s = (value or '').lower()
        s = re.sub(r"[^a-z0-9]+", "-", s).strip('-')
        return s or 'model'

    name_to_slug: Dict[str, str] = {}
    for name in model_daily_scores.keys():
        name_to_slug[name] = _slugify(name)

    chart_data = []
    for day in sorted(all_days):
        row = {"date": day}
        for model_name in model_daily_scores.keys():
            if metric == "mentions":
                counts = model_daily_counts[model_name].get(day, {"total": 0, "brand": 0, "link": 0})
                value = round(((counts["brand"] / counts["total"]) * 100), 2) if counts["total"] else 0.0
            elif metric == "links":
                counts = model_daily_counts[model_name].get(day, {"total": 0, "brand": 0, "link": 0})
                value = round(((counts["link"] / counts["total"]) * 100), 2) if counts["total"] else 0.0
            else:
                values = model_daily_scores[model_name].get(day, [])
                value = round((sum(values) / len(values)), 2) if values else 0.0
            series_key = name_to_slug.get(model_name) or _slugify(model_name)
            row[f"model_{series_key}"] = value
        chart_data.append(row)

    # Infos modèles
    models = []
    for model_name, totals in model_totals.items():
        count = totals["count"]
        all_scores = []
        for day_values in model_daily_scores[model_name].values():
            all_scores.extend(day_values)
        avg_score = round(sum(all_scores) / len(all_scores), 2) if all_scores else 0.0
        brand_rate = round((totals["brand"] / count) * 100, 2) if count else 0.0
        link_rate = round((totals["link"] / count) * 100, 2) if count else 0.0
        models.append({
            "id": name_to_slug.get(model_name) or _slugify(model_name),
            "name": model_name,
            "provider": "",
            "avgScore": avg_score,
            "totalAnalyses": count,
            "brandMentionRate": brand_rate,
            "websiteLinkRate": link_rate,
        })

    model_ranking = sorted(models, key=lambda m: m["avgScore"], reverse=True)
    best_model = model_ranking[0] if model_ranking else None
    max_gap = 0.0
    if len(models) > 1:
        scores = [m["avgScore"] for m in models]
        max_gap = max(scores) - min(scores)

    return {
        "chartData": chart_data,
        "models": models,
        "modelRanking": model_ranking,
        "bestModel": best_model,
        "maxGap": max_gap,
        "totalAnalyses": len(analyses)
    }

# --- Résumé concurrents (share of voice) ---
@router.get("/competitors/summary", response_model=Dict[str, Any])
def get_competitors_summary(
    project_id: str = Query(...),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    db: Session = Depends(get_database_session)
):
    query = db.query(Analysis).filter(Analysis.project_id == project_id)
    if date_from:
        try:
            start_dt = datetime.fromisoformat(date_from)
            query = query.filter(Analysis.created_at >= start_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Paramètre date_from invalide (ISO attendu)")
    if date_to:
        try:
            end_dt = datetime.fromisoformat(date_to)
            query = query.filter(Analysis.created_at <= end_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Paramètre date_to invalide (ISO attendu)")

    analyses = query.options(joinedload(Analysis.competitors)).all()
    from collections import defaultdict
    totals = defaultdict(lambda: {"mentions": 0, "links": 0})
    for a in analyses:
        for c in a.competitors:
            totals[c.competitor_name]["mentions"] += 1 if c.is_mentioned else 0
            totals[c.competitor_name]["links"] += 1 if a.website_linked else 0
    summary = [
        {
            "competitor": name,
            "mentions": data["mentions"],
            "link_rate": 0.0
        }
        for name, data in totals.items()
    ]
    summary.sort(key=lambda x: x["mentions"], reverse=True)
    return {"summary": summary}

# --- Heatmap Tags x Temps ---
@router.get("/tags/heatmap", response_model=Dict[str, Any])
def get_tags_heatmap(
    project_id: str = Query(...),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    db: Session = Depends(get_database_session)
):
    query = db.query(Analysis).options(joinedload(Analysis.prompt)).filter(Analysis.project_id == project_id)
    if date_from:
        try:
            start_dt = datetime.fromisoformat(date_from)
            query = query.filter(Analysis.created_at >= start_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Paramètre date_from invalide (ISO attendu)")
    if date_to:
        try:
            end_dt = datetime.fromisoformat(date_to)
            query = query.filter(Analysis.created_at <= end_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Paramètre date_to invalide (ISO attendu)")

    analyses = query.all()
    # Construire map prompt_id -> tags
    prompt_ids = {a.prompt_id for a in analyses}
    tag_rows = db.query(PromptTag).filter(PromptTag.prompt_id.in_(prompt_ids)).all() if prompt_ids else []
    prompt_tags: Dict[str, list] = {}
    for tr in tag_rows:
        prompt_tags.setdefault(tr.prompt_id, []).append(tr.tag_name)

    from collections import defaultdict
    heat = defaultdict(lambda: defaultdict(int))  # date -> tag -> count
    for a in analyses:
        day = a.created_at.strftime("%Y-%m-%d")
        for t in prompt_tags.get(a.prompt_id, []):
            heat[day][t] += 1

    points = []
    for day in sorted(heat.keys()):
        for t, cnt in heat[day].items():
            points.append({"date": day, "tag": t, "count": cnt})
    return {"points": points}