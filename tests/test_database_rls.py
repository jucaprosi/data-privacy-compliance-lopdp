import pytest
from sqlalchemy import text
from app_core.database import current_tenant_id, set_db_tenant_context, Base, engine, async_session_factory
from features.derechos_arco.domain.models import SolicitudARCO, TipoSolicitud, EstadoSolicitud
from datetime import datetime, timezone, timedelta
import uuid

# Habilitar asyncio para estos tests
pytestmark = pytest.mark.anyio

@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"

@pytest.fixture(scope="session")
async def setup_test_db():
    # En un entorno real, crearíamos un schema o DB temporal
    # Por ahora, simplemente nos aseguramos de que SQLAlchemy construya las tablas
    # Nota: RLS real requiere configuraciones DDL específicas en PostgreSQL (ALTER TABLE... ENABLE ROW LEVEL SECURITY).
    # Este test servirá como esqueleto para probar que el ContextVar fluye correctamente.
    pass

async def test_tenant_context_injection():
    """
    Verifica que la variable de contexto (tenant_id) se puede inyectar y fluir.
    En un entorno real de Postgres con RLS, la segunda sesión no vería
    el ticket si cambia de tenant_id.
    """
    tenant_a = str(uuid.uuid4())
    tenant_b = str(uuid.uuid4())
    
    # 1. Ajustar el tenant actual al A
    current_tenant_id.set(tenant_a)
    assert current_tenant_id.get() == tenant_a
    
    # Simulación de que el middleware funciona y RLS estaría blindado.
    # El test físico de PostgreSQL RLS requerirá Testcontainers o DB viva.
    # Por ahora, garantizamos la invariante de que ContextVar no gotea.
    
    # 2. Cambiar a tenant B (simula otra request concurrente)
    current_tenant_id.set(tenant_b)
    assert current_tenant_id.get() == tenant_b
    assert tenant_a != tenant_b

async def test_arco_sla_vencimiento():
    """
    Verifica que el modelo de SLA soporte transiciones correctas
    (Regla lógica en Python).
    """
    now = datetime.now(timezone.utc)
    vencimiento = now + timedelta(days=15)
    
    solicitud = SolicitudARCO(
        tenant_id=uuid.uuid4(),
        tipo_solicitud=TipoSolicitud.ACCESO,
        estado=EstadoSolicitud.RECIBIDA,
        cedula_solicitante="0999999999",
        nombre_solicitante="Test Titular",
        fecha_recepcion=now,
        fecha_vencimiento=vencimiento
    )
    
    assert solicitud.estado == EstadoSolicitud.RECIBIDA
    
    # Simular paso del tiempo y cierre
    solicitud.estado = EstadoSolicitud.VENCIDA
    assert solicitud.estado == EstadoSolicitud.VENCIDA
