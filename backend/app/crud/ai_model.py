from typing import List, Optional
from sqlalchemy.orm import Session

from .base import CRUDBase
from ..models.ai_model import AIModel
from ..schemas.ai_model import AIModelCreate, AIModelUpdate, AIProviderEnum

class CRUDAIModel(CRUDBase[AIModel, AIModelCreate, AIModelUpdate]):
    def get_active_models(self, db: Session) -> List[AIModel]:
        """Récupère tous les modèles actifs"""
        return db.query(AIModel).filter(AIModel.is_active == True).all()
    
    def get_by_provider(self, db: Session, provider: AIProviderEnum) -> List[AIModel]:
        """Récupère les modèles par fournisseur"""
        return db.query(AIModel).filter(AIModel.provider == provider).all()
    
    def get_by_name(self, db: Session, name: str) -> Optional[AIModel]:
        """Récupère un modèle par nom"""
        return db.query(AIModel).filter(AIModel.name == name).first()
    
    def get_by_identifier(self, db: Session, model_identifier: str) -> Optional[AIModel]:
        """Récupère un modèle par identifiant API"""
        return db.query(AIModel).filter(AIModel.model_identifier == model_identifier).first()
    
    def toggle_active(self, db: Session, *, id: str) -> AIModel:
        """Active/désactive un modèle"""
        model = self.get_or_404(db, id)
        model.is_active = not model.is_active
        db.add(model)
        db.commit()
        db.refresh(model)
        return model
    
    def get_cheapest_by_provider(self, db: Session, provider: AIProviderEnum) -> Optional[AIModel]:
        """Récupère le modèle le moins cher d'un fournisseur"""
        return db.query(AIModel).filter(
            AIModel.provider == provider,
            AIModel.is_active == True
        ).order_by(AIModel.cost_per_1k_tokens.asc()).first()
    
    def get_most_powerful_by_provider(self, db: Session, provider: AIProviderEnum) -> Optional[AIModel]:
        """Récupère le modèle avec le plus de tokens d'un fournisseur"""
        return db.query(AIModel).filter(
            AIModel.provider == provider,
            AIModel.is_active == True
        ).order_by(AIModel.max_tokens.desc()).first()

# Instance globale
crud_ai_model = CRUDAIModel(AIModel) 