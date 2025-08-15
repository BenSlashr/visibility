"""
AdvancedTopicsClassifier - Classification NLP pour l'analyse des intentions SEO et business topics
Utilise une approche keywords matching avec scoring avancé
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict

from .keywords_config import (
    SEO_INTENT_KEYWORDS,
    BUSINESS_TOPICS,
    SECTOR_SPECIFIC_KEYWORDS,
    FRENCH_EXPRESSIONS,
    SCORING_CONFIG
)

logger = logging.getLogger(__name__)


class AdvancedTopicsClassifier:
    """
    Classificateur NLP avancé pour analyser:
    - Intention SEO (commercial, informational, transactional, navigational)
    - Business topics spécifiques au secteur
    - Type de contenu (comparison, tutorial, review, etc.)
    - Entités sectorielles (marques, technologies, produits)
    """
    
    def __init__(self, project_sector: str = 'domotique'):
        self.seo_keywords = SEO_INTENT_KEYWORDS
        self.business_topics = BUSINESS_TOPICS.get(project_sector, BUSINESS_TOPICS['tech_general'])
        self.sector_keywords = SECTOR_SPECIFIC_KEYWORDS.get(project_sector, {})
        self.expressions = FRENCH_EXPRESSIONS
        self.project_sector = project_sector
        self.config = SCORING_CONFIG
        
        # Patterns pour le preprocessing
        self._setup_patterns()
        
        logger.info(f"AdvancedTopicsClassifier initialisé pour le secteur: {project_sector}")
    
    def _setup_patterns(self):
        """Initialisation des patterns regex pour l'analyse"""
        # Pattern pour nettoyer le texte
        self.cleanup_pattern = re.compile(r'[^\w\s\-\'àâäéèêëïîôöùûüÿç]', re.IGNORECASE)
        self.whitespace_pattern = re.compile(r'\s+')
        
        # Patterns pour détecter les types de contenu
        self.content_patterns = {
            'comparison': {
                'keywords': ['vs', 'versus', 'comparaison', 'différence', 'face à face', 'par rapport'],
                'expressions': self.expressions['comparison_expressions'],
                'score': 0
            },
            'tutorial': {
                'keywords': ['comment', 'tutoriel', 'guide', 'étapes', 'procédure', 'méthode'],
                'expressions': [],
                'score': 0
            },
            'review': {
                'keywords': ['avis', 'test', 'review', 'évaluation', 'expérience', 'opinion'],
                'expressions': self.expressions['recommendation_expressions'],
                'score': 0
            },
            'list': {
                'keywords': ['meilleur', 'top', 'liste', 'sélection', 'classement'],
                'expressions': [],
                'score': 0
            },
            'technical': {
                'keywords': ['spécification', 'caractéristique', 'technique', 'performance'],
                'expressions': self.expressions['technical_expressions'],
                'score': 0
            }
        }
    
    def classify_full(self, prompt: str, ai_response: str) -> Dict[str, Any]:
        """
        Classification complète avec scoring avancé
        
        Args:
            prompt: Prompt exécuté
            ai_response: Réponse de l'IA
            
        Returns:
            Dict contenant tous les résultats d'analyse
        """
        try:
            # Préprocessing
            full_text = f"{prompt} {ai_response}".lower()
            cleaned_text = self._preprocess_text(full_text)
            
            # 1. Classification SEO Intent
            seo_results = self._classify_seo_intent(cleaned_text)
            
            # 2. Classification Business Topics
            business_results = self._classify_business_topics(cleaned_text)
            
            # 3. Détection du type de contenu
            content_type = self._detect_content_type(cleaned_text)
            
            # 4. Extraction d'entités sectorielles
            entities = self._extract_sector_entities(cleaned_text)
            
            # 5. Extraction de mots-clés sémantiques
            semantic_keywords = self._extract_semantic_keywords(cleaned_text)
            
            # 6. Score de confiance global
            confidence = self._calculate_global_confidence(
                seo_results, business_results, content_type, entities
            )
            
            result = {
                'seo_intent': seo_results,
                'business_topics': business_results,
                'content_type': content_type,
                'sector_entities': entities,
                'semantic_keywords': semantic_keywords,
                'confidence': confidence,
                'sector': self.project_sector,
                'processing_version': '1.0'
            }
            
            logger.debug(f"Classification complète terminée avec confiance: {confidence}")
            return result
            
        except Exception as e:
            logger.error(f"Erreur lors de la classification: {e}")
            return self._get_default_classification()
    
    def _classify_seo_intent(self, text: str) -> Dict[str, Any]:
        """Classification de l'intention SEO avec pondération"""
        
        intent_scores = {}
        detailed_matches = {}
        
        for intent, categories in self.seo_keywords.items():
            total_score = 0
            matches = []
            
            weight = categories.get('weight', 1.0)
            
            for category, keywords in categories.items():
                if category == 'weight':
                    continue
                    
                category_score = 0
                category_matches = []
                
                for keyword in keywords:
                    # Comptage des occurrences avec contexte
                    count = self._count_keyword_with_context(text, keyword)
                    if count > 0:
                        category_score += count
                        category_matches.append({
                            'keyword': keyword, 
                            'count': count,
                            'contexts': self._extract_keyword_contexts(text, keyword, max_contexts=2)
                        })
                
                if category_matches:
                    matches.append({
                        'category': category,
                        'score': category_score,
                        'matches': category_matches
                    })
                    total_score += category_score
            
            # Application de la pondération
            weighted_score = total_score * weight
            intent_scores[intent] = weighted_score
            detailed_matches[intent] = matches
        
        # Détermination de l'intention principale
        if sum(intent_scores.values()) == 0:
            main_intent = 'informational'  # Défaut
            confidence = 0.1
        else:
            main_intent = max(intent_scores, key=intent_scores.get)
            confidence = intent_scores[main_intent] / sum(intent_scores.values())
        
        return {
            'main_intent': main_intent,
            'confidence': round(confidence, 2),
            'all_scores': {k: round(v, 1) for k, v in intent_scores.items()},
            'detailed_matches': detailed_matches.get(main_intent, [])
        }
    
    def _classify_business_topics(self, text: str) -> List[Dict[str, Any]]:
        """Classification des sujets business avec scoring"""
        
        topic_results = []
        
        for topic, config in self.business_topics.items():
            keywords = config['keywords']
            weight = config.get('weight', 1.0)
            
            score = 0
            matches = []
            contexts = []
            
            for keyword in keywords:
                count = self._count_keyword_with_context(text, keyword)
                if count > 0:
                    score += count
                    keyword_contexts = self._extract_keyword_contexts(text, keyword, max_contexts=1)
                    matches.append({
                        'keyword': keyword, 
                        'count': count,
                        'contexts': keyword_contexts
                    })
                    contexts.extend(keyword_contexts)
            
            if score > 0:
                weighted_score = score * weight
                relevance = self._calculate_topic_relevance(weighted_score)
                
                topic_results.append({
                    'topic': topic,
                    'score': round(weighted_score, 1),
                    'raw_score': score,
                    'weight': weight,
                    'relevance': relevance,
                    'matches_count': len(matches),
                    'top_keywords': [m['keyword'] for m in matches[:3]],  # Top 3 keywords
                    'sample_contexts': contexts[:2]  # 2 contextes d'exemple
                })
        
        # Tri par score décroissant
        topic_results.sort(key=lambda x: x['score'], reverse=True)
        
        return topic_results[:self.config['max_topics_returned']]
    
    def _detect_content_type(self, text: str) -> Dict[str, Any]:
        """Détection du type de contenu"""
        
        # Reset des scores
        for content_type in self.content_patterns:
            self.content_patterns[content_type]['score'] = 0
        
        # Score basé sur expressions spécifiques (poids plus élevé)
        for content_type, config in self.content_patterns.items():
            for expr in config['expressions']:
                if expr in text:
                    config['score'] += 2  # Bonus pour expressions spécifiques
        
        # Score basé sur mots-clés simples
        for content_type, config in self.content_patterns.items():
            for keyword in config['keywords']:
                count = self._count_keyword_with_context(text, keyword)
                config['score'] += count
        
        # Détermination du type principal
        all_scores = {k: v['score'] for k, v in self.content_patterns.items()}
        total_score = sum(all_scores.values())
        
        if total_score == 0:
            main_type = 'general'
            confidence = 0.1
        else:
            main_type = max(all_scores, key=all_scores.get)
            confidence = all_scores[main_type] / total_score
        
        return {
            'main_type': main_type,
            'confidence': round(confidence, 2),
            'all_scores': all_scores
        }
    
    def _extract_sector_entities(self, text: str) -> Dict[str, List[Dict[str, Any]]]:
        """Extraction d'entités spécifiques au secteur avec contexte"""
        
        entities = {}
        
        for entity_type, entity_list in self.sector_keywords.items():
            found_entities = []
            
            for entity in entity_list:
                count = self._count_keyword_with_context(text, entity)
                if count > 0:
                    contexts = self._extract_keyword_contexts(text, entity, max_contexts=1)
                    found_entities.append({
                        'name': entity,
                        'count': count,
                        'contexts': contexts
                    })
            
            if found_entities:
                # Tri par fréquence décroissante
                found_entities.sort(key=lambda x: x['count'], reverse=True)
                entities[entity_type] = found_entities[:10]  # Max 10 entités par type
        
        return entities
    
    def _extract_semantic_keywords(self, text: str) -> List[str]:
        """Extraction de mots-clés sémantiques importants"""
        
        # Mots de plus de 3 caractères, non stop-words
        stop_words = {
            'le', 'la', 'les', 'de', 'du', 'des', 'et', 'est', 'sont', 'avec', 'pour', 
            'dans', 'sur', 'par', 'plus', 'très', 'tout', 'tous', 'toute', 'toutes',
            'avoir', 'être', 'faire', 'dire', 'aller', 'voir', 'savoir', 'pouvoir',
            'falloir', 'vouloir', 'venir', 'mettre', 'prendre', 'donner', 'passer'
        }
        
        words = re.findall(r'\b\w{' + str(self.config['minimum_keyword_length']) + r',}\b', text)
        
        # Filtrage et comptage
        word_counts = defaultdict(int)
        for word in words:
            if word.lower() not in stop_words and not word.isdigit():
                word_counts[word.lower()] += 1
        
        # Retourner les mots les plus fréquents
        sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
        return [word for word, count in sorted_words[:20] if count >= 2]  # Min 2 occurrences
    
    def _count_keyword_with_context(self, text: str, keyword: str) -> int:
        """Comptage intelligent des mots-clés avec gestion du contexte"""
        
        # Gestion des expressions multi-mots
        if ' ' in keyword:
            pattern = re.escape(keyword.lower())
        else:
            # Mot isolé avec frontières de mots pour éviter les faux positifs
            pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
        
        matches = re.findall(pattern, text.lower(), re.IGNORECASE)
        return len(matches)
    
    def _extract_keyword_contexts(self, text: str, keyword: str, max_contexts: int = 3) -> List[str]:
        """Extraction du contexte autour d'un mot-clé"""
        
        contexts = []
        window = self.config['context_window_size']
        
        # Recherche de toutes les occurrences
        pattern = re.escape(keyword.lower())
        for match in re.finditer(pattern, text.lower()):
            start = max(0, match.start() - window * 5)  # ~5 chars par mot en moyenne
            end = min(len(text), match.end() + window * 5)
            
            context = text[start:end].strip()
            if context and context not in contexts:
                contexts.append(context)
                
                if len(contexts) >= max_contexts:
                    break
        
        return contexts
    
    def _calculate_topic_relevance(self, score: float) -> str:
        """Calcul de la pertinence d'un topic basé sur son score"""
        thresholds = self.config['topic_relevance_thresholds']
        
        if score >= thresholds['high']:
            return 'high'
        elif score >= thresholds['medium']:
            return 'medium'
        else:
            return 'low'
    
    def _calculate_global_confidence(self, seo_results: Dict, business_results: List, 
                                   content_type: Dict, entities: Dict) -> float:
        """Calcul du score de confiance global"""
        
        # Facteurs de confiance
        seo_confidence = seo_results.get('confidence', 0)
        content_confidence = content_type.get('confidence', 0)
        
        # Bonus si on a des topics business pertinents
        high_relevance_topics = len([t for t in business_results if t.get('relevance') == 'high'])
        business_bonus = min(0.3, high_relevance_topics * 0.15)
        
        # Bonus si on a des entités sectorielles
        entities_count = sum(len(ent_list) for ent_list in entities.values())
        entities_bonus = min(0.2, entities_count * 0.03)
        
        # Calcul final avec pondération
        global_confidence = (
            seo_confidence * 0.4 +
            content_confidence * 0.3 +
            business_bonus +
            entities_bonus
        )
        
        return min(1.0, round(global_confidence, 2))
    
    def _preprocess_text(self, text: str) -> str:
        """Préprocessing du texte pour optimiser l'analyse"""
        
        # Nettoyage des caractères spéciaux (garde les accents)
        text = self.cleanup_pattern.sub(' ', text)
        
        # Normalisation des espaces
        text = self.whitespace_pattern.sub(' ', text)
        
        return text.strip()
    
    def _get_default_classification(self) -> Dict[str, Any]:
        """Classification par défaut en cas d'erreur"""
        return {
            'seo_intent': {
                'main_intent': 'informational',
                'confidence': 0.1,
                'all_scores': {'informational': 0.1, 'commercial': 0, 'transactional': 0, 'navigational': 0},
                'detailed_matches': []
            },
            'business_topics': [],
            'content_type': {
                'main_type': 'general',
                'confidence': 0.1,
                'all_scores': {}
            },
            'sector_entities': {},
            'semantic_keywords': [],
            'confidence': 0.1,
            'sector': self.project_sector,
            'processing_version': '1.0'
        }


class TopicsAnalysisError(Exception):
    """Exception personnalisée pour les erreurs d'analyse NLP"""
    pass


# Utilitaires pour l'intégration
def get_classifier_for_project(project_sector: str) -> AdvancedTopicsClassifier:
    """Factory pour créer un classificateur adapté au secteur du projet"""
    return AdvancedTopicsClassifier(project_sector=project_sector)


def quick_classify(prompt: str, ai_response: str, sector: str = 'domotique') -> Dict[str, Any]:
    """Classification rapide pour usage ponctuel"""
    classifier = AdvancedTopicsClassifier(project_sector=sector)
    return classifier.classify_full(prompt, ai_response)