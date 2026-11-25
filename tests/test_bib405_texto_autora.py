"""BIB-405: las doce plantillas vuelven al texto de su autora (commit 0537659b).

Árbitro exógeno: lee cada plantilla en 0537659b con ``git show`` (sin red ni
``import yaml``), aplica solo las dos correcciones mecánicas de R1 (quitar el
fragmento de marca y corregir la errata) y compara con el archivo actual, una
vez retirado el metadato de BIB-403 (versión, ``validacion_legal`` y
``secciones_informativas``), que R2 conserva aparte.
"""
import re
import subprocess
from pathlib import Path

import pytest

ORIGEN = "0537659b"
CARPETA = "data/biblioteca/pmv"
CODIGOS = [f"BIB-{n:03d}" for n in range(1, 13)]
MARCA = "PENDIENTE VALIDACIÓN"
ERRATA, CORRECTA = "SPSP-SPD-2025-0041-R", "SPDP-SPD-2025-0041-R"
ANADIDOS_LEG08 = {
    "BIB-003": ["Conserve la prueba mientras sea necesaria"],
    "BIB-005": ["vigente desde su publicación en el Registro Oficial"],
    "BIB-007": ["días calendario"],
    "BIB-009": ["vigente desde su publicación en el Registro Oficial"],
    "BIB-011": ["no es mayor al estrictamente necesario", "vigente desde su publicación en el Registro Oficial"],
}
# Fragmentos de marca (R1): la marca es el corchete o paréntesis que la
# contiene (si dentro le sigue una frase de la autora, esa frase se queda),
# o la oración «PENDIENTE VALIDACIÓN: …» dentro de un texto.
REGLAS = [
    (re.compile(r"\[[^\[\]\n]*: " + MARCA + r"\. ([^\[\]\n]*)\]"), r"\1"),
    (re.compile(r"^\[[^\[\]\n]*" + MARCA + r"[^\[\]\n]*\]\n\n", re.M), ""),
    (re.compile(r" ?\[[^\[\]\n]*" + MARCA + r"[^\[\]\n]*\]"), ""),
    (re.compile(r"; vigencia[^;()\n]*: " + MARCA + r"\)"), ")"),
    (re.compile(r" ?\([^()\n]*: " + MARCA + r"\)"), ""),
    (re.compile(r" " + MARCA + r": [^.\"\n]*\."), ""),
]


def git_show(ruta: str) -> str:
    return subprocess.run(
        ["git", "show", f"{ORIGEN}:{ruta}"], check=True, capture_output=True
    ).stdout.decode("utf-8")


def corregir(texto: str) -> str:
    for patron, sustituto in REGLAS:
        texto = patron.sub(sustituto, texto)
    return texto.replace(ERRATA, CORRECTA)


def sin_metadato_bib403(texto: str) -> str:
    texto = re.sub(r"^version: .*\n", "", texto, flags=re.M)
    texto = re.sub(r"^validacion_legal: .*\n", "", texto, flags=re.M)
    return re.sub(r"^secciones_informativas:\n(?:  - .*\n)+", "", texto, flags=re.M)


def version(texto: str) -> tuple[int, ...]:
    return tuple(int(p) for p in re.search(r"^version: (\S+)", texto, re.M).group(1).split("."))


def actual(codigo: str) -> str:
    return Path(f"{CARPETA}/{codigo}.md").read_bytes().decode("utf-8")


def errores_autora(codigo: str, texto: str) -> list[str]:
    esperado = sin_metadato_bib403(corregir(git_show(f"{CARPETA}/{codigo}.md")))
    errores = []
    if sin_metadato_bib403(texto) != esperado:
        errores.append("el cuerpo no es el de la autora")
    for anadido in ANADIDOS_LEG08.get(codigo, []):
        if anadido in texto:
            errores.append(f"queda el añadido de LEG-08: {anadido}")
    if MARCA in texto:
        errores.append("queda una marca")
    if "SPSP-SPD" in texto:
        errores.append("queda la errata")
    return errores


@pytest.mark.parametrize("codigo", CODIGOS)
def test_cuerpo_de_la_autora(codigo):
    assert errores_autora(codigo, actual(codigo)) == []


@pytest.mark.parametrize("codigo", CODIGOS)
def test_version_sube_si_el_cuerpo_cambio(codigo):
    previo = subprocess.run(
        ["git", "show", f"origin/main:{CARPETA}/{codigo}.md"], capture_output=True
    )
    if previo.returncode:
        pytest.skip("sin origin/main")
    anterior = previo.stdout.decode("utf-8")
    if sin_metadato_bib403(anterior) != sin_metadato_bib403(actual(codigo)):
        assert version(actual(codigo)) > version(anterior)


def test_m1_borrar_frase_de_la_autora_da_rojo():
    texto = actual("BIB-007").replace("Los derechos son irrenunciables (LOPDP art. 24).", "", 1)
    assert "el cuerpo no es el de la autora" in errores_autora("BIB-007", texto)


def test_m2_devolver_anadido_leg08_da_rojo():
    texto = actual("BIB-005").replace(
        "art. 11\"", "art. 11 (vigente desde su publicación en el Registro Oficial)\"", 1
    )
    assert texto != actual("BIB-005")
    assert "queda el añadido de LEG-08: vigente desde su publicación en el Registro Oficial" in errores_autora("BIB-005", texto)


def test_m3_dejar_una_marca_da_rojo():
    texto = actual("BIB-001").replace("(LOPDP arts. 55 a 60).", f"(LOPDP arts. 55 a 60). [{MARCA}]", 1)
    assert texto != actual("BIB-001")
    assert "queda una marca" in errores_autora("BIB-001", texto)
