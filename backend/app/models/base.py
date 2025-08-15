import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import declared_attr

# Base pour tous les modèles
Base = declarative_base()

def generate_uuid():
    """Génère un UUID au format SQLite (hex lowercase)"""
    return uuid.uuid4().hex.lower()

class TimestampMixin:
    """Mixin pour ajouter created_at et updated_at automatiquement"""
    
    created_at = Column(DateTime, default=func.current_timestamp(), nullable=False)
    updated_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())

class BaseModel(Base, TimestampMixin):
    """Modèle de base avec ID UUID et timestamps"""
    
    __abstract__ = True
    
    id = Column(String, primary_key=True, default=generate_uuid)
    
    @declared_attr
    def __tablename__(cls):
        # Génère automatiquement le nom de table à partir du nom de classe
        return cls.__name__.lower() + 's'
    
    def to_dict(self):
        """Convertit l'instance en dictionnaire"""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
    
    def __repr__(self):
        return f"<{self.__class__.__name__}(id='{self.id}')>" 