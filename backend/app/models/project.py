from sqlalchemy import Column, String, Text, ForeignKey, Index, UniqueConstraint, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import BaseModel, Base

class Project(BaseModel):
    """Modèle pour les projets SEO"""
    
    __tablename__ = 'projects'
    
    name = Column(String, nullable=False)
    main_website = Column(String)
    description = Column(Text)
    
    # Relations
    keywords = relationship("ProjectKeyword", back_populates="project", cascade="all, delete-orphan")
    competitors = relationship("Competitor", back_populates="project", cascade="all, delete-orphan")
    prompts = relationship("Prompt", back_populates="project", cascade="all, delete-orphan")
    analyses = relationship("Analysis", back_populates="project", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Project(id='{self.id}', name='{self.name}')>"

class ProjectKeyword(Base):
    """Table de liaison pour les mots-clés des projets"""
    
    __tablename__ = 'project_keywords'
    
    project_id = Column(String, ForeignKey('projects.id', ondelete='CASCADE'), primary_key=True)
    keyword = Column(String, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    project = relationship("Project", back_populates="keywords")
    
    def __repr__(self):
        return f"<ProjectKeyword(project_id='{self.project_id}', keyword='{self.keyword}')>"

class Competitor(BaseModel):
    """Modèle pour les sites concurrents"""
    
    __tablename__ = 'competitors'
    
    project_id = Column(String, ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    name = Column(String, nullable=False)
    website = Column(String, nullable=False)
    
    # Relations
    project = relationship("Project", back_populates="competitors")
    
    # Contrainte d'unicité par projet
    __table_args__ = (
        UniqueConstraint('project_id', 'website', name='uq_project_competitor_website'),
        Index('idx_competitors_project', 'project_id'),
    )
    
    def __repr__(self):
        return f"<Competitor(id='{self.id}', name='{self.name}', website='{self.website}')>"

# Index pour optimiser les requêtes
Index('idx_projects_name', Project.name)
Index('idx_projects_created', Project.created_at.desc())
Index('idx_keywords_keyword', ProjectKeyword.keyword) 