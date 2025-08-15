"""
Implémentations des repositories pour la couche infrastructure
Adapters vers la base de données et systèmes externes
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc

from ..domain.entities import (
    NLPAnalysisResult, 
    NLPProjectSummary, 
    NLPGlobalStats,
    SEOIntent,
    ContentType,
    BusinessTopic,
    SectorEntity,
    SEOIntentType,
    RelevanceLevel
)
from ..domain.ports import INLPResultRepository, INLPConfigurationRepository
from ...models.analysis import Analysis
from ...models.analysis_topics import AnalysisTopics
from ...models.project import Project

logger = logging.getLogger(__name__)


class SQLNLPResultRepository(INLPResultRepository):
    """Repository SQL pour les résultats NLP"""
    
    def __init__(self, db_session_factory):
        self.db_session_factory = db_session_factory
    
    def save_result(self, result: NLPAnalysisResult) -> bool:
        """Sauvegarde un résultat d'analyse"""
        try:
            with self.db_session_factory() as db:
                # Vérifier si existe déjà
                existing = db.query(AnalysisTopics).filter(
                    AnalysisTopics.analysis_id == result.analysis_id
                ).first()
                
                if existing:
                    # Mettre à jour
                    self._update_analysis_topics(existing, result)
                else:
                    # Créer nouveau
                    analysis_topics = self._create_analysis_topics(result)
                    db.add(analysis_topics)
                
                db.commit()
                return True
                
        except Exception as e:
            logger.error(f"Erreur sauvegarde résultat NLP {result.analysis_id}: {str(e)}")
            return False
    
    def get_result(self, analysis_id: str) -> Optional[NLPAnalysisResult]:
        """Récupère un résultat d'analyse"""
        try:
            with self.db_session_factory() as db:
                topics = db.query(AnalysisTopics).filter(
                    AnalysisTopics.analysis_id == analysis_id
                ).first()
                
                if not topics:
                    return None
                
                return self._convert_to_domain_entity(topics)
                
        except Exception as e:
            logger.error(f"Erreur récupération résultat NLP {analysis_id}: {str(e)}")
            return None
    
    def get_results_for_project(self, project_id: str, limit: int = 100) -> List[NLPAnalysisResult]:
        """Récupère les résultats pour un projet"""
        try:
            with self.db_session_factory() as db:
                query = db.query(AnalysisTopics).join(
                    Analysis, AnalysisTopics.analysis_id == Analysis.id
                ).filter(
                    Analysis.project_id == project_id
                ).order_by(desc(AnalysisTopics.created_at)).limit(limit)
                
                topics_list = query.all()
                return [self._convert_to_domain_entity(topics) for topics in topics_list]
                
        except Exception as e:
            logger.error(f"Erreur récupération résultats projet {project_id}: {str(e)}")
            return []
    
    def delete_result(self, analysis_id: str) -> bool:
        """Supprime un résultat d'analyse"""
        try:
            with self.db_session_factory() as db:
                deleted_count = db.query(AnalysisTopics).filter(
                    AnalysisTopics.analysis_id == analysis_id
                ).delete()
                
                db.commit()
                return deleted_count > 0
                
        except Exception as e:
            logger.error(f"Erreur suppression résultat NLP {analysis_id}: {str(e)}")
            return False
    
    def get_global_stats(self) -> NLPGlobalStats:
        """Récupère les statistiques globales"""
        try:
            with self.db_session_factory() as db:
                # Comptes totaux
                total_analyses = db.query(Analysis).count()
                analyzed_with_nlp = db.query(AnalysisTopics).count()
                
                # Confiance moyenne
                avg_confidence = db.query(
                    func.avg(AnalysisTopics.global_confidence)
                ).scalar() or 0
                
                # Distribution des intentions SEO
                seo_intents_query = db.query(
                    AnalysisTopics.seo_intent,
                    func.count(AnalysisTopics.seo_intent)
                ).group_by(AnalysisTopics.seo_intent).all()
                
                seo_intents_distribution = {
                    SEOIntentType(intent): count 
                    for intent, count in seo_intents_query
                }
                
                # Distribution des types de contenu
                content_types_query = db.query(
                    AnalysisTopics.content_type,
                    func.count(AnalysisTopics.content_type)
                ).filter(
                    AnalysisTopics.content_type.isnot(None)
                ).group_by(AnalysisTopics.content_type).all()
                
                content_types_distribution = dict(content_types_query)
                
                # Top business topics
                topics_data = db.query(AnalysisTopics.business_topics).filter(
                    AnalysisTopics.business_topics.isnot(None)
                ).all()
                
                top_business_topics = self._aggregate_business_topics(topics_data)
                
                # Top entities
                entities_data = db.query(AnalysisTopics.sector_entities).filter(
                    AnalysisTopics.sector_entities.isnot(None)
                ).all()
                
                top_entities = self._aggregate_entities(entities_data)
                
                return NLPGlobalStats(
                    total_analyses=total_analyses,
                    analyzed_with_nlp=analyzed_with_nlp,
                    average_confidence=round(avg_confidence, 3),
                    seo_intents_distribution=seo_intents_distribution,
                    content_types_distribution=content_types_distribution,
                    top_business_topics=top_business_topics,
                    top_entities=top_entities
                )
                
        except Exception as e:
            logger.error(f"Erreur calcul stats globales: {str(e)}")
            return NLPGlobalStats(
                total_analyses=0,
                analyzed_with_nlp=0,
                average_confidence=0,
                seo_intents_distribution={},
                content_types_distribution={},
                top_business_topics={},
                top_entities={}
            )
    
    def get_project_summary(self, project_id: str, limit: int = 100) -> NLPProjectSummary:
        """Récupère le résumé pour un projet"""
        try:
            with self.db_session_factory() as db:
                # Récupérer le projet
                project = db.query(Project).filter(Project.id == project_id).first()
                project_name = project.name if project else "Projet inconnu"
                
                # Récupérer les topics du projet
                topics_query = db.query(AnalysisTopics).join(
                    Analysis, AnalysisTopics.analysis_id == Analysis.id
                ).filter(
                    Analysis.project_id == project_id
                ).order_by(desc(AnalysisTopics.created_at)).limit(limit)
                
                topics_list = topics_query.all()
                
                if not topics_list:
                    return self._empty_project_summary(project_id, project_name)
                
                # Calculer les métriques
                total_analyses = len(topics_list)
                average_confidence = sum(t.global_confidence for t in topics_list) / total_analyses
                high_confidence_count = sum(1 for t in topics_list if t.global_confidence >= 0.7)
                
                # Distribution des intentions SEO
                seo_intents_distribution = {}
                for topics in topics_list:
                    intent = SEOIntentType(topics.seo_intent)
                    seo_intents_distribution[intent] = seo_intents_distribution.get(intent, 0) + 1
                
                # Distribution des types de contenu
                content_types_distribution = {}
                for topics in topics_list:
                    if topics.content_type:
                        content_types_distribution[topics.content_type] = \
                            content_types_distribution.get(topics.content_type, 0) + 1
                
                # Top business topics
                top_business_topics = self._aggregate_business_topics(
                    [(t.business_topics,) for t in topics_list if t.business_topics]
                )
                
                # Top entities
                top_entities = self._aggregate_entities(
                    [(t.sector_entities,) for t in topics_list if t.sector_entities]
                )
                
                return NLPProjectSummary(
                    project_id=project_id,
                    project_name=project_name,
                    total_analyses=total_analyses,
                    average_confidence=round(average_confidence, 3),
                    high_confidence_count=high_confidence_count,
                    seo_intents_distribution=seo_intents_distribution,
                    content_types_distribution=content_types_distribution,
                    top_business_topics=top_business_topics,
                    top_entities=top_entities,
                    analysis_period=f"Dernières {limit} analyses"
                )
                
        except Exception as e:
            logger.error(f"Erreur calcul résumé projet {project_id}: {str(e)}")
            return self._empty_project_summary(project_id, "Erreur")
    
    def _create_analysis_topics(self, result: NLPAnalysisResult) -> AnalysisTopics:
        """Convertit une entité domaine en modèle DB"""
        return AnalysisTopics(
            analysis_id=result.analysis_id,
            seo_intent=result.seo_intent.main_intent.value,
            seo_confidence=result.seo_intent.confidence,
            seo_detailed_scores=result.seo_intent.detailed_scores,
            business_topics=self._serialize_business_topics(result.business_topics),
            content_type=result.content_type.main_type,
            content_confidence=result.content_type.confidence,
            sector_entities=self._serialize_sector_entities(result.sector_entities),
            semantic_keywords=result.semantic_keywords,
            global_confidence=result.global_confidence,
            sector_context=result.sector_context,
            processing_version=result.processing_version
        )
    
    def _update_analysis_topics(self, topics: AnalysisTopics, result: NLPAnalysisResult) -> None:
        """Met à jour un modèle DB existant"""
        topics.seo_intent = result.seo_intent.main_intent.value
        topics.seo_confidence = result.seo_intent.confidence
        topics.seo_detailed_scores = result.seo_intent.detailed_scores
        topics.business_topics = self._serialize_business_topics(result.business_topics)
        topics.content_type = result.content_type.main_type
        topics.content_confidence = result.content_type.confidence
        topics.sector_entities = self._serialize_sector_entities(result.sector_entities)
        topics.semantic_keywords = result.semantic_keywords
        topics.global_confidence = result.global_confidence
        topics.sector_context = result.sector_context
        topics.processing_version = result.processing_version
        topics.updated_at = datetime.utcnow()
    
    def _convert_to_domain_entity(self, topics: AnalysisTopics) -> NLPAnalysisResult:
        """Convertit un modèle DB en entité domaine"""
        seo_intent = SEOIntent(
            main_intent=SEOIntentType(topics.seo_intent),
            confidence=topics.seo_confidence,
            detailed_scores=topics.seo_detailed_scores or {}
        )
        
        content_type = ContentType(
            main_type=topics.content_type or "unknown",
            confidence=topics.content_confidence or 0,
            all_scores={}
        )
        
        business_topics = self._deserialize_business_topics(topics.business_topics)
        sector_entities = self._deserialize_sector_entities(topics.sector_entities)
        
        return NLPAnalysisResult(
            analysis_id=topics.analysis_id,
            seo_intent=seo_intent,
            content_type=content_type,
            business_topics=business_topics,
            sector_entities=sector_entities,
            semantic_keywords=topics.semantic_keywords or [],
            global_confidence=topics.global_confidence,
            sector_context=topics.sector_context or "general",
            processing_version=topics.processing_version or "1.0",
            created_at=topics.created_at or datetime.utcnow()
        )
    
    def _serialize_business_topics(self, topics: List[BusinessTopic]) -> List[Dict]:
        """Sérialise les business topics pour la DB"""
        return [
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
            for topic in topics
        ]
    
    def _deserialize_business_topics(self, data: List[Dict]) -> List[BusinessTopic]:
        """Désérialise les business topics depuis la DB"""
        if not data:
            return []
        
        return [
            BusinessTopic(
                topic=item.get('topic', ''),
                score=item.get('score', 0),
                raw_score=item.get('raw_score', 0),
                weight=item.get('weight', 1.0),
                relevance=RelevanceLevel(item.get('relevance', 'low')),
                matches_count=item.get('matches_count', 0),
                top_keywords=item.get('top_keywords', []),
                sample_contexts=item.get('sample_contexts', [])
            )
            for item in data
        ]
    
    def _serialize_sector_entities(self, entities: Dict[str, List[SectorEntity]]) -> Dict[str, List[Dict]]:
        """Sérialise les entités sectorielles pour la DB"""
        result = {}
        for entity_type, entity_list in entities.items():
            result[entity_type] = [
                {
                    'name': entity.name,
                    'count': entity.count,
                    'contexts': entity.contexts,
                    'entity_type': entity.entity_type
                }
                for entity in entity_list
            ]
        return result
    
    def _deserialize_sector_entities(self, data: Dict[str, List[Dict]]) -> Dict[str, List[SectorEntity]]:
        """Désérialise les entités sectorielles depuis la DB"""
        if not data:
            return {}
        
        result = {}
        for entity_type, entity_list in data.items():
            result[entity_type] = [
                SectorEntity(
                    name=item.get('name', ''),
                    count=item.get('count', 1),
                    contexts=item.get('contexts', []),
                    entity_type=item.get('entity_type', entity_type)
                )
                for item in entity_list
            ]
        return result
    
    def _aggregate_business_topics(self, topics_data: List[tuple]) -> Dict[str, int]:
        """Agrège les business topics pour les statistiques"""
        topic_counts = {}
        
        for (topics_json,) in topics_data:
            if not topics_json:
                continue
            
            try:
                topics = topics_json if isinstance(topics_json, list) else json.loads(topics_json)
                for topic_data in topics:
                    topic_name = topic_data.get('topic', '')
                    if topic_name:
                        topic_counts[topic_name] = topic_counts.get(topic_name, 0) + 1
            except (json.JSONDecodeError, AttributeError):
                continue
        
        return dict(sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:10])
    
    def _aggregate_entities(self, entities_data: List[tuple]) -> Dict[str, Dict[str, int]]:
        """Agrège les entités pour les statistiques"""
        entities_counts = {}
        
        for (entities_json,) in entities_data:
            if not entities_json:
                continue
            
            try:
                entities = entities_json if isinstance(entities_json, dict) else json.loads(entities_json)
                for entity_type, entity_list in entities.items():
                    if entity_type not in entities_counts:
                        entities_counts[entity_type] = {}
                    
                    for entity_data in entity_list:
                        entity_name = entity_data.get('name', '')
                        if entity_name:
                            entities_counts[entity_type][entity_name] = \
                                entities_counts[entity_type].get(entity_name, 0) + entity_data.get('count', 1)
            except (json.JSONDecodeError, AttributeError):
                continue
        
        # Garder seulement le top 5 par type
        result = {}
        for entity_type, counts in entities_counts.items():
            result[entity_type] = dict(sorted(counts.items(), key=lambda x: x[1], reverse=True)[:5])
        
        return result
    
    def _empty_project_summary(self, project_id: str, project_name: str) -> NLPProjectSummary:
        """Retourne un résumé vide pour un projet"""
        return NLPProjectSummary(
            project_id=project_id,
            project_name=project_name,
            total_analyses=0,
            average_confidence=0,
            high_confidence_count=0,
            seo_intents_distribution={},
            content_types_distribution={},
            top_business_topics={},
            top_entities={},
            analysis_period="Aucune donnée"
        )


class FileNLPConfigurationRepository(INLPConfigurationRepository):
    """Repository basé sur fichiers pour la configuration NLP"""
    
    def __init__(self, config_dir: str = "app/nlp/config"):
        self.config_dir = config_dir
        self._cache = {}
    
    def get_keywords_for_sector(self, sector: str) -> Dict[str, Any]:
        """Récupère les mots-clés pour un secteur"""
        # TODO: Implémenter la lecture depuis fichiers
        return {}
    
    def get_seo_intent_keywords(self) -> Dict[SEOIntentType, Dict[str, Any]]:
        """Récupère les mots-clés pour les intentions SEO"""
        # TODO: Implémenter la lecture depuis fichiers
        return {}
    
    def get_business_topic_keywords(self, sector: str) -> Dict[str, Any]:
        """Récupère les mots-clés pour les topics business"""
        # TODO: Implémenter la lecture depuis fichiers
        return {}
    
    def update_configuration(self, sector: str, config: Dict[str, Any]) -> bool:
        """Met à jour la configuration pour un secteur"""
        # TODO: Implémenter l'écriture vers fichiers
        return False
    
    def get_configuration_version(self, sector: str) -> str:
        """Retourne la version de la configuration"""
        return "1.0"