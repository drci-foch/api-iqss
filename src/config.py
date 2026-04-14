"""
Configuration de l'application
"""

from pydantic_settings import BaseSettings
from pathlib import Path

# Définir les chemins de base
BASE_DIR = Path(__file__).parent.parent  # Remonte à api-iqss/
DATA_DIR = BASE_DIR / "static-data"


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
    MATRICE_SEJ_PATH: str = str(DATA_DIR / "mat_spe_sej.xlsx")

    # Configuration Générale
    APP_TITLE: str = "Indicateurs Lettres de Liaison"
    APP_VERSION: str = "1.0.0"

    # Environnement : "production" | "uat" | "development"
    APP_ENV: str = "development"

    # Authentification
    JWT_SECRET_KEY: str = "changeme-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 480  # 8 heures

    # LDAP (utilisé uniquement si APP_ENV=production)
    LDAP_SERVER: str = ""
    LDAP_BASE_DN: str = ""

    # Admin seed (créé au démarrage si aucun admin n'existe)
    ADMIN_SEED_USERNAME: str = "admin"
    ADMIN_SEED_PASSWORD: str = "admin"

    # Base SQLite pour les utilisateurs
    DB_PATH: str = str(BASE_DIR / "data" / "auth.db")

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


settings = Settings()
