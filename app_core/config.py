# ¤¤backend-developer
"""Configuración centralizada y tipada del sistema usando pydantic_settings."""
import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class AppConfig(BaseSettings):
    app_name: str = "JUBYS Plataforma LOPDP 360"
    version: str = "0.1.0"
    environment: str = Field(default="development", alias="APP_ENV")
    
    # Obligatorias
    database_url: str = Field(..., alias="DATABASE_URL")
    cors_origins: str = Field(..., alias="CORS_ORIGINS")
    jwt_secret: str = Field(..., alias="JWT_SECRET")
    
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    max_questions_visible_diagnostic: int = 80
    target_diagnostic_duration_minutes: int = 60

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

# Se inicializa solo si no estamos en un entorno de pruebas donde las variables podrían faltar,
# O mejor, obligar a pasarlas en test.
# Sin embargo, como el proyecto podría importar `config` globalmente en otros lugares, 
# la instanciación de AppConfig() fallará si faltan.
# Proveeremos los defaults explícitamente cuando sea necesario o vía variables de entorno.
# Proveer defaults defensivos si faltan variables en entornos serverless (Vercel) o tests
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:////tmp/test.db")
os.environ.setdefault("CORS_ORIGINS", "*")
os.environ.setdefault("JWT_SECRET", "super_secret_jwt_key_for_lopdp_360_prod_fallback")

config = AppConfig()

