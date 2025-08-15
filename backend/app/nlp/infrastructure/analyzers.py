"""
Système de plugins pour les analyseurs NLP
Architecture modulaire et extensible
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Set
from datetime import datetime

from ..domain.entities import (
    NLPAnalysisResult,
    SEOIntent,
    ContentType, 
    BusinessTopic,
    SectorEntity,
    SEOIntentType,
    RelevanceLevel
)
from ..domain.ports import INLPAnalyzer, INLPConfigurationRepository

logger = logging.getLogger(__name__)


class BaseNLPPlugin(ABC):
    """Plugin de base pour l'analyse NLP"""
    
    def __init__(self, name: str, version: str = "1.0"):
        self.name = name
        self.version = version
        self.enabled = True
    
    @abstractmethod
    def analyze(self, prompt: str, ai_response: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyse le contenu et retourne les résultats spécifiques au plugin"""
        pass
    
    @abstractmethod
    def get_supported_languages(self) -> List[str]:
        """Retourne les langues supportées par ce plugin"""
        pass
    
    @abstractmethod
    def get_dependencies(self) -> List[str]:
        """Retourne les dépendances requises par ce plugin"""
        pass
    
    def is_applicable(self, context: Dict[str, Any]) -> bool:
        """Détermine si ce plugin est applicable au contexte donné"""
        return self.enabled
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Retourne les métriques de performance du plugin"""
        return {
            'name': self.name,
            'version': self.version,
            'enabled': self.enabled
        }


class SEOIntentPlugin(BaseNLPPlugin):
    """Plugin pour l'analyse des intentions SEO"""
    
    def __init__(self, config_repository: INLPConfigurationRepository):
        super().__init__("seo_intent", "1.0")
        self.config_repository = config_repository
        self._intent_keywords = None
        
    def analyze(self, prompt: str, ai_response: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyse l'intention SEO du contenu"""
        if self._intent_keywords is None:
            self._intent_keywords = self.config_repository.get_seo_intent_keywords()
        
        combined_text = f"{prompt} {ai_response}".lower()
        intent_scores = {}
        
        # Calculer les scores pour chaque intention
        for intent_type, config in self._intent_keywords.items():
            score = 0
            weight = config.get('weight', 1.0)
            keywords = config.get('keywords', {})
            
            for category, words in keywords.items():
                category_weight = config.get('category_weights', {}).get(category, 1.0)
                for word in words:
                    if word.lower() in combined_text:
                        score += weight * category_weight
            
            intent_scores[intent_type.value] = score
        
        # Déterminer l'intention principale
        if not intent_scores or max(intent_scores.values()) == 0:
            main_intent = SEOIntentType.INFORMATIONAL
            confidence = 0.1
        else:
            main_intent = SEOIntentType(max(intent_scores.items(), key=lambda x: x[1])[0])
            total_score = sum(intent_scores.values())
            confidence = intent_scores[main_intent.value] / total_score if total_score > 0 else 0
        
        return {
            'main_intent': main_intent,
            'confidence': min(confidence, 1.0),
            'detailed_scores': intent_scores
        }
    
    def get_supported_languages(self) -> List[str]:
        return ['fr', 'en']
    
    def get_dependencies(self) -> List[str]:
        return ['config_repository']


class BusinessTopicsPlugin(BaseNLPPlugin):
    """Plugin pour l'analyse des topics business"""
    
    def __init__(self, config_repository: INLPConfigurationRepository):
        super().__init__("business_topics", "1.0")
        self.config_repository = config_repository
        self._topic_keywords = {}
        
    def analyze(self, prompt: str, ai_response: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyse les topics business du contenu"""
        sector = context.get('sector', 'general')
        
        if sector not in self._topic_keywords:
            self._topic_keywords[sector] = self.config_repository.get_business_topic_keywords(sector)
        
        combined_text = f"{prompt} {ai_response}".lower()
        topics = []
        
        for topic_name, config in self._topic_keywords[sector].items():
            matches = []
            total_score = 0
            keywords = config.get('keywords', [])
            weight = config.get('weight', 1.0)
            
            for keyword in keywords:
                if keyword.lower() in combined_text:
                    matches.append(keyword)
                    total_score += weight
            
            if matches:
                # Calculer le score final
                raw_score = len(matches)
                weighted_score = total_score
                final_score = weighted_score * (1 + len(matches) / 10)  # Bonus pour diversité
                
                # Déterminer la pertinence
                if final_score >= 10:
                    relevance = RelevanceLevel.HIGH
                elif final_score >= 5:
                    relevance = RelevanceLevel.MEDIUM
                else:
                    relevance = RelevanceLevel.LOW
                
                topics.append(BusinessTopic(
                    topic=topic_name,
                    score=final_score,
                    raw_score=raw_score,
                    weight=weight,
                    relevance=relevance,
                    matches_count=len(matches),
                    top_keywords=matches[:5],
                    sample_contexts=self._extract_contexts(combined_text, matches[:3])
                ))
        
        # Trier par score décroissant
        topics.sort(key=lambda t: t.score, reverse=True)
        
        return {
            'business_topics': topics[:10]  # Top 10
        }
    
    def _extract_contexts(self, text: str, keywords: List[str]) -> List[str]:
        """Extrait des contextes autour des mots-clés"""
        contexts = []
        for keyword in keywords:
            start = text.find(keyword.lower())
            if start != -1:
                context_start = max(0, start - 50)
                context_end = min(len(text), start + len(keyword) + 50)
                context = text[context_start:context_end].strip()
                contexts.append(f"...{context}...")
        return contexts
    
    def get_supported_languages(self) -> List[str]:
        return ['fr', 'en']
    
    def get_dependencies(self) -> List[str]:
        return ['config_repository']


class ContentTypePlugin(BaseNLPPlugin):
    """Plugin pour détecter le type de contenu"""
    
    CONTENT_TYPE_PATTERNS = {
        'comparison': ['vs', 'versus', 'comparaison', 'compare', 'différence', 'mieux que'],
        'tutorial': ['comment', 'how to', 'étape', 'guide', 'tutorial', 'tuto'],
        'review': ['avis', 'review', 'test', 'opinion', 'retour', 'évaluation'],
        'list': ['liste', 'top', 'meilleur', 'best', 'selection', 'choix'],
        'technical': ['technique', 'technical', 'api', 'code', 'développement', 'implementation'],
        'commercial': ['prix', 'price', 'acheter', 'buy', 'purchase', 'commande', 'vente'],
        'news': ['actualité', 'news', 'nouveau', 'new', 'announce', 'sortie'],
        'faq': ['faq', 'question', 'réponse', 'answer', 'pourquoi', 'why', 'how']
    }
    
    def __init__(self):
        super().__init__("content_type", "1.0")
        
    def analyze(self, prompt: str, ai_response: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Détermine le type de contenu"""
        combined_text = f"{prompt} {ai_response}".lower()
        type_scores = {}
        
        for content_type, patterns in self.CONTENT_TYPE_PATTERNS.items():
            score = 0
            for pattern in patterns:
                score += combined_text.count(pattern.lower())
            type_scores[content_type] = score
        
        if not type_scores or max(type_scores.values()) == 0:
            main_type = 'general'
            confidence = 0.1
        else:
            main_type = max(type_scores.items(), key=lambda x: x[1])[0]
            total_score = sum(type_scores.values())
            confidence = type_scores[main_type] / total_score if total_score > 0 else 0
        
        return {
            'main_type': main_type,
            'confidence': min(confidence, 1.0),
            'all_scores': type_scores
        }
    
    def get_supported_languages(self) -> List[str]:
        return ['fr', 'en']
    
    def get_dependencies(self) -> List[str]:
        return []


class SectorEntitiesPlugin(BaseNLPPlugin):
    """Plugin pour extraire les entités sectorielles"""
    
    def __init__(self, config_repository: INLPConfigurationRepository):
        super().__init__("sector_entities", "1.0")
        self.config_repository = config_repository
        self._sector_entities = {}
        
    def analyze(self, prompt: str, ai_response: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extrait les entités sectorielles"""
        sector = context.get('sector', 'general')
        
        if sector not in self._sector_entities:
            sector_keywords = self.config_repository.get_keywords_for_sector(sector)
            self._sector_entities[sector] = sector_keywords.get('entities', {})
        
        combined_text = f"{prompt} {ai_response}".lower()
        detected_entities = {}
        
        for entity_type, entities_list in self._sector_entities[sector].items():
            detected_entities[entity_type] = []
            
            for entity_name in entities_list:
                count = combined_text.count(entity_name.lower())
                if count > 0:
                    contexts = self._find_entity_contexts(combined_text, entity_name.lower())
                    detected_entities[entity_type].append(SectorEntity(
                        name=entity_name,
                        count=count,
                        contexts=contexts,
                        entity_type=entity_type
                    ))
        
        # Supprimer les types vides
        detected_entities = {k: v for k, v in detected_entities.items() if v}
        
        return {
            'sector_entities': detected_entities
        }
    
    def _find_entity_contexts(self, text: str, entity: str) -> List[str]:
        """Trouve les contextes où l'entité apparaît"""
        contexts = []
        start = 0
        while True:
            pos = text.find(entity, start)
            if pos == -1:
                break
            
            context_start = max(0, pos - 30)
            context_end = min(len(text), pos + len(entity) + 30)
            context = text[context_start:context_end].strip()
            contexts.append(f"...{context}...")
            start = pos + 1
            
            if len(contexts) >= 3:  # Limite à 3 contextes
                break
        
        return contexts
    
    def get_supported_languages(self) -> List[str]:
        return ['fr', 'en']
    
    def get_dependencies(self) -> List[str]:
        return ['config_repository']


class SemanticKeywordsPlugin(BaseNLPPlugin):
    """Plugin pour extraire les mots-clés sémantiques"""
    
    def __init__(self):
        super().__init__("semantic_keywords", "1.0")
        self.stop_words = {
            'fr': {'le', 'la', 'les', 'de', 'du', 'des', 'et', 'ou', 'est', 'sont', 'avec', 'pour', 'dans', 'sur', 'par'},
            'en': {'the', 'a', 'an', 'and', 'or', 'is', 'are', 'with', 'for', 'in', 'on', 'by', 'of', 'to'}
        }
        
    def analyze(self, prompt: str, ai_response: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extrait les mots-clés sémantiques importants"""
        # Analyser principalement la réponse IA
        text = ai_response.lower()
        
        # Extraction basique des mots-clés
        words = self._extract_words(text)
        word_freq = {}
        
        for word in words:
            if self._is_significant_word(word):
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Filtrer et trier par fréquence
        keywords = [
            word for word, freq in sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
            if freq >= 2 and len(word) >= 4
        ][:20]  # Top 20
        
        return {
            'semantic_keywords': keywords
        }
    
    def _extract_words(self, text: str) -> List[str]:
        """Extrait les mots du texte"""
        import re
        # Garder seulement les lettres et espaces
        cleaned = re.sub(r'[^a-zA-ZÀ-ÿ\s]', ' ', text)
        return [word.strip() for word in cleaned.split() if word.strip()]
    
    def _is_significant_word(self, word: str) -> bool:
        """Détermine si un mot est significatif"""
        if len(word) < 3:
            return False
        
        # Vérifier contre les stop words
        for lang_stops in self.stop_words.values():
            if word in lang_stops:
                return False
        
        return True
    
    def get_supported_languages(self) -> List[str]:
        return ['fr', 'en']
    
    def get_dependencies(self) -> List[str]:
        return []


class CompositeNLPAnalyzer(INLPAnalyzer):
    """Analyseur composite utilisant plusieurs plugins"""
    
    def __init__(self, config_repository: INLPConfigurationRepository):
        self.config_repository = config_repository
        self.plugins: List[BaseNLPPlugin] = []
        self.version = "2.0"
        self._initialize_plugins()
        
    def _initialize_plugins(self):
        """Initialise tous les plugins"""
        self.plugins = [
            SEOIntentPlugin(self.config_repository),
            BusinessTopicsPlugin(self.config_repository),
            ContentTypePlugin(),
            SectorEntitiesPlugin(self.config_repository),
            SemanticKeywordsPlugin()
        ]
        
        logger.info(f"Analyseur NLP initialisé avec {len(self.plugins)} plugins")
    
    def analyze(self, prompt: str, ai_response: str, sector: str) -> NLPAnalysisResult:
        """Analyse complète utilisant tous les plugins"""
        start_time = time.time()
        
        context = {
            'sector': sector,
            'prompt_length': len(prompt),
            'response_length': len(ai_response),
            'language': self._detect_language(ai_response)
        }
        
        results = {}
        plugin_performances = {}
        
        # Exécuter chaque plugin applicable
        for plugin in self.plugins:
            if plugin.is_applicable(context):
                plugin_start = time.time()
                try:
                    plugin_result = plugin.analyze(prompt, ai_response, context)
                    results.update(plugin_result)
                    
                    plugin_time = (time.time() - plugin_start) * 1000
                    plugin_performances[plugin.name] = plugin_time
                    
                except Exception as e:
                    logger.error(f"Erreur plugin {plugin.name}: {str(e)}")
                    plugin_performances[plugin.name] = -1
        
        # Construire le résultat final
        analysis_result = self._build_analysis_result(results, context)
        
        total_time = (time.time() - start_time) * 1000
        logger.debug(f"Analyse NLP terminée en {total_time:.2f}ms - Plugins: {plugin_performances}")
        
        return analysis_result
    
    def _build_analysis_result(self, results: Dict[str, Any], context: Dict[str, Any]) -> NLPAnalysisResult:
        """Construit le résultat final à partir des résultats des plugins"""
        
        # SEO Intent
        seo_intent_data = results.get('main_intent', SEOIntentType.INFORMATIONAL)
        seo_intent = SEOIntent(
            main_intent=seo_intent_data,
            confidence=results.get('confidence', 0.1),
            detailed_scores=results.get('detailed_scores', {})
        )
        
        # Content Type
        content_type = ContentType(
            main_type=results.get('main_type', 'general'),
            confidence=results.get('confidence', 0.1),
            all_scores=results.get('all_scores', {})
        )
        
        # Business Topics
        business_topics = results.get('business_topics', [])
        
        # Sector Entities
        sector_entities = results.get('sector_entities', {})
        
        # Semantic Keywords
        semantic_keywords = results.get('semantic_keywords', [])
        
        # Calcul de la confiance globale
        confidences = [
            seo_intent.confidence,
            content_type.confidence,
            1.0 if business_topics else 0.1,
            1.0 if sector_entities else 0.1
        ]
        global_confidence = sum(confidences) / len(confidences)
        
        return NLPAnalysisResult(
            analysis_id="",  # Sera défini par le service
            seo_intent=seo_intent,
            content_type=content_type,
            business_topics=business_topics,
            sector_entities=sector_entities,
            semantic_keywords=semantic_keywords,
            global_confidence=global_confidence,
            sector_context=context['sector'],
            processing_version=self.version,
            created_at=datetime.utcnow()
        )
    
    def _detect_language(self, text: str) -> str:
        """Détection basique de la langue"""
        french_words = ['le', 'la', 'les', 'de', 'et', 'est', 'pour', 'avec', 'sur']
        english_words = ['the', 'and', 'is', 'for', 'with', 'on', 'a', 'an']
        
        text_lower = text.lower()
        french_count = sum(1 for word in french_words if word in text_lower)
        english_count = sum(1 for word in english_words if word in text_lower)
        
        return 'fr' if french_count > english_count else 'en'
    
    def get_supported_sectors(self) -> List[str]:
        """Retourne la liste des secteurs supportés"""
        return ['domotique', 'marketing_digital', 'ecommerce', 'tech_general', 'general']
    
    def get_version(self) -> str:
        """Retourne la version de l'analyseur"""
        return self.version
    
    def add_plugin(self, plugin: BaseNLPPlugin) -> None:
        """Ajoute un plugin à l'analyseur"""
        self.plugins.append(plugin)
        logger.info(f"Plugin {plugin.name} ajouté à l'analyseur")
    
    def remove_plugin(self, plugin_name: str) -> bool:
        """Supprime un plugin de l'analyseur"""
        initial_count = len(self.plugins)
        self.plugins = [p for p in self.plugins if p.name != plugin_name]
        removed = len(self.plugins) < initial_count
        
        if removed:
            logger.info(f"Plugin {plugin_name} supprimé de l'analyseur")
        
        return removed
    
    def get_plugin_status(self) -> List[Dict[str, Any]]:
        """Retourne le statut de tous les plugins"""
        return [plugin.get_performance_metrics() for plugin in self.plugins]