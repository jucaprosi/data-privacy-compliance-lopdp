# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
"""OPS-07 · Observabilidad sin datos personales. ¤observabilidad"""
import io
import json
import logging
import uuid
from pathlib import Path

import json as _json
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.middleware.correlacion import CorrelacionMiddleware
from app_core.observabilidad import configurar_registro, registrar_error, request_id_actual

CEDULA = "1710034065"
CORREO = "persona@ejemplo.invalid"
TELEFONO = "0991234567"
RUC = "1710034065001"


def _registro():
    flujo = io.StringIO()
    return configurar_registro(flujo=flujo), flujo


def _lineas(flujo):
    return [json.loads(l) for l in flujo.getvalue().splitlines() if l.strip()]


def _app(registro):
    app = FastAPI()

    @app.get("/eco")
    def eco():
        logging.getLogger("evydentia").info("dentro de la petición")
        return {"ok": True}

    @app.get("/falla")
    def falla():
        raise RuntimeError(f"no se pudo contactar {TELEFONO}")

    app.add_middleware(CorrelacionMiddleware, registro=registro)
    return TestClient(app, raise_server_exceptions=False)


def test_registro_sin_datos_personales():
    registro, flujo = _registro()
    registro.error(f"falló cédula {CEDULA}, correo {CORREO} y RUC {RUC}")
    texto = flujo.getvalue()
    for dato in (CEDULA, CORREO, RUC):
        assert dato not in texto
    assert _lineas(flujo)[0]["severity"] == "ERROR"


def test_traza_saneada():
    registro, flujo = _registro()
    try:
        raise ValueError(f"teléfono {TELEFONO}")
    except ValueError as exc:
        registrar_error(registro, exc)
    linea = _lineas(flujo)[0]
    assert TELEFONO not in flujo.getvalue()
    assert "ValueError" in linea["message"]
    assert "ReportedErrorEvent" in linea["@type"]


def test_request_id_propagado():
    registro, flujo = _registro()
    cliente = _app(registro)
    r = cliente.get("/eco")
    rid = r.headers["X-Request-ID"]
    uuid.UUID(rid)
    lineas = _lineas(flujo)
    assert len(lineas) == 2 and all(l["request_id"] == rid for l in lineas)
    final = lineas[-1]
    assert final["status"] == 200 and final["method"] == "GET" and "duration_ms" in final

    propio = str(uuid.uuid4())
    assert cliente.get("/eco", headers={"X-Request-ID": propio}).headers["X-Request-ID"] == propio
    assert cliente.get("/eco", headers={"X-Request-ID": "no-uuid"}).headers["X-Request-ID"] != "no-uuid"


def test_error_no_controlado_500_saneado():
    registro, flujo = _registro()
    r = _app(registro).get("/falla")
    assert r.status_code == 500 and r.json()["request_id"] == r.headers["X-Request-ID"]
    assert TELEFONO not in flujo.getvalue()
    assert any("RuntimeError" in l["message"] for l in _lineas(flujo))


def test_path_sin_consulta():
    registro, flujo = _registro()
    _app(registro).get(f"/eco?correo={CORREO}")
    assert CORREO not in flujo.getvalue()
    assert all(l["path"] == "/eco" for l in _lineas(flujo))


def test_alertas_declaradas():
    ruta = Path(__file__).resolve().parents[1] / "governance/operaciones/monitoreo/alertas.json"
    politicas = _json.loads(ruta.read_text(encoding="utf-8"))["politicas"]
    esperadas = {"disponibilidad", "errores_5xx", "latencia_p95", "presupuesto", "gasto_ia"}
    assert esperadas <= set(politicas)
    assert all(politicas[p].get("condicion") for p in esperadas)
    assert politicas["presupuesto"]["umbrales_porcentaje"] == [50, 90, 100]


def test_main_app_correlacion_en_respuesta_y_contexto():
    import main

    flujo = io.StringIO()
    configurar_registro(flujo=flujo)
    try:
        cliente = TestClient(main.app, raise_server_exceptions=False)
        r_auto = cliente.get("/health")
        rid_auto = r_auto.headers.get("X-Request-ID")
        assert rid_auto is not None
        uuid.UUID(rid_auto)

        propio = str(uuid.uuid4())
        r_propio = cliente.get("/health", headers={"X-Request-ID": propio})
        assert r_propio.headers.get("X-Request-ID") == propio
        assert request_id_actual() is None

        lineas = _lineas(flujo)
        ids_registrados = [l.get("request_id") for l in lineas]
        assert rid_auto in ids_registrados
        assert propio in ids_registrados
        ultima = lineas[-1]
        assert ultima["request_id"] == propio
        assert ultima["method"] == "GET" and ultima["path"] == "/health"
    finally:
        configurar_registro()
