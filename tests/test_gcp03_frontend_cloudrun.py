"""GCP-03 · Next.js standalone en Cloud Run (INV_LOPDP_STANDALONE_FRONTEND_CONTAINER).

`¤cloud-run-perf` `¤frontend-ide` `¤seguridad`
"""
from __future__ import annotations

import json
import re
import shlex
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from tests._lector_yaml import leer_yaml

RAIZ = Path(__file__).resolve().parents[1]
FRONTEND = RAIZ / "frontend"
BASE_CONFIG = FRONTEND / "next.config.ts"
CONFIG = FRONTEND / "next.config.cloudrun.ts"
DOCKERFILE = FRONTEND / "Dockerfile.cloudrun"
SERVICIO = RAIZ / "governance/operaciones/cloudrun_frontend_service.yaml"

_EVALUADOR_CLOUDRUN_JS = r"""
const fs = require("fs");
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
  const headers = typeof cloudrun.headers === "function" ? await cloudrun.headers() : [];
  console.log(JSON.stringify({
    output: cloudrun.output ?? null,
    poweredByHeader: cloudrun.poweredByHeader ?? null,
    compress: cloudrun.compress ?? null,
    images: cloudrun.images ?? null,
    excludes: cloudrun.outputFileTracingExcludes ?? null,
    hasRewrites: typeof cloudrun.rewrites === "function",
    headers,
  }));
})();
"""

_PATRON_SECRETO = re.compile(r"(postgres(ql)?(\+\w+)?://|://[^/\s]*:[^@\s]+@|AIza|sk-|-----BEGIN)")


@dataclass
class _EtapaDocker:
    base: str
    alias: str | None
    instrucciones: list[tuple[str, str]] = field(default_factory=list)


def _unir_continuaciones(texto: str) -> list[str]:
    lineas_logicas: list[str] = []
    acumulada = ""
    for cruda in texto.splitlines():
        sin_espacios = cruda.strip()
        if not acumulada and (not sin_espacios or sin_espacios.startswith("#")):
            continue
        if cruda.rstrip().endswith("\\"):
            acumulada += cruda.rstrip()[:-1].strip() + " "
        else:
            acumulada += cruda.strip()
            if acumulada.strip():
                lineas_logicas.append(acumulada.strip())
            acumulada = ""
    if acumulada.strip():
        lineas_logicas.append(acumulada.strip())
    return lineas_logicas


def _parsear_dockerfile(texto: str) -> list[_EtapaDocker]:
    etapas: list[_EtapaDocker] = []
    for linea in _unir_continuaciones(texto):
        partes = linea.split(None, 1)
        verbo = partes[0].upper()
        arg = partes[1].strip() if len(partes) > 1 else ""
        if verbo == "FROM":
            tokens = arg.split()
            alias = tokens[2] if len(tokens) >= 3 and tokens[1].upper() == "AS" else None
            etapas.append(_EtapaDocker(tokens[0], alias))
        elif etapas:
            etapas[-1].instrucciones.append((verbo, arg))
    return etapas


def _parsear_env(etapa: _EtapaDocker) -> dict[str, str]:
    env: dict[str, str] = {}
    for verbo, arg in etapa.instrucciones:
        if verbo != "ENV":
            continue
        for token in shlex.split(arg):
            if "=" in token:
                clave, valor = token.split("=", 1)
                env[clave] = valor
    return env


def _recorrer_escalares(datos, ruta: str = ""):
    if isinstance(datos, dict):
        for clave, valor in datos.items():
            yield from _recorrer_escalares(valor, f"{ruta}.{clave}" if ruta else str(clave))
    elif isinstance(datos, list):
        for i, elemento in enumerate(datos):
            yield from _recorrer_escalares(elemento, f"{ruta}[{i}]")
    else:
        yield ruta, datos


def test_next_standalone_config_valida():
    res = subprocess.run(
        ["node", "-e", _EVALUADOR_CLOUDRUN_JS, str(FRONTEND), str(BASE_CONFIG), str(CONFIG)],
        cwd=RAIZ,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
    )
    assert res.returncode == 0, res.stderr + res.stdout
    cfg = json.loads(res.stdout)
    assert cfg["output"] == "standalone"
    assert cfg["poweredByHeader"] is False
    assert cfg["compress"] is True
    assert cfg["images"] == {"unoptimized": True}
    assert cfg["hasRewrites"] is False
    exclusiones = cfg["excludes"]["*"]
    assert any("sharp" in x for x in exclusiones)
    regla = next(r for r in cfg["headers"] if r["source"] == "/(.*)")
    cabeceras = {h["key"]: h["value"] for h in regla["headers"]}
    assert cabeceras["X-Frame-Options"] == "DENY"
    assert cabeceras["X-Content-Type-Options"] == "nosniff"


def test_dockerfile_multistage_non_root():
    etapas = _parsear_dockerfile(DOCKERFILE.read_text(encoding="utf-8"))
    assert len(etapas) >= 3
    runner = etapas[-1]
    assert runner.alias == "runner"
    compilacion = [e for e in etapas if e.alias != "runner"]
    assert compilacion and all(e.base.startswith("node:") for e in compilacion)
    assert runner.base == "alpine:3.20"

    runs_runner = [arg for verbo, arg in runner.instrucciones if verbo == "RUN"]
    assert any("apk add" in r and "nodejs" in r for r in runs_runner)
    assert any("adduser" in r and "nextjs" in r for r in runs_runner)

    usuarios = [arg for verbo, arg in runner.instrucciones if verbo == "USER"]
    assert usuarios and usuarios[-1] == "nextjs"

    expuestos = [arg for verbo, arg in runner.instrucciones if verbo == "EXPOSE"]
    assert "3000" in expuestos

    env_runner = _parsear_env(runner)
    assert env_runner.get("NODE_ENV") == "production"
    assert env_runner.get("PORT") == "3000"
    assert all(
        "APP_ENV" not in _parsear_env(etapa)
        and not any(verbo == "ARG" and arg.split("=", 1)[0].strip() == "APP_ENV" for verbo, arg in etapa.instrucciones)
        for etapa in etapas
    )

    copias_runner = [arg for verbo, arg in runner.instrucciones if verbo == "COPY"]
    assert any("--from=builder" in c and "--chown=nextjs:nodejs" in c and ".next/standalone" in c for c in copias_runner)
    assert all("node_modules" not in c for c in copias_runner)

    cmds_runner = [json.loads(arg) for verbo, arg in runner.instrucciones if verbo == "CMD"]
    assert cmds_runner and cmds_runner[-1] == ["node", "server.js"]

    builder = next(e for e in etapas if e.alias == "builder")
    runs_builder = [arg for verbo, arg in builder.instrucciones if verbo == "RUN"]
    assert any("next.config.cloudrun.ts" in r and "next build" in r for r in runs_builder)


def test_cloudrun_frontend_manifest_seguro():
    docs = leer_yaml(SERVICIO.read_text(encoding="utf-8"))
    servicios = [d for d in (docs if isinstance(docs, list) else [docs]) if isinstance(d, dict) and d.get("kind") == "Service"]
    assert len(servicios) >= 3
    for doc in servicios:
        for ruta, valor in _recorrer_escalares(doc):
            assert not _PATRON_SECRETO.search(str(valor)), f"posible secreto en {ruta}"
        plantilla = doc["spec"]["template"]
        notas = plantilla["metadata"]["annotations"]
        assert notas.get("run.googleapis.com/vpc-access-connector")
        contenedor = plantilla["spec"]["containers"][0]
        assert contenedor["image"] == "IMAGEN"
        assert [p["containerPort"] for p in contenedor["ports"]] == [3000]
        env_servicio = {e["name"]: e.get("value") for e in contenedor["env"]}
        entorno_etiqueta = doc["metadata"]["labels"]["entorno"]
        assert env_servicio.get("APP_ENV") == entorno_etiqueta
        for sonda in ("startupProbe", "livenessProbe"):
            http_get = contenedor[sonda]["httpGet"]
            assert http_get["port"] == 3000
            assert http_get["path"] == "/health"
