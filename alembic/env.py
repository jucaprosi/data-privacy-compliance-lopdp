# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from app_core.huellas_produccion import BaseNoLocal, es_base_local, exigir_base_local
from app_core.models_base import Base

nombre_var = "MIGRATION_DATABASE_URL" if os.environ.get("MIGRATION_DATABASE_URL") else "DATABASE_URL"
url = os.environ.get("MIGRATION_DATABASE_URL") or os.environ.get("DATABASE_URL")
if not url:
    raise RuntimeError("MIGRATION_DATABASE_URL o DATABASE_URL debe estar definida en el entorno.")

# En la nube (Cloud Run Jobs como evydentia-migrate o Cloud Run Services),
# la conexión a Cloud SQL de producción es legítima y no pasa por la guardia de base local.
en_nube = bool(
    os.environ.get("CLOUD_RUN_JOB")
    or os.environ.get("CLOUD_RUN_EXECUTION")
    or os.environ.get("K_SERVICE")
    or (os.environ.get("ENVIRONMENT") == "production" and os.environ.get("PROJECT_ID") == "evydentia")
)
if not en_nube:
    exigir_base_local()
    if not es_base_local(url):
        raise BaseNoLocal((nombre_var,))

if url.startswith("postgresql://"):
    url = url.replace("postgresql://", "postgresql+psycopg://", 1)
config.set_main_option("sqlalchemy.url", url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
