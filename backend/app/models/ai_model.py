from sqlalchemy import Column, String, Integer, Float, Boolean, Index
from sqlalchemy.orm import relationship
from .base import BaseModel

class AIModel(BaseModel):
    """Modèle pour les modèles IA disponibles"""
    
    __tablename__ = 'ai_models'
    
    name = Column(String, nullable=False, unique=True)
    provider = Column(String, nullable=False)  # "OPENAI", "ANTHROPIC", "GOOGLE"
    model_identifier = Column(String, nullable=False)  # ID pour l'API
    max_tokens = Column(Integer, default=4096)
    cost_per_1k_tokens = Column(Float, default=0.03)
    is_active = Column(Boolean, default=True)
    
    # Relations
    prompts = relationship("Prompt", back_populates="ai_model")
    
    # Index pour optimiser les requêtes
    __table_args__ = (
        Index('idx_ai_models_active', 'is_active', 'provider'),
    )
    
    def __repr__(self):
        return f"<AIModel(id='{self.id}', name='{self.name}', provider='{self.provider}')>"
    
    @property
    def display_name(self):
        """Nom d'affichage complet"""
        return f"{self.name} ({self.provider})"
    
    def calculate_cost(self, tokens_used: int) -> float:
        """Calcule le coût pour un nombre de tokens donné"""
        return (tokens_used / 1000) * self.cost_per_1k_tokens 