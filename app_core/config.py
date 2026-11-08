# ¤¤backend-developer
"""Configuración centralizada y tipada del sistema usando pydantic_settings."""
import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, SecretStr

# ¤appconfig
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

    # FIRMA-06: ANF STB v2. Vacías por defecto: sin ellas no hay ninguna llamada remota.
    anf_stb_url: str = Field(default="", alias="ANF_STB_URL")
    anf_api_token: SecretStr = Field(default=SecretStr(""), alias="ANF_API_TOKEN")
    anf_api_id: str = Field(default="", alias="ANF_API_ID")
    anf_api_password: SecretStr = Field(default=SecretStr(""), alias="ANF_API_PASSWORD")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

# Se inicializa solo si no estamos en un entorno de pruebas donde las variables podrían faltar,
# O mejor, obligar a pasarlas en test.
# Sin embargo, como el proyecto podría importar `config` globalmente en otros lugares, 
# la instanciación de AppConfig() fallará si faltan.
# Proveeremos los defaults explícitamente cuando sea necesario o vía variables de entorno.
# Cargar .env en os.environ ANTES de los defaults: los módulos que leen
# os.environ directamente (app_core/db/session.py) recibirían si no el
# fallback SQLite. override=False respeta las variables ya definidas
# (Vercel, CI, tests).
load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=False)

# Proveer defaults defensivos si faltan variables en entornos serverless (Vercel) o tests
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:////tmp/test.db")
os.environ.setdefault("CORS_ORIGINS", "*")

# === SEC-16 ===
# INV_LOPDP_NO_DEFAULT_SECRETS_IN_CLOUD (Saltzer y Schroeder, 1975, «Fail-safe defaults»): en la nube
# el backend no arranca con secretos ausentes, conocidos, cortos o repetidos. El repositorio es
# público, así que toda clave escrita en el código es conocida.
REGLA_SECRETOS = "INV_LOPDP_NO_DEFAULT_SECRETS_IN_CLOUD"
SECRETOS_OBLIGATORIOS = ("JWT_SECRET", "SESSION_SECRET")
LONGITUD_MINIMA_SECRETO = 32
# Claves que el código ha puesto por defecto. Siguen siendo válidas solo fuera de la nube.
CLAVE_JWT_DESARROLLO = "super_secret_jwt_key_for_lopdp_360_prod_fallback"
CLAVE_FIRMA_DESCARGAS_DESARROLLO = "bib-104-descarga-segura-clave-temporal"
CLAVES_POR_DEFECTO = frozenset({CLAVE_JWT_DESARROLLO, CLAVE_FIRMA_DESCARGAS_DESARROLLO})
# Decisión del CTO (ficha SEC-16, PR #445): para SEC-16, «en la nube» es Cloud Run, que siempre
# define K_SERVICE. VERCEL no cuenta: el PMV en Vercel está congelado y no se toca.
VARIABLE_DE_CLOUD_RUN = "K_SERVICE"


def corre_en_cloud_run(entorno=None) -> bool:
    """Verdadero si está definida `K_SERVICE` (con cualquier valor, también vacío)."""
    entorno = os.environ if entorno is None else entorno
    return VARIABLE_DE_CLOUD_RUN in entorno


def exigir_secretos_en_la_nube(entorno=None) -> None:
    """En la nube (Cloud Run, `K_SERVICE` definida), lanza `RuntimeError` si `JWT_SECRET` o `SESSION_SECRET` faltan, valen una clave por
    defecto, miden menos de 32 caracteres o son iguales. Fuera de la nube no hace nada.

    El mensaje nombra la regla y la variable, nunca el valor.
    """
    entorno = os.environ if entorno is None else entorno
    if not corre_en_cloud_run(entorno):
        return
    motivos = []
    valores = {}
    for nombre in SECRETOS_OBLIGATORIOS:
        valor = (entorno.get(nombre) or "").strip()
        valores[nombre] = valor
        if not valor:
            motivos.append(f"falta {nombre}")
        elif valor in CLAVES_POR_DEFECTO:
            motivos.append(f"{nombre} vale una clave por defecto del código")
        elif len(valor) < LONGITUD_MINIMA_SECRETO:
            motivos.append(f"{nombre} mide menos de {LONGITUD_MINIMA_SECRETO} caracteres")
    jwt_secreto, sesion_secreto = (valores[n] for n in SECRETOS_OBLIGATORIOS)
    if jwt_secreto and jwt_secreto == sesion_secreto:
        motivos.append("JWT_SECRET y SESSION_SECRET son iguales")
    if motivos:
        raise RuntimeError(
            f"{REGLA_SECRETOS}: el backend no arranca en la nube porque {'; '.join(motivos)}. "
            "Cargue secretos propios y distintos en el entorno del despliegue."
        )


exigir_secretos_en_la_nube()
# Fuera de la nube se conserva la clave de desarrollo; en la nube JWT_SECRET ya está y esto no hace nada.
os.environ.setdefault("JWT_SECRET", CLAVE_JWT_DESARROLLO)
# === fin SEC-16 ===

config = AppConfig()
