# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤seguridad
"""Cabeceras HTTP de seguridad en Next.js (`frontend/next.config.ts`) y presupuesto de tiempo en Cloud Run.

Carga y ejecuta la configuración real de `frontend/next.config.ts` y `frontend/next.config.cloudrun.ts`
con Node + TypeScript para evaluar `headers()`, y analiza el manifiesto YAML de Cloud Run mediante
`tests._lector_yaml`.
"""
from __future__ import annotations

import functools
import json
import re
import subprocess
from pathlib import Path

import pytest

from tests._lector_yaml import leer_yaml

RAIZ = Path(__file__).resolve().parent.parent
FRONTEND = RAIZ / "frontend"
NEXT_CONFIG = FRONTEND / "next.config.ts"
NEXT_CLOUDRUN = FRONTEND / "next.config.cloudrun.ts"
CLOUDRUN_BACKEND = RAIZ / "governance" / "operaciones" / "cloudrun_service.yaml"

ESPERADAS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Content-Security-Policy": "frame-ancestors 'none'",
}

_EVALUADOR_JS = r"""
const fs = require("fs");
const path = require("path");
const frontendDir = process.argv[1];
const basePath = process.argv[2];
const cloudrunPath = process.argv[3];
const ts = require(require.resolve("typescript", { paths: [frontendDir] }));

function compilar(ruta, mocks) {
  const codigo = fs.readFileSync(ruta, "utf8");
  const salida = ts.transpileModule(codigo, {
    compilerOptions: {
      module: ts.ModuleKind.CommonJS,
      target: ts.ScriptTarget.ES2022,
      esModuleInterop: true,
    },
  }).outputText;
  const modulo = { exports: {} };
  const req = (id) => (id in mocks ? mocks[id] : require(id));
  new Function("exports", "require", "module", salida)(modulo.exports, req, modulo);
  return modulo.exports.default || modulo.exports;
}

(async () => {
  const base = compilar(basePath, {});
  const cloudrun = compilar(cloudrunPath, { "./next.config": { __esModule: true, default: base } });
  const resumen = async (cfg) => ({
    output: cfg.output ?? null,
    poweredByHeader: cfg.poweredByHeader ?? null,
    compress: cfg.compress ?? null,
    hasRewrites: typeof cfg.rewrites === "function",
    headers: typeof cfg.headers === "function" ? await cfg.headers() : [],
  });
  console.log(JSON.stringify({
    base: await resumen(base),
    cloudrun: await resumen(cloudrun),
  }));
})();
"""


@functools.lru_cache(maxsize=1)
def _evaluar_configs() -> dict:
    res = subprocess.run(
        ["node", "-e", _EVALUADOR_JS, str(FRONTEND), str(NEXT_CONFIG), str(NEXT_CLOUDRUN)],
        cwd=RAIZ,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
    )
    assert res.returncode == 0, res.stderr + res.stdout
    return json.loads(res.stdout)


def _cabeceras_frontend(perfil: str = "base") -> dict[str, str]:
    reglas = _evaluar_configs()[perfil]["headers"]
    regla = next(r for r in reglas if r["source"] == "/(.*)")
    return {h["key"]: h["value"] for h in regla["headers"]}


def _directivas_csp(valor: str) -> dict[str, list[str]]:
    directivas: dict[str, list[str]] = {}
    for parte in valor.split(";"):
        tokens = parte.strip().split()
        if tokens:
            directivas[tokens[0]] = tokens[1:]
    return directivas


def test_cloudrun_backend_conserva_tiempo_maximo_de_generacion():
    """RM-13: el servicio Cloud Run del backend mantiene timeoutSeconds >= 300 para generación en línea."""
    manifiesto = leer_yaml(CLOUDRUN_BACKEND.read_text(encoding="utf-8"))
    timeout = manifiesto["spec"]["template"]["spec"]["timeoutSeconds"]
    assert int(timeout) >= 300


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
    assert cabeceras["Referrer-Policy"] in {
        "no-referrer",
        "same-origin",
        "strict-origin",
        "strict-origin-when-cross-origin",
    }
    permisos = cabeceras["Permissions-Policy"]
    for recurso in ("camera", "microphone", "geolocation"):
        assert f"{recurso}=()" in permisos


def test_el_frontend_empieza_con_la_csp_en_modo_informe_y_no_obligatoria():
    """La política completa no bloquea nada hasta que el propietario la pase a obligatoria."""
    frontend = _cabeceras_frontend()
    assert frontend["Content-Security-Policy"] == "frame-ancestors 'none'", (
        "La única CSP obligatoria debe ser frame-ancestors: una política completa en modo obligatorio puede romper la interfaz"
    )
    directivas = _directivas_csp(frontend["Content-Security-Policy-Report-Only"])
    assert directivas["default-src"] == ["'self'"]
    assert directivas["object-src"] == ["'none'"]
    assert "'self'" in directivas["script-src"] and "'unsafe-eval'" not in directivas["script-src"]
    assert "https://storage.googleapis.com" in directivas["connect-src"]


def test_el_frontend_no_relaja_script_src_con_unsafe_inline():
    """Cualquier concesión a unsafe-inline en scripts debe quedar decidida y documentada, no colarse."""
    directivas = _directivas_csp(_cabeceras_frontend()["Content-Security-Policy-Report-Only"])
    assert "'unsafe-inline'" not in directivas["script-src"]
    assert "'unsafe-eval'" not in directivas["script-src"]


def test_next_config_cloudrun_hereda_cabeceras():
    base = _cabeceras_frontend("base")
    cloudrun = _cabeceras_frontend("cloudrun")
    assert cloudrun == base
    assert _evaluar_configs()["cloudrun"]["hasRewrites"] is False
