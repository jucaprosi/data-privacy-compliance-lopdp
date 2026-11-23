# -*- coding: utf-8 -*-
# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤adpa
"""Árbitro de alcance de un PR: los archivos que cambia caben en la `propiedad` de la ficha de su tarea.

La tarea sale del nombre de la rama: `tarea/<persona>/<id>...`, por ejemplo `adpa-03-roadmap` → ADPA-03.
Una rama sin ficha (CI-23) no se comprueba contra un alcance, pero se advierte de los archivos que
ninguna ficha viva posee (`::warning::` y `sin_ficha=true`) y, con `--estricto-sin-ficha`, falla. Las ramas
`pmv/**` quedan fuera solo si el PR va hacia `pmv/consolidacion` (`--destino`); sin `--destino`, o hacia
otra rama (por ejemplo `main`), se advierten y con `--estricto-sin-ficha` fallan como cualquier rama sin ficha.
Para el propietario: en el workflow, pasar `--destino "${{ github.base_ref }}"` y activar
`--estricto-sin-ficha`. Fuera de PREFIJOS_ESTRICTOS, salirse del alcance solo avisa: esa
lista es una decisión del propietario y extenderla bloquea a todo el equipo.

Mismo reparto que R5 de `verificar_reparto.py`, contra la ficha de la tarea.

LEG-06 R5 (alcance transversal): la ficha que declara `transversal = "aviso-de-autor"` (solo LEG-06) toca archivos
fuera de su propiedad si el diff de cada uno contra la base (a) añade exactamente una línea igual a `linea_de_aviso`
de su extensión, (b) no borra ni modifica ninguna otra línea y (c) la deja en la posición de R2. El BOM no es una
línea: se compara el texto que le sigue. LEG-06 R6: en la base del PR no puede haber otra ficha en `en_curso`.
"""
from __future__ import annotations

import argparse
import os
import importlib.util
import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PREFIJOS_ESTRICTOS = ("ADPA",)
_ID_EN_RAMA = re.compile(r"^(?:[^/]+/)*?([a-z]+-\d+[a-z]?)(?:-|$)")
PREFIJO_SIN_FICHA = "pmv/"  # CI-23: ramas del PMV, sin ficha por decisión del CTO
DESTINO_PMV = "pmv/consolidacion"  # solo hacia ella se eximen
EXENCIONES = "governance/tareas/_exenciones_propiedad.txt"
TRANSVERSALES = {"LEG-06": "aviso-de-autor"}  # LEG-06 R5: ninguna otra ficha puede declarar `transversal`
DIR_TAREAS_REL = "governance/tareas"


# ¤adpa
def _cargar_aviso():
    """LEG-06: `scripts/poner_aviso_de_autor.py`, dueño de `linea_de_aviso` y de la posición de R2."""
    ruta = Path(__file__).resolve().parent / "poner_aviso_de_autor.py"
    spec = importlib.util.spec_from_file_location("poner_aviso_de_autor", ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


# ¤adpa
def _cargar_indice():
    ruta = Path(__file__).resolve().parent / "generar_indice_tareas.py"
    spec = importlib.util.spec_from_file_location("generar_indice_tareas", ruta)
    modulo = importlib.util.module_from_spec(spec)
    sys.modules["generar_indice_tareas"] = modulo  # las clases de datos lo exigen antes de ejecutar el módulo
    spec.loader.exec_module(modulo)
    return modulo


# ¤adpa
def _cargar_git_diff():
    """CI-26 R2: el lector común de rutas del diff (`scripts/_git_diff.py`), cargado como los módulos hermanos."""
    ruta = Path(__file__).resolve().parent / "_git_diff.py"
    spec = importlib.util.spec_from_file_location("_git_diff", ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


# ¤adpa
def id_de_rama(rama: str, ids_conocidos) -> str | None:
    """El id de la rama con la grafía de su ficha (`sec-13a` → `SEC-13a`); sin ficha → None."""
    coincidencia = _ID_EN_RAMA.match(rama)
    if not coincidencia:
        return None
    candidato = coincidencia.group(1).lower()
    return next((i for i in ids_conocidos if i.lower() == candidato), None)


# ¤adpa
def retira_solo_exenciones_propias(diff: str, tarea_id: str, siembra: tuple[str, ...] = ()) -> bool:
    """El diff (`git diff --unified=0`) de EXENCIONES solo borra líneas propias (CI-25).

    Una línea borrada `X|<entrada>|motivo` es propia si empieza por `<tarea_id>|` o si `<entrada>` está en el campo
    `siembra` de la ficha (la ficha que siembra las marcas de otra obliga a retirar las exenciones de esa otra).
    Cualquier «+», alta, renombrado o borrado del archivo sigue invalidando.
    """
    prefijo = f"{tarea_id}|"
    sembradas = set(siembra)
    borradas = 0
    for linea in diff.splitlines():
        if linea.startswith(("deleted file", "new file", "rename ", "copy ", "+++ /dev/null", "--- /dev/null")):
            return False
        if linea.startswith(("+++", "---")):
            continue
        if linea.startswith("+"):
            return False
        if linea.startswith("-"):
            texto = linea[1:]
            entrada = texto.split("|", 2)[1] if texto.count("|") >= 2 else None
            if not (texto.startswith(prefijo) or (entrada is not None and entrada in sembradas)):
                return False
            borradas += 1
    return borradas > 0


# ¤adpa
def archivos_de_cierre(tarea_id: str) -> set[str]:
    """Lo que cierra una tarea no es parte de su alcance funcional: su ficha (GOB-06: los briefs no se versionan)."""
    return {f"governance/tareas/{tarea_id}.md"}


# ¤adpa
def fuera_de_alcance(archivos: list[str], tarea_id: str, propiedad: tuple[str, ...], indice,
                     exenciones_propias: bool = False) -> list[str]:
    patrones = [p.partition("#")[0] for p in propiedad]
    cierre = archivos_de_cierre(tarea_id) | ({EXENCIONES} if exenciones_propias else set())
    return [a for a in archivos if a not in cierre and not any(indice.rutas_se_solapan(a, p) for p in patrones)]


# ¤adpa
def sin_duena_viva(archivos: list[str], tareas, indice) -> list[str]:
    """CI-23: archivos que ninguna ficha no hecha posee."""
    patrones = [p.partition("#")[0] for t in tareas if getattr(t, "estado", "pendiente") != "hecha"
                for p in t.propiedad]
    return [a for a in archivos if not any(indice.rutas_se_solapan(a, p) for p in patrones)]


# ¤adpa
def _salida_github(clave: str, valor: str) -> None:
    ruta = os.environ.get("GITHUB_OUTPUT")
    if ruta:
        with open(ruta, "a", encoding="utf-8") as f:
            f.write(f"{clave}={valor}" + chr(10))


# ¤adpa
def es_estricta(tarea_id: str) -> bool:
    return tarea_id.rsplit("-", 1)[0].upper() in PREFIJOS_ESTRICTOS


# ¤adpa
def _archivos_del_diff(base: str, cabeza: str) -> list[str]:
    return _cargar_git_diff().archivos_del_diff(base, cabeza, RAIZ)


# ¤adpa
def _diff_de_exenciones(base: str, cabeza: str) -> str:
    return subprocess.run(["git", "diff", "--unified=0", "-M", f"{base}...{cabeza}", "--", EXENCIONES], cwd=RAIZ,
                          capture_output=True, text=True, encoding="utf-8", check=True).stdout


# ¤ip
def transversal_de(tarea, indice) -> str | None:
    """El campo `transversal` de la ficha (LEG-06 R5); el índice no lo carga, así que se lee de su cabecera."""
    if hasattr(tarea, "transversal"):
        return getattr(tarea, "transversal") or None
    archivo = getattr(tarea, "archivo", "")
    if not archivo:
        return None
    ruta = Path(getattr(indice, "DIR_TAREAS", RAIZ / DIR_TAREAS_REL)) / archivo
    try:
        return indice.leer_cabecera(ruta.read_text(encoding="utf-8")).get("transversal") or None
    except (OSError, ValueError):
        return None


# ¤ip
def _lineas_sin_bom(texto: str, aviso) -> tuple[str, list[str]]:
    bom = aviso.BOM if texto.startswith(aviso.BOM) else ""
    return bom, aviso.trozos(texto[len(bom):])


# ¤ip
def condiciones_transversales(ruta: str, texto_base: str | None, texto_cabeza: str | None, aviso=None) -> list[str]:
    """LEG-06 R5: las condiciones que incumple el diff de `ruta`; vacía si cumple (a), (b) y (c).

    (a) la cabeza tiene una línea más que la base y una línea de aviso más;
    (b) quitando esa línea de aviso de la cabeza queda la base, línea a línea con su final y su BOM;
    (c) esa línea está en `posicion_de_aviso` de la base.
    """
    aviso = aviso or _cargar_aviso()
    if not aviso.es_de_r1(ruta):
        return ["no es un archivo de código de R1"]
    if texto_base is None or texto_cabeza is None:
        return ["solo se admite modificar un archivo existente, no crearlo ni borrarlo"]
    extension = aviso.extension_de(ruta)
    linea = aviso.linea_de_aviso(extension)
    bom_b, base = _lineas_sin_bom(texto_base, aviso)
    bom_c, cabeza = _lineas_sin_bom(texto_cabeza, aviso)
    limpias_b = [x.rstrip("\r\n") for x in base]
    limpias_c = [x.rstrip("\r\n") for x in cabeza]
    fallos = []
    if not (len(cabeza) == len(base) + 1 and limpias_c.count(linea) == limpias_b.count(linea) + 1):
        fallos.append("(a) no añade exactamente una línea de aviso")
    i = limpias_c.index(linea) if linea in limpias_c else -1
    sin_aviso = cabeza[:i] + cabeza[i + 1:] if i >= 0 else cabeza
    if bom_b != bom_c or sin_aviso != base:
        fallos.append("(b) borra o modifica otras líneas")
    if i != aviso.posicion_de_aviso(base, extension):
        fallos.append(f"(c) el aviso no está en la posición de R2 (línea {aviso.posicion_de_aviso(base, extension) + 1})")
    return fallos


# ¤ip
def _git(*args: str, entrada: bytes | None = None) -> bytes:
    return subprocess.run(["git", "-c", "core.quotepath=off", *args], cwd=RAIZ, input=entrada,
                          capture_output=True, check=True).stdout


# ¤ip
def _textos_en(revision: str, rutas: list[str]) -> dict[str, str | None]:
    """El texto de cada ruta en `revision` (None si ahí no existe), con un solo `git cat-file --batch`."""
    if not rutas:
        return {}
    salida = _git("cat-file", "--batch", entrada="".join(f"{revision}:{r}\n" for r in rutas).encode("utf-8"))
    textos: dict[str, str | None] = {}
    pos = 0
    for ruta in rutas:
        fin = salida.index(b"\n", pos)
        cabecera = salida[pos:fin].decode("utf-8", errors="replace")
        pos = fin + 1
        if cabecera.endswith((" missing", " ambiguous")):
            textos[ruta] = None
            continue
        tamano = int(cabecera.rsplit(" ", 1)[1])
        textos[ruta] = salida[pos:pos + tamano].decode("utf-8", errors="replace")
        pos += tamano + 1
    return textos


# ¤ip
def _base_del_diff(base: str, cabeza: str) -> str:
    """La revisión contra la que compara `base...cabeza`: su ancestro común."""
    return _git("merge-base", base, cabeza).decode("utf-8").strip()


# ¤ip
def _fichas_en_curso_en_base(base: str, indice) -> list[str]:
    """LEG-06 R6: los ids de las fichas con `estado = "en_curso"` en la revisión base del PR."""
    nombres = _git("ls-tree", "-z", "--name-only", f"{base}:{DIR_TAREAS_REL}").decode("utf-8").split("\0")
    rutas = [f"{DIR_TAREAS_REL}/{n}" for n in nombres
             if n.endswith(".md") and n.lower() != "readme.md" and not n.lower().startswith("plantilla")]
    en_curso = []
    for ruta, texto in _textos_en(base, rutas).items():
        try:
            datos = indice.leer_cabecera(texto or "")
        except ValueError:
            continue
        if datos.get("estado") == "en_curso":
            en_curso.append(str(datos.get("id", Path(ruta).stem)))
    return sorted(en_curso)


# ¤ip
def comprobar_transversal(tarea, transversal: str, fuera: list[str], args, indice) -> int:
    """LEG-06 R5 y R6: el alcance de la ficha transversal; da rojo con el nombre de cada archivo que incumple."""
    if TRANSVERSALES.get(tarea.id) != transversal:
        print(f"ALCANCE NO VÁLIDO: {tarea.id} declara «transversal = {transversal}»; solo puede "
              f"{', '.join(f'{k} («{v}»)' for k, v in TRANSVERSALES.items())}.")
        return 1
    otras = [i for i in _fichas_en_curso_en_base(args.base, indice) if i != tarea.id]
    if otras:
        print(f"ALCANCE NO VÁLIDO: {tarea.id} es transversal y en la base hay fichas en «en_curso» (R6): "
              f"{', '.join(otras)}.")
        return 1
    if not fuera:
        print(f"ALCANCE OK: {tarea.id} solo toca su propiedad.")
        return 0
    base = _base_del_diff(args.base, args.cabeza)
    textos_base, textos_cabeza = _textos_en(base, fuera), _textos_en(args.cabeza, fuera)
    aviso = _cargar_aviso()
    malos = {a: f for a in fuera if (f := condiciones_transversales(a, textos_base[a], textos_cabeza[a], aviso))}
    if malos:
        print(f"ALCANCE NO VÁLIDO: {tarea.id} toca archivos ajenos sin cumplir R5:")
        for archivo, fallos in malos.items():
            print(f"  - {archivo}: {'; '.join(fallos)}")
        return 1
    print(f"ALCANCE OK: {tarea.id} toca su propiedad y solo añade el aviso en {len(fuera)} archivo(s) ajeno(s) (R5).")
    return 0


# ¤adpa
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--rama", required=True, help="nombre de la rama del PR")
    ap.add_argument("--base", required=True, help="revisión base del PR")
    ap.add_argument("--cabeza", required=True, help="revisión de la cabeza del PR")
    ap.add_argument("--estricto-sin-ficha", action="store_true",
                    help="sale con 1 si una rama sin ficha toca archivos sin dueña viva (CI-23)")
    ap.add_argument("--destino", default=None,
                    help="rama de destino del PR (github.base_ref); `pmv/**` solo se exime hacia pmv/consolidacion")
    args = ap.parse_args(argv)

    indice = _cargar_indice()
    tareas = indice.cargar_tareas()[0]
    tarea_id = id_de_rama(args.rama, [t.id for t in tareas])
    tarea = next((t for t in tareas if t.id == tarea_id), None)
    if tarea is None:
        print(f"ALCANCE: la rama «{args.rama}» no corresponde a ninguna ficha; no se comprueba.")
        if args.rama.startswith(PREFIJO_SIN_FICHA) and args.destino == DESTINO_PMV:
            return 0
        huerfanos = sin_duena_viva(_archivos_del_diff(args.base, args.cabeza), tareas, indice)
        _salida_github("sin_ficha", "true" if huerfanos else "false")
        for archivo in huerfanos:
            print(f"::warning::ALCANCE: «{archivo}» no es propiedad de ninguna ficha viva (rama sin ficha)")
        return 1 if huerfanos and args.estricto_sin_ficha else 0

    archivos = _archivos_del_diff(args.base, args.cabeza)
    propias = EXENCIONES in archivos and retira_solo_exenciones_propias(
        _diff_de_exenciones(args.base, args.cabeza), tarea.id, tuple(getattr(tarea, "siembra", ())))
    fuera = fuera_de_alcance(archivos, tarea.id, tarea.propiedad, indice, propias)
    if EXENCIONES in fuera:
        # Regla del CTO (2026-11-13): en las exenciones solo se borran líneas propias; lo demás es ERROR siempre.
        print(f"ALCANCE NO VÁLIDO: {tarea.id} cambia {EXENCIONES} sin limitarse a borrar sus líneas «{tarea.id}|…».")
        return 1
    transversal = transversal_de(tarea, indice)
    if transversal:
        return comprobar_transversal(tarea, transversal, fuera, args, indice)
    if not fuera:
        print(f"ALCANCE OK: {tarea.id} solo toca su propiedad.")
        return 0
    estricta = es_estricta(tarea.id)
    print(f"ALCANCE {'NO VÁLIDO' if estricta else 'EXCEDIDO (solo aviso)'}: {tarea.id} toca archivos ajenos:")
    for archivo in fuera:
        print(f"  - {archivo}")
    return 1 if estricta else 0


if __name__ == "__main__":
    sys.exit(main())
