from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class BaseSchema(BaseModel):
    """Schéma de base avec configuration pour SQLAlchemy"""
    model_config = ConfigDict(from_attributes=True)

class TimestampSchema(BaseSchema):
    """Schéma avec timestamps automatiques"""
    created_at: datetime
    updated_at: Optional[datetime] = None

class BaseCreateSchema(BaseSchema):
    """Schéma de base pour la création"""
    pass

class BaseUpdateSchema(BaseSchema):
    """Schéma de base pour la mise à jour"""
    pass

class BaseReadSchema(TimestampSchema):
    """Schéma de base pour la lecture avec ID et timestamps"""
    id: str 