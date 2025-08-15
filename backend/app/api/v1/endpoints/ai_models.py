from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.deps import get_database_session
from app.crud.ai_model import crud_ai_model
from app.schemas.ai_model import (
    AIModelCreate, AIModelUpdate, AIModelRead, AIModelSummary, AIProviderEnum
)

router = APIRouter()

@router.get("/", response_model=List[AIModelRead])
def get_ai_models(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre maximum d'éléments à retourner"),
    provider: Optional[AIProviderEnum] = Query(None, description="Filtrer par fournisseur"),
    active_only: bool = Query(False, description="Afficher seulement les modèles actifs"),
    db: Session = Depends(get_database_session)
):
    """
    Récupère la liste des modèles IA avec filtres
    
    - **skip**: nombre d'éléments à ignorer (pagination)
    - **limit**: nombre maximum d'éléments à retourner
    - **provider**: filtrer par fournisseur (OPENAI, ANTHROPIC, etc.)
    - **active_only**: afficher seulement les modèles actifs
    """
    if active_only:
        models = crud_ai_model.get_active_models(db)
    elif provider:
        models = crud_ai_model.get_by_provider(db, provider)
    else:
        models = crud_ai_model.get_multi(db, skip=skip, limit=limit)
    
    # Appliquer pagination pour les filtres si nécessaire
    if provider or active_only:
        models = models[skip:skip + limit]
    
    return models

@router.get("/active", response_model=List[AIModelRead])
def get_active_ai_models(
    db: Session = Depends(get_database_session)
):
    """
    Récupère la liste des modèles IA actifs uniquement
    
    Retourne tous les modèles configurés et actifs, prêts à être utilisés
    pour les analyses de visibilité.
    """
    models = crud_ai_model.get_active_models(db)
    return models

@router.post("/", response_model=AIModelRead, status_code=status.HTTP_201_CREATED)
def create_ai_model(
    model_in: AIModelCreate,
    db: Session = Depends(get_database_session)
):
    """
    Crée un nouveau modèle IA
    
    - **name**: nom d'affichage du modèle (doit être unique)
    - **provider**: fournisseur (OPENAI, ANTHROPIC, GOOGLE, MISTRAL)
    - **model_identifier**: identifiant pour l'API du fournisseur
    - **max_tokens**: nombre maximum de tokens
    - **cost_per_1k_tokens**: coût par 1000 tokens
    - **is_active**: modèle actif ou non
    """
    # Vérifier l'unicité du nom
    existing_model = crud_ai_model.get_by_name(db, model_in.name)
    if existing_model:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Un modèle avec ce nom existe déjà"
        )
    
    # Vérifier l'unicité de l'identifiant
    existing_identifier = crud_ai_model.get_by_identifier(db, model_in.model_identifier)
    if existing_identifier:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Un modèle avec cet identifiant existe déjà"
        )
    
    model = crud_ai_model.create(db, obj_in=model_in)
    return model

@router.get("/{model_id}", response_model=AIModelRead)
def get_ai_model(
    model_id: str,
    db: Session = Depends(get_database_session)
):
    """
    Récupère un modèle IA par ID
    """
    model = crud_ai_model.get_or_404(db, model_id)
    return model

@router.put("/{model_id}", response_model=AIModelRead)
def update_ai_model(
    model_id: str,
    model_in: AIModelUpdate,
    db: Session = Depends(get_database_session)
):
    """
    Met à jour un modèle IA
    """
    model = crud_ai_model.get_or_404(db, model_id)
    
    # Vérifier l'unicité du nom si changé
    if model_in.name and model_in.name != model.name:
        existing = crud_ai_model.get_by_name(db, model_in.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Un modèle avec ce nom existe déjà"
            )
    
    # Vérifier l'unicité de l'identifiant si changé
    if model_in.model_identifier and model_in.model_identifier != model.model_identifier:
        existing = crud_ai_model.get_by_identifier(db, model_in.model_identifier)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Un modèle avec cet identifiant existe déjà"
            )
    
    model = crud_ai_model.update(db, db_obj=model, obj_in=model_in)
    return model

@router.delete("/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ai_model(
    model_id: str,
    db: Session = Depends(get_database_session)
):
    """
    Supprime un modèle IA
    
    ⚠️ Cette action est irréversible
    """
    model = crud_ai_model.get_or_404(db, model_id)
    crud_ai_model.remove(db, id=model_id)

@router.post("/{model_id}/toggle", response_model=AIModelRead)
def toggle_ai_model_status(
    model_id: str,
    db: Session = Depends(get_database_session)
):
    """
    Active/désactive un modèle IA
    
    Bascule l'état actif/inactif du modèle
    """
    model = crud_ai_model.toggle_active(db, id=model_id)
    return model

@router.get("/active/list", response_model=List[AIModelSummary])
def get_active_ai_models(
    db: Session = Depends(get_database_session)
):
    """
    Récupère tous les modèles IA actifs
    
    Utile pour les listes de sélection dans l'interface
    """
    models = crud_ai_model.get_active_models(db)
    return [
        AIModelSummary(
            id=model.id,
            name=model.name,
            provider=model.provider,
            is_active=model.is_active,
            cost_per_1k_tokens=model.cost_per_1k_tokens,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
        for model in models
    ]

@router.get("/provider/{provider}", response_model=List[AIModelRead])
def get_ai_models_by_provider(
    provider: AIProviderEnum,
    active_only: bool = Query(True, description="Afficher seulement les modèles actifs"),
    db: Session = Depends(get_database_session)
):
    """
    Récupère les modèles IA d'un fournisseur spécifique
    
    - **provider**: fournisseur (OPENAI, ANTHROPIC, GOOGLE, MISTRAL)
    - **active_only**: afficher seulement les modèles actifs
    """
    models = crud_ai_model.get_by_provider(db, provider)
    
    if active_only:
        models = [model for model in models if model.is_active]
    
    return models

@router.get("/provider/{provider}/cheapest", response_model=AIModelRead)
def get_cheapest_model_by_provider(
    provider: AIProviderEnum,
    db: Session = Depends(get_database_session)
):
    """
    Récupère le modèle le moins cher d'un fournisseur
    
    Utile pour sélectionner automatiquement le modèle le plus économique
    """
    model = crud_ai_model.get_cheapest_by_provider(db, provider)
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Aucun modèle actif trouvé pour le fournisseur {provider}"
        )
    return model

@router.get("/provider/{provider}/most-powerful", response_model=AIModelRead)
def get_most_powerful_model_by_provider(
    provider: AIProviderEnum,
    db: Session = Depends(get_database_session)
):
    """
    Récupère le modèle avec le plus de tokens d'un fournisseur
    
    Utile pour les analyses complexes nécessitant beaucoup de contexte
    """
    model = crud_ai_model.get_most_powerful_by_provider(db, provider)
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Aucun modèle actif trouvé pour le fournisseur {provider}"
        )
    return model 