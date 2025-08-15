"""
Service NLP pour l'analyse sémantique des réponses IA
Intégration avec AdvancedTopicsClassifier et gestion des données
"""

import logging
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session

from ..models import Analysis, AnalysisTopics, Project
from ..nlp.topics_classifier import AdvancedTopicsClassifier, TopicsAnalysisError
from ..nlp.keywords_config import SECTOR_SPECIFIC_KEYWORDS

logger = logging.getLogger(__name__)


class NLPService:
    """
    Service principal pour l'analyse NLP des réponses IA
    Gère la classification, le stockage et l'agrégation des résultats
    """
    
    def __init__(self):
        self.classifiers = {}  # Cache des classificateurs par secteur
        logger.info("NLPService initialisé")
    
    def analyze_analysis(self, db: Session, analysis: Analysis) -> Optional[AnalysisTopics]:
        """
        Analyse NLP complète d'une analyse existante
        
        Args:
            db: Session de base de données
            analysis: Analyse à traiter
            
        Returns:
            AnalysisTopics créé ou None en cas d'erreur
        """
        try:
            # Récupérer le projet pour déterminer le secteur
            project = db.query(Project).filter(Project.id == analysis.project_id).first()
            if not project:
                logger.error(f"Projet introuvable pour l'analyse {analysis.id}")
                return None
            
            # Déterminer le secteur (défaut: domotique)
            sector = self._determine_project_sector(project)
            
            # Obtenir le classificateur approprié
            classifier = self._get_classifier(sector)
            
            # Classification NLP
            results = classifier.classify_full(
                prompt=analysis.prompt_executed,
                ai_response=analysis.ai_response
            )
            
            # Vérifier si une analyse NLP existe déjà
            existing_topics = db.query(AnalysisTopics).filter(
                AnalysisTopics.analysis_id == analysis.id
            ).first()
            
            if existing_topics:
                # Mise à jour
                self._update_analysis_topics(existing_topics, results, sector)
                logger.debug(f"Analyse NLP mise à jour pour l'analyse {analysis.id}")
            else:
                # Création
                existing_topics = self._create_analysis_topics(analysis.id, results, sector)
                db.add(existing_topics)
                logger.debug(f"Nouvelle analyse NLP créée pour l'analyse {analysis.id}")
            
            db.commit()
            return existing_topics
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse NLP de {analysis.id}: {e}")
            db.rollback()
            return None
    
    def analyze_batch(self, db: Session, analysis_ids: List[str]) -> Dict[str, bool]:
        """
        Analyse NLP en lot pour plusieurs analyses
        
        Args:
            db: Session de base de données
            analysis_ids: Liste des IDs d'analyses à traiter
            
        Returns:
            Dict {analysis_id: success_boolean}
        """
        results = {}
        
        # Récupérer toutes les analyses en une fois
        analyses = db.query(Analysis).filter(Analysis.id.in_(analysis_ids)).all()
        analyses_by_id = {a.id: a for a in analyses}
        
        for analysis_id in analysis_ids:
            analysis = analyses_by_id.get(analysis_id)
            if not analysis:
                results[analysis_id] = False
                continue
            
            # Analyser individuellement
            topics = self.analyze_analysis(db, analysis)
            results[analysis_id] = topics is not None
        
        logger.info(f"Analyse en lot terminée: {sum(results.values())}/{len(analysis_ids)} succès")
        return results
    
    def get_analysis_topics(self, db: Session, analysis_id: str) -> Optional[AnalysisTopics]:
        """Récupérer les topics d'une analyse"""
        return db.query(AnalysisTopics).filter(
            AnalysisTopics.analysis_id == analysis_id
        ).first()
    
    def get_project_topics_summary(self, db: Session, project_id: str, 
                                 limit: int = 100) -> Dict[str, Any]:
        """
        Résumé des topics pour un projet
        
        Args:
            db: Session de base de données
            project_id: ID du projet
            limit: Nombre max d'analyses à considérer
            
        Returns:
            Résumé des topics du projet
        """
        try:
            # Récupérer les analyses récentes avec leurs topics
            query = db.query(AnalysisTopics).join(Analysis).filter(
                Analysis.project_id == project_id
            ).order_by(Analysis.created_at.desc()).limit(limit)
            
            topics_list = query.all()
            
            if not topics_list:
                return self._get_empty_summary()
            
            # Agrégation des données
            return self._aggregate_topics_data(topics_list)
            
        except Exception as e:
            logger.error(f"Erreur lors du résumé des topics pour le projet {project_id}: {e}")
            return self._get_empty_summary()
    
    def get_topics_trends(self, db: Session, project_id: str, 
                         days: int = 30) -> Dict[str, Any]:
        """
        Analyse des tendances des topics sur une période
        
        Args:
            db: Session de base de données
            project_id: ID du projet
            days: Nombre de jours à analyser
            
        Returns:
            Données de tendances
        """
        from datetime import datetime, timedelta
        
        try:
            # Date limite
            date_limit = datetime.utcnow() - timedelta(days=days)
            
            # Récupérer les topics récents
            query = db.query(AnalysisTopics).join(Analysis).filter(
                Analysis.project_id == project_id,
                Analysis.created_at >= date_limit
            ).order_by(Analysis.created_at.asc())
            
            topics_list = query.all()
            
            return self._calculate_trends(topics_list, days)
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul des tendances pour le projet {project_id}: {e}")
            return {'trends': [], 'period_days': days, 'total_analyses': 0}
    
    def reanalyze_project(self, db: Session, project_id: str) -> Dict[str, Any]:
        """
        Re-analyse complète des topics d'un projet
        Utile après mise à jour des dictionnaires de mots-clés
        
        Args:
            db: Session de base de données
            project_id: ID du projet
            
        Returns:
            Résultat de la re-analyse
        """
        try:
            # Récupérer toutes les analyses du projet
            analyses = db.query(Analysis).filter(
                Analysis.project_id == project_id
            ).order_by(Analysis.created_at.desc()).limit(500).all()  # Limite pour performance
            
            if not analyses:
                return {'success': False, 'message': 'Aucune analyse trouvée'}
            
            # Supprimer les topics existants
            db.query(AnalysisTopics).filter(
                AnalysisTopics.analysis_id.in_([a.id for a in analyses])
            ).delete(synchronize_session=False)
            
            # Re-analyser toutes les analyses
            analysis_ids = [a.id for a in analyses]
            results = self.analyze_batch(db, analysis_ids)
            
            success_count = sum(results.values())
            
            return {
                'success': True,
                'total_analyses': len(analyses),
                'success_count': success_count,
                'failure_count': len(analyses) - success_count,
                'project_id': project_id
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la re-analyse du projet {project_id}: {e}")
            db.rollback()
            return {'success': False, 'message': str(e)}
    
    def get_available_sectors(self) -> List[str]:
        """Liste des secteurs disponibles pour la classification"""
        return list(SECTOR_SPECIFIC_KEYWORDS.keys())
    
    def _get_classifier(self, sector: str) -> AdvancedTopicsClassifier:
        """Obtenir un classificateur (avec cache)"""
        if sector not in self.classifiers:
            self.classifiers[sector] = AdvancedTopicsClassifier(project_sector=sector)
        return self.classifiers[sector]
    
    def _determine_project_sector(self, project: Project) -> str:
        """
        Déterminer le secteur d'un projet
        Logique: analyse des mots-clés, description, ou défaut
        """
        # Pour l'instant, logique simple basée sur des mots-clés dans la description
        if not project.description:
            return 'domotique'  # Défaut
        
        description_lower = project.description.lower()
        
        # Détection par mots-clés
        if any(kw in description_lower for kw in ['domotique', 'smart home', 'maison connectée', 'volet', 'store']):
            return 'domotique'
        elif any(kw in description_lower for kw in ['marketing', 'digital', 'seo', 'publicité']):
            return 'marketing_digital'
        elif any(kw in description_lower for kw in ['ecommerce', 'e-commerce', 'boutique', 'vente en ligne']):
            return 'ecommerce'
        else:
            return 'tech_general'  # Défaut générique
    
    def _create_analysis_topics(self, analysis_id: str, results: Dict[str, Any], 
                              sector: str) -> AnalysisTopics:
        """Créer un nouvel objet AnalysisTopics"""
        
        seo_intent = results['seo_intent']
        content_type = results['content_type']
        
        return AnalysisTopics(
            analysis_id=analysis_id,
            seo_intent=seo_intent['main_intent'],
            seo_confidence=seo_intent['confidence'],
            seo_detailed_scores=seo_intent['all_scores'],
            business_topics=results['business_topics'],
            content_type=content_type['main_type'],
            content_confidence=content_type['confidence'],
            sector_entities=results['sector_entities'],
            semantic_keywords=results['semantic_keywords'],
            global_confidence=results['confidence'],
            sector_context=sector,
            processing_version=results['processing_version']
        )
    
    def _update_analysis_topics(self, topics: AnalysisTopics, results: Dict[str, Any], 
                              sector: str) -> None:
        """Mettre à jour un objet AnalysisTopics existant"""
        
        seo_intent = results['seo_intent']
        content_type = results['content_type']
        
        topics.seo_intent = seo_intent['main_intent']
        topics.seo_confidence = seo_intent['confidence']
        topics.seo_detailed_scores = seo_intent['all_scores']
        topics.business_topics = results['business_topics']
        topics.content_type = content_type['main_type']
        topics.content_confidence = content_type['confidence']
        topics.sector_entities = results['sector_entities']
        topics.semantic_keywords = results['semantic_keywords']
        topics.global_confidence = results['confidence']
        topics.sector_context = sector
        topics.processing_version = results['processing_version']
    
    def _aggregate_topics_data(self, topics_list: List[AnalysisTopics]) -> Dict[str, Any]:
        """Agrégation des données de topics pour un résumé"""
        
        from collections import Counter
        
        total_analyses = len(topics_list)
        
        # Compteurs
        seo_intents = Counter(t.seo_intent for t in topics_list)
        content_types = Counter(t.content_type for t in topics_list)
        
        # Business topics (extraction des topics principaux)
        all_business_topics = []
        for topics in topics_list:
            if topics.business_topics and isinstance(topics.business_topics, list):
                all_business_topics.extend([t.get('topic') for t in topics.business_topics if t.get('topic')])
        
        business_topics_count = Counter(all_business_topics)
        
        # Entités sectorielles
        all_brands = []
        all_technologies = []
        for topics in topics_list:
            if topics.sector_entities and isinstance(topics.sector_entities, dict):
                brands = topics.sector_entities.get('brands', [])
                if isinstance(brands, list):
                    all_brands.extend([b.get('name') if isinstance(b, dict) else b for b in brands])
                
                techs = topics.sector_entities.get('technologies', [])
                if isinstance(techs, list):
                    all_technologies.extend([t.get('name') if isinstance(t, dict) else t for t in techs])
        
        brands_count = Counter(all_brands)
        technologies_count = Counter(all_technologies)
        
        # Confiance moyenne
        avg_confidence = sum(t.global_confidence for t in topics_list) / total_analyses if total_analyses > 0 else 0
        high_confidence_count = sum(1 for t in topics_list if t.is_high_confidence)
        
        return {
            'total_analyses': total_analyses,
            'average_confidence': round(avg_confidence, 2),
            'high_confidence_count': high_confidence_count,
            'high_confidence_rate': round(high_confidence_count / total_analyses * 100, 1) if total_analyses > 0 else 0,
            
            'seo_intents': {
                'distribution': dict(seo_intents.most_common()),
                'top_intent': seo_intents.most_common(1)[0] if seo_intents else None
            },
            
            'content_types': {
                'distribution': dict(content_types.most_common()),
                'top_type': content_types.most_common(1)[0] if content_types else None
            },
            
            'business_topics': {
                'top_topics': dict(business_topics_count.most_common(10)),
                'total_topics': len(business_topics_count)
            },
            
            'sector_entities': {
                'top_brands': dict(brands_count.most_common(10)),
                'top_technologies': dict(technologies_count.most_common(10)),
                'brands_diversity': len(brands_count),
                'technologies_diversity': len(technologies_count)
            }
        }
    
    def _calculate_trends(self, topics_list: List[AnalysisTopics], days: int) -> Dict[str, Any]:
        """Calcul des tendances sur une période"""
        
        from collections import defaultdict
        from datetime import datetime, timedelta
        
        # Grouper par période (par semaine pour plus de 14 jours, sinon par jour)
        period_size = 7 if days > 14 else 1
        trends_data = defaultdict(lambda: defaultdict(int))
        
        for topics in topics_list:
            if hasattr(topics, 'analysis') and topics.analysis.created_at:
                period_key = topics.analysis.created_at.strftime('%Y-%m-%d')
                if period_size == 7:
                    # Grouper par semaine
                    week_start = topics.analysis.created_at - timedelta(days=topics.analysis.created_at.weekday())
                    period_key = week_start.strftime('%Y-%m-%d')
                
                trends_data[period_key]['total'] += 1
                trends_data[period_key][f"intent_{topics.seo_intent}"] += 1
                
                if topics.content_type:
                    trends_data[period_key][f"content_{topics.content_type}"] += 1
        
        # Convertir en format utilisable
        trends = []
        for period, data in sorted(trends_data.items()):
            trends.append({
                'period': period,
                'metrics': dict(data)
            })
        
        return {
            'trends': trends,
            'period_days': days,
            'period_size': period_size,
            'total_analyses': len(topics_list)
        }
    
    def _get_empty_summary(self) -> Dict[str, Any]:
        """Résumé vide par défaut"""
        return {
            'total_analyses': 0,
            'average_confidence': 0,
            'high_confidence_count': 0,
            'high_confidence_rate': 0,
            'seo_intents': {'distribution': {}, 'top_intent': None},
            'content_types': {'distribution': {}, 'top_type': None},
            'business_topics': {'top_topics': {}, 'total_topics': 0},
            'sector_entities': {
                'top_brands': {}, 'top_technologies': {},
                'brands_diversity': 0, 'technologies_diversity': 0
            }
        }

    def get_global_nlp_stats(self, db: Session) -> Dict[str, Any]:
        """
        Statistiques globales NLP sur toutes les analyses
        
        Args:
            db: Session de base de données
            
        Returns:
            Dictionnaire avec les statistiques globales
        """
        try:
            # Compter les analyses avec et sans topics
            total_analyses = db.query(Analysis).count()
            with_topics = db.query(AnalysisTopics).count()
            
            # Répartition des intentions SEO
            seo_intents = db.query(AnalysisTopics.seo_intent, 
                                  db.func.count(AnalysisTopics.seo_intent)).group_by(
                                      AnalysisTopics.seo_intent).all()
            
            # Répartition des types de contenu (filtrer les NULL)
            content_types = db.query(AnalysisTopics.content_type,
                                   db.func.count(AnalysisTopics.content_type)).filter(
                                       AnalysisTopics.content_type.isnot(None)
                                   ).group_by(AnalysisTopics.content_type).all()
            
            # Confiance moyenne
            avg_confidence = db.query(db.func.avg(AnalysisTopics.global_confidence)).scalar() or 0
            
            return {
                "total_analyses": total_analyses,
                "analyzed_with_nlp": with_topics,
                "nlp_coverage": round(with_topics / total_analyses * 100, 1) if total_analyses > 0 else 0,
                "average_confidence": round(avg_confidence, 3),
                "seo_intents_distribution": dict(seo_intents) if seo_intents else {},
                "content_types_distribution": dict(content_types) if content_types else {}
            }
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des stats globales NLP: {str(e)}")
            # Retourner des stats vides en cas d'erreur
            return {
                "total_analyses": 0,
                "analyzed_with_nlp": 0,
                "nlp_coverage": 0,
                "average_confidence": 0,
                "seo_intents_distribution": {},
                "content_types_distribution": {}
            }


# Instance globale du service (singleton)
nlp_service = NLPService()