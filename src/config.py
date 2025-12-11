"""
Configuration de l'application
"""

from pydantic_settings import BaseSettings
from pathlib import Path

# Définir les chemins de base
BASE_DIR = Path(__file__).parent.parent  # Remonte à api-iqss/
DATA_DIR = BASE_DIR / "data" / "db"


class Settings(BaseSettings):
    # Base de données GAM (Oracle)
    GAM_HOST: str = "srvorat500.hopital-foch.net"
    GAM_PORT: int = 1521
    GAM_SERVICE: str = "AXIN"
    GAM_USER: str
    GAM_PASSWORD: str

    # Base de données ESL (SQL Server)
    ESL_HOST: str = "SRVAPP600.hopital-foch.net"
    ESL_PORT: int = 1433
    ESL_DATABASE: str = "master"
    ESL_USER: str
    ESL_PASSWORD: str

    MATRICE_PATH: str = str(DATA_DIR / "iql_matspe_7.xlsx")

    # Configuration Générale
    APP_TITLE: str = "Indicateurs Lettres de Liaison"
    APP_VERSION: str = "1.0.0"

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


settings = Settings()
