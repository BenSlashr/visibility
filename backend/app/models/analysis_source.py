from datetime import datetime
from urllib.parse import urlparse

from sqlalchemy import Column, String, Text, ForeignKey, Boolean, Integer, DateTime, JSON, Index
from sqlalchemy.orm import relationship

from .base import BaseModel


class AnalysisSource(BaseModel):
    """Source/citation extraite depuis une réponse IA et liée à une analyse."""

    __tablename__ = 'analysis_sources'

    # Clé primaire générée par Base (id, timestamps)
    analysis_id = Column(String, ForeignKey('analyses.id', ondelete='CASCADE'), nullable=False)

    # Données source
    url = Column(Text, nullable=False)
    domain = Column(String, nullable=True)
    title = Column(String, nullable=True)
    snippet = Column(Text, nullable=True)
    citation_label = Column(String, nullable=True)  # ex: "[1]"
    position = Column(Integer, nullable=True)  # offset dans le texte source

    # Validation/enrichissement (optionnel)
    is_valid = Column(Boolean, default=None, nullable=True)
    http_status = Column(Integer, nullable=True)
    content_type = Column(String, nullable=True)
    fetched_at = Column(DateTime, nullable=True)
    fetch_error = Column(String, nullable=True)
    confidence = Column(Integer, nullable=True)  # 0-100
    # 'metadata' est réservé par SQLAlchemy pour la base déclarative -> utiliser un nom d'attribut différent
    metadata_json = Column('metadata', JSON, nullable=True)

    # Relation
    analysis = relationship('Analysis', back_populates='sources')

    __table_args__ = (
        Index('idx_analysis_sources_analysis', 'analysis_id'),
        Index('idx_analysis_sources_domain', 'domain'),
    )

    @staticmethod
    def derive_domain(url: str) -> str:
        try:
            parsed = urlparse(url)
            host = parsed.netloc.lower()
            return host[4:] if host.startswith('www.') else host
        except Exception:
            return ''


