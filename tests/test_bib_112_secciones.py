# ¤adpa
# ¤¤developer-architect
"""Árbitro BIB-112: secciones reservadas por tarea pendiente y catálogo de errores de Biblioteca."""
import re
from pathlib import Path
import pytest
from app_core.errors import CATALOGO_ERRORES
from features.biblioteca import biblioteca_service  # noqa: F401  importar la compuerta registra los errores

ROOT = Path(__file__).resolve().parents[1]
ARCHIVOS = {"biblioteca_service.py": ROOT / "features/biblioteca/biblioteca_service.py",
            "domain/errores.py": ROOT / "features/biblioteca/domain/errores.py"}
CODIGOS_BIB_105 = ("BIB_SIN_CAPACIDAD", "BIB_AUTOR_NO_INDEPENDIENTE", "BIB_VERSION_INMUTABLE",
                   "BIB_PUBLICACION_INCOMPLETA", "BIB_REVISION_PENDIENTE", "BIB_NO_ENCONTRADA",
                   "BIB_CONFLICTO_VERSION", "BIB_ARCHIVO_INVALIDO", "BIB_SUSTITUCION_REQUERIDA")


# ¤adpa
def _secciones_pendientes() -> list[tuple[str, str]]:
    """Pares (archivo, ID) que las fichas pendientes declaran con el sufijo #ID."""
    pares = []
    for ficha in sorted((ROOT / "governance/tareas").glob("*.md")):
        texto = ficha.read_text(encoding="utf-8")
        cabecera = texto.split("+++")[1] if texto.count("+++") >= 2 else ""
        if not re.search(r'^estado\s*=\s*"pendiente"', cabecera, re.M):
            continue
        for archivo in ARCHIVOS:
            for id_ in re.findall(r'features/biblioteca/' + re.escape(archivo) + r'#([A-Z]+-\d+[a-z]?)', cabecera):  # admite sufijos de letra (DEMO-03d)
                pares.append((archivo, id_))
    return pares


PARES = _secciones_pendientes()


def test_hay_secciones_pendientes_que_comprobar():
    assert PARES, "no se leyó ninguna ficha pendiente con sección"


@pytest.mark.parametrize("archivo,id_", PARES)
def test_cada_tarea_pendiente_tiene_su_par_de_marcas_una_vez(archivo, id_):
    texto = ARCHIVOS[archivo].read_text(encoding="utf-8")
    abre = len(re.findall(rf"^# === {re.escape(id_)} ===$", texto, re.M))
    cierra = len(re.findall(rf"^# === fin {re.escape(id_)} ===$", texto, re.M))
    assert (abre, cierra) == (1, 1), f"{id_} en {archivo}: abre={abre}, cierra={cierra}"


@pytest.mark.parametrize("archivo", ARCHIVOS)
def test_la_sala_tiene_su_seccion_bib_112(archivo):
    texto = ARCHIVOS[archivo].read_text(encoding="utf-8")
    assert texto.count("# === BIB-112 ===") == 1 and texto.count("# === fin BIB-112 ===") == 1


def test_la_compuerta_importa_errores():
    assert hasattr(biblioteca_service, "errores")


def test_catalogo_conserva_los_codigos_de_bib_105():
    for codigo in CODIGOS_BIB_105:
        assert codigo in CATALOGO_ERRORES and CATALOGO_ERRORES[codigo].codigo == codigo


def test_registrar_acepta_idempotente_y_rechaza_duplicado_distinto():
    from app_core.errors import CodigoErrorNegocio
    from features.biblioteca.domain import errores
    nuevo = CodigoErrorNegocio("BIB_PRUEBA_112", 409, "x")
    try:
        errores.registrar(nuevo)
        errores.registrar(nuevo)
        with pytest.raises(ValueError):
            errores.registrar(CodigoErrorNegocio("BIB_PRUEBA_112", 400, "otro"))
    finally:
        CATALOGO_ERRORES.pop("BIB_PRUEBA_112", None)
