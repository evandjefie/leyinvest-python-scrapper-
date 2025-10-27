"""
Configuration et gestion de la connexion à la base de données MySQL
"""
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from typing import Generator
from app.config import settings
from app.utils.logger import app_logger

# Création du moteur SQLAlchemy avec pool de connexions
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,  # Vérifie la connexion avant utilisation
    pool_recycle=3600,   # Recycle les connexions après 1h
    echo=settings.DEBUG  # Log SQL en mode debug
)

# Event listener pour logger les erreurs de connexion
@event.listens_for(engine, "connect")
def receive_connect(dbapi_conn, connection_record):
    app_logger.debug("Nouvelle connexion à la base de données établie")


@event.listens_for(engine, "checkout")
def receive_checkout(dbapi_conn, connection_record, connection_proxy):
    app_logger.debug("Connexion extraite du pool")


# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base pour les modèles
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dépendance FastAPI pour obtenir une session de base de données

    Yields:
        Session SQLAlchemy
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        app_logger.error(f"Erreur lors de l'utilisation de la session DB: {e}")
        db.rollback()
        raise
    finally:
        db.close()


@contextmanager
def get_db_context():
    """
    Context manager pour utilisation en dehors de FastAPI

    Usage:
        with get_db_context() as db:
            db.query(...)
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        app_logger.error(f"Erreur dans le context manager DB: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def init_db():
    """
    Initialise la base de données (crée toutes les tables)
    """
    try:
        Base.metadata.create_all(bind=engine)
        app_logger.info("Base de données initialisée avec succès")
    except Exception as e:
        app_logger.error(f"Erreur lors de l'initialisation de la base: {e}")
        raise


def check_db_connection() -> bool:
    """
    Vérifie la connexion à la base de données

    Returns:
        True si la connexion est OK, False sinon
    """
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        app_logger.info("Connexion à la base de données vérifiée")
        return True
    except Exception as e:
        app_logger.error(f"Échec de la connexion à la base: {e}")
        return False
