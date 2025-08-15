from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case

from app.core.deps import get_database_session
from app.models.analysis import Analysis
from app.models.analysis_source import AnalysisSource
from app.schemas.source import SourceListItem, SourceDomainSummary
from app.models.project import Competitor
from app.models.prompt import PromptTag


router = APIRouter()


@router.get("/", response_model=List[SourceListItem])
def list_sources(
    project_id: Optional[str] = Query(None),
    prompt_id: Optional[str] = Query(None),
    domain: Optional[str] = Query(None),
    search: Optional[str] = Query(None, description="Recherche full-text sur url/title/snippet"),
    tag: Optional[str] = Query(None, description="Filtrer par tag de prompt"),
    # Filtres avancés alignés avec l'UI
    brand_mentioned: Optional[bool] = Query(None, description="Filtrer par mention de marque (true/false)"),
    has_link: Optional[bool] = Query(None, description="Filtrer les analyses avec lien vers le site"),
    exclude_competitors: bool = Query(False, description="Exclure les domaines concurrents (si project_id)"),
    unique_by_domain: bool = Query(False, description="Limiter à une URL par domaine (selon tri)"),
    sort: str = Query("date_desc", regex="^(date_desc|date_asc|domain)$"),
    date_range: Optional[str] = Query(None, description="last7|last30|last90"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_database_session)
):
    q = db.query(AnalysisSource, Analysis).join(Analysis, AnalysisSource.analysis_id == Analysis.id)
    if project_id:
        q = q.filter(Analysis.project_id == project_id)
    if prompt_id:
        q = q.filter(Analysis.prompt_id == prompt_id)
    if domain:
        q = q.filter(AnalysisSource.domain == domain)
    if search:
        like = f"%{search}%"
        q = q.filter(
            (AnalysisSource.url.like(like)) |
            (AnalysisSource.title.like(like)) |
            (AnalysisSource.snippet.like(like))
        )

    # Filtre par tag (via prompts)
    if tag:
        prompt_ids_subq = db.query(PromptTag.prompt_id).filter(PromptTag.tag_name == tag).subquery()
        q = q.filter(Analysis.prompt_id.in_(prompt_ids_subq))

    # Filtre mention marque
    if brand_mentioned is not None:
        q = q.filter(Analysis.brand_mentioned == brand_mentioned)

    # Période
    if date_range in {"last7", "last30", "last90"}:
        from datetime import datetime, timedelta
        days = 7 if date_range == 'last7' else (30 if date_range == 'last30' else 90)
        cutoff = datetime.utcnow() - timedelta(days=days)
        q = q.filter(AnalysisSource.created_at >= cutoff)

    # Filtre lien vers le site (basé sur l'analyse)
    if has_link is not None:
        if has_link:
            q = q.filter(Analysis.website_linked == True)
        else:
            q = q.filter(Analysis.website_linked == False)

    # Exclure concurrents dynamiquement (sécurité supplémentaire)
    competitor_domains: Optional[set] = None
    if exclude_competitors and project_id:
        try:
            rows = db.query(Competitor.website).filter(Competitor.project_id == project_id).all()
            competitor_domains = set()
            from urllib.parse import urlparse
            for (site,) in rows:
                if not site:
                    continue
                try:
                    parsed = urlparse(site if site.startswith('http') else f'http://{site}')
                    host = (parsed.netloc or '').lower()
                    if host.startswith('www.'):
                        host = host[4:]
                    if host:
                        competitor_domains.add(host)
                except Exception:
                    continue
        except Exception:
            competitor_domains = None

    # Tri
    if sort == 'date_asc':
        q = q.order_by(AnalysisSource.created_at.asc())
    elif sort == 'domain':
        q = q.order_by(AnalysisSource.domain.asc(), AnalysisSource.created_at.desc())
    else:
        q = q.order_by(AnalysisSource.created_at.desc())

    # Récupération brute (on peut sur-échantillonner pour unique_by_domain)
    base_rows = q.all() if unique_by_domain else q.offset(skip).limit(limit).all()

    # Construction et post-filtrage
    items: List[SourceListItem] = []
    for s, a in base_rows:
        # Exclure concurrents si demandé
        if competitor_domains and (s.domain or ''):
            d = (s.domain or '').lower()
            if d in competitor_domains or any(d.endswith('.' + cd) for cd in competitor_domains):
                continue
        items.append(SourceListItem(
            id=s.id,
            created_at=s.created_at,
            updated_at=s.updated_at,
            analysis_id=s.analysis_id,
            prompt_id=a.prompt_id,
            prompt_name=a.prompt.name if a.prompt else '',
            ai_model_used=a.ai_model_used,
            url=s.url,
            domain=s.domain,
            title=s.title,
            snippet=s.snippet,
            citation_label=s.citation_label,
        ))

    # Unicité par domaine (garder le premier selon tri appliqué)
    if unique_by_domain:
        seen = set()
        unique_items: List[SourceListItem] = []
        for it in items:
            key = (it.domain or '').lower()
            if key and key not in seen:
                seen.add(key)
                unique_items.append(it)
        # Pagination après déduplication
        items = unique_items[skip:skip + limit]

    return items


@router.get("/domains", response_model=List[SourceDomainSummary])
def list_domains(
    project_id: Optional[str] = Query(None),
    prompt_id: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    tag: Optional[str] = Query(None, description="Filtrer par tag de prompt"),
    exclude_competitors: bool = Query(False),
    date_range: Optional[str] = Query(None, description="last7|last30|last90"),
    db: Session = Depends(get_database_session)
):
    q = db.query(
        AnalysisSource.domain.label('domain'),
        func.count(func.distinct(AnalysisSource.url)).label('pages'),
        func.count(func.distinct(AnalysisSource.analysis_id)).label('analyses'),
        # Agrégations spécifiques
        func.sum(case((Analysis.brand_mentioned == True, 1), else_=0)).label('me_mentions'),
        func.sum(case((Analysis.website_linked == True, 1), else_=0)).label('me_links'),
        # Approx competitor mentions: ranking_position not null or brand_mentioned False but competitor context
        # MVP: compter les analyses avec ranking_position non nul
        func.sum(case((Analysis.ranking_position != None, 1), else_=0)).label('competitor_mentions'),
        func.min(AnalysisSource.created_at).label('first_seen'),
        func.max(AnalysisSource.created_at).label('last_seen')
    ).join(Analysis, AnalysisSource.analysis_id == Analysis.id)

    if project_id:
        q = q.filter(Analysis.project_id == project_id)
    if prompt_id:
        q = q.filter(Analysis.prompt_id == prompt_id)
    if search:
        like = f"%{search}%"
        q = q.filter(AnalysisSource.domain.like(like))
    if tag:
        prompt_ids_subq = db.query(PromptTag.prompt_id).filter(PromptTag.tag_name == tag).subquery()
        q = q.filter(Analysis.prompt_id.in_(prompt_ids_subq))
    if date_range in {"last7", "last30", "last90"}:
        from datetime import datetime, timedelta
        days = 7 if date_range == 'last7' else (30 if date_range == 'last30' else 90)
        cutoff = datetime.utcnow() - timedelta(days=days)
        q = q.filter(AnalysisSource.created_at >= cutoff)

    # Exclure concurrents: déjà filtré à l'insertion, mais on ajoute une safety si un champ dédié existe plus tard
    # Ici: pas d'info directe concurrent => no-op (placeholder)

    q = q.group_by(AnalysisSource.domain).order_by(func.count(func.distinct(AnalysisSource.url)).desc())

    rows = q.all()
    result: List[SourceDomainSummary] = []
    for r in rows:
        analyses = int(r.analyses or 0)
        me_links = int(r.me_links or 0)
        me_mentions = int(r.me_mentions or 0)
        result.append(SourceDomainSummary(
            id=f"{r.domain}",
            created_at=r.first_seen,
            updated_at=r.last_seen,
            domain=r.domain or '',
            pages=int(r.pages or 0),
            analyses=analyses,
            me_mentions=me_mentions,
            me_links=me_links,
            competitor_mentions=int(r.competitor_mentions or 0),
            me_link_rate=(me_links / analyses) if analyses > 0 else 0.0,
            me_mention_rate=(me_mentions / analyses) if analyses > 0 else 0.0,
            first_seen=r.first_seen,
            last_seen=r.last_seen,
        ))
    return [r for r in result if r.domain]


@router.get("/opportunities", response_model=List[SourceDomainSummary])
def list_opportunities(
    project_id: str = Query(..., description="Projet requis pour détecter la présence"),
    prompt_id: Optional[str] = Query(None),
    tag: Optional[str] = Query(None, description="Filtrer par tag de prompt"),
    date_range: Optional[str] = Query(None, description="last7|last30|last90"),
    db: Session = Depends(get_database_session)
):
    """
    Domaines fréquemment cités dans les sources où le site du projet n'est pas mentionné/lié dans l'analyse.
    Hypothèse MVP: une analyse sans `website_linked` est considérée "non présente".
    """
    q = db.query(
        AnalysisSource.domain.label('domain'),
        func.count(func.distinct(AnalysisSource.url)).label('pages'),
        func.count(func.distinct(AnalysisSource.analysis_id)).label('analyses'),
        func.sum(case((Analysis.ranking_position != None, 1), else_=0)).label('competitor_mentions'),
        func.min(AnalysisSource.created_at).label('first_seen'),
        func.max(AnalysisSource.created_at).label('last_seen')
    ).join(Analysis, AnalysisSource.analysis_id == Analysis.id)

    q = q.filter(Analysis.project_id == project_id)
    if prompt_id:
        q = q.filter(Analysis.prompt_id == prompt_id)
    if tag:
        prompt_ids_subq = db.query(PromptTag.prompt_id).filter(PromptTag.tag_name == tag).subquery()
        q = q.filter(Analysis.prompt_id.in_(prompt_ids_subq))

    # Opportunité = analyses où le site n'est pas lié
    q = q.filter(Analysis.website_linked == False)

    if date_range in {"last7", "last30", "last90"}:
        from datetime import datetime, timedelta
        days = 7 if date_range == 'last7' else (30 if date_range == 'last30' else 90)
        cutoff = datetime.utcnow() - timedelta(days=days)
        q = q.filter(AnalysisSource.created_at >= cutoff)

    q = q.group_by(AnalysisSource.domain).order_by(func.count(func.distinct(AnalysisSource.url)).desc())

    rows = q.all()
    return [
        SourceDomainSummary(
            id=f"{r.domain}",
            created_at=r.first_seen,
            updated_at=r.last_seen,
            domain=r.domain or '',
            pages=int(r.pages or 0),
            analyses=int(r.analyses or 0),
            me_mentions=0,
            me_links=0,
            competitor_mentions=int(r.competitor_mentions or 0),
            me_link_rate=0.0,
            me_mention_rate=0.0,
            first_seen=r.first_seen,
            last_seen=r.last_seen,
        ) for r in rows if r.domain
    ]



