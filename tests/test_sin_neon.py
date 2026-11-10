"""NEON-00 · Árbitro sin Neon.

`main` es solo EVYDENTIA: la palabra «neon» (sin distinguir mayúsculas) no puede aparecer en
el repositorio rastreado salvo en tres sitios, todos cerrados y que solo pueden decrecer:

1. la lista blanca `tests/sin_neon/permitidos.txt` (`archivo|motivo`; acepta globs);
2. las fichas de `governance/tareas/*.md` con estado `hecha` (la historia se conserva);
3. los pendientes `tests/sin_neon/pendientes/<ID>.txt`, uno por ficha dueña de la limpieza.

Criterio híbrido de los pendientes (decisión del Arquitecto ADPA):
- documentos (`.md`): `archivo|N`, el recuento de menciones, sin texto ni número de línea
  (los documentos se reformulan a diario);
- código y configuración: `archivo|texto de la línea recortado`, una línea por aparición
  (el recuento de cada pareja es el número de líneas repetidas). Una línea editada que aún
  menciona Neon cuenta como nueva y obliga a quitar la mención.

El árbitro falla si el recuento actual de un archivo o pareja SUPERA el permitido o si aparece
uno nuevo; una mención que desaparece no pone nada en rojo. «Solo puede decrecer» se comprueba
contra la versión de esas listas en origin/main: ningún recuento sube y no entran claves nuevas
(la holgura la cierra NEON-04, cuyo árbitro final exige permitido igual a cero).

En las fichas de `governance/tareas/` el identificador `NEON-NN` no cuenta como mención.
Sin `import yaml`; no toca la red ni recursos de Neon.
"""
from __future__ import annotations

import fnmatch
import importlib.util
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DIR_LISTAS = RAIZ / "tests" / "sin_neon"
PERMITIDOS = DIR_LISTAS / "permitidos.txt"
DIR_PENDIENTES = DIR_LISTAS / "pendientes"

FICHAS_DUENAS = ("NEON-01", "NEON-02", "NEON-03", "NEON-04", "FIRMA-02")

# El árbitro y sus listas nombran a Neon por definición: no se auditan a sí mismos.
AUTOEXCLUIDOS = ("tests/test_sin_neon.py", "tests/sin_neon/**")

PATRON = re.compile(r"neon", re.IGNORECASE)
ID_FICHA = re.compile(r"NEON-\d{2}", re.IGNORECASE)
PREFIJO_FICHAS = "governance/tareas/"
LARGO_TEXTO = 100


def recortar(texto: str) -> str:
    return texto.strip()[:LARGO_TEXTO].strip()


def es_documento(ruta: str) -> bool:
    return ruta.endswith(".md")


def clave(ruta: str, texto: str) -> tuple[str, str]:
    """Documento: (archivo, ""). Código y configuración: (archivo, texto recortado)."""
    return (ruta, "") if es_documento(ruta) else (ruta, recortar(texto))


def leer_menciones() -> list[tuple[str, int, str]]:
    """`git grep -n -i neon` sobre los archivos rastreados: (archivo, línea, texto)."""
    r = subprocess.run(
        ["git", "-c", "core.quotepath=false", "grep", "-n", "-i", "neon"],
        cwd=RAIZ, capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    assert r.returncode in (0, 1), r.stderr
    salida = []
    for linea in r.stdout.split("\n"):
        if not linea:
            continue
        ruta, n, texto = linea.split(":", 2)
        salida.append((ruta, int(n), texto))
    return salida


def leer_permitidos(texto: str) -> list[tuple[str, str]]:
    filas = []
    for crudo in texto.replace("\r", "").split("\n"):
        crudo = crudo.strip()
        if not crudo or crudo.startswith("#"):
            continue
        archivo, _, motivo = crudo.partition("|")
        filas.append((archivo.strip(), motivo.strip()))
    return filas


def leer_pendientes(texto: str) -> Counter:
    """`archivo|N` para documentos; `archivo|texto` para código, una línea por aparición."""
    cuenta: Counter = Counter()
    for crudo in texto.replace("\r", "").split("\n"):
        if not crudo.strip() or crudo.startswith("#"):
            continue
        archivo, _, resto = crudo.partition("|")
        if es_documento(archivo):
            cuenta[(archivo, "")] += int(resto)
        else:
            cuenta[(archivo, recortar(resto))] += 1
    return cuenta


def fichas_hechas() -> set[str]:
    nombre = "_indice_tareas_neon00"
    spec = importlib.util.spec_from_file_location(nombre, RAIZ / "scripts" / "generar_indice_tareas.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[nombre] = mod  # los dataclasses lo exigen
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    tareas, _ = mod.cargar_tareas()
    return {f"{PREFIJO_FICHAS}{t.id}.md" for t in tareas if t.estado == "hecha"}


def _coincide(ruta: str, patron: str) -> bool:
    return ruta == patron or fnmatch.fnmatchcase(ruta, patron.replace("**", "*"))


def contar(menciones, permitidos, hechas):
    """Cuenta por clave las menciones que ni la lista blanca ni las fichas hechas cubren."""
    patrones = [a for a, _ in permitidos] + list(AUTOEXCLUIDOS)
    actual: Counter = Counter()
    ejemplo: dict[tuple[str, str], str] = {}
    for ruta, n, texto in menciones:
        if ruta in hechas or any(_coincide(ruta, p) for p in patrones):
            continue
        if ruta.startswith(PREFIJO_FICHAS) and not PATRON.search(ID_FICHA.sub("", texto)):
            continue
        k = clave(ruta, texto)
        actual[k] += 1
        ejemplo.setdefault(k, f"{ruta}:{n}: {texto.strip()[:LARGO_TEXTO]}")
    return actual, ejemplo


def evaluar(menciones, permitidos, pendientes: dict[str, Counter], hechas) -> list[str]:
    """Lo que ninguna lista cubre: claves nuevas y recuentos que superan lo permitido."""
    actual, ejemplo = contar(menciones, permitidos, hechas)
    permitido: Counter = Counter()
    for cuenta in pendientes.values():
        permitido.update(cuenta)
    return [f"{ejemplo[k]} (hay {v}, permitido {permitido[k]})" for k, v in actual.items() if v > permitido[k]]


def no_crece(actual: dict[str, Counter], base: dict[str, Counter]) -> list[str]:
    """Contra origin/main: ningún recuento sube y no entran claves nuevas."""
    errores = []
    for ficha, cuenta in actual.items():
        if ficha not in base:
            continue
        for k, v in cuenta.items():
            if v > base[ficha].get(k, 0):
                errores.append(f"pendientes/{ficha}.txt crece en {k[0]} {k[1][:40]!r}: {v} > {base[ficha].get(k, 0)}")
    return errores


def problemas_de_listas(permitidos, pendientes_por_ficha, contiene, *, permitidos_base=None,
                        pendientes_base=None) -> list[str]:
    """Errores estructurales: IDs desconocidos, listas que crecen y «pendiente: brief» ya cumplido."""
    errores = []
    for ficha in pendientes_por_ficha:
        if ficha not in FICHAS_DUENAS:
            errores.append(f"pendientes/{ficha}.txt: ID desconocido (válidos: {', '.join(FICHAS_DUENAS)})")
    if permitidos_base is not None:
        nuevas = {a for a, _ in permitidos} - {a for a, _ in permitidos_base}
        errores += [f"permitidos.txt: entrada nueva {a}" for a in sorted(nuevas)]
    if pendientes_base is not None:
        errores += no_crece(pendientes_por_ficha, pendientes_base)
    for archivo, motivo in permitidos:
        if motivo.startswith("pendiente: brief") and not contiene(archivo):
            errores.append(f"{archivo}: ya no contiene «neon»; retire su línea «pendiente: brief» de permitidos.txt")
    return errores


def _version_de_main(ruta: Path) -> str | None:
    rel = ruta.relative_to(RAIZ).as_posix()
    r = subprocess.run(["git", "show", f"origin/main:{rel}"], cwd=RAIZ, capture_output=True,
                       text=True, encoding="utf-8")
    return r.stdout if r.returncode == 0 else None


def _bases():
    """Listas de origin/main; sin referencia o con archivo nuevo, no hay con qué comparar."""
    p = _version_de_main(PERMITIDOS)
    permitidos_base = leer_permitidos(p) if p is not None else None
    pendientes_base = {}
    for f in sorted(DIR_PENDIENTES.glob("*.txt")):
        v = _version_de_main(f)
        if v is not None:
            pendientes_base[f.stem] = leer_pendientes(v)
    return permitidos_base, pendientes_base


def _cargar_listas():
    permitidos = leer_permitidos(PERMITIDOS.read_text(encoding="utf-8"))
    pendientes = {p.stem: leer_pendientes(p.read_text(encoding="utf-8"))
                  for p in sorted(DIR_PENDIENTES.glob("*.txt"))}
    return permitidos, pendientes


def _contiene(ruta: str) -> bool:
    p = RAIZ / ruta
    return p.is_file() and bool(PATRON.search(p.read_text(encoding="utf-8", errors="replace")))


def test_sin_menciones_fuera_de_las_listas():
    permitidos, pendientes = _cargar_listas()
    sueltas = evaluar(leer_menciones(), permitidos, pendientes, fichas_hechas())
    assert not sueltas, "Menciones a Neon fuera de las listas:\n" + "\n".join(sueltas[:40])


def test_listas_cerradas_y_sin_crecer():
    permitidos, pendientes = _cargar_listas()
    permitidos_base, pendientes_base = _bases()
    errores = problemas_de_listas(permitidos, pendientes, _contiene,
                                  permitidos_base=permitidos_base, pendientes_base=pendientes_base)
    assert not errores, "\n".join(errores)


# ---- Mutaciones sobre datos simulados -------------------------------------------------------

CODIGO = ("app_core/x.py", 3, "  # conecta a Neon  ")
DOC = ("governance/apoyo/B.md", 10, "usa Neon")


def _p(*claves):
    c: Counter = Counter()
    for k in claves:
        c[k] += 1
    return {"NEON-01": c}


def test_m1_mencion_nueva_en_archivo_vigente_falla():
    assert evaluar([CODIGO], [], {}, set())
    assert not evaluar([CODIGO], [("app_core/x.py", "m")], {}, set())
    assert not evaluar([CODIGO], [], _p(clave(CODIGO[0], CODIGO[2])), set())


def test_m2_entrada_nueva_en_permitidos_falla():
    base = [("a.py", "m")]
    assert problemas_de_listas(base + [("b.py", "m")], {}, lambda _: True, permitidos_base=base)
    assert not problemas_de_listas(base, {}, lambda _: True, permitidos_base=base)


def test_m3_pendientes_de_id_desconocido_falla():
    errores = problemas_de_listas([], {"OTRA": Counter({("a.py", "x"): 1})}, lambda _: True)
    assert any("ID desconocido" in e for e in errores)


def test_m4_brief_cumplido_sin_retirar_la_linea_falla():
    fila = [("verificadores/README.md", "pendiente: brief NEON-04")]
    assert any("ya no contiene" in e for e in problemas_de_listas(fila, {}, lambda _: False))
    assert not problemas_de_listas(fila, {}, lambda _: True)


def test_documento_mover_lineas_no_falla_y_una_mas_si():
    permitido = _p(clave(DOC[0], ""))
    assert not evaluar([DOC], [], permitido, set())
    assert not evaluar([(DOC[0], 99, "otra redacción con Neon")], [], permitido, set())
    assert evaluar([DOC, (DOC[0], 11, "otra Neon")], [], permitido, set())


def test_codigo_editado_que_aun_menciona_falla():
    permitido = _p(clave(CODIGO[0], CODIGO[2]))
    assert not evaluar([(CODIGO[0], 77, CODIGO[2])], [], permitido, set())
    assert evaluar([(CODIGO[0], 3, "# conecta a Neon de otra forma")], [], permitido, set())


def test_mencion_que_desaparece_no_pone_rojo():
    permitido = _p(clave(DOC[0], ""), clave(CODIGO[0], CODIGO[2]))
    assert not evaluar([], [], permitido, set())


def test_recuento_por_pareja_y_no_crece():
    dos = [CODIGO, (CODIGO[0], 9, CODIGO[2])]
    assert evaluar(dos, [], _p(clave(CODIGO[0], CODIGO[2])), set())
    assert not evaluar(dos, [], _p(clave(CODIGO[0], CODIGO[2]), clave(CODIGO[0], CODIGO[2])), set())
    base, mas = _p(clave("a.py", "x")), _p(clave("a.py", "x"), clave("a.py", "x"))
    assert no_crece(mas, base)
    assert no_crece(_p(clave("b.py", "y")), base)
    assert not no_crece(base, mas)


def test_id_de_ficha_y_fichas_hechas_no_cuentan():
    ficha = [("governance/tareas/IA-08.md", 7, 'depende_de = ["NEON-02"]')]
    assert not evaluar(ficha, [], {}, set())
    proveedor = [("governance/tareas/IA-08.md", 7, "usa la base de Neon")]
    assert evaluar(proveedor, [], {}, set())
    assert not evaluar(proveedor, [], {}, {"governance/tareas/IA-08.md"})
    assert evaluar([("docs/x.md", 1, "NEON-02")], [], {}, set())


def test_formato_de_pendientes():
    c = leer_pendientes("# c\ngovernance/a.md|3\napp/x.py|texto uno\napp/x.py|texto uno\n")
    assert c[("governance/a.md", "")] == 3 and c[("app/x.py", "texto uno")] == 2


def test_listas_con_crlf_se_leen_igual():
    lf = "# c\ngovernance/a.md|3\napp/x.py|texto uno\n"
    assert leer_pendientes(lf.replace("\n", "\r\n")) == leer_pendientes(lf)
    perm = "a.py|motivo uno\nb.py|motivo dos\n"
    assert leer_permitidos(perm.replace("\n", "\r\n")) == leer_permitidos(perm)
