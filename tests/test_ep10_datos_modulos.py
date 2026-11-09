# ¤entorno-pruebas ¤seguridad-tenant
"""EP-10: datos de ejemplo de los demás módulos, sembrados por sus compuertas.

Mutación documentada: agregar a modulos.py un `INSERT INTO rat_actividades ...` (o importar
`features.rat.services.rat_engine`) hace fallar test_1; la prueba del mutante lo fija.
"""
from __future__ import annotations

import ast
import hashlib
import inspect
import re
import uuid
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from scripts import sembrar_entorno_pruebas as siembra
from scripts.datos_sinteticos import modulos, organizaciones

RAIZ = Path(__file__).resolve().parents[1]
MODULOS = RAIZ / "scripts" / "datos_sinteticos" / "modulos.py"
IDS = tuple(o.id for o in organizaciones.ORGANIZACIONES)
SALAS = ("rat", "dpo_cockpit", "auditoria_capa")
ESCRITURA = re.compile(r"\b(?:INSERT\s+INTO|UPDATE\s+\w+\s+SET|DELETE\s+FROM)\b", re.IGNORECASE)
CORREO = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")


def _violaciones(codigo: str) -> list[str]:
    malas = [f"SQL de escritura: {m.group(0)}" for m in ESCRITURA.finditer(codigo)]
    for nodo in ast.walk(ast.parse(codigo)):
        nombres = []
        if isinstance(nodo, ast.ImportFrom) and nodo.module:
            nombres = [nodo.module] + [f"{nodo.module}.{a.name}" for a in nodo.names]
        elif isinstance(nodo, ast.Import):
            nombres = [a.name for a in nodo.names]
        for n in nombres:
            partes = n.split(".")
            if partes[0] == "features" and len(partes) >= 2:
                if len(partes) < 3 or partes[2] != f"{partes[1]}_service":
                    if not (len(partes) == 2 and isinstance(nodo, ast.ImportFrom)
                            and all(a.name == f"{partes[1]}_service" for a in nodo.names)):
                        malas.append(f"import fuera de la compuerta: {n}")
    return malas


# 1 -------------------------------------------------------------------------------------------------

def test_1_modulos_sin_sql_de_escritura_y_solo_por_compuertas():
    assert _violaciones(MODULOS.read_text(encoding="utf-8")) == []


def test_1_mutante_insert_directo_o_motor_interno_falla():
    assert _violaciones('x = "INSERT INTO rat_actividades (id) VALUES (1)"')
    assert _violaciones("from features.rat.services.rat_engine import crear_o_actualizar_actividad")
    assert _violaciones("from features.rat import rat_engine")
    assert not _violaciones("from features.rat import rat_service")


def test_las_salas_son_la_lista_cerrada_de_la_ficha():
    assert tuple(s.nombre for s in modulos.SALAS) == SALAS


# 2, 3 y 5 con PostgreSQL real -----------------------------------------------------------------------

async def _huella(session) -> tuple[dict, str]:
    consultas = {
        "rat": "SELECT id, tenant_id, codigo, nombre FROM rat_actividades WHERE tenant_id = ANY(:ids) "
               "AND id LIKE 'ep10-%' ORDER BY id",
        "dpo_cockpit": "SELECT id, tenant_id, asunto, sha256_hash FROM dpo_dictamenes "
                       "WHERE tenant_id = ANY(:ids) AND id LIKE 'ep10-%' ORDER BY id",
        "auditoria_capa": "SELECT id, tenant_id, descripcion_hallazgo FROM capa_tickets "
                          "WHERE tenant_id = ANY(:ids) AND id LIKE 'ep10-%' ORDER BY id",
    }
    conteos, h = {}, hashlib.sha256()
    for nombre, sql in consultas.items():
        filas = (await session.execute(text(sql), {"ids": list(IDS)})).all()
        conteos[nombre] = len(filas)
        h.update(repr((nombre, [tuple(f) for f in filas])).encode())
    return conteos, h.hexdigest()


@pytest.fixture
def notificaciones_vigiladas(monkeypatch):
    """Registra cualquier intento de enviar un correo durante la siembra."""
    from features.notificaciones.services import adaptadores, destinatarios_entorno

    enviados: list[str] = []

    async def _no_enviar(self, correo, *a, **k):
        enviados.append(type(self).__name__)
        raise AssertionError("La siembra intentó enviar un correo.")

    for modulo in (adaptadores, destinatarios_entorno):
        for _, clase in inspect.getmembers(modulo, inspect.isclass):
            if clase.__module__ == modulo.__name__ and "enviar_correo" in vars(clase):
                monkeypatch.setattr(clase, "enviar_correo", _no_enviar)
    monkeypatch.setenv("APP_ENV", "pruebas")
    return enviados


@pytest.mark.asyncio
async def test_2_3_4_5_siembra_por_compuerta_idempotente_y_sin_correos(
    db_engine, tmp_path, capsys, notificaciones_vigiladas,
):
    from features.auditoria_capa import auditoria_capa_service
    from features.dpo_cockpit import dpo_cockpit_service
    from features.rat import rat_service

    cuenta = f"t-{uuid.uuid4().hex[:8]}@example.invalid"
    cuentas = [organizaciones.CuentaDePrueba(cuenta, "coordinador", "ep-org-micro")]
    almacen = siembra.AlmacenLocal(tmp_path)
    fabrica = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    uid = organizaciones.id_de_usuario(cuenta)
    try:
        async with fabrica() as s:
            primera = await siembra.sembrar(s, cuentas, almacen)
        async with fabrica() as s:
            conteos_1, hash_1 = await _huella(s)
        async with fabrica() as s:
            segunda = await siembra.sembrar(s, cuentas, almacen)
        async with fabrica() as s:
            conteos_2, hash_2 = await _huella(s)

        # 3. Idempotencia: la segunda corrida no crea nada y deja los mismos conteos y hash.
        assert conteos_1 == conteos_2 and hash_1 == hash_2
        assert conteos_1 == {sala: len(IDS) for sala in SALAS}
        assert all(d["creados"] == 0 for d in segunda.values()), segunda
        assert all(primera[f"modulo_{sala}"]["creados"] + primera[f"modulo_{sala}"]["existentes"]
                   == len(IDS) for sala in SALAS)

        # 2. Por cada sala, la compuerta de lectura encuentra el registro sembrado.
        lectores = {
            "rat": lambda s, t: rat_service.listar_actividades_rat(s, t),
            "dpo_cockpit": lambda s, t: dpo_cockpit_service.listar_bitacora_dpo(s, t),
            "auditoria_capa": lambda s, t: auditoria_capa_service.listar_tickets_capa(s, t),
        }
        async with fabrica() as s:
            for org in organizaciones.ORGANIZACIONES:
                for sala, leer in lectores.items():
                    ids = {r.id for r in await leer(s, org.id)}
                    assert modulos.id_ejemplo(sala, org.id) in ids, (sala, org.id)

        # 4. Con APP_ENV=pruebas ningún correo sale durante la siembra.
        assert notificaciones_vigiladas == []

        # 5. Solo organizaciones FICTICIA y correos .invalid o @example.test.
        async with fabrica() as s:
            nombres = (await s.execute(
                text("SELECT DISTINCT t.razon_social FROM tenants t WHERE t.id = ANY(:ids)"),
                {"ids": list(IDS)})).scalars().all()
            correos = (await s.execute(
                text("SELECT DISTINCT u.email FROM users u JOIN user_tenant_roles r ON r.user_id = u.id "
                     "WHERE r.tenant_id = ANY(:ids)"), {"ids": list(IDS)})).scalars().all()
        assert nombres and all("FICTICIA" in n.upper() for n in nombres)
        assert correos and all(c.endswith(".invalid") or c.endswith("@example.test") for c in correos)

        print(siembra.formatear(primera) + siembra.formatear(segunda))
        assert not CORREO.search(capsys.readouterr().out)
    finally:
        async with fabrica() as s:
            await s.execute(text("DELETE FROM user_tenant_roles WHERE user_id = :u"), {"u": uid})
            await s.execute(text("DELETE FROM users WHERE id = :u"), {"u": uid})
            await s.commit()
