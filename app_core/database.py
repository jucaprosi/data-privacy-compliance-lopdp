# ¤¤backend-developer
import os
from contextvars import ContextVar
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, declared_attr
from sqlalchemy import text
from fastapi import HTTPException, Depends

# Configuración de BD (Se asume PostgreSQL 16 con asyncpg o SQLite para desarrollo/serverless)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/lopdp360")

# Motor asíncrono defensivo (SQLite no acepta pool_size ni max_overflow)
engine_kwargs = {"echo": False, "future": True}
if "sqlite" not in DATABASE_URL:
    engine_kwargs.update({"pool_size": 10, "max_overflow": 20})

try:
    engine = create_async_engine(DATABASE_URL, **engine_kwargs)
    async_session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False
    )
except Exception:
    engine = None
    async_session_factory = None

# ContextVar para propagar el tenant_id actual de forma segura en código asíncrono
current_tenant_id: ContextVar[str] = ContextVar("current_tenant_id", default="00000000-0000-0000-0000-000000000000")

async def set_db_tenant_context(session: AsyncSession, tenant_id: str):
    """
    Inyecta el tenant_id en la sesión actual de PostgreSQL.
    Esto permite que las políticas RLS evalúen 'app.current_tenant_id'.
    """
    await session.execute(text(f"SET LOCAL app.current_tenant_id = '{tenant_id}';"))

from app_core.security import get_current_tenant

async def get_db_session(tenant_id: str = Depends(get_current_tenant)) -> AsyncGenerator[AsyncSession, None]:
    """
    Dependencia de FastAPI para obtener una sesión de BD asíncrona inyectada con el tenant actual.
    """
    if async_session_factory is None:
        raise HTTPException(status_code=503, detail="Base de datos no disponible o driver no configurado.")

    current_tenant_id.set(tenant_id)
    async with async_session_factory() as session:
        # Inyectar el tenant en PostgreSQL (SQLite omite RLS)
        if "sqlite" not in DATABASE_URL:
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
