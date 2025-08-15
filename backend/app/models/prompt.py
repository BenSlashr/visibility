from sqlalchemy import Column, String, Text, ForeignKey, Boolean, Integer, DateTime, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import BaseModel, Base

class Prompt(BaseModel):
    """Modèle pour les templates d'analyse"""
    
    __tablename__ = 'prompts'
    
    project_id = Column(String, ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    ai_model_id = Column(String, ForeignKey('ai_models.id'), nullable=True)  # Nullable pour multi-agents
    name = Column(String, nullable=False)
    template = Column(Text, nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    is_multi_agent = Column(Boolean, default=False)  # Nouveau champ
    last_executed_at = Column(DateTime)
    execution_count = Column(Integer, default=0)
    
    # Relations
    project = relationship("Project", back_populates="prompts")
    ai_model = relationship("AIModel", back_populates="prompts")  # Pour compatibilité ascendante
    ai_models = relationship("PromptAIModel", back_populates="prompt", cascade="all, delete-orphan")  # Multi-agents
    tags = relationship("PromptTag", back_populates="prompt", cascade="all, delete-orphan")
    analyses = relationship("Analysis", back_populates="prompt", cascade="all, delete-orphan")
    
    # Index pour optimiser les requêtes
    __table_args__ = (
        Index('idx_prompts_project', 'project_id', 'is_active'),
        Index('idx_prompts_model', 'ai_model_id'),
        Index('idx_prompts_multi_agent', 'is_multi_agent'),
        Index('idx_prompts_last_executed', 'last_executed_at'),
    )
    
    def __repr__(self):
        return f"<Prompt(id='{self.id}', name='{self.name}', project_id='{self.project_id}')>"
    
    @property
    def tag_names(self):
        """Retourne la liste des noms de tags"""
        return [tag.tag_name for tag in self.tags]
    
    @property
    def active_ai_models(self):
        """Retourne la liste des modèles IA actifs pour ce prompt"""
        if not self.is_multi_agent:
            return [self.ai_model] if self.ai_model else []
        return [pam.ai_model for pam in self.ai_models if pam.is_active and pam.ai_model.is_active]
    
    @property
    def default_ai_model(self):
        """Retourne le modèle IA par défaut (pour compatibilité)"""
        if not self.is_multi_agent:
            return self.ai_model
        # Pour multi-agents, retourner le premier modèle actif
        active_models = self.active_ai_models
        return active_models[0] if active_models else None


class PromptAIModel(Base):
    """Table de liaison pour les prompts multi-agents"""
    
    __tablename__ = 'prompt_ai_models'
    
    prompt_id = Column(String, ForeignKey('prompts.id', ondelete='CASCADE'), primary_key=True)
    ai_model_id = Column(String, ForeignKey('ai_models.id', ondelete='CASCADE'), primary_key=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    prompt = relationship("Prompt", back_populates="ai_models")
    ai_model = relationship("AIModel")
    
    # Index pour optimiser les requêtes
    __table_args__ = (
        Index('idx_prompt_ai_models_prompt', 'prompt_id'),
        Index('idx_prompt_ai_models_active', 'is_active'),
    )
    
    def __repr__(self):
        return f"<PromptAIModel(prompt_id='{self.prompt_id}', ai_model_id='{self.ai_model_id}')>"


class PromptTag(Base):
    """Table de liaison pour les tags des prompts"""
    
    __tablename__ = 'prompt_tags'
    
    prompt_id = Column(String, ForeignKey('prompts.id', ondelete='CASCADE'), primary_key=True)
    tag_name = Column(String, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    prompt = relationship("Prompt", back_populates="tags")
    
    # Index pour recherche par tag
    __table_args__ = (
        Index('idx_prompt_tags_tag', 'tag_name'),
    )
    
    def __repr__(self):
        return f"<PromptTag(prompt_id='{self.prompt_id}', tag='{self.tag_name}')>" 