# ¤seguridad
"""Cabeceras HTTP de seguridad del backend (vercel.json) y coherencia con el frontend.

El backend es una API JSON, pero FastAPI también sirve /docs y /redoc, que cargan recursos de
un CDN: por eso aquí no hay una CSP completa (una política restrictiva los rompería) y solo se
exige `frame-ancestors 'none'` contra el clickjacking. La política de contenido completa vive
en el frontend (next.config.ts), en modo informe.

Estas pruebas leen la configuración declarada. Que el despliegue real las emita lo verifica el
propietario con `curl -I` sobre el dominio (no verificado aquí).
"""
import json
import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
VERCEL = RAIZ / "vercel.json"
NEXT_CONFIG = RAIZ / "frontend" / "next.config.ts"

ESPERADAS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Content-Security-Policy": "frame-ancestors 'none'",
}


def _cabeceras_backend() -> dict[str, str]:
    config = json.loads(VERCEL.read_text(encoding="utf-8"))
    reglas = [r for r in config.get("headers", []) if r.get("source") == "/(.*)"]
    assert len(reglas) == 1, "vercel.json debe declarar una única regla de cabeceras para /(.*)"
    return {h["key"]: h["value"] for h in reglas[0]["headers"]}


def _cabeceras_frontend() -> dict[str, str]:
    """Pares clave/valor literales de CABECERAS_SEGURIDAD en next.config.ts."""
    texto = NEXT_CONFIG.read_text(encoding="utf-8")
    bloque = texto.split("const CABECERAS_SEGURIDAD = [", 1)[1].split("];", 1)[0]
    pares = re.findall(r'\{\s*key:\s*"([^"]+)",\s*value:\s*(?:"([^"]*)"|([A-Z_]+))\s*\}', bloque)
    return {clave: (literal or f"<{constante}>") for clave, literal, constante in pares}


def test_vercel_json_sigue_valido_y_conserva_la_duracion_maxima():
    """Añadir cabeceras no puede pisar maxDuration, que RM-13 necesita para la generación en línea."""
    config = json.loads(VERCEL.read_text(encoding="utf-8"))
    assert config["functions"]["api/index.py"]["maxDuration"] == 300


@pytest.mark.parametrize("clave,valor", sorted(ESPERADAS.items()))
def test_backend_declara_la_cabecera_con_su_valor(clave, valor):
    assert _cabeceras_backend().get(clave) == valor


def test_backend_fuerza_https_por_un_ano_como_minimo():
    hsts = _cabeceras_backend()["Strict-Transport-Security"]
    segundos = int(re.search(r"max-age=(\d+)", hsts).group(1))
    assert segundos >= 31_536_000
    assert "includeSubDomains" in hsts


def test_backend_no_filtra_el_referer_ni_concede_permisos_del_navegador():
    cabeceras = _cabeceras_backend()
    assert cabeceras["Referrer-Policy"] in {"no-referrer", "same-origin", "strict-origin"}
    permisos = cabeceras["Permissions-Policy"]
    for recurso in ("camera", "microphone", "geolocation"):
        assert f"{recurso}=()" in permisos


def test_backend_no_lleva_una_csp_completa_que_rompa_la_documentacion():
    """/docs y /redoc cargan recursos de un CDN: una default-src restrictiva los dejaría en blanco."""
    csp = _cabeceras_backend()["Content-Security-Policy"]
    assert "default-src" not in csp and "script-src" not in csp


def test_el_frontend_declara_todas_las_cabeceras_del_backend_con_el_mismo_valor():
    """Las dos configuraciones no se desalinean: lo que protege a la API protege también a la interfaz."""
    backend, frontend = _cabeceras_backend(), _cabeceras_frontend()
    # El Referrer-Policy difiere a propósito: la API no necesita enviar referencia; la interfaz sí
    # conserva el origen para sus propios enlaces.
    comunes = set(backend) - {"Referrer-Policy"}
    faltan = sorted(comunes - set(frontend))
    assert not faltan, f"El frontend no declara: {faltan}"
    distintas = {k: (backend[k], frontend[k]) for k in comunes if backend[k] != frontend[k]}
    assert not distintas, f"Valores distintos entre vercel.json y next.config.ts: {distintas}"


def test_el_frontend_empieza_con_la_csp_en_modo_informe_y_no_obligatoria():
    """La política completa no bloquea nada hasta que el propietario la pase a obligatoria."""
    frontend = _cabeceras_frontend()
    assert "Content-Security-Policy-Report-Only" in frontend
    assert frontend["Content-Security-Policy"] == "frame-ancestors 'none'", (
        "La única CSP obligatoria debe ser frame-ancestors: una política completa en modo obligatorio puede romper la interfaz"
    )
    texto = NEXT_CONFIG.read_text(encoding="utf-8")
    informe = texto.split("const CSP_INFORME = [", 1)[1].split("].join", 1)[0]
    assert "default-src 'self'" in informe and "object-src 'none'" in informe
    assert "script-src 'self'" in informe and "unsafe-eval" not in informe


def test_el_frontend_no_relaja_script_src_con_unsafe_inline():
    """Cualquier concesión a unsafe-inline en scripts debe quedar decidida y documentada, no colarse."""
    texto = NEXT_CONFIG.read_text(encoding="utf-8")
    informe = texto.split("const CSP_INFORME = [", 1)[1].split("].join", 1)[0]
    linea_script = next(l for l in informe.splitlines() if "script-src" in l)
    assert "unsafe-inline" not in linea_script
