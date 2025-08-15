"""
Configuration bridge pour utiliser les anciens mots-clés
pendant la transition vers la nouvelle architecture
"""

import logging
from typing import Dict, List, Any
from ..domain.entities import SEOIntentType
from ..domain.ports import INLPConfigurationRepository

logger = logging.getLogger(__name__)


class LegacyConfigurationRepository(INLPConfigurationRepository):
    """
    Repository qui utilise l'ancienne configuration de mots-clés
    Permet la transition sans perdre les mots-clés existants
    """
    
    def __init__(self):
        # Import l'ancienne configuration
        try:
            from ...nlp.keywords_config import (
                SEO_INTENT_KEYWORDS,
                BUSINESS_TOPICS_KEYWORDS, 
                SECTOR_SPECIFIC_KEYWORDS
            )
            self.seo_keywords = SEO_INTENT_KEYWORDS
            self.business_keywords = BUSINESS_TOPICS_KEYWORDS
            self.sector_keywords = SECTOR_SPECIFIC_KEYWORDS
            logger.info("Configuration legacy chargée avec succès")
        except ImportError as e:
            logger.warning(f"Impossible de charger l'ancienne config: {str(e)}")
            self._initialize_fallback_config()
    
    def _initialize_fallback_config(self):
        """Configuration de fallback si l'ancienne n'est pas disponible"""
        self.seo_keywords = {
            'commercial': {
                'keywords': {
                    'comparaison': ['vs', 'versus', 'contre', 'comparaison', 'compare'],
                    'achat': ['prix', 'price', 'cost', 'acheter', 'buy', 'purchase'],
                    'evaluation': ['review', 'avis', 'test', 'évaluation', 'opinion']
                },
                'weight': 2.0
            },
            'informational': {
                'keywords': {
                    'information': ['comment', 'how to', 'guide', 'tutorial', 'explication'],
                    'definition': ['qu\'est-ce', 'what is', 'définition', 'meaning'],
                    'liste': ['liste', 'list', 'top', 'meilleur', 'best']
                },
                'weight': 1.5
            },
            'transactional': {
                'keywords': {
                    'action': ['télécharger', 'download', 'installer', 'install'],
                    'service': ['service', 'solution', 'outil', 'tool']
                },
                'weight': 1.8
            },
            'navigational': {
                'keywords': {
                    'navigation': ['site', 'website', 'page', 'accueil', 'home'],
                    'marque': ['brand', 'marque', 'société', 'company']
                },
                'weight': 1.0
            }
        }
        
        self.business_keywords = {
            'pricing': {
                'keywords': ['prix', 'price', 'cost', 'tarif', 'abonnement', 'gratuit'],
                'weight': 2.0
            },
            'features': {
                'keywords': ['fonctionnalité', 'feature', 'caractéristique', 'option'],
                'weight': 1.5
            },
            'installation': {
                'keywords': ['installation', 'install', 'setup', 'configuration'],
                'weight': 1.5
            },
            'security': {
                'keywords': ['sécurité', 'security', 'protection', 'safe'],
                'weight': 1.8
            },
            'compatibility': {
                'keywords': ['compatible', 'compatibility', 'support', 'works with'],
                'weight': 1.3
            }
        }
        
        self.sector_keywords = {
            'domotique': {
                'entities': {
                    'brands': ['Somfy', 'Velux', 'Fibaro', 'Legrand', 'Schneider'],
                    'technologies': ['Z-Wave', 'Zigbee', 'WiFi', 'Bluetooth', 'KNX'],
                    'products': ['volet', 'store', 'portail', 'éclairage', 'chauffage']
                }
            },
            'general': {
                'entities': {
                    'brands': [],
                    'technologies': [],
                    'products': []
                }
            }
        }
    
    def get_keywords_for_sector(self, sector: str) -> Dict[str, Any]:
        """Récupère les mots-clés pour un secteur"""
        return self.sector_keywords.get(sector, self.sector_keywords.get('general', {}))
    
    def get_seo_intent_keywords(self) -> Dict[SEOIntentType, Dict[str, Any]]:
        """Récupère les mots-clés pour les intentions SEO"""
        result = {}
        for intent_str, config in self.seo_keywords.items():
            try:
                intent_type = SEOIntentType(intent_str)
                result[intent_type] = config
            except ValueError:
                logger.warning(f"Intention SEO inconnue ignorée: {intent_str}")
        return result
    
    def get_business_topic_keywords(self, sector: str) -> Dict[str, Any]:
        """Récupère les mots-clés pour les topics business"""
        # Pour l'instant, on retourne les mêmes pour tous les secteurs
        # TODO: spécialiser par secteur
        return self.business_keywords
    
    def update_configuration(self, sector: str, config: Dict[str, Any]) -> bool:
        """Met à jour la configuration pour un secteur"""
        # TODO: Implémenter la sauvegarde
        logger.warning("Mise à jour config non implémentée dans le repository legacy")
        return False
    
    def get_configuration_version(self, sector: str) -> str:
        """Retourne la version de la configuration"""
        return "legacy-1.0"


# Configuration de l'adapter avec des fallbacks sûrs

class SafeLegacyConfigurationRepository(LegacyConfigurationRepository):
    """
    Version sécurisée qui gère gracieusement les erreurs
    et fournit toujours une configuration minimale
    """
    
    def __init__(self):
        try:
            super().__init__()
            logger.info("Configuration legacy sécurisée initialisée")
        except Exception as e:
            logger.error(f"Erreur initialisation config legacy: {str(e)}")
            self._initialize_minimal_config()
    
    def _initialize_minimal_config(self):
        """Configuration minimale en cas d'échec total"""
        logger.warning("Utilisation de la configuration minimale de secours")
        
        self.seo_keywords = {
            'informational': {
                'keywords': {'general': ['comment', 'how', 'guide', 'tutorial']},
                'weight': 1.0
            }
        }
        
        self.business_keywords = {
            'general': {
                'keywords': ['feature', 'fonctionnalité', 'service'],
                'weight': 1.0
            }
        }
        
        self.sector_keywords = {
            'general': {
                'entities': {
                    'brands': [],
                    'technologies': [],
                    'products': []
                }
            }
        }
    
    def get_keywords_for_sector(self, sector: str) -> Dict[str, Any]:
        """Version sécurisée qui retourne toujours quelque chose"""
        try:
            result = super().get_keywords_for_sector(sector)
            return result if result else {'entities': {'brands': [], 'technologies': [], 'products': []}}
        except Exception as e:
            logger.error(f"Erreur récupération config secteur {sector}: {str(e)}")
            return {'entities': {'brands': [], 'technologies': [], 'products': []}}
    
    def get_seo_intent_keywords(self) -> Dict[SEOIntentType, Dict[str, Any]]:
        """Version sécurisée pour les intentions SEO"""
        try:
            result = super().get_seo_intent_keywords()
            if not result:
                # Fallback minimal
                result = {
                    SEOIntentType.INFORMATIONAL: {
                        'keywords': {'general': ['information', 'guide']},
                        'weight': 1.0
                    }
                }
            return result
        except Exception as e:
            logger.error(f"Erreur récupération config SEO: {str(e)}")
            return {
                SEOIntentType.INFORMATIONAL: {
                    'keywords': {'general': ['information']},
                    'weight': 1.0
                }
            }
    
    def get_business_topic_keywords(self, sector: str) -> Dict[str, Any]:
        """Version sécurisée pour les topics business"""
        try:
            result = super().get_business_topic_keywords(sector)
            return result if result else {'general': {'keywords': [], 'weight': 1.0}}
        except Exception as e:
            logger.error(f"Erreur récupération config topics {sector}: {str(e)}")
            return {'general': {'keywords': ['feature'], 'weight': 1.0}}