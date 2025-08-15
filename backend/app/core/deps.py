from typing import Generator
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from .database import get_db

# Dépendance pour obtenir la session de base de données
def get_database_session(db: Session = Depends(get_db)) -> Session:
    """
    Dépendance FastAPI pour obtenir une session de base de données
    """
    return db

# Exemple de dépendance pour l'authentification (à implémenter plus tard)
def get_current_user():
    """
    Dépendance pour obtenir l'utilisateur actuel (authentification)
    À implémenter selon les besoins d'authentification
    """
    # TODO: Implémenter l'authentification
    pass

# Dépendance pour vérifier les clés API des LLM
def verify_api_keys():
    """
    Vérifie que les clés API nécessaires sont configurées
    """
    from .config import settings
    
    if not settings.OPENAI_API_KEY and not settings.ANTHROPIC_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Aucune clé API configurée pour les LLM"
        ) 