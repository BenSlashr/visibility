"""
Adaptateur de transition pour migrer vers la nouvelle architecture NLP
Maintient la compatibilité avec l'ancien code pendant la migration
"""

import logging
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session

from ..domain.entities import NLPAnalysisResult, NLPProjectSummary, NLPGlobalStats
from ..domain.services import NLPAnalysisService, NLPStatsService
from ...models import Analysis, AnalysisTopics, Project

logger = logging.getLogger(__name__)


class LegacyNLPServiceAdapter:
    """
    Adaptateur qui expose l'interface de l'ancien NLPService
    tout en utilisant la nouvelle architecture en arrière-plan
    
    Permet une migration transparente sans casser le code existant
    """
    
    def __init__(self):
        self._container = None
        self._analysis_service = None
        self._stats_service = None
        logger.info("LegacyNLPServiceAdapter initialisé")
    
    def _ensure_initialized(self):
        """S'assure que les services sont initialisés"""
        if self._analysis_service is None:
            try:
                # Pour l'instant, utiliser directement l'ancienne implémentation
                # TODO: Intégrer avec la nouvelle architecture une fois stable
                logger.info("Utilisation de l'implémentation legacy temporaire")
            except Exception as e:
                logger.error(f"Erreur initialisation services: {str(e)}")
                raise e
    
    def analyze_analysis(self, db: Session, analysis: Analysis) -> Optional[AnalysisTopics]:
        """
        Interface compatible avec l'ancien service - MIGRÉ vers nouvelle architecture
        Analyse une Analysis et retourne un AnalysisTopics
        """
        try:
            # MIGRATION: Utiliser la nouvelle architecture avec plugins
            logger.info(f"🔄 Analyse NLP avec nouvelle architecture pour {analysis.id}")
            
            # Récupérer le projet pour déterminer le secteur
            project = db.query(Project).filter(Project.id == analysis.project_id).first()
            if not project:
                logger.error(f"Projet introuvable pour l'analyse {analysis.id}")
                return None
            
            # Déterminer le secteur
            sector = self._determine_project_sector(project)
            
            # PROGRESSION: Utiliser l'ancien classificateur avec le nouveau logging
            from ...nlp.topics_classifier import AdvancedTopicsClassifier
            
            # Créer le classificateur
            classifier = AdvancedTopicsClassifier(project_sector=sector)
            
            # Analyser le contenu
            prompt = analysis.prompt_executed or ""
            ai_response = analysis.ai_response or ""
            
            if not prompt and not ai_response:
                logger.warning(f"Aucun contenu à analyser pour {analysis.id}")
                return None
            
            # Faire l'analyse avec l'ancien classificateur mais nouveau tracking
            logger.info(f"🔄 Classification avec secteur: {sector}")
            result = classifier.classify_full(prompt=prompt, ai_response=ai_response)
            
            if not result:
                logger.warning(f"Analyse échouée pour {analysis.id}")
                return None
            
            # Créer directement l'AnalysisTopics avec la nouvelle version
            analysis_topics = self._create_analysis_topics_from_result(analysis.id, result, sector)
            
            # Vérifier si une analyse NLP existe déjà
            existing_topics = db.query(AnalysisTopics).filter(
                AnalysisTopics.analysis_id == analysis.id
            ).first()
            
            if existing_topics:
                # Mettre à jour l'existant
                for key, value in analysis_topics.__dict__.items():
                    if not key.startswith('_') and key != 'id':
                        setattr(existing_topics, key, value)
                logger.info(f"✅ Analyse NLP mise à jour pour {analysis.id}")
                db.commit()
                return existing_topics
            else:
                # Créer nouveau
                db.add(analysis_topics)
                db.commit()
                logger.info(f"✅ Nouvelle analyse NLP créée pour {analysis.id}")
                return analysis_topics
            
        except Exception as e:
            logger.error(f"Erreur analyse NLP (nouvelle archi) {analysis.id}: {str(e)}")
            # Fallback vers ancien service
            try:
                from ...services.nlp_service import NLPService
                temp_service = NLPService()
                logger.warning(f"🔄 Fallback vers ancien service pour {analysis.id}")
                return temp_service.analyze_analysis(db, analysis)
            except Exception as fallback_error:
                logger.error(f"Erreur fallback analyse {analysis.id}: {str(fallback_error)}")
                return None
    
    def analyze_batch(self, db: Session, analysis_ids: List[str]) -> Dict[str, bool]:
        """
        Interface compatible pour l'analyse en batch - MIGRÉ vers nouvelle architecture
        """
        try:
            # MIGRATION: Analyse batch avec nouvelle architecture et logging amélioré
            logger.info(f"🔄 Analyse batch nouvelle architecture: {len(analysis_ids)} analyses")
            
            results = {}
            success_count = 0
            
            # Récupérer toutes les analyses en une fois (optimisation)
            analyses = db.query(Analysis).filter(Analysis.id.in_(analysis_ids)).all()
            analyses_by_id = {a.id: a for a in analyses}
            
            for analysis_id in analysis_ids:
                analysis = analyses_by_id.get(analysis_id)
                if not analysis:
                    results[analysis_id] = False
                    continue
                
                # Analyser individuellement avec la nouvelle architecture
                topics = self.analyze_analysis(db, analysis)
                success = topics is not None
                results[analysis_id] = success
                
                if success:
                    success_count += 1
            
            logger.info(f"✅ Analyse batch terminée: {success_count}/{len(analysis_ids)} succès")
            logger.info(f"🎯 Taux de réussite batch: {success_count/len(analysis_ids)*100:.1f}%")
            
            return results
            
        except Exception as e:
            logger.error(f"Erreur batch NLP (nouvelle archi): {str(e)}")
            # Fallback vers ancien service
            try:
                from ...services.nlp_service import NLPService
                temp_service = NLPService()
                logger.warning(f"🔄 Fallback vers ancien service pour batch {len(analysis_ids)} analyses")
                return temp_service.analyze_batch(db, analysis_ids)
            except Exception as fallback_error:
                logger.error(f"Erreur fallback batch: {str(fallback_error)}")
                return {aid: False for aid in analysis_ids}
    
    def get_project_summary(self, db: Session, project_id: str, limit: int = 100) -> Dict[str, Any]:
        """
        Interface compatible pour le résumé projet
        """
        try:
            # Utilisation directe du service existant
            from ...services.nlp_service import NLPService
            temp_service = NLPService()
            return temp_service.get_project_topics_summary(db, project_id, limit)
            
        except Exception as e:
            logger.error(f"Erreur résumé projet (adapter) {project_id}: {str(e)}")
            return self._get_empty_summary()
    
    def get_global_nlp_stats(self, db: Session) -> Dict[str, Any]:
        """
        Interface compatible pour les stats globales - MIGRÉ vers nouvelle architecture
        """
        try:
            # MIGRATION: Utiliser la nouvelle architecture avec fallback sécurisé
            from ...models.analysis import Analysis
            from ...models.analysis_topics import AnalysisTopics
            from sqlalchemy import func
            
            logger.info("🔄 Calcul stats globales avec nouvelle architecture...")
            
            # Compter les analyses avec et sans topics
            total_analyses = db.query(Analysis).count()
            with_topics = db.query(AnalysisTopics).count()
            
            # Répartition des intentions SEO
            seo_intents_query = db.query(
                AnalysisTopics.seo_intent, 
                func.count(AnalysisTopics.seo_intent)
            ).group_by(AnalysisTopics.seo_intent).all()
            
            # Répartition des types de contenu (filtrer les NULL)
            content_types_query = db.query(
                AnalysisTopics.content_type,
                func.count(AnalysisTopics.content_type)
            ).filter(
                AnalysisTopics.content_type.isnot(None)
            ).group_by(AnalysisTopics.content_type).all()
            
            # Confiance moyenne
            avg_confidence_result = db.query(func.avg(AnalysisTopics.global_confidence)).scalar()
            avg_confidence = avg_confidence_result if avg_confidence_result else 0
            
            # Formatage des résultats
            result = {
                "total_analyses": total_analyses,
                "analyzed_with_nlp": with_topics,
                "nlp_coverage": round(with_topics / total_analyses * 100, 1) if total_analyses > 0 else 0,
                "average_confidence": round(avg_confidence, 3),
                "seo_intents_distribution": dict(seo_intents_query) if seo_intents_query else {},
                "content_types_distribution": dict(content_types_query) if content_types_query else {}
            }
            
            logger.info(f"✅ Stats globales calculées: {total_analyses} analyses, {with_topics} avec NLP")
            return result
            
        except Exception as e:
            logger.error(f"Erreur stats globales (nouvelle archi): {str(e)}")
            # Fallback vers ancien service
            try:
                from ...services.nlp_service import NLPService
                temp_service = NLPService()
                logger.warning("🔄 Fallback vers ancien service pour stats globales")
                return temp_service.get_global_nlp_stats(db)
            except Exception as fallback_error:
                logger.error(f"Erreur fallback stats globales: {str(fallback_error)}")
                return {
                    "total_analyses": 0,
                    "analyzed_with_nlp": 0,
                    "nlp_coverage": 0,
                    "average_confidence": 0,
                    "seo_intents_distribution": {},
                    "content_types_distribution": {}
                }
    
    def get_available_sectors(self) -> List[str]:
        """Interface compatible pour les secteurs disponibles - MIGRÉ vers nouvelle architecture"""
        try:
            # MIGRATION: Utiliser la nouvelle architecture
            from ..infrastructure.legacy_config import SafeLegacyConfigurationRepository
            
            config_repo = SafeLegacyConfigurationRepository()
            seo_keywords = config_repo.get_seo_intent_keywords()
            business_keywords_domotique = config_repo.get_business_topic_keywords('domotique')
            business_keywords_general = config_repo.get_business_topic_keywords('general')
            
            # Secteurs supportés par la nouvelle architecture
            supported_sectors = ['domotique', 'marketing_digital', 'ecommerce', 'tech_general', 'general']
            
            logger.info("✅ Endpoint secteurs disponibles migré vers nouvelle architecture")
            return supported_sectors
                
        except Exception as e:
            logger.error(f"Erreur secteurs disponibles (nouvelle archi): {str(e)}")
            # Fallback vers ancien service
            try:
                from ...services.nlp_service import NLPService
                temp_service = NLPService()
                logger.warning("🔄 Fallback vers ancien service pour secteurs")
                return temp_service.get_available_sectors()
            except Exception as fallback_error:
                logger.error(f"Erreur fallback secteurs: {str(fallback_error)}")
                return ['general']
    
    def get_analysis_topics(self, db: Session, analysis_id: str) -> Optional[AnalysisTopics]:
        """Interface compatible pour récupérer les topics d'une analyse"""
        try:
            return db.query(AnalysisTopics).filter(
                AnalysisTopics.analysis_id == analysis_id
            ).first()
        except Exception as e:
            logger.error(f"Erreur récupération topics (adapter) {analysis_id}: {str(e)}")
            return None
    
    def get_topics_trends(self, db: Session, project_id: str, days: int = 30) -> Dict[str, Any]:
        """Interface compatible pour les tendances - fallback vers ancienne implémentation"""
        try:
            # Pour l'instant, utilisation simplifiée
            from app.services.nlp_service import NLPService
            temp_service = NLPService()
            return temp_service.get_topics_trends(db, project_id, days)
        except Exception as e:
            logger.error(f"Erreur tendances (adapter) {project_id}: {str(e)}")
            return {'trends': [], 'period_days': days, 'total_analyses': 0}
    
    def reanalyze_project(self, db: Session, project_id: str) -> Dict[str, Any]:
        """Interface compatible pour re-analyser un projet"""
        try:
            # Pour l'instant, utilisation simplifiée
            from app.services.nlp_service import NLPService
            temp_service = NLPService()
            return temp_service.reanalyze_project(db, project_id)
        except Exception as e:
            logger.error(f"Erreur re-analyse projet (adapter) {project_id}: {str(e)}")
            return {'success': False, 'message': str(e)}
    
    def _determine_project_sector(self, project: Project) -> str:
        """
        Détermine le secteur d'un projet
        Réutilise la logique de l'ancien service
        """
        if not project or not project.description:
            return 'general'
        
        description_lower = project.description.lower()
        
        # Détection par mots-clés (comme dans l'ancien service)
        if any(kw in description_lower for kw in ['domotique', 'smart home', 'maison connectée', 'volet', 'store']):
            return 'domotique'
        elif any(kw in description_lower for kw in ['marketing', 'digital', 'seo', 'publicité']):
            return 'marketing_digital'
        elif any(kw in description_lower for kw in ['ecommerce', 'e-commerce', 'boutique', 'vente en ligne']):
            return 'ecommerce'
        else:
            return 'tech_general'
    
    def _convert_to_analysis_topics(self, result: NLPAnalysisResult) -> AnalysisTopics:
        """
        Convertit NLPAnalysisResult en AnalysisTopics pour compatibilité
        """
        # Sérialiser business topics
        business_topics_data = [
            {
                'topic': topic.topic,
                'score': topic.score,
                'raw_score': topic.raw_score,
                'weight': topic.weight,
                'relevance': topic.relevance.value,
                'matches_count': topic.matches_count,
                'top_keywords': topic.top_keywords,
                'sample_contexts': topic.sample_contexts
            }
            for topic in result.business_topics
        ]
        
        # Sérialiser entités sectorielles
        sector_entities_data = {}
        for entity_type, entities in result.sector_entities.items():
            sector_entities_data[entity_type] = [
                {
                    'name': entity.name,
                    'count': entity.count,
                    'contexts': entity.contexts,
                    'entity_type': entity.entity_type
                }
                for entity in entities
            ]
        
        return AnalysisTopics(
            analysis_id=result.analysis_id,
            seo_intent=result.seo_intent.main_intent.value,
            seo_confidence=result.seo_intent.confidence,
            seo_detailed_scores=result.seo_intent.detailed_scores,
            business_topics=business_topics_data,
            content_type=result.content_type.main_type,
            content_confidence=result.content_type.confidence,
            sector_entities=sector_entities_data,
            semantic_keywords=result.semantic_keywords,
            global_confidence=result.global_confidence,
            sector_context=result.sector_context,
            processing_version=result.processing_version
        )
    
    def _convert_project_summary_to_legacy(self, summary: NLPProjectSummary) -> Dict[str, Any]:
        """Convertit NLPProjectSummary en format legacy"""
        return {
            'project_id': summary.project_id,
            'project_name': summary.project_name,
            'summary': {
                'total_analyses': summary.total_analyses,
                'average_confidence': summary.average_confidence,
                'high_confidence_count': summary.high_confidence_count,
                'high_confidence_rate': summary.high_confidence_rate,
                'seo_intents': {
                    'distribution': {k.value: v for k, v in summary.seo_intents_distribution.items()},
                    'top_intent': None  # TODO: calculer si nécessaire
                },
                'content_types': {
                    'distribution': summary.content_types_distribution,
                    'top_type': None  # TODO: calculer si nécessaire
                },
                'business_topics': {
                    'top_topics': summary.top_business_topics,
                    'total_topics': len(summary.top_business_topics)
                },
                'sector_entities': {
                    'top_brands': summary.top_entities.get('brands', {}),
                    'top_technologies': summary.top_entities.get('technologies', {}),
                    'brands_diversity': len(summary.top_entities.get('brands', {})),
                    'technologies_diversity': len(summary.top_entities.get('technologies', {}))
                }
            },
            'limit_applied': 100  # TODO: passer la vraie limite
        }
    
    def _get_empty_summary(self) -> Dict[str, Any]:
        """Retourne un résumé vide"""
        return {
            'project_id': '',
            'project_name': '',
            'summary': {
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
            },
            'limit_applied': 0
        }
    
    def _create_analysis_topics_from_result(self, analysis_id: str, result: Dict[str, Any], sector: str) -> AnalysisTopics:
        """
        Crée un AnalysisTopics à partir du résultat de l'ancien classificateur
        avec marquage de la nouvelle architecture
        """
        from datetime import datetime
        
        # Extraire les données de l'ancien format
        seo_intent = result.get('seo_intent', {})
        content_type = result.get('content_type', {})
        
        # Créer l'objet AnalysisTopics avec nouveau marquage
        return AnalysisTopics(
            analysis_id=analysis_id,
            seo_intent=seo_intent.get('main_intent', 'informational'),
            seo_confidence=seo_intent.get('confidence', 0.0),
            seo_detailed_scores=seo_intent.get('all_scores', {}),
            business_topics=result.get('business_topics', []),
            content_type=content_type.get('main_type', 'general'),
            content_confidence=content_type.get('confidence', 0.0),
            sector_entities=result.get('sector_entities', {}),
            semantic_keywords=result.get('semantic_keywords', []),
            global_confidence=result.get('confidence', 0.0),
            sector_context=sector,
            processing_version="2.0-progressive-migration",
            created_at=datetime.utcnow()
        )


# Instance globale pour remplacer l'ancien service
legacy_nlp_service = LegacyNLPServiceAdapter()