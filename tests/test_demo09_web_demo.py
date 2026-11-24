# -*- coding: utf-8 -*-
# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤demo ¤arbitro
"""DEMO-09: la web de demo se publica con la imagen web de producción del mismo commit.

Solo lee archivos del repositorio (sin red, sin base de datos, sin `import yaml`):
`governance/operaciones/entornos/demo/cloudrun_frontend.yaml`, `governance/operaciones/DEMO_COMERCIAL.md` §5,
`frontend/cloudbuild.yaml` y `frontend/Dockerfile.cloudrun`.

Mutaciones (governance/especificaciones/DEMO-09.md §5), aplicadas una a una con la suite corrida y el
archivo restaurado:
- m1 manifiesto: `image` vuelve a `.../evydentia-demo-containers/evydentia-web-demo`
  -> falla `test_la_imagen_del_manifiesto_es_la_del_procedimiento`.
- m2 manifiesto o §5 con otro client id -> falla `test_el_client_id_es_uno_solo`.
- m3 §5 con `--build-arg NEXT_PUBLIC_GOOGLE_CLIENT_ID=...` -> falla `test_el_procedimiento_no_compila_aparte`.
- m4 `Dockerfile.cloudrun` con un segundo `ARG NEXT_PUBLIC_X` -> falla `test_solo_el_client_id_entra_al_compilar`.

DEMO-10 (governance/especificaciones/DEMO-10.md §5):
- m5 §5.2 sin el `throw` de la comprobación, o con la comprobación después del `deploy`
  -> falla `test_el_procedimiento_comprueba_el_permiso_antes_de_publicar`.
- m6 §5.3 con `$ANTERIOR = "evydentia-web-demo-00005-8f5"` -> falla `test_volver_atras_usa_la_etiqueta_anterior`.
"""
from __future__ import annotations

import re
from pathlib import Path

from tests._lector_yaml import leer_yaml

RAIZ = Path(__file__).resolve().parents[1]
MANIFIESTO = RAIZ / "governance" / "operaciones" / "entornos" / "demo" / "cloudrun_frontend.yaml"
GUIA = RAIZ / "governance" / "operaciones" / "DEMO_COMERCIAL.md"
CLOUDBUILD = RAIZ / "frontend" / "cloudbuild.yaml"
DOCKERFILE = RAIZ / "frontend" / "Dockerfile.cloudrun"

_CLIENT_ID = re.compile(r"\d+-[a-z0-9]+\.apps\.googleusercontent\.com")


def _leer(ruta: Path) -> str:
    return ruta.read_bytes().decode("utf-8").replace("\r\n", "\n")


def _seccion_5() -> str:
    texto = _leer(GUIA)
    inicio = re.search(r"^## 5\. ", texto, re.M)
    assert inicio, "DEMO_COMERCIAL.md no tiene la §5"
    resto = texto[inicio.start():]
    fin = re.search(r"^## (?!5\. )", resto[3:], re.M)
    return resto[: fin.start() + 3] if fin else resto


def _imagen_del_manifiesto() -> str:
    docs = leer_yaml(_leer(MANIFIESTO))
    servicio = docs[0] if isinstance(docs, list) else docs
    return servicio["spec"]["template"]["spec"]["containers"][0]["image"]


def _entorno_del_manifiesto() -> dict:
    docs = leer_yaml(_leer(MANIFIESTO))
    servicio = docs[0] if isinstance(docs, list) else docs
    env = servicio["spec"]["template"]["spec"]["containers"][0]["env"]
    return {e["name"]: e["value"] for e in env}


def _cloudbuild() -> dict:
    return leer_yaml(_leer(CLOUDBUILD))


def test_la_imagen_del_manifiesto_es_la_del_procedimiento():
    coincidencias = re.findall(r'\$IMAGEN\s*=\s*"([^"]+)"', _seccion_5())
    assert len(coincidencias) == 1, "§5 debe definir $IMAGEN una sola vez"
    imagenes = _cloudbuild()["images"]
    assert len(imagenes) == 1
    assert imagenes[0].endswith(":${_ETIQUETA}")
    de_cloudbuild = imagenes[0][: -len(":${_ETIQUETA}")]
    assert _imagen_del_manifiesto() == coincidencias[0] == de_cloudbuild


def test_el_client_id_es_uno_solo():
    args = _cloudbuild()["steps"][0]["args"]
    indice = args.index("--build-arg")
    nombre, _, de_cloudbuild = args[indice + 1].partition("=")
    assert nombre == "NEXT_PUBLIC_GOOGLE_CLIENT_ID"
    assert _CLIENT_ID.fullmatch(de_cloudbuild)
    assert _entorno_del_manifiesto()["NEXT_PUBLIC_GOOGLE_CLIENT_ID"] == de_cloudbuild
    for encontrado in _CLIENT_ID.findall(_seccion_5()):
        assert encontrado == de_cloudbuild


def test_el_procedimiento_no_compila_aparte():
    seccion = _seccion_5()
    assert "docker build" not in seccion
    assert "--build-arg" not in seccion
    envios = re.findall(r"gcloud builds submit[^\n]*", seccion)
    assert envios, "§5 debe construir con gcloud builds submit si falta la imagen"
    for envio in envios:
        assert "--config cloudbuild.yaml" in envio


def test_solo_el_client_id_entra_al_compilar():
    arg = re.findall(r"^\s*ARG\s+(NEXT_PUBLIC_\w+)", _leer(DOCKERFILE), re.M)
    assert arg == ["NEXT_PUBLIC_GOOGLE_CLIENT_ID"]
    args = _cloudbuild()["steps"][0]["args"]
    assert args.count("--build-arg") == 1
    assert args[args.index("--build-arg") + 1].startswith("NEXT_PUBLIC_GOOGLE_CLIENT_ID=")


def _subseccion(titulo: str) -> str:
    seccion = _seccion_5()
    inicio = re.search(rf"^### {re.escape(titulo)} ", seccion, re.M)
    assert inicio, f"§5 no tiene la subsección {titulo}"
    resto = seccion[inicio.start():]
    fin = re.search(r"^### ", resto[4:], re.M)
    return resto[: fin.start() + 4] if fin else resto


def _bloques_powershell(texto: str) -> list[str]:
    return re.findall(r"```powershell\n(.*?)```", texto, re.S)


def test_el_procedimiento_comprueba_el_permiso_antes_de_publicar():
    bloque = _bloques_powershell(_subseccion("5.2"))[0]
    despliegue = bloque.find("gcloud run deploy")
    assert despliegue >= 0
    antes = bloque[:despliegue]
    for pieza in (
        "get-iam-policy evydentia-containers",
        "roles/artifactregistry.reader",
        "serverless-robot-prod.iam.gserviceaccount.com",
        "projectNumber",
        "throw",
    ):
        assert pieza in antes, f"falta antes del deploy: {pieza}"
    assert "517105327086" not in bloque


def test_volver_atras_usa_la_etiqueta_anterior():
    assert not re.search(r"evydentia-web-demo-\d{5}-", _seccion_5())
    paso = _subseccion("5.2")
    etiqueta = paso.find('--update-tags="anterior=')
    assert 0 <= etiqueta < paso.find("gcloud run deploy")
    volver = _subseccion("5.3")
    assert '--to-tags="anterior=100"' in volver
    assert not re.search(r"\$ANTERIOR\s*=", volver)
