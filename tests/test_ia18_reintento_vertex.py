# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤gemini-vertex ¤arbitro
"""IA-18: plazo por petición desde el presupuesto, fallos con código y duración, reintento solo transitorio.

Cliente falso y reloj simulado: ninguna prueba abre la red ni duerme de verdad.
"""
import asyncio
import logging
import re
from pathlib import Path
from types import SimpleNamespace

import pytest
from google.genai import errors
from pydantic import BaseModel

from features.inferencia import inferencia_service as svc
from features.inferencia.domain.errores import InferenciaNoDisponible
from features.inferencia.domain.modelos_permitidos import MODELO_GENERACION
from features.inferencia.domain.prompts import PromptVersionado

RAIZ = Path(__file__).resolve().parent.parent
SECRETO_PROMPT = "TEXTO-SECRETO-DEL-PROMPT"
SECRETO_MENSAJE = "MENSAJE-SECRETO-DE-LA-EXCEPCION"
PROMPT = PromptVersionado(id="ia18.prueba", version=1, sistema="sistema", plantilla=SECRETO_PROMPT)


class Esquema(BaseModel):
    estado: str


class Reloj:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


def _apierror(code, status):
    return errors.APIError(code, {"error": {"status": status, "message": SECRETO_MENSAJE}})


class ModelosFalsos:
    """Cada paso es (segundos que dura, resultado o excepción). Anota el `timeout` de cada petición."""

    def __init__(self, reloj, pasos):
        self.reloj = reloj
        self.pasos = list(pasos)
        self.plazos = []

    async def generate_content(self, **kw):
        http = getattr(kw.get("config"), "http_options", None)
        self.plazos.append(getattr(http, "timeout", None))
        duracion, salida = self.pasos[len(self.plazos) - 1]
        self.reloj.t += duracion
        if isinstance(salida, Exception):
            raise salida
        return SimpleNamespace(text=salida, model_version="gemini-prueba-001")


@pytest.fixture
def reloj(monkeypatch):
    r = Reloj()
    monkeypatch.setattr(svc, "_reloj", r)
    return r


@pytest.fixture(autouse=True)
def entorno(monkeypatch):
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "proyecto-prueba")
    monkeypatch.setenv("VERTEX_LOCATION", "us")
    monkeypatch.setenv("VERTEX_LOCATION_EMBEDDING", "us-central1")
    monkeypatch.setattr(svc, "_cliente", None)

    async def consumir(org):
        return None

    svc.inyectar_consumidor_de_prueba(consumir)
    yield
    svc.inyectar_cliente_de_prueba(None)
    svc.inyectar_consumidor_de_prueba(None)


def _cliente(reloj, pasos):
    modelos = ModelosFalsos(reloj, pasos)
    svc.inyectar_cliente_de_prueba(SimpleNamespace(aio=SimpleNamespace(models=modelos)))
    return modelos


def _estructurado():
    return svc.generar_estructurado(
        "sistema", SECRETO_PROMPT, Esquema, modelo=MODELO_GENERACION, org_id="org"
    )


def _transcribir():
    return svc.transcribir_pdf(b"%PDF", PROMPT, modelo=MODELO_GENERACION)


def _sin_tope():
    return svc.generar_trazado_sin_tope(PROMPT, {}, Esquema, modelo=MODELO_GENERACION)


BUCLES = [("generar", _estructurado, '{"estado": "ok"}'), ("transcribir", _transcribir, "texto"),
          ("sin_tope", _sin_tope, '{"estado": "ok"}')]
IDS = [b[0] for b in BUCLES]


def _correr(bucle):
    return asyncio.run(bucle())


# ---------------------------------------------------------------- R1 rastro útil
@pytest.mark.parametrize("nombre,bucle,ok", BUCLES, ids=IDS)
def test_r1_el_warning_lleva_codigo_estado_intento_y_duracion(nombre, bucle, ok, reloj, caplog):
    """Mutación m1: registrar solo el tipo, o registrar el prompt, da rojo."""
    caplog.set_level(logging.DEBUG)
    _cliente(reloj, [(60.0, _apierror(503, "UNAVAILABLE")), (10.0, ok)])
    _correr(bucle)
    avisos = [r.getMessage() for r in caplog.records if r.levelno == logging.WARNING]
    assert len(avisos) == 1
    aviso = avisos[0]
    for esperado in ("APIError", "503", "UNAVAILABLE", "60.0"):
        assert esperado in aviso
    assert re.search(r"\b1\b", aviso.replace("60.0", ""))
    assert SECRETO_PROMPT not in caplog.text and SECRETO_MENSAJE not in caplog.text


@pytest.mark.parametrize("nombre,bucle,ok", BUCLES, ids=IDS)
def test_r1_cada_intento_fallido_registra_el_suyo(nombre, bucle, ok, reloj, caplog):
    caplog.set_level(logging.DEBUG)
    _cliente(reloj, [(20.0, _apierror(503, "UNAVAILABLE")), (30.5, _apierror(504, "DEADLINE_EXCEEDED"))])
    with pytest.raises(InferenciaNoDisponible):
        _correr(bucle)
    texto = "\n".join(r.getMessage() for r in caplog.records if r.levelno == logging.WARNING)
    assert "503" in texto and "504" in texto and "20.0" in texto and "30.5" in texto
    assert SECRETO_PROMPT not in caplog.text and SECRETO_MENSAJE not in caplog.text


# ---------------------------------------------------------------- R2 reintento transitorio
@pytest.mark.parametrize("nombre,bucle,ok", BUCLES, ids=IDS)
@pytest.mark.parametrize("codigo,estado", [(429, "RESOURCE_EXHAUSTED"), (503, "UNAVAILABLE"), (504, "DEADLINE_EXCEEDED")])
def test_r2_un_codigo_transitorio_reintenta_una_vez(nombre, bucle, ok, codigo, estado, reloj):
    modelos = _cliente(reloj, [(5.0, _apierror(codigo, estado)), (5.0, ok)])
    _correr(bucle)
    assert len(modelos.plazos) == 2


@pytest.mark.parametrize("nombre,bucle,ok", BUCLES, ids=IDS)
@pytest.mark.parametrize(
    "fallo",
    [_apierror(400, "INVALID_ARGUMENT"), _apierror(500, "INTERNAL"), ValueError("otro"), RuntimeError("x")],
    ids=["400", "500", "ValueError", "RuntimeError"],
)
def test_r2_otros_fallos_no_reintentan(nombre, bucle, ok, fallo, reloj):
    """Mutación m2: reintentar ante cualquier excepción da rojo."""
    modelos = _cliente(reloj, [(1.0, fallo), (1.0, ok)])
    with pytest.raises(InferenciaNoDisponible):
        _correr(bucle)
    assert len(modelos.plazos) == 1


@pytest.mark.parametrize("nombre,bucle,ok", BUCLES, ids=IDS)
@pytest.mark.parametrize("vacia", ["", None])
def test_r2_respuesta_vacia_falla_a_la_primera(nombre, bucle, ok, vacia, reloj):
    modelos = _cliente(reloj, [(1.0, vacia), (1.0, ok)])
    with pytest.raises(InferenciaNoDisponible):
        _correr(bucle)
    assert len(modelos.plazos) == 1


def test_r2_esquema_invalido_falla_a_la_primera(reloj):
    modelos = _cliente(reloj, [(1.0, '{"otro": 1}'), (1.0, '{"estado": "ok"}')])
    with pytest.raises(InferenciaNoDisponible):
        _correr(_estructurado)
    assert len(modelos.plazos) == 1


def test_r2_como_maximo_un_reintento(reloj):
    modelos = _cliente(reloj, [(1.0, _apierror(503, "UNAVAILABLE"))] * 3)
    with pytest.raises(InferenciaNoDisponible):
        _correr(_estructurado)
    assert len(modelos.plazos) == 2


# ---------------------------------------------------------------- R3 plazo total
@pytest.mark.parametrize("nombre,bucle,ok", BUCLES, ids=IDS)
def test_r3_sin_tiempo_no_se_reintenta_y_lo_dice(nombre, bucle, ok, reloj, caplog):
    """Mutación m3: reintentar sin mirar el plazo da rojo. Mutación m4: un bucle sin la regla da rojo."""
    caplog.set_level(logging.DEBUG)
    # Primer intento de 90 s: quedan 50 s, menos que lo que duró.
    modelos = _cliente(reloj, [(90.0, _apierror(504, "DEADLINE_EXCEEDED")), (1.0, ok)])
    with pytest.raises(InferenciaNoDisponible):
        _correr(bucle)
    assert len(modelos.plazos) == 1
    assert "reintento omitido por plazo" in caplog.text


@pytest.mark.parametrize("nombre,bucle,ok", BUCLES, ids=IDS)
def test_r3_con_tiempo_suficiente_reintenta(nombre, bucle, ok, reloj, caplog):
    caplog.set_level(logging.DEBUG)
    modelos = _cliente(reloj, [(60.0, _apierror(504, "DEADLINE_EXCEEDED")), (1.0, ok)])
    _correr(bucle)
    assert len(modelos.plazos) == 2
    assert "reintento omitido por plazo" not in caplog.text


def test_r3_el_presupuesto_es_140_s():
    assert svc.PLAZO_TOTAL_S == 140


# ---------------------------------------------------------------- R5 plazo por llamada
@pytest.mark.parametrize("nombre,bucle,ok", BUCLES, ids=IDS)
def test_r5_cada_peticion_lleva_lo_que_queda_menos_el_margen(nombre, bucle, ok, reloj):
    """Mutación m5: un `TIMEOUT_MS` fijo de 60 s, o cualquier constante menor que el presupuesto, da rojo."""
    modelos = _cliente(reloj, [(60.0, _apierror(504, "DEADLINE_EXCEEDED")), (1.0, ok)])
    _correr(bucle)
    primero, segundo = modelos.plazos
    assert primero >= 130_000
    assert primero == (svc.PLAZO_TOTAL_S - 5) * 1000
    assert segundo == (svc.PLAZO_TOTAL_S - 60 - 5) * 1000


def test_r5_la_configuracion_aplica_el_plazo_por_peticion():
    from features.inferencia.services import cliente_vertex

    fuente = (RAIZ / "features/inferencia/services/cliente_vertex.py").read_text(encoding="utf-8")
    assert "TIMEOUT_MS" not in fuente
    anotado = []

    class Modelos:
        async def generate_content(self, **kw):
            anotado.append(kw["config"].http_options.timeout)
            return SimpleNamespace(text="x")

    cliente = SimpleNamespace(aio=SimpleNamespace(models=Modelos()))
    asyncio.run(cliente_vertex.generar_json(cliente, "m", "s", "u", Esquema, plazo_ms=123_000))
    asyncio.run(cliente_vertex.transcribir(cliente, "m", "s", "i", b"pdf", plazo_ms=124_000))
    assert anotado == [123_000, 124_000]


# ---------------------------------------------------------------- R7 Cloud Run
def test_r7_el_despliegue_del_backend_tiene_plazo_suficiente():
    """Mutación m6: `--timeout 60s` da rojo. Lee el workflow como texto."""
    texto = (RAIZ / ".github/workflows/deploy-gcp.yml").read_text(encoding="utf-8")
    plazos = [int(m) for m in re.findall(r"--timeout\s+(\d+)s", texto)]
    assert plazos, "el workflow debe fijar --timeout"
    assert min(plazos) >= svc.PLAZO_TOTAL_S + 10
