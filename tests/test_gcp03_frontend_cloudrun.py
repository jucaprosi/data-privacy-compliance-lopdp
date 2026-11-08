"""GCP-03 · Next.js standalone en Cloud Run (INV_LOPDP_STANDALONE_FRONTEND_CONTAINER).

`¤cloud-run-perf` `¤frontend-ide` `¤seguridad`
"""

import re
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[1]
CONFIG = RAIZ / "frontend/next.config.cloudrun.ts"
DOCKERFILE = RAIZ / "frontend/Dockerfile.cloudrun"
SERVICIO = RAIZ / "governance/operaciones/cloudrun_frontend_service.yaml"


def _servicios():
    """Documentos del manifiesto (sin PyYAML: el repositorio no lo trae)."""
    texto = SERVICIO.read_text(encoding="utf-8")
    return [d for d in re.split(r"^---\s*$", texto, flags=re.M) if "kind: Service" in d]


def test_next_standalone_config_valida():
    texto = CONFIG.read_text(encoding="utf-8")
    assert re.search(r'output:\s*"standalone"', texto)
    assert re.search(r"poweredByHeader:\s*false", texto)
    assert re.search(r"compress:\s*true", texto)
    # Extiende la base: conserva cabeceras de seguridad y proxy sin tocar Vercel (R3).
    assert 'from "./next.config"' in texto and "...base" in texto
    assert (RAIZ / "frontend/vercel.json").exists()


def test_dockerfile_multistage_non_root():
    texto = DOCKERFILE.read_text(encoding="utf-8")
    etapas = re.findall(r"^FROM\s+(\S+)", texto, flags=re.M)
    assert len(etapas) >= 3 and all(e.startswith("node:") for e in etapas)
    assert "adduser --system --uid 1001" in texto and re.search(r"^USER nextjs$", texto, flags=re.M)
    assert ".next/standalone" in texto and re.search(r'^CMD \[.node., .server\.js.\]$', texto, flags=re.M)  # sin el literal que marca «usa Node»
    ejecucion = texto.split("AS runner", 1)[1]
    assert "node_modules" not in ejecucion  # solo las dependencias que trae el standalone
    assert "next.config.cloudrun.ts" in texto


def test_cloudrun_frontend_manifest_seguro():
    servicios = _servicios()
    assert servicios
    patron_secreto = re.compile(r"(postgres(ql)?(\+\w+)?://|://[^/\s]*:[^@\s]+@|AIza|sk-|-----BEGIN)")
    assert not patron_secreto.search(SERVICIO.read_text(encoding="utf-8"))
    for svc in servicios:
        assert re.search(r"containerPort:\s*3000(?![0-9])", svc)
        assert len(re.findall(r"(?<![A-Za-z])port:\s*3000(?![0-9])", svc)) >= 2  # startupProbe y livenessProbe
        assert "startupProbe:" in svc and "livenessProbe:" in svc
        assert "run.googleapis.com/vpc-access-connector:" in svc
