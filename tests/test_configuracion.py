import pytest
import os
from pydantic import ValidationError
from app_core.config import AppConfig

def test_config_fails_missing_critical_vars(monkeypatch):
    """Valida que si faltan variables críticas, la aplicación arroja error al arrancar."""
    # Delete environment variables if they exist
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    monkeypatch.delenv("JWT_SECRET", raising=False)
    
    with pytest.raises(ValidationError) as excinfo:
        AppConfig(_env_file=None)
    
    errors = str(excinfo.value)
    assert "database_url" in errors or "DATABASE_URL" in errors
    assert "cors_origins" in errors or "CORS_ORIGINS" in errors
    assert "jwt_secret" in errors or "JWT_SECRET" in errors

def test_config_succeeds_with_critical_vars(monkeypatch):
    """Valida que la configuración carga correctamente si las variables están presentes."""
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://mock")
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000")
    monkeypatch.setenv("JWT_SECRET", "super_secret_mock")
    
    config = AppConfig(_env_file=None)
    
    assert config.database_url == "postgresql+asyncpg://mock"
    assert config.cors_origins == "http://localhost:3000"
    assert config.jwt_secret == "super_secret_mock"
