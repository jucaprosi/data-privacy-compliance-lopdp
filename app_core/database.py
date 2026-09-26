import os
from contextvars import ContextVar
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, declared_attr
from sqlalchemy import text

# Configuración de BD (Se asume PostgreSQL 16 con asyncpg)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/lopdp360")

# Motor asíncrono
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    pool_size=10,
    max_overflow=20
)

# Fábrica de sesiones
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

# ContextVar para propagar el tenant_id actual de forma segura en código asíncrono
current_tenant_id: ContextVar[str] = ContextVar("current_tenant_id", default="00000000-0000-0000-0000-000000000000")

async def set_db_tenant_context(session: AsyncSession, tenant_id: str):
    """
    Inyecta el tenant_id en la sesión actual de PostgreSQL.
    Esto permite que las políticas RLS evalúen 'app.current_tenant_id'.
    """
    await session.execute(text(f"SET LOCAL app.current_tenant_id = '{tenant_id}';"))

from fastapi import Depends
# Importar lazy para evitar ciclos si es necesario, o import normal
from app_core.security import get_current_tenant

async def get_db_session(tenant_id: str = Depends(get_current_tenant)) -> AsyncGenerator[AsyncSession, None]:
    """
    Dependencia de FastAPI para obtener una sesión de BD asíncrona inyectada con el tenant actual.
    """
    current_tenant_id.set(tenant_id)
    async with async_session_factory() as session:
        # Inyectar el tenant en el contexto de la transacción actual
        await set_db_tenant_context(session, tenant_id)
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# Base declarativa unificada para modelos ADPA
class Base:
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

Base = declarative_base(cls=Base)
