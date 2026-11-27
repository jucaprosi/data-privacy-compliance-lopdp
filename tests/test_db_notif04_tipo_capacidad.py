# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤notificaciones ¤arbitro
"""NOTIF-04: la migración amplía el CHECK de `avisos_plataforma.tipo`. Necesita PostgreSQL."""
import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from tests.test_norm05_privilegios_backend import propietario  # noqa: F401 - fixture de NORM-05

INSERTAR = text("INSERT INTO avisos_plataforma (id, usuario_id, tipo, referencia, titulo, texto) "
                "VALUES (:id, :u, :t, :r, 't', 'x')")


async def _usuario(s) -> str:
    u = f"u-n04m-{uuid.uuid4().hex[:10]}"
    await s.execute(text("INSERT INTO users (id, email, nombre) VALUES (:id, :e, 'Prueba')"),
                    {"id": u, "e": f"{u}@prueba.invalid"})
    return u


@pytest.mark.asyncio
async def test_db_el_tipo_nuevo_se_inserta_y_uno_desconocido_se_rechaza(propietario):  # noqa: F811
    """Mutación m4: no ampliar el CHECK da rojo al insertar el tipo nuevo."""
    async with propietario() as s:
        u = await _usuario(s)
        await s.execute(INSERTAR, {"id": str(uuid.uuid4()), "u": u, "t": "capacidad_editorial", "r": "c1"})
        await s.execute(INSERTAR, {"id": str(uuid.uuid4()), "u": u, "t": "version_por_revisar", "r": "v1"})
        with pytest.raises(IntegrityError):
            await s.execute(INSERTAR, {"id": str(uuid.uuid4()), "u": u, "t": "otro_tipo", "r": "x"})
        await s.rollback()
