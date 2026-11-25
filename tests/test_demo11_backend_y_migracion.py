# -*- coding: utf-8 -*-
# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤demo ¤arbitro
"""DEMO-11: backend y migración de la demo, con su job, su secreto y la membresía del rol.

Solo lee archivos del repositorio (sin red, sin base de datos, sin `import yaml`):
`governance/operaciones/entornos/demo/{job_migracion,secretos,cloud_sql,cloudrun_backend,job_purga}.yaml`
y `governance/operaciones/DEMO_COMERCIAL.md` §5 y §6.

Mutaciones (governance/especificaciones/DEMO-11.md §5), aplicadas una a una con la suite corrida y el
archivo restaurado:
- m1 `job_migracion.yaml` con `value: <url literal>` en `DATABASE_URL`
  -> falla `test_job_migracion_cumple_r1`.
- m2 `secretos.yaml`: `DATABASE_URL` también leído por la cuenta del backend
  -> falla `test_secreto_database_url_solo_lo_lee_el_job`.
- m3 `cloud_sql.yaml` sin `miembro_de: [lopdp_app]` -> falla `test_membresia_del_rol_de_la_aplicacion`.
- m4 §6.2 con la copia previa después de `jobs execute` -> falla `test_seccion_6_completa_y_en_orden`.
- m5 `evydentia-backend-demo` como paquete en cualquiera de los tres
  -> falla `test_un_solo_paquete_de_imagen_del_backend`.
"""
from __future__ import annotations

import re
from pathlib import Path

from tests._lector_yaml import leer_yaml

RAIZ = Path(__file__).resolve().parents[1]
DEMO = RAIZ / "governance" / "operaciones" / "entornos" / "demo"
JOB = DEMO / "job_migracion.yaml"
SECRETOS = DEMO / "secretos.yaml"
CLOUD_SQL = DEMO / "cloud_sql.yaml"
BACKEND = DEMO / "cloudrun_backend.yaml"
PURGA = DEMO / "job_purga.yaml"
GUIA = RAIZ / "governance" / "operaciones" / "DEMO_COMERCIAL.md"

PAQUETE = "us-central1-docker.pkg.dev/evydentia-demo/evydentia-demo-containers/backend"
INSTANCIA = "evydentia-demo:us-central1:evydentia-demo-db"


def _leer(ruta: Path) -> str:
    return ruta.read_bytes().decode("utf-8").replace("\r\n", "\n")


def _seccion(numero: str) -> str:
    texto = _leer(GUIA)
    inicio = re.search(rf"^## {numero}\. ", texto, re.M)
    assert inicio, f"DEMO_COMERCIAL.md no tiene la §{numero}"
    resto = texto[inicio.start():]
    fin = re.search(r"^## ", resto[3:], re.M)
    return resto[: fin.start() + 3] if fin else resto


def _contenedor_job(ruta: Path) -> tuple[dict, dict]:
    spec = leer_yaml(_leer(ruta))["spec"]["template"]["spec"]["template"]["spec"]
    return spec, spec["containers"][0]


def _contenedor_backend() -> dict:
    docs = leer_yaml(_leer(BACKEND))
    return docs[0]["spec"]["template"]["spec"]["containers"][0]


def test_job_migracion_cumple_r1():
    doc = leer_yaml(_leer(JOB))
    assert doc["metadata"]["name"] == "migrar-demo"
    assert doc["metadata"]["project"] == "evydentia-demo"
    assert doc["metadata"]["region"] == "us-central1"
    assert doc["spec"]["template"]["spec"]["taskCount"] == 1
    anot = doc["spec"]["template"]["metadata"]["annotations"]
    assert anot["run.googleapis.com/cloudsql-instances"] == INSTANCIA
    spec, cont = _contenedor_job(JOB)
    assert spec["maxRetries"] == 0
    assert spec["timeoutSeconds"] == 600
    assert cont["image"] == PAQUETE
    assert " ".join(cont["command"] + cont["args"]) == "alembic upgrade heads"
    cuenta = spec["serviceAccountName"]
    assert cuenta != _leer_cuenta_backend()
    assert cuenta != _contenedor_job(PURGA)[0]["serviceAccountName"]
    env = {e["name"]: e for e in cont["env"]}
    assert env["APP_ENV"]["value"] == "demo"
    url = env["DATABASE_URL"]
    assert "value" not in url, "DATABASE_URL nunca va literal"
    assert url["valueFrom"]["secretKeyRef"]["name"] == "DATABASE_URL"


def _leer_cuenta_backend() -> str:
    return leer_yaml(_leer(BACKEND))[0]["spec"]["template"]["spec"]["serviceAccountName"]


def test_secreto_database_url_solo_lo_lee_el_job():
    secretos = {s["nombre"]: s for s in leer_yaml(_leer(SECRETOS))["secretos"]}
    assert "DATABASE_URL" in secretos
    cuenta_job = _contenedor_job(JOB)[0]["serviceAccountName"]
    assert secretos["DATABASE_URL"]["leen"] == [cuenta_job]
    # El backend sigue con DATABASE_URL_APP.
    env = {e["name"]: e for e in _contenedor_backend()["env"]}
    assert env["DATABASE_URL"]["valueFrom"]["secretKeyRef"]["name"] == "DATABASE_URL_APP"


def test_membresia_del_rol_de_la_aplicacion():
    texto = _leer(CLOUD_SQL)
    doc = leer_yaml(texto)
    usuarios = {u["name"]: u for u in doc["users"]}
    app = usuarios["evydentia_demo_app"]
    assert app.get("miembro_de") == ["lopdp_app"]
    assert not {"ADMIN", "SET"} & set(app.get("atributos", []))
    assert doc["roles_y_politicas"]["rol_aplicacion"] == "evydentia_demo_app"
    assert "12 cabezas" not in texto and "rm25b" not in texto, "las cabezas no se listan a mano"
    assert "migrar-demo" in texto and "§6" in texto


def test_seccion_6_completa_y_en_orden():
    s6 = _seccion("6")
    for sub in ("6.1", "6.2", "6.3", "6.4", "6.5"):
        assert re.search(rf"^### {re.escape(sub)} ", s6, re.M), f"falta la §{sub}"
    copia = s6.find("gcloud sql backups create")
    ejecuta = s6.find("gcloud run jobs execute migrar-demo")
    actualiza = s6.find("gcloud run jobs update migrar-demo")
    rol = s6.find("pg_has_role('evydentia_demo_app', 'lopdp_app', 'MEMBER')")
    assert -1 < copia < ejecuta, "la copia previa va antes de jobs execute"
    assert -1 < rol < ejecuta and -1 < actualiza < ejecuta
    assert "--wait" in s6[ejecuta:].splitlines()[0]
    assert "alembic heads" in s6[ejecuta:]
    # El mismo commit que §5.2.
    linea_commit = "$COMMIT = (git rev-parse --short origin/main).Trim()"
    assert linea_commit in _seccion("5") and linea_commit in s6
    assert "--no-traffic" in s6 and "anterior=100" in s6
    bajo = s6.lower()
    assert "postgresql://" not in bajo
    assert not re.search(r"pgpassword|password\s*=|contraseña\s*[:=]", bajo)


def test_un_solo_paquete_de_imagen_del_backend():
    assert _contenedor_backend()["image"] == PAQUETE
    assert _contenedor_job(JOB)[1]["image"] == PAQUETE
    s61 = _seccion("6").split("### 6.2 ")[0]
    assert f'$IMAGEN = "{PAQUETE}"' in s61
    for ruta in (BACKEND, JOB):
        assert "evydentia-demo-containers/evydentia-backend-demo" not in _leer(ruta)
    assert "evydentia-demo-containers/evydentia-backend-demo" not in s61
