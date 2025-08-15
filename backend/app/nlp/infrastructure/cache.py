"""
Système de cache pour les résultats NLP
Support Redis et In-Memory avec TTL et invalidation
"""

import json
import logging
import time
import hashlib
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Pattern
from datetime import datetime, timedelta

from ..domain.entities import NLPAnalysisResult
from ..domain.ports import INLPCacheManager

logger = logging.getLogger(__name__)


class InMemoryNLPCache(INLPCacheManager):
    """Cache en mémoire pour développement et tests"""
    
    def __init__(self, default_ttl: int = 3600, max_size: int = 1000):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._access_times: Dict[str, float] = {}
        self.default_ttl = default_ttl
        self.max_size = max_size
        self._stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'evictions': 0,
            'invalidations': 0
        }
    
    def get_cached_result(self, content_hash: str) -> Optional[NLPAnalysisResult]:
        """Récupère un résultat en cache"""
        self._cleanup_expired()
        
        if content_hash in self._cache:
            cache_entry = self._cache[content_hash]
            
            # Vérifier l'expiration
            if time.time() < cache_entry['expires_at']:
                self._access_times[content_hash] = time.time()
                self._stats['hits'] += 1
                
                # Désérialiser le résultat
                return self._deserialize_result(cache_entry['data'])
            else:
                # Expiré, supprimer
                del self._cache[content_hash]
                del self._access_times[content_hash]
        
        self._stats['misses'] += 1
        return None
    
    def cache_result(self, content_hash: str, result: NLPAnalysisResult, ttl_seconds: int = None) -> None:
        """Met en cache un résultat"""
        if ttl_seconds is None:
            ttl_seconds = self.default_ttl
        
        # Éviction si cache plein
        if len(self._cache) >= self.max_size:
            self._evict_lru()
        
        expires_at = time.time() + ttl_seconds
        serialized_result = self._serialize_result(result)
        
        self._cache[content_hash] = {
            'data': serialized_result,
            'expires_at': expires_at,
            'created_at': time.time()
        }
        self._access_times[content_hash] = time.time()
        self._stats['sets'] += 1
        
        logger.debug(f"Résultat mis en cache: {content_hash[:8]}... (TTL: {ttl_seconds}s)")
    
    def invalidate_cache(self, pattern: str = "*") -> None:
        """Invalide le cache selon un pattern"""
        import fnmatch
        
        if pattern == "*":
            # Tout vider
            count = len(self._cache)
            self._cache.clear()
            self._access_times.clear()
        else:
            # Filtrage par pattern
            keys_to_remove = [
                key for key in self._cache.keys() 
                if fnmatch.fnmatch(key, pattern)
            ]
            count = len(keys_to_remove)
            
            for key in keys_to_remove:
                del self._cache[key]
                del self._access_times[key]
        
        self._stats['invalidations'] += count
        logger.info(f"Cache invalidé: {count} entrées supprimées (pattern: {pattern})")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Récupère les statistiques du cache"""
        self._cleanup_expired()
        
        return {
            'type': 'in_memory',
            'size': len(self._cache),
            'max_size': self.max_size,
            'hit_rate': self._calculate_hit_rate(),
            'stats': self._stats.copy(),
            'memory_usage_mb': self._estimate_memory_usage(),
            'oldest_entry': self._get_oldest_entry_age(),
            'default_ttl': self.default_ttl
        }
    
    def _cleanup_expired(self) -> None:
        """Nettoie les entrées expirées"""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self._cache.items()
            if current_time >= entry['expires_at']
        ]
        
        for key in expired_keys:
            del self._cache[key]
            del self._access_times[key]
        
        if expired_keys:
            logger.debug(f"Nettoyage cache: {len(expired_keys)} entrées expirées supprimées")
    
    def _evict_lru(self) -> None:
        """Éviction LRU (Least Recently Used)"""
        if not self._access_times:
            return
        
        # Trouver la clé la moins récemment utilisée
        lru_key = min(self._access_times.items(), key=lambda x: x[1])[0]
        
        del self._cache[lru_key]
        del self._access_times[lru_key]
        self._stats['evictions'] += 1
        
        logger.debug(f"Éviction LRU: {lru_key[:8]}...")
    
    def _serialize_result(self, result: NLPAnalysisResult) -> Dict[str, Any]:
        """Sérialise un résultat pour le cache"""
        return {
            'analysis_id': result.analysis_id,
            'seo_intent': {
                'main_intent': result.seo_intent.main_intent.value,
                'confidence': result.seo_intent.confidence,
                'detailed_scores': result.seo_intent.detailed_scores
            },
            'content_type': {
                'main_type': result.content_type.main_type,
                'confidence': result.content_type.confidence,
                'all_scores': result.content_type.all_scores
            },
            'business_topics': [
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
            ],
            'sector_entities': {
                entity_type: [
                    {
                        'name': entity.name,
                        'count': entity.count,
                        'contexts': entity.contexts,
                        'entity_type': entity.entity_type
                    }
                    for entity in entities
                ]
                for entity_type, entities in result.sector_entities.items()
            },
            'semantic_keywords': result.semantic_keywords,
            'global_confidence': result.global_confidence,
            'sector_context': result.sector_context,
            'processing_version': result.processing_version,
            'created_at': result.created_at.isoformat()
        }
    
    def _deserialize_result(self, data: Dict[str, Any]) -> NLPAnalysisResult:
        """Désérialise un résultat depuis le cache"""
        from ..domain.entities import SEOIntent, ContentType, BusinessTopic, SectorEntity, SEOIntentType, RelevanceLevel
        
        # Reconstruction des objets complexes
        seo_intent = SEOIntent(
            main_intent=SEOIntentType(data['seo_intent']['main_intent']),
            confidence=data['seo_intent']['confidence'],
            detailed_scores=data['seo_intent']['detailed_scores']
        )
        
        content_type = ContentType(
            main_type=data['content_type']['main_type'],
            confidence=data['content_type']['confidence'],
            all_scores=data['content_type']['all_scores']
        )
        
        business_topics = [
            BusinessTopic(
                topic=topic_data['topic'],
                score=topic_data['score'],
                raw_score=topic_data['raw_score'],
                weight=topic_data['weight'],
                relevance=RelevanceLevel(topic_data['relevance']),
                matches_count=topic_data['matches_count'],
                top_keywords=topic_data['top_keywords'],
                sample_contexts=topic_data['sample_contexts']
            )
            for topic_data in data['business_topics']
        ]
        
        sector_entities = {
            entity_type: [
                SectorEntity(
                    name=entity_data['name'],
                    count=entity_data['count'],
                    contexts=entity_data['contexts'],
                    entity_type=entity_data['entity_type']
                )
                for entity_data in entities_data
            ]
            for entity_type, entities_data in data['sector_entities'].items()
        }
        
        return NLPAnalysisResult(
            analysis_id=data['analysis_id'],
            seo_intent=seo_intent,
            content_type=content_type,
            business_topics=business_topics,
            sector_entities=sector_entities,
            semantic_keywords=data['semantic_keywords'],
            global_confidence=data['global_confidence'],
            sector_context=data['sector_context'],
            processing_version=data['processing_version'],
            created_at=datetime.fromisoformat(data['created_at'])
        )
    
    def _calculate_hit_rate(self) -> float:
        """Calcule le taux de hit du cache"""
        total = self._stats['hits'] + self._stats['misses']
        return round(self._stats['hits'] / total * 100, 2) if total > 0 else 0
    
    def _estimate_memory_usage(self) -> float:
        """Estime l'usage mémoire en MB"""
        total_size = 0
        for entry in self._cache.values():
            total_size += len(json.dumps(entry['data']))
        return round(total_size / 1024 / 1024, 2)
    
    def _get_oldest_entry_age(self) -> Optional[int]:
        """Retourne l'âge de la plus ancienne entrée en secondes"""
        if not self._cache:
            return None
        
        oldest_time = min(entry['created_at'] for entry in self._cache.values())
        return int(time.time() - oldest_time)


class RedisNLPCache(INLPCacheManager):
    """Cache Redis pour production"""
    
    def __init__(self, redis_client, key_prefix: str = "nlp:", default_ttl: int = 3600):
        self.redis = redis_client
        self.key_prefix = key_prefix
        self.default_ttl = default_ttl
        self._stats_key = f"{key_prefix}stats"
        
    def get_cached_result(self, content_hash: str) -> Optional[NLPAnalysisResult]:
        """Récupère un résultat en cache"""
        try:
            key = f"{self.key_prefix}{content_hash}"
            cached_data = self.redis.get(key)
            
            if cached_data:
                self._increment_stat('hits')
                data = json.loads(cached_data.decode('utf-8'))
                return self._deserialize_result(data)
            else:
                self._increment_stat('misses')
                return None
                
        except Exception as e:
            logger.error(f"Erreur lecture cache Redis: {str(e)}")
            self._increment_stat('errors')
            return None
    
    def cache_result(self, content_hash: str, result: NLPAnalysisResult, ttl_seconds: int = None) -> None:
        """Met en cache un résultat"""
        try:
            if ttl_seconds is None:
                ttl_seconds = self.default_ttl
            
            key = f"{self.key_prefix}{content_hash}"
            serialized_result = self._serialize_result(result)
            data = json.dumps(serialized_result)
            
            self.redis.setex(key, ttl_seconds, data)
            self._increment_stat('sets')
            
            logger.debug(f"Résultat mis en cache Redis: {content_hash[:8]}... (TTL: {ttl_seconds}s)")
            
        except Exception as e:
            logger.error(f"Erreur écriture cache Redis: {str(e)}")
            self._increment_stat('errors')
    
    def invalidate_cache(self, pattern: str = "*") -> None:
        """Invalide le cache selon un pattern"""
        try:
            search_pattern = f"{self.key_prefix}{pattern}"
            keys = self.redis.keys(search_pattern)
            
            if keys:
                count = self.redis.delete(*keys)
                self._increment_stat('invalidations', count)
                logger.info(f"Cache Redis invalidé: {count} clés supprimées (pattern: {pattern})")
            
        except Exception as e:
            logger.error(f"Erreur invalidation cache Redis: {str(e)}")
            self._increment_stat('errors')
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Récupère les statistiques du cache"""
        try:
            # Stats personnalisées
            stats = {}
            stats_keys = ['hits', 'misses', 'sets', 'invalidations', 'errors']
            for stat_key in stats_keys:
                value = self.redis.hget(self._stats_key, stat_key)
                stats[stat_key] = int(value) if value else 0
            
            # Stats Redis
            redis_info = self.redis.info('memory')
            
            # Compter les clés NLP
            nlp_keys = self.redis.keys(f"{self.key_prefix}*")
            
            return {
                'type': 'redis',
                'size': len(nlp_keys),
                'hit_rate': self._calculate_hit_rate(stats),
                'stats': stats,
                'memory_usage_mb': round(redis_info.get('used_memory', 0) / 1024 / 1024, 2),
                'redis_version': redis_info.get('redis_version', 'unknown'),
                'default_ttl': self.default_ttl
            }
            
        except Exception as e:
            logger.error(f"Erreur récupération stats cache Redis: {str(e)}")
            return {'type': 'redis', 'error': str(e)}
    
    def _increment_stat(self, stat_name: str, value: int = 1) -> None:
        """Incrémente une statistique"""
        try:
            self.redis.hincrby(self._stats_key, stat_name, value)
        except Exception as e:
            logger.error(f"Erreur incrémentation stat {stat_name}: {str(e)}")
    
    def _serialize_result(self, result: NLPAnalysisResult) -> Dict[str, Any]:
        """Sérialise un résultat pour Redis"""
        # Réutiliser la même logique que InMemoryCache
        cache = InMemoryNLPCache()
        return cache._serialize_result(result)
    
    def _deserialize_result(self, data: Dict[str, Any]) -> NLPAnalysisResult:
        """Désérialise un résultat depuis Redis"""
        # Réutiliser la même logique que InMemoryCache
        cache = InMemoryNLPCache()
        return cache._deserialize_result(data)
    
    def _calculate_hit_rate(self, stats: Dict[str, int]) -> float:
        """Calcule le taux de hit"""
        total = stats.get('hits', 0) + stats.get('misses', 0)
        return round(stats.get('hits', 0) / total * 100, 2) if total > 0 else 0


class MultiLevelNLPCache(INLPCacheManager):
    """Cache multi-niveaux (L1: Memory, L2: Redis)"""
    
    def __init__(self, memory_cache: InMemoryNLPCache, redis_cache: RedisNLPCache):
        self.l1_cache = memory_cache
        self.l2_cache = redis_cache
        
    def get_cached_result(self, content_hash: str) -> Optional[NLPAnalysisResult]:
        """Récupère un résultat avec stratégie multi-niveaux"""
        # Essayer L1 d'abord
        result = self.l1_cache.get_cached_result(content_hash)
        if result:
            logger.debug(f"Cache L1 hit: {content_hash[:8]}...")
            return result
        
        # Essayer L2
        result = self.l2_cache.get_cached_result(content_hash)
        if result:
            logger.debug(f"Cache L2 hit: {content_hash[:8]}... (promu vers L1)")
            # Promouvoir vers L1
            self.l1_cache.cache_result(content_hash, result, ttl_seconds=300)  # 5 min en L1
            return result
        
        return None
    
    def cache_result(self, content_hash: str, result: NLPAnalysisResult, ttl_seconds: int = None) -> None:
        """Met en cache dans les deux niveaux"""
        # L1 avec TTL court
        self.l1_cache.cache_result(content_hash, result, ttl_seconds=300)  # 5 min
        
        # L2 avec TTL long
        self.l2_cache.cache_result(content_hash, result, ttl_seconds=ttl_seconds or 3600)  # 1h
    
    def invalidate_cache(self, pattern: str = "*") -> None:
        """Invalide les deux niveaux"""
        self.l1_cache.invalidate_cache(pattern)
        self.l2_cache.invalidate_cache(pattern)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Récupère les stats combinées"""
        l1_stats = self.l1_cache.get_cache_stats()
        l2_stats = self.l2_cache.get_cache_stats()
        
        return {
            'type': 'multi_level',
            'l1_cache': l1_stats,
            'l2_cache': l2_stats,
            'combined_hit_rate': self._calculate_combined_hit_rate(l1_stats, l2_stats)
        }
    
    def _calculate_combined_hit_rate(self, l1_stats: Dict, l2_stats: Dict) -> float:
        """Calcule le taux de hit combiné"""
        l1_hits = l1_stats.get('stats', {}).get('hits', 0)
        l1_misses = l1_stats.get('stats', {}).get('misses', 0)
        l2_hits = l2_stats.get('stats', {}).get('hits', 0)
        l2_misses = l2_stats.get('stats', {}).get('misses', 0)
        
        total_hits = l1_hits + l2_hits
        total_requests = l1_hits + l1_misses + l2_hits + l2_misses
        
        return round(total_hits / total_requests * 100, 2) if total_requests > 0 else 0


# Factory pour créer le cache selon l'environnement

class CacheFactory:
    """Factory pour créer le système de cache approprié"""
    
    @staticmethod
    def create_development_cache() -> INLPCacheManager:
        """Cache pour développement (in-memory)"""
        return InMemoryNLPCache(default_ttl=1800, max_size=500)  # 30min, 500 entrées
    
    @staticmethod
    def create_production_cache(redis_client) -> INLPCacheManager:
        """Cache pour production (multi-niveaux)"""
        memory_cache = InMemoryNLPCache(default_ttl=300, max_size=100)  # 5min, 100 entrées
        redis_cache = RedisNLPCache(redis_client, default_ttl=3600)  # 1h
        return MultiLevelNLPCache(memory_cache, redis_cache)
    
    @staticmethod
    def create_test_cache() -> INLPCacheManager:
        """Cache pour tests (in-memory sans TTL)"""
        return InMemoryNLPCache(default_ttl=86400, max_size=50)  # 24h, 50 entrées