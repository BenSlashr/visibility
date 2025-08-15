from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from .config import settings

# Configuration du moteur SQLAlchemy
if settings.DATABASE_URL.startswith("sqlite"):
    # Configuration optimisée pour SQLite
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={
            "check_same_thread": False,
        },
        poolclass=StaticPool,
        echo=settings.DEBUG,  # Log des requêtes SQL en mode debug
    )
    
    # Optimisations SQLite critiques
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        """Configure les PRAGMAs SQLite pour optimiser les performances"""
        cursor = dbapi_connection.cursor()
        # Activer les foreign keys (CRITIQUE)
        cursor.execute("PRAGMA foreign_keys=ON")
        # WAL mode pour concurrence (CRITIQUE)
        cursor.execute("PRAGMA journal_mode=WAL")
        # Optimisations supplémentaires
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=10000")
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.close()
        
else:
    # Configuration pour autres bases de données (PostgreSQL, MySQL, etc.)
    engine = create_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
    )

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Import de la Base depuis les modèles
from ..models import Base

def get_db():
    """
    Générateur de session de base de données pour les dépendances FastAPI
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """
    Créer toutes les tables dans la base de données
    """
    Base.metadata.create_all(bind=engine)

def drop_tables():
    """
    Supprimer toutes les tables (utile pour les tests)
    """
    Base.metadata.drop_all(bind=engine) 