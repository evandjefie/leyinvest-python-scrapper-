"""
Configuration centralisée de l'application BRVM API
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Configuration de l'application avec gestion des variables d'environnement"""

    # Application
    APP_NAME: str = "BRVM Data API"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "API officielle pour consulter les cours des actions BRVM et les indicateurs du marché"
    DEBUG: bool = False

    # Base de données
    DATABASE_URL: str = "mysql+pymysql://root:password@localhost:3306/brvm_db"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # URLs BRVM
    BRVM_ACTIONS_URL: str = "https://www.brvm.org/fr/cours-actions/0"
    BRVM_PDF_BASE_URL: str = "https://www.brvm.org/sites/default/files/boc_{date}_2.pdf"

    # Scheduler
    SCRAPER_INTERVAL_MINUTES: int = 30
    PDF_DOWNLOAD_HOURS: list = [12, 18]

    # Webhooks
    WEBHOOK_TIMEOUT: int = 10
    WEBHOOK_MAX_RETRIES: int = 3

    # Fichiers
    DOWNLOADS_DIR: str = "downloads"
    LOGS_DIR: str = "logs"
    LOG_LEVEL: str = "INFO"
    LOG_MAX_BYTES: int = 10485760  # 10 MB
    LOG_BACKUP_COUNT: int = 5

    # Timezone
    TIMEZONE: str = "Africa/Abidjan"

    DATA_RETENTION_DAYS: int = 60

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore"  # Ignore les variables d'environnement supplémentaires (comme celles de Docker)
    }


settings = Settings()
