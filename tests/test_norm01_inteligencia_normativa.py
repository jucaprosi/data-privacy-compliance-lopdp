# ¤inteligencia-normativa ¤vigilancia-spdp ¤arbitro
"""NORM-01: ingesta de la SPDP, SHA-256, deduplicación en tres capas y custodia del original.

Servidor HTTP simulado (`httpx.MockTransport`), almacén en memoria y una base PostgreSQL local; sin red real.
"""
import hashlib
import os

import httpx
import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app_core.pasillo import inteligencia_normativa as pasillo
from features.inteligencia_normativa import inteligencia_normativa_service as svc
from features.inteligencia_normativa.domain import errores
from features.inteligencia_normativa.services import deduplicacion, monitoreo
from features.inteligencia_normativa.services.conector_spdp import ConectorSpdp, extraer_enlaces

BASE = "https://spdp.example.invalid/"
NUMERO = "SPDP-SPD-2026-0005-R"
PDF_A = b"%PDF-1.7\ncontenido original A\n%%EOF"
PDF_B = b"%PDF-1.7\ncontenido corregido B\n%%EOF"


def _pagina(*enlaces: tuple[str, str]) -> bytes:
    cuerpo = "".join(f'<li><a href="{u}">{t}</a></li>' for u, t in enlaces)
    return f"<html><body><ul>{cuerpo}</ul></body></html>".encode()


class TrozosAsincronos(httpx.AsyncByteStream):
    def __init__(self, trozos):
        self.trozos = trozos

    async def __aiter__(self):
        for t in self.trozos:
            yield t


class Servidor:
    """Fuente simulada: `rutas` mapea ruta a (estado, cuerpo o trozos); registra cada petición."""

    def __init__(self, rutas: dict):
        self.rutas = rutas
        self.peticiones: list[str] = []
        self.agentes: list[str] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.peticiones.append(request.url.path)
        self.agentes.append(request.headers.get("user-agent", ""))
        estado, cuerpo = self.rutas.get(request.url.path, (404, b""))
        if isinstance(cuerpo, list):
            return httpx.Response(estado, stream=TrozosAsincronos(cuerpo))
        return httpx.Response(estado, content=cuerpo)


class AlmacenEnMemoria:
    def __init__(self):
        self.objetos: dict[str, bytes] = {}
        self.guardados: list[str] = []

    def guardar(self, clave: str, contenido: bytes, tipo: str) -> bool:
        self.guardados.append(clave)
        if clave in self.objetos:
            return False
        self.objetos[clave] = contenido
        return True


def _conector(servidor: Servidor, esperas: list | None = None, **kw) -> ConectorSpdp:
    async def dormir(segundos: float) -> None:
        if esperas is not None:
            esperas.append(segundos)

    cliente = httpx.AsyncClient(transport=httpx.MockTransport(servidor), headers={"User-Agent": "EvydentiaMonitorNormativo/1.0"})
    return ConectorSpdp(cliente, url_base=BASE, dormir=dormir, **kw)


def _rutas_con(*pdfs: tuple[str, bytes | list, str]) -> dict:
    """Sección de resoluciones con los PDF dados; las otras dos secciones, vacías."""
    rutas = {
        "/marco-normativo/": (200, _pagina()),
        "/consultas-absueltas/": (200, _pagina()),
        "/resoluciones/": (200, _pagina(*[(f"/archivos/{n}.pdf", titulo) for n, _, titulo in pdfs])),
    }
    for nombre, contenido, _ in pdfs:
        rutas[f"/archivos/{nombre}.pdf"] = (200, contenido)
    return rutas


@pytest_asyncio.fixture
async def fabrica(db_engine):
    f = async_sessionmaker(db_engine, expire_on_commit=False, class_=AsyncSession)

    async def limpiar():
        async with f() as s:
            await s.execute(text(
                "TRUNCATE normativa_versiones, normativa_resoluciones, normativa_monitoreo_logs CASCADE"
            ))
            await s.commit()

    await limpiar()
    yield f
    await limpiar()


async def _correr(fabrica, servidor, almacen=None, esperas=None, **kw):
    almacen = almacen if almacen is not None else AlmacenEnMemoria()
    resumen = await monitoreo.ejecutar(
        "manual", conector=_conector(servidor, esperas, **kw), almacen=almacen, sesion_factory=fabrica,
    )
    return resumen, almacen


async def _fila(fabrica, sql: str, **params):
    async with fabrica() as s:
        return (await s.execute(text(sql), params)).all()


# ---------------------------------------------------------------- escenarios de aceptación

@pytest.mark.asyncio
async def test_resolucion_nueva_con_hash_y_original(fabrica):
    servidor = Servidor(_rutas_con(("r5", PDF_A, f"Resolución {NUMERO}")))
    resumen, almacen = await _correr(fabrica, servidor)

    sha = hashlib.sha256(PDF_A).hexdigest()
    assert (resumen.estado, resumen.nuevos, resumen.versiones_nuevas, resumen.errores) == ("ok", 1, 0, 0)
    (fila,) = await _fila(fabrica, "SELECT numero_resolucion, anio_emision, estado, archivo_sha256, ruta_original, "
                                   "tamano_bytes, seccion_fuente FROM normativa_resoluciones")
    assert (fila.numero_resolucion, fila.anio_emision, fila.estado) == (NUMERO, 2026, "pendiente_revision")
    assert fila.archivo_sha256 == sha and fila.tamano_bytes == len(PDF_A) and fila.seccion_fuente == "resoluciones"
    assert almacen.objetos[fila.ruta_original] == PDF_A  # byte a byte
    assert fila.ruta_original == f"spdp/{sha}.pdf"


@pytest.mark.asyncio
async def test_rechaza_no_pdf(fabrica):
    servidor = Servidor(_rutas_con(("r5", b"<html>no soy un pdf</html>", f"Resolución {NUMERO}")))
    resumen, almacen = await _correr(fabrica, servidor)

    assert resumen.estado == "parcial" and resumen.errores == 1
    assert resumen.codigos_error == [errores.NORMATIVA_ARCHIVO_NO_PDF]
    assert almacen.objetos == {}
    assert await _fila(fabrica, "SELECT 1 FROM normativa_resoluciones") == []
    (log,) = await _fila(fabrica, "SELECT estado, errores, codigos_error FROM normativa_monitoreo_logs")
    assert (log.estado, log.errores, log.codigos_error) == ("parcial", 1, [errores.NORMATIVA_ARCHIVO_NO_PDF])


@pytest.mark.asyncio
async def test_misma_resolucion_otro_hash_crea_version(fabrica):
    almacen = AlmacenEnMemoria()
    await _correr(fabrica, Servidor(_rutas_con(("r5", PDF_A, f"Resolución {NUMERO}"))), almacen)
    resumen, _ = await _correr(fabrica, Servidor(_rutas_con(("r5", PDF_B, f"Resolución {NUMERO}"))), almacen)

    assert (resumen.nuevos, resumen.versiones_nuevas) == (0, 1)
    (res,) = await _fila(fabrica, "SELECT archivo_sha256, ruta_original FROM normativa_resoluciones")
    (ver,) = await _fila(fabrica, "SELECT archivo_sha256, ruta_original, motivo FROM normativa_versiones")
    assert res.archivo_sha256 == hashlib.sha256(PDF_A).hexdigest()  # la resolución no se sobrescribe
    assert ver.archivo_sha256 == hashlib.sha256(PDF_B).hexdigest() and ver.motivo == "cambio_en_fuente"
    assert almacen.objetos[res.ruta_original] == PDF_A and almacen.objetos[ver.ruta_original] == PDF_B


@pytest.mark.asyncio
async def test_detiene_ante_429(fabrica):
    rutas = _rutas_con(("r5", PDF_A, f"Resolución {NUMERO}"))
    rutas["/archivos/r5.pdf"] = (429, b"")
    servidor = Servidor(rutas)
    resumen, _ = await _correr(fabrica, servidor)

    assert resumen.estado == "fallida" and resumen.codigos_error == [errores.NORMATIVA_FUENTE_BLOQUEADA]
    assert servidor.peticiones == ["/resoluciones/", "/archivos/r5.pdf"]  # ni reintento ni otras secciones
    (log,) = await _fila(fabrica, "SELECT estado FROM normativa_monitoreo_logs")
    assert log.estado == "fallida"


@pytest.mark.asyncio
async def test_lopdp_app_solo_lectura(fabrica):
    async with fabrica() as s:
        await s.execute(text("SET LOCAL ROLE lopdp_app"))
        assert (await s.execute(text("SELECT count(*) FROM normativa_resoluciones"))).scalar() == 0
        for sentencia in (
            "DELETE FROM normativa_resoluciones",
            "DELETE FROM normativa_versiones",
            "DELETE FROM normativa_monitoreo_logs",
        ):
            with pytest.raises(DBAPIError, match="permission denied"):
                async with s.begin_nested():
                    await s.execute(text(sentencia))
        with pytest.raises(DBAPIError, match="permission denied"):
            async with s.begin_nested():
                await s.execute(text(
                    "INSERT INTO normativa_resoluciones (numero_resolucion, anio_emision, titulo, url_fuente, "
                    "seccion_fuente, archivo_sha256, ruta_original, tamano_bytes) "
                    "VALUES ('X-2026-0001', 2026, 't', 'u', 'resoluciones', :h, 'r', 1)"
                ), {"h": "a" * 64})
        await s.rollback()


# ---------------------------------------------------------------- reglas

@pytest.mark.asyncio
async def test_mismo_numero_y_mismo_hash_no_hace_nada(fabrica):
    servidor = Servidor(_rutas_con(("r5", PDF_A, f"Resolución {NUMERO}")))
    await _correr(fabrica, servidor)
    resumen, _ = await _correr(fabrica, servidor)
    assert (resumen.nuevos, resumen.versiones_nuevas, resumen.estado) == (0, 0, "ok")
    assert len(await _fila(fabrica, "SELECT 1 FROM normativa_resoluciones")) == 1
    assert await _fila(fabrica, "SELECT 1 FROM normativa_versiones") == []


@pytest.mark.asyncio
async def test_nada_se_asigna_vigente_sin_persona(fabrica):
    await _correr(fabrica, Servidor(_rutas_con(("r5", PDF_A, f"Resolución {NUMERO}"))))
    estados = await _fila(fabrica, "SELECT DISTINCT estado, revisada_por FROM normativa_resoluciones")
    assert [(e.estado, e.revisada_por) for e in estados] == [("pendiente_revision", None)]


@pytest.mark.asyncio
async def test_cada_corrida_queda_registrada(fabrica):
    resumen, _ = await _correr(fabrica, Servidor(_rutas_con(("r5", PDF_A, f"Resolución {NUMERO}"))))
    (log,) = await _fila(fabrica, "SELECT origen, documentos_vistos, nuevos, versiones_nuevas, errores, estado, fin "
                                  "FROM normativa_monitoreo_logs")
    assert (log.origen, log.documentos_vistos, log.nuevos, log.versiones_nuevas, log.errores, log.estado) == (
        "manual", 1, 1, 0, 0, "ok")
    assert log.fin is not None and resumen.id


@pytest.mark.asyncio
async def test_documento_sin_numero_reconocible_se_registra_como_error(fabrica):
    servidor = Servidor(_rutas_con(("circular", PDF_A, "Circular informativa")))
    resumen, almacen = await _correr(fabrica, servidor)
    assert resumen.codigos_error == [errores.NORMATIVA_NUMERO_NO_RECONOCIDO] and resumen.estado == "parcial"
    assert almacen.objetos == {}


@pytest.mark.asyncio
async def test_pagina_de_verificacion_detiene_la_corrida(fabrica):
    servidor = Servidor({"/resoluciones/": (200, b"<html>Verifying you are human. captcha</html>")})
    resumen, _ = await _correr(fabrica, servidor)
    assert resumen.estado == "fallida" and servidor.peticiones == ["/resoluciones/"]


@pytest.mark.asyncio
async def test_versiones_son_inmutables(fabrica):
    almacen = AlmacenEnMemoria()
    await _correr(fabrica, Servidor(_rutas_con(("r5", PDF_A, f"Resolución {NUMERO}"))), almacen)
    await _correr(fabrica, Servidor(_rutas_con(("r5", PDF_B, f"Resolución {NUMERO}"))), almacen)
    for sentencia in ("UPDATE normativa_versiones SET motivo = 'republicacion'", "DELETE FROM normativa_versiones"):
        async with fabrica() as s:
            with pytest.raises(DBAPIError, match="inmutable"):
                await s.execute(text(sentencia))


# ---------------------------------------------------------------- conector

@pytest.mark.asyncio
async def test_sha256_en_streaming_aunque_la_cabecera_llegue_partida():
    trozos = [b"%P", b"DF-1.7\nprimera ", b"parte ", b"segunda parte\n%%EOF"]
    servidor = Servidor({"/f.pdf": (200, trozos)})
    async with _conector(servidor) as c:
        d = await c.descargar(BASE + "f.pdf")
    esperado = b"".join(trozos)
    assert d.sha256 == hashlib.sha256(esperado).hexdigest() and d.contenido == esperado and d.tamano == len(esperado)


@pytest.mark.asyncio
async def test_espera_exponencial_y_tres_reintentos_ante_5xx():
    esperas: list[float] = []
    servidor = Servidor({"/f.pdf": (503, b"")})
    async with _conector(servidor, esperas, pausa=0.5) as c:
        with pytest.raises(errores.FuenteNoDisponible):
            await c.descargar(BASE + "f.pdf")
    assert len(servidor.peticiones) == 4  # una petición y tres reintentos
    esperas_de_reintento = [e for e in esperas if e != 0.5]  # 0,5 s es la pausa de cortesía de esta prueba
    assert esperas_de_reintento == [1.0, 2.0, 4.0]


@pytest.mark.asyncio
async def test_pausa_de_cortesia_entre_peticiones_y_user_agent_generico():
    esperas: list[float] = []
    servidor = Servidor(_rutas_con(("r5", PDF_A, f"Resolución {NUMERO}")))
    async with _conector(servidor, esperas) as c:
        await c.listar("resoluciones")
        await c.descargar(BASE + "archivos/r5.pdf")
    assert esperas == [2.0]  # ninguna pausa antes de la primera petición; 2 s entre la primera y la segunda
    assert set(servidor.agentes) == {"EvydentiaMonitorNormativo/1.0"}


@pytest.mark.asyncio
async def test_403_no_se_reintenta():
    servidor = Servidor({"/f.pdf": (403, b"")})
    async with _conector(servidor) as c:
        with pytest.raises(errores.FuenteBloqueada):
            await c.descargar(BASE + "f.pdf")
    assert servidor.peticiones == ["/f.pdf"]


def test_extraer_enlaces_sin_duplicados_y_con_url_absoluta():
    html = _pagina(("/a/x.pdf", "Uno <b>SPDP-SPD-2026-0001-R</b>"), ("/a/x.pdf", "repetido"), ("/a/y.PDF", "Dos"))
    enlaces = extraer_enlaces(html.decode(), BASE + "resoluciones/", "resoluciones")
    assert [e.url for e in enlaces] == [BASE + "a/x.pdf", BASE + "a/y.PDF"]
    assert enlaces[0].titulo == "Uno SPDP-SPD-2026-0001-R"


def test_sin_url_base_falla_cerrado(monkeypatch):
    monkeypatch.delenv("NORMATIVA_SPDP_URL_BASE", raising=False)
    with pytest.raises(errores.FuenteSinConfigurar):
        ConectorSpdp()._base()
    with pytest.raises(errores.FuenteSinConfigurar):
        ConectorSpdp(url_base="http://inseguro.example.invalid/")._base()


def test_almacen_de_produccion_falla_cerrado_con_error_neutro():
    with pytest.raises(errores.AlmacenNoDisponible) as e:
        monitoreo.almacen_por_defecto()
    assert e.value.codigo == errores.NORMATIVA_ALMACEN_NO_DISPONIBLE
    assert "google" not in e.value.detalle.lower() and "gs://" not in e.value.detalle


class AlmacenQueFalla:
    def guardar(self, clave: str, contenido: bytes, tipo: str) -> bool:
        raise errores.AlmacenNoDisponible("almacén normativo no disponible")


@pytest.mark.asyncio
async def test_si_el_almacen_falla_no_se_registra_nada(fabrica):
    servidor = Servidor(_rutas_con(("r5", PDF_A, f"Resolución {NUMERO}")))
    resumen, _ = await _correr(fabrica, servidor, AlmacenQueFalla())
    assert resumen.codigos_error == [errores.NORMATIVA_ALMACEN_NO_DISPONIBLE] and resumen.nuevos == 0
    assert await _fila(fabrica, "SELECT 1 FROM normativa_resoluciones") == []


@pytest.mark.asyncio
async def test_escritura_unica_y_deduplicacion_por_hash_en_el_almacen(fabrica):
    almacen = AlmacenEnMemoria()
    servidor = Servidor(_rutas_con(("r5", PDF_A, f"Resolución {NUMERO}")))
    await _correr(fabrica, servidor, almacen)
    await _correr(fabrica, servidor, almacen)
    assert len(almacen.objetos) == 1 and len(almacen.guardados) == 2  # el segundo intento no sobrescribe
    assert list(almacen.objetos.values()) == [PDF_A]


def test_el_numero_y_el_anio_se_reconocen_en_titulo_o_archivo():
    assert deduplicacion.reconocer_numero("sin número", "spdp-spd-2025-0028-r.pdf") == ("SPDP-SPD-2025-0028-R", 2025)
    with pytest.raises(errores.NumeroNoReconocido):
        deduplicacion.reconocer_numero("nada", "nada.pdf")


def test_decision_de_las_tres_capas():
    d = deduplicacion.Decision
    assert deduplicacion.decidir(None, "a") is d.NUEVA
    assert deduplicacion.decidir("a", "a") is d.NADA
    assert deduplicacion.decidir("a", "b") is d.VERSION


# ---------------------------------------------------------------- compuerta y pasillo

@pytest.mark.asyncio
async def test_compuerta_lista_y_detalla_con_versiones(fabrica):
    almacen = AlmacenEnMemoria()
    await _correr(fabrica, Servidor(_rutas_con(("r5", PDF_A, f"Resolución {NUMERO}"))), almacen)
    await _correr(fabrica, Servidor(_rutas_con(("r5", PDF_B, f"Resolución {NUMERO}"))), almacen)
    svc.inyectar_dependencias_de_prueba(sesion_factory=fabrica)
    try:
        lista = await pasillo.listar_resoluciones(pasillo.filtros(estado="pendiente_revision", anio=2026))
        assert [r.numero_resolucion for r in lista] == [NUMERO]
        assert await pasillo.listar_resoluciones(pasillo.filtros(estado="vigente")) == []
        detalle = await pasillo.obtener_resolucion(lista[0].id)
        assert detalle.tamano_bytes == len(PDF_A) and [v.motivo for v in detalle.versiones] == ["cambio_en_fuente"]
        with pytest.raises(pasillo.error_normativo()) as e:
            await pasillo.obtener_resolucion("00000000-0000-0000-0000-000000000000")
        assert e.value.codigo == errores.NORMATIVA_RESOLUCION_NO_ENCONTRADA
    finally:
        svc.inyectar_dependencias_de_prueba()


@pytest.mark.asyncio
async def test_compuerta_ejecuta_el_monitoreo(fabrica):
    servidor = Servidor(_rutas_con(("r5", PDF_A, f"Resolución {NUMERO}")))
    almacen = AlmacenEnMemoria()
    svc.inyectar_dependencias_de_prueba(conector=_conector(servidor), almacen=almacen, sesion_factory=fabrica)
    try:
        resumen = await pasillo.ejecutar_monitoreo("programado")
    finally:
        svc.inyectar_dependencias_de_prueba()
    assert resumen.origen == "programado" and resumen.nuevos == 1 and len(almacen.objetos) == 1
