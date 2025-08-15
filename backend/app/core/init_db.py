"""
Script d'initialisation de la base de données
Crée les tables et insère les données par défaut
"""
import logging
from sqlalchemy.orm import Session

from .database import engine, SessionLocal
from ..models import Base, AIModel, AppSetting
from ..enums import AIProviderEnum

logger = logging.getLogger(__name__)

def create_tables():
    """Crée toutes les tables de la base de données"""
    logger.info("Création des tables de base de données...")
    Base.metadata.create_all(bind=engine)
    logger.info("Tables créées avec succès")

def init_ai_models(db: Session):
    """Initialise les modèles IA par défaut"""
    logger.info("Initialisation des modèles IA...")
    
    # Vérifier si des modèles existent déjà
    existing_models = db.query(AIModel).count()
    if existing_models > 0:
        logger.info(f"{existing_models} modèles IA déjà présents, pas d'initialisation")
        return
    
    # Modèles IA par défaut
    default_ai_models = [
        {
            'name': 'GPT-3.5 Turbo',
            'provider': AIProviderEnum.OPENAI,
            'model_identifier': 'gpt-3.5-turbo',
            'max_tokens': 4096,
            'cost_per_1k_tokens': 0.0015,
            'is_active': True
        },
        {
            'name': 'ChatGPT-4o Latest',
            'provider': AIProviderEnum.OPENAI,
            'model_identifier': 'chatgpt-4o-latest',
            'max_tokens': 8192,
            'cost_per_1k_tokens': 0.005,
            'is_active': True
        },
        {
            'name': 'Claude 3 Haiku',
            'provider': AIProviderEnum.ANTHROPIC,
            'model_identifier': 'claude-3-haiku-20240307',
            'max_tokens': 4096,
            'cost_per_1k_tokens': 0.00025,
            'is_active': True
        },
        {
            'name': 'Gemini 2.5 Flash',
            'provider': AIProviderEnum.GOOGLE,
            'model_identifier': 'gemini-2.0-flash-exp',
            'max_tokens': 8192,
            'cost_per_1k_tokens': 0.00015,
            'is_active': True
        },
        {
            'name': 'Mistral Small',
            'provider': AIProviderEnum.MISTRAL,
            'model_identifier': 'mistral-small-latest',
            'max_tokens': 4096,
            'cost_per_1k_tokens': 0.002,
            'is_active': True
        }
    ]
    
    for model_data in default_ai_models:
        ai_model = AIModel(**model_data)
        db.add(ai_model)
    
    db.commit()
    logger.info(f"Initialisé {len(default_ai_models)} modèles IA")

def init_app_settings(db: Session):
    """Initialise les paramètres de l'application"""
    logger.info("Initialisation des paramètres de l'application...")
    
    # Vérifier si des paramètres existent déjà
    existing_settings = db.query(AppSetting).count()
    if existing_settings > 0:
        logger.info(f"{existing_settings} paramètres déjà présents, pas d'initialisation")
        return
    
    # Paramètres par défaut
    default_settings = [
        {
            'key': 'openai_api_key',
            'value': '',
            'description': 'Clé API OpenAI pour les modèles GPT'
        },
        {
            'key': 'anthropic_api_key',
            'value': '',
            'description': 'Clé API Anthropic pour les modèles Claude'
        },
        {
            'key': 'default_max_tokens',
            'value': '4096',
            'description': 'Nombre maximum de tokens par défaut pour les analyses'
        },
        {
            'key': 'analysis_timeout_seconds',
            'value': '30',
            'description': 'Timeout en secondes pour les appels aux APIs IA'
        },
        {
            'key': 'auto_detect_ranking',
            'value': '1',
            'description': 'Détection automatique des positions dans les classements'
        },
        {
            'key': 'max_concurrent_analyses',
            'value': '3',
            'description': 'Nombre maximum d\'analyses simultanées'
        },
        {
            'key': 'enable_cost_tracking',
            'value': '1',
            'description': 'Activer le suivi des coûts des analyses'
        }
    ]
    
    for setting_data in default_settings:
        app_setting = AppSetting(**setting_data)
        db.add(app_setting)
    
    db.commit()
    logger.info(f"Initialisé {len(default_settings)} paramètres d'application")

def init_database():
    """Initialise complètement la base de données"""
    logger.info("Initialisation de la base de données Visibility Tracker...")
    
    # Créer les tables
    create_tables()
    
    # Initialiser les données par défaut
    db = SessionLocal()
    try:
        init_ai_models(db)
        init_app_settings(db)
        logger.info("Base de données initialisée avec succès ✅")
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation : {e}")
        db.rollback()
        raise
    finally:
        db.close()

def reset_database():
    """Supprime et recrée toute la base de données (ATTENTION: perte de données)"""
    logger.warning("ATTENTION: Suppression complète de la base de données...")
    Base.metadata.drop_all(bind=engine)
    init_database()
    logger.info("Base de données réinitialisée ✅")

if __name__ == "__main__":
    # Pour exécuter directement le script
    logging.basicConfig(level=logging.INFO)
    init_database() 