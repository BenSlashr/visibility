from sqlalchemy import Column, String, Text, ForeignKey, Boolean, Integer, Float, DateTime, Index, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import BaseModel, Base

class Analysis(BaseModel):
    """Modèle pour les résultats d'analyse"""
    
    __tablename__ = 'analyses'
    
    # Relations principales
    prompt_id = Column(String, ForeignKey('prompts.id', ondelete='CASCADE'), nullable=False)
    project_id = Column(String, ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)  # Dénormalisé
    ai_model_id = Column(String, ForeignKey('ai_models.id'), nullable=True)  # Nouveau champ pour traçabilité
    
    # Contenu de l'analyse
    prompt_executed = Column(Text, nullable=False)
    ai_response = Column(Text, nullable=False)
    variables_used = Column(JSON)  # JSON des variables utilisées
    
    # Métriques de visibilité
    brand_mentioned = Column(Boolean, default=False)
    website_mentioned = Column(Boolean, default=False)
    website_linked = Column(Boolean, default=False)
    ranking_position = Column(Integer)  # Position si classement détecté
    
    # Métadonnées techniques
    ai_model_used = Column(String, nullable=False)
    tokens_used = Column(Integer, default=0)
    processing_time_ms = Column(Integer, default=0)
    cost_estimated = Column(Float, default=0.0)
    # Indicateur technique: recherche web utilisée (OpenAI Responses)
    web_search_used = Column(Boolean, default=False)
    
    # Relations
    prompt = relationship("Prompt", back_populates="analyses")
    project = relationship("Project", back_populates="analyses")
    ai_model = relationship("AIModel")  # Nouvelle relation
    competitors = relationship("AnalysisCompetitor", back_populates="analysis", cascade="all, delete-orphan")
    sources = relationship("AnalysisSource", back_populates="analysis", cascade="all, delete-orphan")
    topics = relationship("AnalysisTopics", back_populates="analysis", cascade="all, delete-orphan", uselist=False)
    
    # Index cruciaux pour performance
    __table_args__ = (
        Index('idx_analyses_project_date', 'project_id', 'created_at'),
        Index('idx_analyses_prompt_date', 'prompt_id', 'created_at'),
        Index('idx_analyses_ai_model', 'ai_model_id'),  # Nouveau index
        Index('idx_analyses_brand_mentioned', 'brand_mentioned', 'created_at'),
        Index('idx_analyses_ranking', 'ranking_position', 'created_at'),
    )
    
    def __repr__(self):
        return f"<Analysis(id='{self.id}', prompt_id='{self.prompt_id}', ai_model='{self.ai_model_used}')>"
    
    @property
    def visibility_score(self) -> float:
        """
        Calcule un score de visibilité de 0 à 100 basé sur les métriques
        
        Pondération :
        - Mention de marque: 30 points
        - Mention de site: 25 points  
        - Lien vers le site: 35 points
        - Position dans classement: 10 points (bonus selon position)
        """
        score = 0.0
        
        # Mention de marque (30 points)
        if self.brand_mentioned:
            score += 30
        
        # Mention de site web (25 points)
        if self.website_mentioned:
            score += 25
        
        # Liens vers le site (35 points)
        if self.website_linked:
            score += 35
        
        # Position dans classement (10 points max, bonus selon position)
        if self.ranking_position is not None:
            if self.ranking_position == 1:
                score += 10  # Première position = bonus complet
            elif self.ranking_position <= 3:
                score += 7   # Top 3 = bon bonus
            elif self.ranking_position <= 5:
                score += 5   # Top 5 = bonus moyen
            elif self.ranking_position <= 10:
                score += 3   # Top 10 = petit bonus
            else:
                score += 1   # Mentionné = minimum
        
        return min(100.0, score)
    
    def get_variables_dict(self):
        """Parse le JSON des variables utilisées"""
        import json
        try:
            return json.loads(self.variables_used) if self.variables_used else {}
        except (json.JSONDecodeError, TypeError):
            return {}

class AnalysisCompetitor(Base):
    """Table de liaison pour les concurrents analysés"""
    
    __tablename__ = 'analysis_competitors'
    
    analysis_id = Column(String, ForeignKey('analyses.id', ondelete='CASCADE'), primary_key=True)
    competitor_name = Column(String, primary_key=True)
    is_mentioned = Column(Boolean, default=False)
    mention_context = Column(Text)  # Contexte de la mention
    ranking_position = Column(Integer)  # Position dans le classement (si applicable)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    analysis = relationship("Analysis", back_populates="competitors")
    
    def __repr__(self):
        return f"<AnalysisCompetitor(analysis_id='{self.analysis_id}', competitor='{self.competitor_name}')>" 