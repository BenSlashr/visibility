from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Index, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import BaseModel, Base

class SERPImport(BaseModel):
    """Modèle pour traquer les imports CSV de positionnement"""
    
    __tablename__ = 'serp_imports'
    
    project_id = Column(String, ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    filename = Column(String, nullable=False)
    import_date = Column(DateTime, default=datetime.utcnow)
    total_keywords = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)  # Seul un import actif par projet
    notes = Column(Text, nullable=True)
    
    # Relations
    project = relationship("Project")
    keywords = relationship("SERPKeyword", back_populates="import_batch", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_serp_imports_project', 'project_id'),
        Index('idx_serp_imports_active', 'project_id', 'is_active'),
        Index('idx_serp_imports_date', 'import_date'),
    )
    
    def __repr__(self):
        return f"<SERPImport(id='{self.id}', project_id='{self.project_id}', filename='{self.filename}')>"


class SERPKeyword(BaseModel):
    """Modèle pour les mots-clés SERP importés"""
    
    __tablename__ = 'serp_keywords'
    
    import_id = Column(String, ForeignKey('serp_imports.id', ondelete='CASCADE'), nullable=False)
    project_id = Column(String, ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    keyword = Column(String, nullable=False)
    keyword_normalized = Column(String, nullable=False)  # Version normalisée pour matching
    volume = Column(Integer, nullable=True) 
    position = Column(Integer, nullable=False)
    url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    import_batch = relationship("SERPImport", back_populates="keywords")
    project = relationship("Project")
    prompt_associations = relationship("PromptSERPAssociation", back_populates="serp_keyword")
    
    __table_args__ = (
        Index('idx_serp_keywords_project', 'project_id'),
        Index('idx_serp_keywords_import', 'import_id'),
        Index('idx_serp_keywords_normalized', 'keyword_normalized'),
        Index('idx_serp_keywords_position', 'position'),
    )
    
    def __repr__(self):
        return f"<SERPKeyword(id='{self.id}', keyword='{self.keyword}', position={self.position})>"


class PromptSERPAssociation(Base):
    """Table de liaison pour associer prompts et mots-clés SERP"""
    
    __tablename__ = 'prompt_serp_associations'
    
    prompt_id = Column(String, ForeignKey('prompts.id', ondelete='CASCADE'), primary_key=True)
    serp_keyword_id = Column(String, ForeignKey('serp_keywords.id', ondelete='CASCADE'), primary_key=True)
    matching_score = Column(Float, nullable=True)  # Score de confiance du matching
    association_type = Column(String, default='manual')  # manual, auto, suggested
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations (utiliser des strings pour éviter les imports circulaires)
    prompt = relationship("Prompt", back_populates="serp_associations")
    serp_keyword = relationship("SERPKeyword", back_populates="prompt_associations")
    
    __table_args__ = (
        Index('idx_prompt_serp_prompt', 'prompt_id'),
        Index('idx_prompt_serp_keyword', 'serp_keyword_id'),
        Index('idx_prompt_serp_type', 'association_type'),
    )
    
    def __repr__(self):
        return f"<PromptSERPAssociation(prompt_id='{self.prompt_id}', serp_keyword_id='{self.serp_keyword_id}', type='{self.association_type}')>"