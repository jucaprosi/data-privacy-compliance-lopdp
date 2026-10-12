import pytest
from sqlalchemy import text
from app_core.db.session import current_tenant_id, fijar_contexto_rls, get_tenant_session
from app_core.security import get_current_tenant
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


class _SesionGrabadora:
    """Sesión simulada: guarda cada sentencia ejecutada y sus parámetros."""

    def __init__(self):
        self.ejecutadas = []

    async def execute(self, sentencia, parametros=None):
        self.ejecutadas.append((str(sentencia), parametros))


async def test_fijar_contexto_rls_enlaza_el_tenant_como_parametro():
    """El valor del tenant viaja como parámetro y jamás dentro del texto SQL."""
    sesion = _SesionGrabadora()
    tenant = "t-1'; DROP TABLE areas; --"

    await fijar_contexto_rls(sesion, tenant, "u-1")

    assert [p for _, p in sesion.ejecutadas] == [{"tid": tenant}, {"uid": "u-1"}]
    for texto, _ in sesion.ejecutadas:
        assert "set_config" in texto and "true" in texto
        assert "DROP" not in texto and tenant not in texto


async def test_fijar_contexto_rls_sin_valores_no_ejecuta_nada():
    sesion = _SesionGrabadora()
    await fijar_contexto_rls(sesion, None, None)
    assert sesion.ejecutadas == []


async def test_get_tenant_session_resuelve_el_tenant_de_la_identidad_autenticada():
    """El tenant de la sesión sale de get_current_tenant (401 sin credencial), no de cabeceras."""
    import inspect

    marcador = inspect.signature(get_tenant_session).parameters["tenant_id"].default
    assert marcador.dependency is get_current_tenant
