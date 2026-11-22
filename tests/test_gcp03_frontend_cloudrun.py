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
    assert runner.base == "alpine:3.21"

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


# --------------------------------------------------------------------------- GCP-03b
# El client id de Google entra al compilar y la imagen se etiqueta por commit
# (governance/especificaciones/GCP-03b.md). frontend/cloudbuild.yaml se lee como texto (R-ADPA).

CLOUDBUILD = FRONTEND / "cloudbuild.yaml"
FUENTES = FRONTEND / "src"
CLIENT_ID = "NEXT_PUBLIC_GOOGLE_CLIENT_ID"

# R2 · toda variable NEXT_PUBLIC_* que lee frontend/src está en uno de los tres grupos de §1
DE_COMPILACION = frozenset({CLIENT_ID})
DE_SERVIDOR = frozenset({"NEXT_PUBLIC_API_URL"})
SOLO_DESARROLLO = frozenset({
    "NEXT_PUBLIC_AUTH_MODE", "NEXT_PUBLIC_USER_ID", "NEXT_PUBLIC_USER_ROLE", "NEXT_PUBLIC_USER_EMAIL",
    "NEXT_PUBLIC_TENANT_ID", "NEXT_PUBLIC_OPERADOR_PLATAFORMA", "NEXT_PUBLIC_EVIDENCIA_FISICA",
})

_ITEM_LISTA = re.compile(r"^\s*-\s*'([^']*)'\s*$", re.MULTILINE)


def _etapas() -> list[_EtapaDocker]:
    return _parsear_dockerfile(DOCKERFILE.read_text(encoding="utf-8"))


def _nombre_arg(arg: str) -> str:
    return arg.split("=", 1)[0].strip()


def _cloudbuild() -> tuple[str, list[str], list[str]]:
    """(texto, argumentos del paso de docker, imágenes publicadas)."""
    texto = CLOUDBUILD.read_text(encoding="utf-8")
    pasos, _, resto = texto.partition("\nimages:")
    return texto, _ITEM_LISTA.findall(pasos), _ITEM_LISTA.findall(resto.split("\noptions:")[0])


def _build_args(argumentos: list[str]) -> dict[str, str]:
    pares = [argumentos[i + 1] for i, a in enumerate(argumentos[:-1]) if a == "--build-arg"]
    return dict(p.split("=", 1) if "=" in p else (p, "") for p in pares)


def test_client_id_entra_al_compilar():
    # R1 · m1: quitar el ARG da rojo
    builder = next(e for e in _etapas() if e.alias == "builder")
    orden = builder.instrucciones
    arg = [i for i, (v, a) in enumerate(orden) if v == "ARG" and _nombre_arg(a) == CLIENT_ID]
    env = [i for i, (v, a) in enumerate(orden)
           if v == "ENV" and _parsear_env(_EtapaDocker("", None, [(v, a)])).get(CLIENT_ID) == "${%s}" % CLIENT_ID]
    compila = [i for i, (v, a) in enumerate(orden) if v == "RUN" and "next build" in a]
    assert arg, f"la etapa builder no declara ARG {CLIENT_ID}"
    assert env, f"la etapa builder no fija ENV {CLIENT_ID}=${{{CLIENT_ID}}}"
    assert compila and arg[0] < env[0] < compila[0], "ARG y ENV del client id deben ir antes de compilar"


def test_cloudbuild_pasa_el_client_id():
    # R1 · m2: quitar el --build-arg da rojo
    _, argumentos, _ = _cloudbuild()
    valor = _build_args(argumentos).get(CLIENT_ID, "")
    assert re.fullmatch(r"\d+-[a-z0-9]+\.apps\.googleusercontent\.com", valor), valor


def test_variables_del_cliente_clasificadas():
    # R2 · m3: una variable nueva sin clasificar, o un ARG de una variable de desarrollo, da rojo
    grupos = DE_COMPILACION | DE_SERVIDOR | SOLO_DESARROLLO
    assert len(grupos) == len(DE_COMPILACION) + len(DE_SERVIDOR) + len(SOLO_DESARROLLO), "grupos solapados"
    usadas = {v for p in FUENTES.rglob("*") if p.suffix in {".ts", ".tsx", ".js", ".jsx", ".mjs"}
              for v in re.findall(r"NEXT_PUBLIC_[A-Z0-9_]+", p.read_text(encoding="utf-8"))}
    assert usadas, "no se encontró ninguna NEXT_PUBLIC_* en frontend/src"
    assert usadas <= grupos, f"variables sin clasificar en la prueba: {sorted(usadas - grupos)}"
    etapas = _etapas()
    builder = next(e for e in etapas if e.alias == "builder")
    args_builder = {_nombre_arg(a) for v, a in builder.instrucciones if v == "ARG"}
    horneadas = {_nombre_arg(a) for e in etapas for v, a in e.instrucciones if v == "ARG"}
    horneadas |= {k for e in etapas for k in _parsear_env(e)}
    _, argumentos, _ = _cloudbuild()
    build_args = set(_build_args(argumentos))
    for variable in DE_COMPILACION:
        assert variable in args_builder and variable in build_args, variable
    for variable in SOLO_DESARROLLO:  # una identidad de prueba nunca entra al bundle de producción
        assert variable not in horneadas and variable not in build_args, variable


def test_imagen_etiquetada_por_commit():
    # R3 · m4: volver a «v2» da rojo; sin _ETIQUETA, Cloud Build rechaza la construcción (MUST_MATCH)
    texto, argumentos, imagenes = _cloudbuild()
    etiqueta = argumentos[argumentos.index("-t") + 1]
    assert etiqueta.endswith("/web:${_ETIQUETA}"), etiqueta
    assert imagenes == [etiqueta]
    assert ":v2" not in texto
    assert re.search(r"^options:\s*\n\s+substitutionOption:\s*'?MUST_MATCH'?\s*$", texto, re.MULTILINE)
    assert "substitutions:" not in texto and "ALLOW_LOOSE" not in texto, "_ETIQUETA no lleva valor por defecto"
