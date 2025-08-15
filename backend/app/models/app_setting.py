from sqlalchemy import Column, String, Text, DateTime, func
from .base import Base

class AppSetting(Base):
    """Modèle pour la configuration globale de l'application"""
    
    __tablename__ = 'app_settings'
    
    key = Column(String, primary_key=True)
    value = Column(Text, nullable=False)
    description = Column(Text)
    updated_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    def __repr__(self):
        return f"<AppSetting(key='{self.key}', value='{self.value}')>"
    
    @classmethod
    def get_value(cls, session, key: str, default=None):
        """Récupère une valeur de configuration"""
        setting = session.query(cls).filter(cls.key == key).first()
        return setting.value if setting else default
    
    @classmethod
    def set_value(cls, session, key: str, value: str, description: str = None):
        """Met à jour ou crée une valeur de configuration"""
        setting = session.query(cls).filter(cls.key == key).first()
        if setting:
            setting.value = value
            if description:
                setting.description = description
        else:
            setting = cls(key=key, value=value, description=description)
            session.add(setting)
        return setting
    
    def get_bool_value(self) -> bool:
        """Convertit la valeur en booléen"""
        return self.value.lower() in ('1', 'true', 'yes', 'on')
    
    def get_int_value(self) -> int:
        """Convertit la valeur en entier"""
        try:
            return int(self.value)
        except (ValueError, TypeError):
            return 0
    
    def get_float_value(self) -> float:
        """Convertit la valeur en float"""
        try:
            return float(self.value)
        except (ValueError, TypeError):
            return 0.0 