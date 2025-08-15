from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from datetime import datetime, timedelta
from sqlalchemy.orm import joinedload
from sqlalchemy import and_
import logging
from app.models.prompt import Prompt, PromptTag
from app.models.analysis import Analysis
from app.models.analysis_topics import AnalysisTopics
from sqlalchemy.orm import Session

from app.core.deps import get_database_session
from app.core.database import get_db
from app.nlp.adapters.legacy_adapter import legacy_nlp_service
from app.crud.analysis import crud_analysis
from app.crud.project import crud_project
from app.crud.prompt import crud_prompt
from app.schemas.analysis import (
    AnalysisCreate, AnalysisUpdate, AnalysisRead, AnalysisSummary,
    AnalysisStats, ProjectAnalysisStats, AnalysisCompetitorRead,
    AnalysisSourceRead
)

logger = logging.getLogger(__name__)
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
    prompt_text: Optional[str] = Query(None, description="Filtrer par texte exact du prompt"),
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
    
    # Filtre par prompt_text (recherche partielle dans le template du prompt)
    if prompt_text:
        base_query = base_query.join(Prompt).filter(Prompt.template.contains(prompt_text))
    
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

# --- Gap Analysis (DOIT ÊTRE AVANT /{analysis_id}) ---
@router.get("/gap-analysis", response_model=Dict[str, Any])
def get_gap_analysis(
    project_id: str = Query(..., description="ID du projet"),
    date_from: Optional[str] = Query(None, description="Date de début (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Date de fin (YYYY-MM-DD)"),
    competitor_filter: Optional[str] = Query(None, description="Filtrer par concurrent spécifique"),
    priority_filter: Optional[str] = Query(None, description="Filtrer par priorité (critical, medium, low)"),
    db: Session = Depends(get_database_session)
):
    """
    Analyse des gaps de visibilité par rapport aux concurrents.
    
    Cette API identifie les requêtes où les concurrents sont bien positionnés
    mais où notre marque/site est peu ou pas mentionnée.
    """
    # Vérifier que le projet existe
    project = crud_project.get_or_404(db, project_id)
    
    # Construire la requête de base
    query = db.query(Analysis).options(
        joinedload(Analysis.competitors),
        joinedload(Analysis.prompt)
    ).filter(Analysis.project_id == project_id)
    
    # Filtres de dates
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
    
    # Charger les tags des prompts
    prompt_ids = {a.prompt_id for a in analyses}
    prompt_tags_rows = db.query(PromptTag).filter(PromptTag.prompt_id.in_(prompt_ids)).all() if prompt_ids else []
    prompt_tags: Dict[str, List[str]] = {}
    for pt in prompt_tags_rows:
        prompt_tags.setdefault(pt.prompt_id, []).append(pt.tag_name)
    
    # Analyser les gaps
    from collections import defaultdict
    
    # Structure: prompt_executed -> competitor -> [analyses]
    query_competitors = defaultdict(lambda: defaultdict(list))
    query_our_performance = defaultdict(lambda: {"brand_mentions": 0, "website_mentions": 0, "total": 0})
    
    for analysis in analyses:
        query_key = analysis.prompt_executed[:100]  # Tronquer pour grouper les requêtes similaires
        
        # Performance de notre marque/site
        perf = query_our_performance[query_key]
        perf["total"] += 1
        if analysis.brand_mentioned:
            perf["brand_mentions"] += 1
        if analysis.website_mentioned:
            perf["website_mentions"] += 1
        
        # Performance des concurrents
        for competitor in analysis.competitors:
            if competitor.is_mentioned:
                query_competitors[query_key][competitor.competitor_name].append(analysis)
    
    # Calculer les gaps
    gaps = []
    gap_id = 1
    
    for query_text, competitors in query_competitors.items():
        our_perf = query_our_performance[query_text]
        our_rate = max(
            (our_perf["brand_mentions"] / our_perf["total"]) * 100 if our_perf["total"] > 0 else 0,
            (our_perf["website_mentions"] / our_perf["total"]) * 100 if our_perf["total"] > 0 else 0
        )
        
        for competitor_name, comp_analyses in competitors.items():
            # Filtrer par concurrent si demandé
            if competitor_filter and competitor_name != competitor_filter:
                continue
                
            # Calculer les métriques du concurrent
            competitor_mentions = len(comp_analyses)
            total_analyses = our_perf["total"]
            competitor_rate = (competitor_mentions / total_analyses) * 100 if total_analyses > 0 else 0
            
            # Calculer le gap score
            gap_score = max(0, competitor_rate - our_rate)
            
            # Déterminer le type de gap
            if gap_score >= 70:
                gap_type = "critical"
            elif gap_score >= 40:
                gap_type = "medium"  
            else:
                gap_type = "low"
            
            # Filtrer par priorité si demandé
            if priority_filter and gap_type != priority_filter:
                continue
            
            # Estimer la pertinence business (basé sur les tags et le contenu)
            sample_analysis = comp_analyses[0]
            tags = prompt_tags.get(sample_analysis.prompt_id, [])
            
            # Heuristique de pertinence basée sur les tags
            high_value_tags = ["commercial", "prix", "comparaison", "meilleur", "alternative"]
            medium_value_tags = ["guide", "tutoriel", "comment"]
            
            business_relevance = "low"
            for tag in tags:
                if any(hvt in tag.lower() for hvt in high_value_tags):
                    business_relevance = "high"
                    break
                elif any(mvt in tag.lower() for mvt in medium_value_tags):
                    business_relevance = "medium"
            
            # Action suggérée
            if our_rate == 0:
                suggested_action = f"Créer contenu ciblant '{query_text[:50]}...'"
            elif our_rate < competitor_rate / 2:
                suggested_action = f"Optimiser contenu existant pour '{query_text[:50]}...'"
            else:
                suggested_action = f"Améliorer positionnement sur '{query_text[:50]}...'"
            
            # Vérifier si du contenu existe (basé sur notre taux > 0)
            content_exists = our_rate > 0
            
            gaps.append({
                "id": str(gap_id),
                "query": query_text,
                "prompt_id": sample_analysis.prompt_id,  # Ajout du prompt_id pour filtrage précis
                "competitor_name": competitor_name,
                "competitor_mentions": competitor_mentions,
                "competitor_rate": round(competitor_rate, 1),
                "our_mentions": our_perf["brand_mentions"] + our_perf["website_mentions"],
                "our_rate": round(our_rate, 1),
                "gap_score": round(gap_score, 1),
                "frequency_estimate": max(1, int(total_analyses * 4.33)),  # Estimation mensuelle
                "last_seen": comp_analyses[-1].created_at.isoformat(),
                "gap_type": gap_type,
                "business_relevance": business_relevance,
                "suggested_action": suggested_action,
                "content_exists": content_exists
            })
            
            gap_id += 1
    
    # Trier par gap score décroissant
    gaps.sort(key=lambda x: x["gap_score"], reverse=True)
    
    # Calculer les statistiques globales
    total_gaps = len(gaps)
    critical_gaps = len([g for g in gaps if g["gap_type"] == "critical"])
    medium_gaps = len([g for g in gaps if g["gap_type"] == "medium"])
    low_gaps = len([g for g in gaps if g["gap_type"] == "low"])
    
    average_gap_score = round(sum(g["gap_score"] for g in gaps) / total_gaps, 1) if total_gaps > 0 else 0
    potential_monthly_mentions = sum(g["frequency_estimate"] for g in gaps if g["gap_type"] in ["critical", "medium"])
    
    return {
        "gaps": gaps,
        "stats": {
            "total_gaps": total_gaps,
            "critical_gaps": critical_gaps,
            "medium_gaps": medium_gaps,
            "low_gaps": low_gaps,
            "average_gap_score": average_gap_score,
            "potential_monthly_mentions": potential_monthly_mentions,
            "total_analyses_analyzed": len(analyses)
        }
    }

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

# =============================================================================
# NLP ANALYSIS ENDPOINTS
# =============================================================================

@router.get("/{analysis_id}/nlp", response_model=Dict[str, Any])
def get_analysis_nlp(
    analysis_id: str = Path(..., description="ID de l'analyse"),
    db: Session = Depends(get_database_session)
):
    """
    Récupère l'analyse NLP complète d'une analyse spécifique
    """
    # Vérifier que l'analyse existe
    analysis = crud_analysis.get_or_404(db, analysis_id)
    
    # Récupérer les topics existants
    topics = legacy_nlp_service.get_analysis_topics(db, analysis_id)
    
    if not topics:
        # Si pas de topics, les générer
        topics = legacy_nlp_service.analyze_analysis(db, analysis)
        if not topics:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Impossible d'analyser le contenu NLP"
            )
    
    return {
        "analysis_id": analysis_id,
        "nlp_results": {
            "seo_intent": {
                "main_intent": topics.seo_intent,
                "confidence": topics.seo_confidence,
                "detailed_scores": topics.seo_detailed_scores
            },
            "business_topics": topics.business_topics,
            "content_type": {
                "main_type": topics.content_type,
                "confidence": topics.content_confidence
            },
            "sector_entities": topics.sector_entities,
            "semantic_keywords": topics.semantic_keywords,
            "global_confidence": topics.global_confidence,
            "sector_context": topics.sector_context,
            "processing_version": topics.processing_version,
            "created_at": topics.created_at.isoformat() if topics.created_at else None
        }
    }

@router.post("/{analysis_id}/nlp/reanalyze", response_model=Dict[str, Any])
def reanalyze_analysis_nlp(
    analysis_id: str = Path(..., description="ID de l'analyse"),
    db: Session = Depends(get_database_session)
):
    """
    Force la re-analyse NLP d'une analyse spécifique
    """
    # Vérifier que l'analyse existe
    analysis = crud_analysis.get_or_404(db, analysis_id)
    
    # Supprimer l'analyse NLP existante si elle existe
    existing_topics = db.query(AnalysisTopics).filter(
        AnalysisTopics.analysis_id == analysis_id
    ).first()
    
    if existing_topics:
        db.delete(existing_topics)
        db.commit()
    
    # Re-analyser
    topics = legacy_nlp_service.analyze_analysis(db, analysis)
    
    if not topics:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Impossible de re-analyser le contenu NLP"
        )
    
    return {
        "success": True,
        "analysis_id": analysis_id,
        "message": "Analyse NLP mise à jour avec succès",
        "new_results": topics.to_summary_dict()
    }

@router.get("/nlp/project-summary/{project_id}", response_model=Dict[str, Any])
def get_project_nlp_summary(
    project_id: str = Path(..., description="ID du projet"),
    limit: int = Query(100, ge=1, le=500, description="Nombre max d'analyses à considérer"),
    db: Session = Depends(get_database_session)
):
    """
    Résumé NLP pour toutes les analyses d'un projet
    """
    # Vérifier que le projet existe
    project = crud_project.get_or_404(db, project_id)
    
    # Obtenir le résumé
    summary = legacy_nlp_service.get_project_summary(db, project_id, limit)
    
    return {
        "project_id": project_id,
        "project_name": project.name,
        "summary": summary,
        "limit_applied": limit
    }

@router.get("/nlp/project-trends/{project_id}", response_model=Dict[str, Any])
def get_project_nlp_trends(
    project_id: str = Path(..., description="ID du projet"),
    days: int = Query(30, ge=7, le=365, description="Nombre de jours à analyser"),
    db: Session = Depends(get_database_session)
):
    """
    Analyse des tendances NLP pour un projet sur une période
    """
    # Vérifier que le projet existe
    project = crud_project.get_or_404(db, project_id)
    
    # Obtenir les tendances  
    trends = legacy_nlp_service.get_topics_trends(db, project_id, days)
    
    return {
        "project_id": project_id,
        "project_name": project.name,
        "trends_data": trends
    }

@router.post("/nlp/batch-analyze", response_model=Dict[str, Any])
def batch_analyze_nlp(
    analysis_ids: List[str],
    db: Session = Depends(get_database_session)
):
    """
    Analyse NLP en lot pour plusieurs analyses
    """
    if len(analysis_ids) > 50:  # Limite pour éviter la surcharge
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 50 analyses peuvent être traitées en une fois"
        )
    
    # Vérifier que toutes les analyses existent
    existing_analyses = db.query(Analysis.id).filter(Analysis.id.in_(analysis_ids)).all()
    existing_ids = {a.id for a in existing_analyses}
    missing_ids = set(analysis_ids) - existing_ids
    
    if missing_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analyses introuvables: {list(missing_ids)}"
        )
    
    # Analyser en lot
    results = legacy_nlp_service.analyze_batch(db, analysis_ids)
    
    success_count = sum(results.values())
    failure_count = len(analysis_ids) - success_count
    
    return {
        "total_requested": len(analysis_ids),
        "success_count": success_count,
        "failure_count": failure_count,
        "results": results,
        "success_rate": round(success_count / len(analysis_ids) * 100, 1) if analysis_ids else 0
    }

@router.post("/nlp/project-reanalyze/{project_id}", response_model=Dict[str, Any])
def reanalyze_project_nlp(
    project_id: str = Path(..., description="ID du projet"),
    db: Session = Depends(get_database_session)
):
    """
    Re-analyse complète des topics NLP d'un projet
    Utile après mise à jour des dictionnaires de mots-clés
    """
    # Vérifier que le projet existe
    project = crud_project.get_or_404(db, project_id)
    
    # Lancer la re-analyse
    result = legacy_nlp_service.reanalyze_project(db, project_id)
    
    if not result.get('success'):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get('message', 'Erreur lors de la re-analyse')
        )
    
    return {
        "project_id": project_id,
        "project_name": project.name,
        **result
    }

@router.get("/nlp/available-sectors", response_model=List[str])
def get_available_sectors():
    """
    Liste des secteurs disponibles pour la classification NLP
    """
    return legacy_nlp_service.get_available_sectors()

@router.get("/nlp/stats/global", response_model=Dict[str, Any])
def get_global_nlp_stats(
    db: Session = Depends(get_database_session)
):
    """
    Statistiques globales NLP sur toutes les analyses
    """
    return legacy_nlp_service.get_global_nlp_stats(db)

