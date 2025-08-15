from sqlalchemy import Column, String, Float, ForeignKey, JSON, DateTime, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import BaseModel, Base

class AnalysisTopics(BaseModel):
    """Modèle pour stocker les résultats de l'analyse NLP/Topics"""
    
    __tablename__ = 'analysis_topics'
    
    # Relation avec l'analyse
    analysis_id = Column(String, ForeignKey('analyses.id', ondelete='CASCADE'), nullable=False, unique=True)
    
    # Classification SEO Intent
    seo_intent = Column(String, nullable=False)  # 'commercial', 'informational', 'transactional', 'navigational'
    seo_confidence = Column(Float, nullable=False, default=0.0)  # 0.0 à 1.0
    seo_detailed_scores = Column(JSON)  # Scores détaillés par intention
    
    # Business Topics (top 5)
    business_topics = Column(JSON)  # Liste des topics avec scores: [{'topic': 'pricing', 'score': 4.2, 'relevance': 'high'}]
    
    # Type de contenu
    content_type = Column(String)  # 'comparison', 'tutorial', 'review', 'list', 'technical'
    content_confidence = Column(Float, default=0.0)
    
    # Entités sectorielles détectées
    sector_entities = Column(JSON)  # {'brands': ['Somfy'], 'technologies': ['Z-Wave']}
    
    # Mots-clés sémantiques extraits
    semantic_keywords = Column(JSON)  # Liste des mots-clés principaux identifiés
    
    # Score de confiance global
    global_confidence = Column(Float, nullable=False, default=0.0)
    
    # Métadonnées
    sector_context = Column(String)  # Secteur utilisé pour la classification
    processing_version = Column(String, default='1.0')  # Version de l'algo utilisé
    
    # Relations
    analysis = relationship("Analysis", back_populates="topics")
    
    # Index pour performance
    __table_args__ = (
        Index('idx_analysis_topics_intent', 'seo_intent', 'seo_confidence'),
        Index('idx_analysis_topics_content_type', 'content_type'),
        Index('idx_analysis_topics_confidence', 'global_confidence'),
        Index('idx_analysis_topics_sector', 'sector_context'),
    )
    
    def __repr__(self):
        return f"<AnalysisTopics(analysis_id='{self.analysis_id}', intent='{self.seo_intent}', confidence={self.global_confidence})>"
    
    @property
    def primary_business_topic(self) -> str:
        """Retourne le topic business principal (score le plus élevé)"""
        if not self.business_topics or not isinstance(self.business_topics, list):
            return None
        
        if len(self.business_topics) == 0:
            return None
            
        return self.business_topics[0].get('topic') if self.business_topics[0] else None
    
    @property
    def is_high_confidence(self) -> bool:
        """Indique si l'analyse a une confiance élevée (>= 0.7)"""
        return self.global_confidence >= 0.7
    
    @property
    def detected_brands(self) -> list:
        """Retourne la liste des marques détectées"""
        if not self.sector_entities or not isinstance(self.sector_entities, dict):
            return []
        return self.sector_entities.get('brands', [])
    
    @property
    def detected_technologies(self) -> list:
        """Retourne la liste des technologies détectées"""
        if not self.sector_entities or not isinstance(self.sector_entities, dict):
            return []
        return self.sector_entities.get('technologies', [])
    
    def get_business_topics_by_relevance(self, min_relevance: str = 'medium') -> list:
        """Retourne les topics business filtrés par niveau de pertinence"""
        if not self.business_topics or not isinstance(self.business_topics, list):
            return []
        
        relevance_order = {'low': 1, 'medium': 2, 'high': 3}
        min_level = relevance_order.get(min_relevance, 2)
        
        return [
            topic for topic in self.business_topics 
            if relevance_order.get(topic.get('relevance', 'low'), 1) >= min_level
        ]
    
    def to_summary_dict(self) -> dict:
        """Conversion en dictionnaire pour les résumés/APIs"""
        return {
            'analysis_id': self.analysis_id,
            'seo_intent': self.seo_intent,
            'seo_confidence': round(self.seo_confidence, 2),
            'content_type': self.content_type,
            'primary_topic': self.primary_business_topic,
            'global_confidence': round(self.global_confidence, 2),
            'brands_detected': len(self.detected_brands),
            'technologies_detected': len(self.detected_technologies),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }