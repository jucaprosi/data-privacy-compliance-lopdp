# ¤seguridad
"""Cabeceras HTTP de seguridad en Next.js (`frontend/next.config.ts`) y presupuesto de tiempo en Cloud Run.

El frontend sirve la interfaz y define la política completa de cabeceras de seguridad en
`frontend/next.config.ts` (y la hereda en `frontend/next.config.cloudrun.ts`). La CSP completa
empieza en modo informe (`Content-Security-Policy-Report-Only`) y solo `frame-ancestors 'none'` es
obligatoria para evitar clickjacking sin romper recursos de la interfaz.

El tiempo máximo de la generación en línea de la hoja de ruta (RM-13 / RM-18) se declara en el
manifiesto de Cloud Run (`governance/operaciones/cloudrun_service.yaml`).
"""
import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
NEXT_CONFIG = RAIZ / "frontend" / "next.config.ts"
NEXT_CLOUDRUN = RAIZ / "frontend" / "next.config.cloudrun.ts"
CLOUDRUN_BACKEND = RAIZ / "governance" / "operaciones" / "cloudrun_service.yaml"

ESPERADAS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Content-Security-Policy": "frame-ancestors 'none'",
}


def _cabeceras_frontend() -> dict[str, str]:
    """Pares clave/valor literales de CABECERAS_SEGURIDAD en next.config.ts."""
    texto = NEXT_CONFIG.read_text(encoding="utf-8")
    bloque = texto.split("const CABECERAS_SEGURIDAD = [", 1)[1].split("];", 1)[0]
    pares = re.findall(r'\{\s*key:\s*"([^"]+)",\s*value:\s*(?:"([^"]*)"|([A-Z_]+))\s*\}', bloque)
    return {clave: (literal or f"<{constante}>") for clave, literal, constante in pares}


def test_cloudrun_backend_conserva_tiempo_maximo_de_generacion():
    """RM-13: el servicio Cloud Run del backend mantiene timeoutSeconds >= 300 para generación en línea."""
    manifiesto = CLOUDRUN_BACKEND.read_text(encoding="utf-8")
    coincidencia = re.search(r"^\s*timeoutSeconds:\s*(\d+)\s*$", manifiesto, flags=re.M)
    assert coincidencia, "cloudrun_service.yaml debe declarar timeoutSeconds"
    assert int(coincidencia.group(1)) >= 300


@pytest.mark.parametrize("clave,valor", sorted(ESPERADAS.items()))
def test_frontend_declara_la_cabecera_con_su_valor(clave, valor):
    assert _cabeceras_frontend().get(clave) == valor


def test_frontend_fuerza_https_por_un_ano_como_minimo():
    hsts = _cabeceras_frontend()["Strict-Transport-Security"]
    segundos = int(re.search(r"max-age=(\d+)", hsts).group(1))
    assert segundos >= 31_536_000
    assert "includeSubDomains" in hsts


def test_frontend_no_filtra_el_referer_ni_concede_permisos_del_navegador():
    cabeceras = _cabeceras_frontend()
    assert cabeceras["Referrer-Policy"] in {"no-referrer", "same-origin", "strict-origin", "strict-origin-when-cross-origin"}
    permisos = cabeceras["Permissions-Policy"]
    for recurso in ("camera", "microphone", "geolocation"):
        assert f"{recurso}=()" in permisos


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
    assert "https://storage.googleapis.com" in informe


def test_el_frontend_no_relaja_script_src_con_unsafe_inline():
    """Cualquier concesión a unsafe-inline en scripts debe quedar decidida y documentada, no colarse."""
    texto = NEXT_CONFIG.read_text(encoding="utf-8")
    informe = texto.split("const CSP_INFORME = [", 1)[1].split("].join", 1)[0]
    linea_script = next(l for l in informe.splitlines() if "script-src" in l)
    assert "unsafe-inline" not in linea_script


def test_next_config_cloudrun_hereda_cabeceras():
    texto = NEXT_CLOUDRUN.read_text(encoding="utf-8")
    assert 'from "./next.config"' in texto and "...base" in texto
