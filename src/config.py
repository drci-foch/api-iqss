"""
Configuration de l'application
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Base de données GAM
    GAM_DRIVER: str = "oracle.jdbc.OracleDriver"
    GAM_URL: str
    GAM_USER: str
    GAM_PASSWORD: str

    # Base de données ESL
    ESL_DRIVER: str = "com.microsoft.sqlserver.jdbc.SQLServerDriver"
    ESL_URL: str
    ESL_USER: str
    ESL_PASSWORD: str

    # Configuration Email
    SMTP_HOST: str = "smtp.office365.com"
    SMTP_PORT: int = 587
    SMTP_USER: str
    SMTP_PASSWORD: str
    EMAIL_FROM: str
    EMAIL_TO: str
    EMAIL_CC: Optional[str] = None

    # Configuration Générale
    APP_TITLE: str = "Indicateurs Lettres de Liaison"
    APP_VERSION: str = "1.0.0"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
