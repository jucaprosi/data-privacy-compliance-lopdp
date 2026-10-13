# -*- coding: utf-8 -*-
# ¤arbitro
# ¤ci-cd
"""Pruebas del script de verificación de despliegue (OPS-03).

Usa un servidor simulado (mock / servidor HTTP local) para comprobar:
1. Despliegue operativo completo: devuelve 0.
2. /api/v1/health con código != 200: devuelve 1 con el motivo.
3. /api/v1/health con status != 'OPERATIONAL' (ej. DEGRADED): devuelve 1 con el motivo.
4. /api/v1/health con routers fallidos: devuelve 1 con el motivo.
5. /openapi.json al que le faltan rutas esperadas: devuelve 1 con el motivo.
6. Error de red / host inalcanzable: devuelve 1 con el motivo.
7. Comportamiento CLI: argumentos y códigos de salida 0 y 1.
"""
from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import pytest

from scripts import verificar_despliegue


class MockDeployHandler(BaseHTTPRequestHandler):
    health_status_code = 200
    health_body = {
        "status": "OPERATIONAL",
        "platform": "JUBYS Plataforma LOPDP 360",
        "version": "1.0.0",
        "routers": {
            "total": 16,
            "cargados": [
                "diagnostico", "rat", "riesgos_mtge", "dpo_cockpit",
                "auditoria_capa", "evidencias", "regulacion_rag", "arco",
                "rag_router", "terceros_router", "ai_copilot", "niif18",
                "preanalisis", "implementation_assistant", "roadmaps",
                "organizacion",
            ],
            "fallidos": [],
        },
        "salas_adpa": [
            "diagnostico", "rat", "riesgos_mtge", "dpo_cockpit",
            "auditoria_capa", "evidencias", "regulacion_rag", "ai_copilot",
        ],
    }

    openapi_status_code = 200
    openapi_body = {
        "paths": {ruta: {} for ruta in verificar_despliegue.RUTAS_ESPERADAS_BASE}
    }

    def do_GET(self):
        if self.path in ("/api/v1/health", "/health"):
            data = json.dumps(self.health_body).encode("utf-8")
            self.send_response(self.health_status_code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        elif self.path == "/openapi.json":
            data = json.dumps(self.openapi_body).encode("utf-8")
            self.send_response(self.openapi_status_code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Silenciar logs del servidor durante los tests
        pass


@pytest.fixture
def mock_server():
    server = HTTPServer(("127.0.0.1", 0), MockDeployHandler)
    port = server.server_port
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    # Reset default behavior
    MockDeployHandler.health_status_code = 200
    MockDeployHandler.health_body = {
        "status": "OPERATIONAL",
        "routers": {
            "total": 16,
            "cargados": ["r1", "r2"],
            "fallidos": [],
        },
    }
    MockDeployHandler.openapi_status_code = 200
    MockDeployHandler.openapi_body = {
        "paths": {ruta: {} for ruta in verificar_despliegue.RUTAS_ESPERADAS_BASE}
    }

    yield f"http://127.0.0.1:{port}"
    server.shutdown()
    server.server_close()


def test_despliegue_operativo_exitoso(mock_server):
    """Un despliegue con 200 OPERATIONAL y todas las rutas devuelve 0."""
    MockDeployHandler.health_status_code = 200
    MockDeployHandler.health_body = {
        "status": "OPERATIONAL",
        "routers": {
            "total": 2,
            "cargados": ["diagnostico", "organizacion"],
            "fallidos": [],
        },
    }
    MockDeployHandler.openapi_status_code = 200
    MockDeployHandler.openapi_body = {
        "paths": {r: {} for r in verificar_despliegue.RUTAS_ESPERADAS_BASE}
    }

    exito, motivos = verificar_despliegue.ejecutar_verificacion(mock_server)
    assert exito is True
    assert len(motivos) == 1
    assert "exitosamente" in motivos[0]

    ret = verificar_despliegue.main([mock_server])
    assert ret == 0


def test_falla_si_health_no_responde_200(mock_server):
    """Si /api/v1/health responde 503 u otro código, devuelve 1 y detalla el motivo."""
    MockDeployHandler.health_status_code = 503
    MockDeployHandler.health_body = {"status": "DEGRADED", "routers": {"fallidos": ["x"]}}

    exito, motivos = verificar_despliegue.ejecutar_verificacion(mock_server)
    assert exito is False
    assert any("503" in m for m in motivos)

    ret = verificar_despliegue.main([mock_server])
    assert ret == 1


def test_falla_si_status_no_es_operational(mock_server):
    """Si /api/v1/health responde 200 pero status no es OPERATIONAL, devuelve 1."""
    MockDeployHandler.health_status_code = 200
    MockDeployHandler.health_body = {
        "status": "STARTUP_ERROR",
        "routers": {"total": 1, "cargados": ["a"], "fallidos": []},
    }

    exito, motivos = verificar_despliegue.ejecutar_verificacion(mock_server)
    assert exito is False
    assert any("OPERATIONAL" in m for m in motivos)


def test_falla_si_hay_routers_fallidos(mock_server):
    """Si hay routers en 'fallidos', devuelve 1 indicando los routers que fallaron."""
    MockDeployHandler.health_status_code = 200
    MockDeployHandler.health_body = {
        "status": "OPERATIONAL",
        "routers": {
            "total": 2,
            "cargados": ["diagnostico"],
            "fallidos": [{"router": "roadmaps", "error": "ModuleNotFoundError"}],
        },
    }

    exito, motivos = verificar_despliegue.ejecutar_verificacion(mock_server)
    assert exito is False
    assert any("roadmaps" in m for m in motivos)


def test_falla_si_faltan_rutas_en_openapi(mock_server):
    """Si /openapi.json omite rutas requeridas, devuelve 1 listando las faltantes."""
    MockDeployHandler.health_status_code = 200
    MockDeployHandler.health_body = {
        "status": "OPERATIONAL",
        "routers": {"total": 1, "cargados": ["diagnostico"], "fallidos": []},
    }
    MockDeployHandler.openapi_status_code = 200
    # Omitir /api/v1/organizacion/me/roles
    MockDeployHandler.openapi_body = {
        "paths": {
            r: {}
            for r in verificar_despliegue.RUTAS_ESPERADAS_BASE
            if r != "/api/v1/organizacion/me/roles"
        }
    }

    exito, motivos = verificar_despliegue.ejecutar_verificacion(mock_server)
    assert exito is False
    assert any("/api/v1/organizacion/me/roles" in m for m in motivos)

    ret = verificar_despliegue.main([mock_server])
    assert ret == 1


def test_falla_ante_servidor_inalcanzable():
    """Un puerto sin servicio o dominio inexistente devuelve 1 con el error de red."""
    # Usar un puerto inalcanzable en localhost
    url_invalida = "http://127.0.0.1:59999"
    exito, motivos = verificar_despliegue.ejecutar_verificacion(url_invalida, timeout=0.5)
    assert exito is False
    assert any("No se pudo conectar" in m for m in motivos)

    ret = verificar_despliegue.main([url_invalida, "--timeout", "0.5"])
    assert ret == 1


def test_normalizar_url():
    """Valida que normalizar_url_base agrega el protocolo https por defecto si falta."""
    assert verificar_despliegue.normalizar_url_base("ejemplo.com") == "https://ejemplo.com"
    assert verificar_despliegue.normalizar_url_base("http://ejemplo.com/") == "http://ejemplo.com"
    assert verificar_despliegue.normalizar_url_base("https://ejemplo.com/api/") == "https://ejemplo.com/api"
