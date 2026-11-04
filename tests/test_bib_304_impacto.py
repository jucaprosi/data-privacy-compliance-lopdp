# ¤adpa ¤arbitro
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from api.errores import ErrorNegocio
from features.biblioteca.services import impacto
from features.notificaciones.notificaciones_service import construir_aviso_impacto

RAIZ = Path(__file__).parents[1]


def test_aviso_no_expone_contenido_sensible_ni_acredita_envio():
    aviso = construir_aviso_impacto("exp-1", "tenant-1", "https://app.example")
    assert aviso == {
        "tipo": "biblioteca_version_publicada", "tenant_id": "tenant-1", "expediente_id": "exp-1",
        "asunto": "Revisión documental pendiente",
        "mensaje": "Hay una nueva versión disponible. Registra la decisión de tu organización.",
        "enlace": "https://app.example/biblioteca?impacto=exp-1",
    }
    assert "enviado" not in str(aviso).lower()


@pytest.mark.asyncio
async def test_decision_invalida_falla_antes_de_persistir():
    session = AsyncMock()
    with pytest.raises(ErrorNegocio) as exc:
        await impacto.decidir(session, "tenant", "actor", "exp", "ignorar", "")
    assert exc.value.code == "BIB_IMPACTO_DECISION_INVALIDA"
    session.execute.assert_not_awaited()


def test_mutacion_sobrescribir_aprobado_esta_bloqueada_en_base():
    """Mutación decisiva: quitar OLD.estado='aprobado' haría fallar esta prueba."""
    migracion = (RAIZ / "alembic/versions/20261113_biblioteca_impactos.py").read_text()
    assert "OLD.estado='aprobado'" in migracion
    assert "NEW.contenido_markdown IS DISTINCT FROM OLD.contenido_markdown" in migracion
    assert "BIB_DOCUMENTO_APROBADO_INMUTABLE" in migracion


def test_servicio_no_actualiza_documentos_al_decidir():
    fuente = (RAIZ / "features/biblioteca/services/impacto.py").read_text()
    bloque = fuente.split("async def decidir", 1)[1].split("async def preparar_avisos", 1)[0]
    assert "UPDATE biblioteca_impactos_organizacion" in bloque
    assert "UPDATE biblioteca_documentos" not in bloque


def test_migracion_fuerza_rls_y_concede_columnas_minimas():
    migracion = (RAIZ / "alembic/versions/20261113_biblioteca_impactos.py").read_text()
    assert migracion.count("FORCE ROW LEVEL SECURITY") == 3
    assert "GRANT UPDATE(decision,motivo,decidente_id,decidido_en)" in migracion
    assert "GRANT UPDATE(estado,intentos,ultimo_intento_en,recibido_en,ultimo_error)" in migracion
