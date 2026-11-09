# ¤arbitro
# ¤¤qa-engineer
"""Árbitro BIB-120: la fecha de negocio de la Biblioteca es la de America/Guayaquil.

El reloj se inyecta con `hoy_negocio(ahora=...)` y con el parámetro `ahora` de las consultas, sin parchear
`datetime` ni depender de la zona del sistema. El instante elegido, 2031-03-15 04:30 UTC, es el
2031-03-14 a las 23:30 en Guayaquil: un día distinto en cada zona y lejos del reloj real.

La persistencia reutiliza el mundo sintético de BIB-107 (PostgreSQL local, `lopdp_app`, transacción que se
revierte) y se ejecuta con la sesión de PostgreSQL en UTC, como el CI, y en America/Guayaquil.

Mutaciones (governance/tareas/BIB-120.md), todas en rojo:
- M1: quitar `AT TIME ZONE` en `documentos_consulta.py`: falla `desde`/`hasta` con la sesión en UTC.
- M2: `:hoy = date.today()`: fallan «vencido» y «por vencer», porque ignoran el reloj inyectado.
- M3: `ZONA_NEGOCIO` en UTC: fallan `test_hoy_negocio_*` y «vencido».
"""
from datetime import date, datetime, timedelta, timezone
import pytest
from app_core.zona_negocio import ZONA_NEGOCIO, ZONA_NEGOCIO_NOMBRE, hoy_negocio
from features.biblioteca.services import documentos_consulta as consulta
from tests.test_bib_107_documentos import _crear, mundo  # noqa: F401  (fixture sintética de BIB-107)

AHORA = datetime(2031, 3, 15, 4, 30, tzinfo=timezone.utc)
DIA_LOCAL = date(2031, 3, 14)


# ¤arbitro
def test_hoy_negocio_a_las_23_30_de_guayaquil_es_el_dia_local_y_no_el_de_utc():
    assert ZONA_NEGOCIO_NOMBRE == "America/Guayaquil"
    assert ZONA_NEGOCIO.utcoffset(None) == timedelta(hours=-5)
    assert hoy_negocio(AHORA) == DIA_LOCAL
    assert hoy_negocio(AHORA.replace(tzinfo=None)) == DIA_LOCAL  # sin zona se toma como UTC
    assert hoy_negocio(datetime(2031, 3, 14, 23, 30, tzinfo=ZONA_NEGOCIO)) == DIA_LOCAL
    assert hoy_negocio(datetime(2031, 3, 15, 5, 0, tzinfo=timezone.utc)) == date(2031, 3, 15)


# ¤arbitro
@pytest.mark.asyncio
@pytest.mark.parametrize("zona_sesion", ["UTC", "America/Guayaquil"])
async def test_db_documento_de_las_23_30_cae_en_el_dia_local(mundo, zona_sesion):  # noqa: F811
    actor = mundo.ids["redactor_a"]
    nuevo, hoy_vence, ayer_vencio = [await _crear(mundo, mundo.ta, actor) for _ in range(3)]
    await mundo.como_propietario("UPDATE biblioteca_documentos SET creado_en=:c WHERE id=:id", c=AHORA, id=nuevo.id)
    for doc, revision in ((hoy_vence, DIA_LOCAL), (ayer_vencio, DIA_LOCAL - timedelta(days=1))):
        await mundo.como_propietario(
            "UPDATE biblioteca_documentos SET estado='aprobado', aprobado_por=:u, aprobado_en=:c, "
            "proxima_revision=:p, creado_en=:c - interval '10 days' WHERE id=:id",
            u=mundo.ids["editor"], c=AHORA, p=revision, id=doc.id)
    await mundo.como_propietario(f"SET LOCAL TIME ZONE '{zona_sesion}'")

    del_dia = await consulta.listar_documentos(mundo.sesion, mundo.ta, actor, desde=DIA_LOCAL, hasta=DIA_LOCAL, ahora=AHORA)
    assert [d.id for d in del_dia] == [nuevo.id]
    assert await consulta.listar_documentos(mundo.sesion, mundo.ta, actor, desde=DIA_LOCAL + timedelta(days=1),
                                            ahora=AHORA) == []

    vencidos = await consulta.listar_documentos(mundo.sesion, mundo.ta, actor, estado="vencido", ahora=AHORA)
    assert [d.id for d in vencidos] == [ayer_vencio.id]
    assert (await consulta.obtener_documento(mundo.sesion, mundo.ta, actor, hoy_vence.id, ahora=AHORA)).estado == "aprobado"

    p = await consulta.pendientes(mundo.sesion, mundo.ta, actor, ahora=AHORA)
    assert (p.borrador, p.por_vencer, p.vencidos) == (1, 1, 1)
