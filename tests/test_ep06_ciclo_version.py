# ¤entorno-pruebas ¤ci-cd
"""EP-06: ciclo de una versión en el entorno de pruebas.

Ejecuta los dos scripts de PowerShell con -SoloMostrar y compara el orden de los pasos. Comprueba también
la guardia de la huella, que la imagen va siempre por digest, que la URL no se imprime y que el reinicio
solo actúa tras la confirmación (un `gcloud` falso en el PATH deja una marca si alguien lo llama).
"""
from __future__ import annotations

import os
import re
import shutil
import stat
import subprocess
import uuid
from pathlib import Path

import pytest

from scripts import digest_verificado as dv

RAIZ = Path(__file__).resolve().parents[1]
DESPLEGAR = RAIZ / "scripts" / "desplegar_entorno_pruebas.ps1"
REINICIAR = RAIZ / "scripts" / "reiniciar_entorno_pruebas.ps1"
SHELL = shutil.which("pwsh") or shutil.which("powershell")
requiere_powershell = pytest.mark.skipif(SHELL is None, reason="PowerShell no está instalado")

DIGEST = "sha256:" + "ab" * 32
PROYECTO = f"pruebas-{uuid.uuid4().hex[:6]}"
HUELLA = f"prod-{uuid.uuid4().hex[:6]}"


def _correr(script: Path, *argumentos: str, entorno: dict | None = None) -> subprocess.CompletedProcess:
    env = {**os.environ, "HUELLA_PROYECTO_PRODUCCION": HUELLA, **(entorno or {})}
    return subprocess.run(
        [SHELL, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", str(script), *argumentos],
        cwd=RAIZ, capture_output=True, text=True, env=env, timeout=120,
    )


def _pasos(salida: str) -> list[str]:
    return re.findall(r"^PASO \d+ (.+)$", salida, flags=re.MULTILINE)


def _desplegar(proyecto: str = PROYECTO, digest: str = DIGEST, entorno: dict | None = None):
    return _correr(
        DESPLEGAR, "-Proyecto", proyecto, "-Digest", digest,
        "-Imagen", "us-central1-docker.pkg.dev/proyecto-x/repo/evydentia",
        "-Servicios", "api,web,worker", "-InstanciaCloudSql", "proyecto-x:us-central1:sql", "-SoloMostrar",
        entorno=entorno,
    )


def _reiniciar(*extra: str, proyecto: str = PROYECTO, entorno: dict | None = None):
    return _correr(
        REINICIAR, "-Proyecto", proyecto, "-InstanciaCloudSql", f"{proyecto}:us-central1:sql",
        "-BaseDeDatos", "evydentia", "-Buckets", f"{proyecto}-evidencias,{proyecto}-video", *extra,
        entorno=entorno,
    )


# --- Despliegue ------------------------------------------------------------------------------------

@requiere_powershell
def test_desplegar_solo_mostrar_sigue_el_orden_del_contrato():
    r = _desplegar()
    assert r.returncode == 0, r.stdout + r.stderr
    pasos = _pasos(r.stdout)
    assert len(pasos) == 5
    assert "Alembic" in pasos[0] and "huella" in pasos[1]
    assert pasos.index(next(p for p in pasos if "migrar" in p)) < pasos.index(next(p for p in pasos if "desplegar" in p))
    assert "verificador" in pasos[4]
    assert "SOLO MOSTRAR" in r.stdout


@requiere_powershell
def test_desplegar_usa_siempre_el_digest_en_los_tres_servicios():
    r = _desplegar()
    despliegues = [l for l in r.stdout.splitlines() if "gcloud run deploy" in l]
    assert len(despliegues) == 3
    assert all(f"@{DIGEST} " in l and f"--project {PROYECTO}" in l for l in despliegues)


@requiere_powershell
@pytest.mark.parametrize("imagen", ["repo/evydentia:latest", f"repo/evydentia@{DIGEST}"])
def test_desplegar_rechaza_imagen_con_etiqueta(imagen):
    r = _correr(DESPLEGAR, "-Proyecto", PROYECTO, "-Digest", DIGEST, "-Imagen", imagen,
                "-Servicios", "a,b,c", "-InstanciaCloudSql", "x:y:z", "-SoloMostrar")
    assert r.returncode != 0 and "DETENIDO" in r.stdout


@requiere_powershell
def test_desplegar_rechaza_digest_invalido():
    r = _desplegar(digest="latest")
    assert r.returncode != 0 and "DETENIDO" in r.stdout


@requiere_powershell
def test_desplegar_aborta_ante_la_huella_de_produccion():
    r = _desplegar(proyecto=f"{HUELLA}-app")
    assert r.returncode != 0 and "produccion" in r.stdout
    assert "gcloud run deploy" not in r.stdout


@requiere_powershell
def test_desplegar_sin_huella_definida_no_corre():
    r = _desplegar(entorno={"HUELLA_PROYECTO_PRODUCCION": ""})
    assert r.returncode != 0 and "HUELLA_PROYECTO_PRODUCCION" in r.stdout


@requiere_powershell
def test_la_url_de_conexion_no_se_imprime(tmp_path):
    secreto = f"postgresql://u-{uuid.uuid4().hex[:6]}:clave@localhost:5434/x"
    archivo = tmp_path / "url.txt"
    archivo.write_text(secreto, encoding="utf-8")
    r = _correr(DESPLEGAR, "-Proyecto", PROYECTO, "-Digest", DIGEST, "-Imagen", "repo/evydentia",
                "-Servicios", "a,b,c", "-InstanciaCloudSql", "x:y:z", "-ArchivoUrl", str(archivo), "-SoloMostrar")
    assert r.returncode == 0
    assert secreto not in r.stdout + r.stderr and "postgresql://" not in r.stdout


def test_los_scripts_no_imprimen_la_variable_de_la_url():
    for script in (DESPLEGAR, REINICIAR):
        texto = script.read_text(encoding="utf-8")
        impresion = re.compile(r'(Write-(Output|Host)|Muestra|Falla)\s+"[^"]*\$env:MIGRATION_DATABASE_URL')
        assert not impresion.search(texto)
        assert "Get-Content $ArchivoUrl" in texto  # la URL sale de un archivo local, no de un parámetro


# --- Reinicio --------------------------------------------------------------------------------------

@requiere_powershell
def test_reiniciar_solo_mostrar_sigue_el_orden_y_solo_toca_el_proyecto():
    r = _reiniciar("-SoloMostrar")
    assert r.returncode == 0, r.stdout + r.stderr
    pasos = _pasos(r.stdout)
    assert len(pasos) == 7
    claves = ["huella", "confirmacion", "pertenencia", "recrear", "migrar", "vaciar", "siembra"]
    assert [next(i for i, p in enumerate(pasos) if c in p) for c in claves] == list(range(7))
    comandos = [l for l in r.stdout.splitlines() if "gcloud " in l]
    assert comandos and all(f"--project {PROYECTO}" in l for l in comandos)
    assert "sembrar_entorno_pruebas.py" in r.stdout


@requiere_powershell
def test_reiniciar_aborta_ante_la_huella_de_produccion():
    r = _reiniciar("-SoloMostrar", proyecto=f"{HUELLA}-app")
    assert r.returncode != 0 and "produccion" in r.stdout
    assert "gcloud " not in r.stdout


@pytest.fixture
def gcloud_falso(tmp_path):
    marca = tmp_path / "gcloud-llamado"
    carpeta = tmp_path / "bin"
    carpeta.mkdir()
    sh = carpeta / "gcloud"
    sh.write_text(f"#!/bin/sh\necho llamado >> '{marca}'\n", encoding="utf-8")
    sh.chmod(sh.stat().st_mode | stat.S_IEXEC)
    (carpeta / "gcloud.cmd").write_text(f"@echo llamado>>\"{marca}\"\r\n", encoding="utf-8")
    entorno = {"PATH": f"{carpeta}{os.pathsep}{os.environ.get('PATH', '')}"}
    return entorno, marca


@requiere_powershell
def test_reiniciar_sin_confirmacion_correcta_no_actua(gcloud_falso):
    entorno, marca = gcloud_falso
    r = _reiniciar("-Confirmacion", "otro-proyecto", entorno=entorno)
    assert r.returncode != 0 and "confirmacion" in r.stdout
    assert not marca.exists()
    assert "PASO 3" not in r.stdout


@requiere_powershell
def test_reiniciar_comprueba_la_pertenencia_de_los_buckets_antes_de_borrar():
    salida = _reiniciar("-SoloMostrar").stdout
    primera_pertenencia = salida.index("storage buckets describe")
    assert salida.index("projects describe") < salida.index("sql databases delete")
    assert primera_pertenencia < salida.index("sql databases delete")
    assert primera_pertenencia < salida.index("storage rm")
    for linea in (l for l in salida.splitlines() if "buckets describe" in l):
        assert "project_number" in linea


@requiere_powershell
def test_reiniciar_se_detiene_si_no_puede_probar_la_pertenencia(gcloud_falso):
    """gcloud falso no devuelve numeros: la pertenencia no se prueba y no se borra nada."""
    entorno, marca = gcloud_falso
    r = _reiniciar("-Confirmacion", PROYECTO, entorno=entorno)
    assert r.returncode != 0 and "DETENIDO" in r.stdout
    assert "PASO 4" not in r.stdout
    assert marca.read_text().count("llamado") == 1


# --- Digest verificado -------------------------------------------------------------------------------

def test_digest_que_paso_el_verificador_se_puede_promover(tmp_path):
    archivo = tmp_path / "digest.json"
    dv.guardar(DIGEST, 0, archivo)
    assert dv.leer(archivo)["digest"] == DIGEST
    assert dv.comprobar(DIGEST, archivo)["codigo_salida"] == 0


def test_digest_que_fallo_o_no_paso_se_rechaza(tmp_path):
    archivo = tmp_path / "digest.json"
    otro = "sha256:" + "cd" * 32
    dv.guardar(otro, 3, archivo)
    with pytest.raises(dv.DigestError):
        dv.comprobar(otro, archivo)
    with pytest.raises(dv.DigestError):
        dv.leer(archivo)
    with pytest.raises(dv.DigestError):
        dv.comprobar(DIGEST, archivo)
    assert dv.main(["--archivo", str(archivo), "comprobar", "--digest", otro]) == 1


def test_un_fallo_posterior_anula_el_verde_anterior(tmp_path):
    archivo = tmp_path / "digest.json"
    dv.guardar(DIGEST, 0, archivo)
    dv.guardar(DIGEST, 1, archivo)
    with pytest.raises(dv.DigestError):
        dv.comprobar(DIGEST, archivo)


def test_digest_invalido_y_registro_dentro_del_repositorio_se_rechazan():
    with pytest.raises(dv.DigestError):
        dv.normalizar("latest")
    with pytest.raises(dv.DigestError):
        dv.guardar(DIGEST, 0, RAIZ / "herramientas" / "digest.json")
