# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤vigilancia-spdp ¤inteligencia-normativa ¤seguridad ¤arbitro
"""NORM-04: el monitoreo de la SPDP descarga de verdad.

Almacén de escritura solo en el Job, lector de solo lectura en el backend y punto de entrada del Job.
Sin red ni credenciales: `AlmacenGcs` se sustituye por un doble en memoria. Los casos de la corrida única
(R4) y de la fuente sin configurar (R5) abren la base: PostgreSQL local o el CI.

Mutaciones (governance/especificaciones/NORM-04.md §5), una a una con la suite corrida y el archivo restaurado:
- m1 `almacen_normativo.py` toma `GCP_STORAGE_BUCKET` -> falla `test_el_almacen_escribe_en_el_bucket_normativo`.
- m2 acepta `K_SERVICE` para escribir -> falla `test_el_backend_no_puede_escribir`.
- m3 `_lector()` vuelve al lector cerrado -> falla `test_el_backend_sirve_el_original_con_la_misma_huella`.
- m4 el punto de entrada sale siempre con 0 -> falla `test_codigo_de_salida_segun_el_estado_de_la_corrida`.
- m5 quita la comprobación de la corrida en curso -> falla `test_no_abre_otra_corrida_si_hay_una_en_curso`.
- m6 imprime `DATABASE_URL` -> falla `test_la_salida_no_contiene_la_url_de_la_base`.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app_core.storage.gcs import ObjetoYaExiste
from features.inteligencia_normativa import inteligencia_normativa_service as svc
from features.inteligencia_normativa import trabajo_monitoreo
from features.inteligencia_normativa.domain import errores
from features.inteligencia_normativa.schemas import ResumenCorrida
from features.inteligencia_normativa.services import almacen_normativo, monitoreo, revision

BUCKET_NORMATIVO = "evydentia-corpus-normativo"
BUCKET_GENERAL = "evydentia-documentos"
CLAVE = "spdp/" + "ab" * 32 + ".pdf"
PDF = b"%PDF-1.7\noriginal de la resolucion\n%%EOF"

ENTORNO_JOB = {"CLOUD_RUN_JOB": "evydentia-monitoreo-normativo", "GCP_STORAGE_BUCKET_NORMATIVO": BUCKET_NORMATIVO,
               "GCP_STORAGE_BUCKET": BUCKET_GENERAL}
ENTORNO_BACKEND = {"K_SERVICE": "evydentia-backend", "GCP_STORAGE_BUCKET_NORMATIVO": BUCKET_NORMATIVO,
                   "GCP_STORAGE_BUCKET": BUCKET_GENERAL}


class AlmacenEnMemoria:
    """Doble de `AlmacenGcs`: escritura única y lectura con tope, por bucket."""

    def __init__(self, bucket: str, objetos: dict | None = None):
        self.bucket = bucket
        self.objetos = objetos if objetos is not None else {}

    def subir(self, clave, contenido, tipo_mime):
        if clave in self.objetos:
            raise ObjetoYaExiste(clave)
        self.objetos[clave] = contenido

    def descargar(self, clave, maximo_bytes):
        return self.objetos.get(clave)


class Fabrica:
    """Sustituye la creación del cliente real: registra los buckets pedidos y comparte los objetos."""

    def __init__(self):
        self.buckets: list[str] = []
        self.objetos: dict = {}

    def __call__(self, bucket: str) -> AlmacenEnMemoria:
        self.buckets.append(bucket)
        return AlmacenEnMemoria(bucket, self.objetos)


# --- R1 · almacén de escritura, solo en el Job -------------------------------------------------------------------


def test_el_almacen_escribe_en_el_bucket_normativo():
    fabrica = Fabrica()
    almacen = almacen_normativo.almacen_normativo_por_defecto(ENTORNO_JOB, crear=fabrica)
    assert fabrica.buckets == [BUCKET_NORMATIVO]
    assert almacen.guardar(CLAVE, PDF, "application/pdf") is True
    assert almacen.guardar(CLAVE, PDF, "application/pdf") is False
    assert fabrica.objetos[CLAVE] == PDF


@pytest.mark.parametrize("entorno", [
    {"K_SERVICE": "evydentia-backend", "GCP_STORAGE_BUCKET_NORMATIVO": BUCKET_NORMATIVO},
    {"CLOUD_RUN_JOB": "evydentia-monitoreo-normativo"},
    {"CLOUD_RUN_JOB": "evydentia-monitoreo-normativo", "GCP_STORAGE_BUCKET_NORMATIVO": "  "},
    {"CLOUD_RUN_JOB": "evydentia-monitoreo-normativo", "GCP_STORAGE_BUCKET": BUCKET_GENERAL},
    {},
])
def test_el_backend_no_puede_escribir(entorno):
    fabrica = Fabrica()
    with pytest.raises(errores.AlmacenNoDisponible):
        almacen_normativo.almacen_normativo_por_defecto(entorno, crear=fabrica)
    assert fabrica.buckets == []  # falla cerrado sin crear el cliente


def test_monitoreo_devuelve_el_almacen_normativo(monkeypatch):
    fabrica = Fabrica()
    monkeypatch.setattr(almacen_normativo, "_crear_gcs", fabrica)
    for clave, valor in ENTORNO_JOB.items():
        monkeypatch.setenv(clave, valor)
    monkeypatch.delenv("K_SERVICE", raising=False)
    assert monitoreo.almacen_por_defecto().guardar(CLAVE, PDF, "application/pdf") is True
    assert fabrica.buckets == [BUCKET_NORMATIVO]


# --- R2 · lector, en el backend ----------------------------------------------------------------------------------


def test_el_backend_sirve_el_original_con_la_misma_huella(monkeypatch):
    fabrica = Fabrica()
    monkeypatch.setattr(almacen_normativo, "_crear_gcs", fabrica)
    almacen_normativo.almacen_normativo_por_defecto(ENTORNO_JOB, crear=fabrica).guardar(CLAVE, PDF, "application/pdf")
    monkeypatch.delenv("CLOUD_RUN_JOB", raising=False)
    for clave, valor in ENTORNO_BACKEND.items():
        monkeypatch.setenv(clave, valor)
    lector = svc._lector()
    assert not isinstance(lector, revision.LectorOriginalesCerrado)
    contenido = revision.leer_original(lector, CLAVE)
    assert hashlib.sha256(contenido).hexdigest() == hashlib.sha256(PDF).hexdigest()
    assert fabrica.buckets[-1] == BUCKET_NORMATIVO


def test_el_lector_falla_cerrado_fuera_del_backend(monkeypatch):
    fabrica = Fabrica()
    monkeypatch.setattr(almacen_normativo, "_crear_gcs", fabrica)
    for entorno in ({}, {"CLOUD_RUN_JOB": "x", "GCP_STORAGE_BUCKET_NORMATIVO": BUCKET_NORMATIVO},
                    {"K_SERVICE": "x"}):
        lector = almacen_normativo.lector_normativo_por_defecto(entorno, crear=fabrica)
        assert isinstance(lector, revision.LectorOriginalesCerrado)
    assert fabrica.buckets == []


def test_el_lector_no_tiene_permiso_de_escritura():
    lector = almacen_normativo.lector_normativo_por_defecto(ENTORNO_BACKEND, crear=Fabrica())
    assert not hasattr(lector, "guardar") and not hasattr(lector, "subir")


# --- R3 · punto de entrada del Job -------------------------------------------------------------------------------


def _resumen(estado: str) -> ResumenCorrida:
    ahora = datetime.now(timezone.utc)
    return ResumenCorrida(id="00000000-0000-0000-0000-000000000001", origen="programado", estado=estado, inicio=ahora,
                          fin=ahora, documentos_vistos=3, nuevos=1, versiones_nuevas=0, errores=0, codigos_error=[])


async def _libre():
    return False


@pytest.mark.asyncio
@pytest.mark.parametrize("estado,codigo", [("ok", 0), ("parcial", 0), ("fallida", 1)])
async def test_codigo_de_salida_segun_el_estado_de_la_corrida(estado, codigo):
    origenes = []

    async def disparar(origen):
        origenes.append(origen)
        return _resumen(estado)

    assert await trabajo_monitoreo.correr(disparar=disparar, en_curso=_libre, salida=lambda _: None) == codigo
    assert origenes == ["programado"]


@pytest.mark.asyncio
async def test_un_error_inesperado_sale_con_1_sin_detalle(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://usuario:clave-secreta@host/base")
    impreso: list[str] = []

    async def disparar(origen):
        raise RuntimeError("fallo con postgresql+asyncpg://usuario:clave-secreta@host/base")

    assert await trabajo_monitoreo.correr(disparar=disparar, en_curso=_libre, salida=impreso.append) == 1
    assert "clave-secreta" not in " ".join(impreso)


@pytest.mark.asyncio
async def test_la_salida_no_contiene_la_url_de_la_base(monkeypatch):
    url = "postgresql+asyncpg://usuario:clave-secreta@host/base"
    monkeypatch.setenv("DATABASE_URL", url)
    impreso: list[str] = []

    async def disparar(origen):
        return _resumen("ok")

    await trabajo_monitoreo.correr(disparar=disparar, en_curso=_libre, salida=impreso.append)
    assert impreso
    assert url not in " ".join(impreso) and "clave-secreta" not in " ".join(impreso)


# --- R4 y R5 · con la base ---------------------------------------------------------------------------------------


@pytest_asyncio.fixture
async def fabrica_db(db_engine):
    f = async_sessionmaker(db_engine, expire_on_commit=False, class_=AsyncSession)

    async def limpiar():
        async with f() as s:
            await s.execute(text(
                "TRUNCATE normativa_versiones, normativa_resoluciones, normativa_monitoreo_logs CASCADE"))
            await s.commit()

    await limpiar()
    yield f
    await limpiar()


async def _sembrar_corrida(fabrica, hace: timedelta, *, cerrada: bool) -> None:
    inicio = datetime.now(timezone.utc) - hace
    async with fabrica() as s:
        await monitoreo._como_normativa(s)
        await s.execute(
            text("INSERT INTO normativa_monitoreo_logs (inicio, fin, origen, estado) VALUES (:i, :f, 'manual', 'fallida')"),
            {"i": inicio, "f": inicio + timedelta(seconds=30) if cerrada else None})
        await s.commit()


@pytest.mark.asyncio
async def test_no_abre_otra_corrida_si_hay_una_en_curso(fabrica_db):
    await _sembrar_corrida(fabrica_db, timedelta(minutes=5), cerrada=False)
    llamadas = []

    async def disparar(origen):
        llamadas.append(origen)
        return _resumen("ok")

    codigo = await trabajo_monitoreo.correr(disparar=disparar, sesion_factory=fabrica_db, salida=lambda _: None)
    assert codigo == 0 and llamadas == []


@pytest.mark.asyncio
@pytest.mark.parametrize("hace,cerrada", [(timedelta(minutes=45), False), (timedelta(minutes=5), True)])
async def test_una_corrida_vieja_o_cerrada_no_bloquea(fabrica_db, hace, cerrada):
    await _sembrar_corrida(fabrica_db, hace, cerrada=cerrada)
    llamadas = []

    async def disparar(origen):
        llamadas.append(origen)
        return _resumen("ok")

    await trabajo_monitoreo.correr(disparar=disparar, sesion_factory=fabrica_db, salida=lambda _: None)
    assert llamadas == ["programado"]


@pytest.mark.asyncio
async def test_sin_la_url_de_la_spdp_la_corrida_queda_fallida(fabrica_db, monkeypatch):
    monkeypatch.delenv("NORMATIVA_SPDP_URL_BASE", raising=False)
    from features.inteligencia_normativa.services.conector_spdp import ConectorSpdp

    resumen = await monitoreo.ejecutar("programado", conector=ConectorSpdp(), almacen=AlmacenEnMemoria(BUCKET_NORMATIVO),
                                       sesion_factory=fabrica_db)
    assert resumen.estado == "fallida"
    assert resumen.codigos_error == [errores.NORMATIVA_FUENTE_SIN_CONFIGURAR]
