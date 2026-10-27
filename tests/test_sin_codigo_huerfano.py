# ¤frontend-ide
# ¤arbitro
"""Árbitro estático: ningún componente de ``components/modules/`` queda sin montar (LIM-01).

Un componente que ningún archivo de ``frontend/src`` importa es código muerto: no se ve en
pantalla y aun así hay que mantenerlo (API-01 tuvo que corregir dos sin poder verlos). Las
pruebas no cuentan como uso.

Prueba de mutación (LIM-01): crear ``modules/ComponenteHuerfanoMutacion.tsx`` sin importarlo
hace fallar ``test_no_hay_componentes_huerfanos_en_modules`` con su ruta; al retirarlo, pasa.
"""

from pathlib import Path
import re


RAIZ = Path(__file__).parents[1]
FRONTEND_SRC = RAIZ / "frontend" / "src"
MODULOS = FRONTEND_SRC / "components" / "modules"
EXTENSIONES = (".ts", ".tsx", ".js", ".jsx")
IMPORTACION = re.compile(
    r"""(?:\bfrom\s*|\bimport\s*\(|\brequire\s*\()\s*["'](?P<ruta>[^"']+)["']"""
)

EXCEPCIONES: set[Path] = set()


def _resolver_importacion(origen: Path, ruta: str) -> set[Path]:
    if ruta.startswith("@/"):
        base = FRONTEND_SRC / ruta[2:]
    elif ruta.startswith("."):
        base = origen.parent / ruta
    else:
        return set()

    candidatos = {base}
    candidatos.update(Path(f"{base}{extension}") for extension in EXTENSIONES)
    candidatos.update(base / f"index{extension}" for extension in EXTENSIONES)
    return {candidato.resolve() for candidato in candidatos}


def _archivos_importados() -> set[Path]:
    importados: set[Path] = set()
    fuentes = (
        archivo
        for archivo in FRONTEND_SRC.rglob("*")
        if archivo.is_file() and archivo.suffix in EXTENSIONES
    )
    for fuente in fuentes:
        texto = fuente.read_text(encoding="utf-8")
        for coincidencia in IMPORTACION.finditer(texto):
            importados.update(_resolver_importacion(fuente, coincidencia.group("ruta")))
    return importados


def test_no_hay_componentes_huerfanos_en_modules() -> None:
    importados = _archivos_importados()
    componentes = {
        archivo.resolve()
        for archivo in MODULOS.rglob("*.tsx")
        if archivo.name != "index.tsx"
    }
    huerfanos = sorted(
        archivo.relative_to(RAIZ).as_posix()
        for archivo in componentes - importados - {ruta.resolve() for ruta in EXCEPCIONES}
    )

    assert not huerfanos, "Componentes sin importar desde frontend/src:\n" + "\n".join(huerfanos)


def test_las_excepciones_siguen_siendo_huerfanas() -> None:
    """Una excepción que ya se monta o ya no existe debe salir de la lista."""
    importados = _archivos_importados()
    vencidas = sorted(
        ruta.relative_to(RAIZ).as_posix()
        for ruta in EXCEPCIONES
        if not ruta.exists() or ruta.resolve() in importados
    )
    assert not vencidas, "Retire de EXCEPCIONES:\n" + "\n".join(vencidas)
