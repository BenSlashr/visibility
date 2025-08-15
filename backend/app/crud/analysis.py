from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc, and_, case
from datetime import datetime, timedelta

from .base import CRUDBase
from ..models.analysis import Analysis, AnalysisCompetitor
from ..schemas.analysis import AnalysisCreate, AnalysisUpdate, AnalysisStats, ProjectAnalysisStats

class CRUDAnalysis(CRUDBase[Analysis, AnalysisCreate, AnalysisUpdate]):
    def create_with_competitors(self, db: Session, *, obj_in: AnalysisCreate) -> Analysis:
        """Crée une analyse avec les données des concurrents"""
        # Créer l'analyse principale
        analysis_data = obj_in.dict(exclude={'competitor_analyses'})
        # Convertir le dict variables_used en JSON string
        if 'variables_used' in analysis_data:
            import json
            analysis_data['variables_used'] = json.dumps(analysis_data['variables_used'])
        
        db_analysis = Analysis(**analysis_data)
        db.add(db_analysis)
        db.flush()  # Pour obtenir l'ID
        
        # Ajouter les analyses des concurrents
        for competitor_analysis in obj_in.competitor_analyses:
            competitor_data = competitor_analysis.dict()
            competitor_data['analysis_id'] = db_analysis.id
            db_competitor_analysis = AnalysisCompetitor(**competitor_data)
            db.add(db_competitor_analysis)
        
        db.commit()
        db.refresh(db_analysis)
        return db_analysis
    
    def get_with_relations(self, db: Session, id: str) -> Optional[Analysis]:
        """Récupère une analyse avec toutes ses relations"""
        analysis = db.query(Analysis).options(
            joinedload(Analysis.competitors),
            joinedload(Analysis.prompt),
            joinedload(Analysis.project)
        ).filter(Analysis.id == id).first()
        
        # Reconvertir variables_used de JSON string vers dict
        if analysis and analysis.variables_used:
            import json
            try:
                if isinstance(analysis.variables_used, str):
                    analysis.variables_used = json.loads(analysis.variables_used)
            except (json.JSONDecodeError, TypeError):
                analysis.variables_used = {}
        elif analysis:
            analysis.variables_used = {}
            
        return analysis
    
    def get_by_project(self, db: Session, project_id: str, *, skip: int = 0, limit: int = 100) -> List[Analysis]:
        """Récupère les analyses d'un projet avec les données des concurrents"""
        analyses = db.query(Analysis).options(
            joinedload(Analysis.competitors),
            joinedload(Analysis.prompt),
            joinedload(Analysis.project)
        ).filter(
            Analysis.project_id == project_id
        ).order_by(desc(Analysis.created_at)).offset(skip).limit(limit).all()
        
        # Reconvertir variables_used de JSON string vers dict pour chaque analyse
        for analysis in analyses:
            if analysis.variables_used:
                import json
                try:
                    if isinstance(analysis.variables_used, str):
                        analysis.variables_used = json.loads(analysis.variables_used)
                except (json.JSONDecodeError, TypeError):
                    analysis.variables_used = {}
            else:
                analysis.variables_used = {}
                
        return analyses
    
    def get_by_prompt(self, db: Session, prompt_id: str, *, skip: int = 0, limit: int = 100) -> List[Analysis]:
        """Récupère les analyses d'un prompt"""
        return db.query(Analysis).filter(
            Analysis.prompt_id == prompt_id
        ).order_by(desc(Analysis.created_at)).offset(skip).limit(limit).all()
    
    def get_recent(self, db: Session, days: int = 7, limit: int = 50) -> List[Analysis]:
        """Récupère les analyses récentes"""
        since_date = datetime.utcnow() - timedelta(days=days)
        return db.query(Analysis).filter(
            Analysis.created_at >= since_date
        ).order_by(desc(Analysis.created_at)).limit(limit).all()
    
    def get_with_brand_mentions(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[Analysis]:
        """Récupère les analyses où la marque est mentionnée"""
        return db.query(Analysis).filter(
            Analysis.brand_mentioned == True
        ).order_by(desc(Analysis.created_at)).offset(skip).limit(limit).all()
    
    def get_with_rankings(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[Analysis]:
        """Récupère les analyses avec position dans un classement"""
        return db.query(Analysis).filter(
            Analysis.ranking_position.isnot(None)
        ).order_by(Analysis.ranking_position.asc()).offset(skip).limit(limit).all()
    
    def get_stats_by_project(self, db: Session, project_id: str) -> ProjectAnalysisStats:
        """Calcule les statistiques d'analyses pour un projet"""
        # Requête principale pour les stats
        stats = db.query(
            func.count(Analysis.id).label('total_analyses'),
            func.sum(case((Analysis.brand_mentioned == True, 1), else_=0)).label('brand_mentions'),
            func.sum(case((Analysis.website_mentioned == True, 1), else_=0)).label('website_mentions'),
            func.sum(case((Analysis.website_linked == True, 1), else_=0)).label('website_links'),
            func.sum(Analysis.cost_estimated).label('total_cost'),
            func.sum(Analysis.tokens_used).label('total_tokens'),
            func.avg(Analysis.processing_time_ms).label('avg_processing_time'),
            func.min(Analysis.ranking_position).label('top_ranking_position'),
            func.max(Analysis.created_at).label('last_analysis')
        ).filter(Analysis.project_id == project_id).first()
        
        if not stats or stats.total_analyses == 0:
            return ProjectAnalysisStats(
                project_id=project_id,
                project_name="",  # À enrichir depuis le project
                total_analyses=0,
                brand_mentions=0,
                website_mentions=0,
                website_links=0,
                average_visibility_score=0.0,
                total_cost=0.0,
                total_tokens=0,
                average_processing_time=0.0,
                top_ranking_position=None,
                last_analysis=None,
                brand_mention_rate=0.0,
                website_mention_rate=0.0,
                website_link_rate=0.0,
                analyses_last_7_days=0,
                analyses_last_30_days=0,
                cost_last_7_days=0.0,
                cost_last_30_days=0.0
            )
        
        # Calculer le score de visibilité moyen
        visibility_scores = db.query(Analysis).filter(Analysis.project_id == project_id).all()
        avg_visibility = sum(analysis.visibility_score for analysis in visibility_scores) / len(visibility_scores) if visibility_scores else 0
        
        # Calculer les taux
        total_analyses = stats.total_analyses or 0
        brand_mention_rate = (stats.brand_mentions or 0) / total_analyses if total_analyses > 0 else 0
        website_mention_rate = (stats.website_mentions or 0) / total_analyses if total_analyses > 0 else 0
        website_link_rate = (stats.website_links or 0) / total_analyses if total_analyses > 0 else 0
        
        # Calculer les stats par période
        now = datetime.now()
        seven_days_ago = now - timedelta(days=7)
        thirty_days_ago = now - timedelta(days=30)
        
        # Analyses des 7 derniers jours
        analyses_7d = db.query(func.count(Analysis.id), func.sum(Analysis.cost_estimated)).filter(
            Analysis.project_id == project_id,
            Analysis.created_at >= seven_days_ago
        ).first()
        
        # Analyses des 30 derniers jours
        analyses_30d = db.query(func.count(Analysis.id), func.sum(Analysis.cost_estimated)).filter(
            Analysis.project_id == project_id,
            Analysis.created_at >= thirty_days_ago
        ).first()
        
        return ProjectAnalysisStats(
            project_id=project_id,
            project_name="",  # À enrichir depuis le project
            total_analyses=total_analyses,
            brand_mentions=stats.brand_mentions or 0,
            website_mentions=stats.website_mentions or 0,
            website_links=stats.website_links or 0,
            average_visibility_score=avg_visibility,
            total_cost=float(stats.total_cost or 0),
            total_tokens=stats.total_tokens or 0,
            average_processing_time=float(stats.avg_processing_time or 0),
            top_ranking_position=stats.top_ranking_position,
            last_analysis=stats.last_analysis,
            brand_mention_rate=brand_mention_rate,
            website_mention_rate=website_mention_rate,
            website_link_rate=website_link_rate,
            analyses_last_7_days=analyses_7d[0] or 0 if analyses_7d else 0,
            analyses_last_30_days=analyses_30d[0] or 0 if analyses_30d else 0,
            cost_last_7_days=float(analyses_7d[1] or 0) if analyses_7d else 0.0,
            cost_last_30_days=float(analyses_30d[1] or 0) if analyses_30d else 0.0
        )
    
    def get_global_stats(self, db: Session) -> AnalysisStats:
        """Calcule les statistiques globales"""
        stats = db.query(
            func.count(Analysis.id).label('total_analyses'),
            func.sum(case((Analysis.brand_mentioned == True, 1), else_=0)).label('brand_mentions'),
            func.sum(case((Analysis.website_mentioned == True, 1), else_=0)).label('website_mentions'),
            func.sum(case((Analysis.website_linked == True, 1), else_=0)).label('website_links'),
            func.sum(Analysis.cost_estimated).label('total_cost'),
            func.sum(Analysis.tokens_used).label('total_tokens'),
            func.avg(Analysis.processing_time_ms).label('avg_processing_time'),
            func.min(Analysis.ranking_position).label('top_ranking_position')
        ).first()
        
        if not stats or stats.total_analyses == 0:
            return AnalysisStats()
        
        # Calculer le score de visibilité moyen
        visibility_scores = db.query(Analysis).all()
        avg_visibility = sum(analysis.visibility_score for analysis in visibility_scores) / len(visibility_scores) if visibility_scores else 0
        
        return AnalysisStats(
            total_analyses=stats.total_analyses or 0,
            brand_mentions=stats.brand_mentions or 0,
            website_mentions=stats.website_mentions or 0,
            website_links=stats.website_links or 0,
            average_visibility_score=avg_visibility,
            total_cost=float(stats.total_cost or 0),
            total_tokens=stats.total_tokens or 0,
            average_processing_time=float(stats.avg_processing_time or 0),
            top_ranking_position=stats.top_ranking_position
        )
    
    def search_by_ai_response(self, db: Session, search_term: str, *, skip: int = 0, limit: int = 100) -> List[Analysis]:
        """Recherche dans les réponses IA"""
        return db.query(Analysis).filter(
            Analysis.ai_response.contains(search_term)
        ).order_by(desc(Analysis.created_at)).offset(skip).limit(limit).all()
    
    def get_best_performing(self, db: Session, limit: int = 10) -> List[Analysis]:
        """Récupère les analyses avec les meilleurs scores de visibilité"""
        analyses = db.query(Analysis).all()
        # Trier par score de visibilité (calculé dynamiquement)
        sorted_analyses = sorted(analyses, key=lambda x: x.visibility_score, reverse=True)
        return sorted_analyses[:limit]
    
    def get_cost_summary_by_period(self, db: Session, days: int = 30) -> Dict[str, Any]:
        """Résumé des coûts par période"""
        since_date = datetime.utcnow() - timedelta(days=days)
        
        stats = db.query(
            func.sum(Analysis.cost_estimated).label('total_cost'),
            func.sum(Analysis.tokens_used).label('total_tokens'),
            func.count(Analysis.id).label('total_analyses'),
            func.avg(Analysis.cost_estimated).label('avg_cost_per_analysis')
        ).filter(Analysis.created_at >= since_date).first()
        
        return {
            'period_days': days,
            'total_cost': float(stats.total_cost or 0),
            'total_tokens': stats.total_tokens or 0,
            'total_analyses': stats.total_analyses or 0,
            'avg_cost_per_analysis': float(stats.avg_cost_per_analysis or 0),
            'cost_per_token': float(stats.total_cost / stats.total_tokens) if stats.total_tokens else 0
        }

# Instance globale
crud_analysis = CRUDAnalysis(Analysis) 