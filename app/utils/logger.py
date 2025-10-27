"""
Système de logging centralisé avec rotation des fichiers
"""
import logging
import os
from logging.handlers import RotatingFileHandler
from app.config import settings


def setup_logger(name: str = __name__) -> logging.Logger:
    """
    Configure et retourne un logger avec rotation de fichiers

    Args:
        name: Nom du logger

    Returns:
        Logger configuré
    """
    # Créer le répertoire de logs s'il n'existe pas
    os.makedirs(settings.LOGS_DIR, exist_ok=True)

    logger = logging.getLogger(name)

    # Éviter les doublons de handlers
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, settings.LOG_LEVEL))

    # Format détaillé des logs
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Handler fichier avec rotation
    log_file = os.path.join(settings.LOGS_DIR, 'app.log')
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=settings.LOG_MAX_BYTES,
        backupCount=settings.LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # Handler console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


# Logger principal de l'application
app_logger = setup_logger('brvm_api')
