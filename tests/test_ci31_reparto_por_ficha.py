"""CI-31 · Reparto sin numeración global ni tabla de tandas compartida (especificaciones/CI-31.md §5).

Prueba de mutación documentada (cada mutación se aplica en la propia prueba y debe hacerla fallar):
  m1  perder o duplicar una línea de bloque al migrar → `test_migracion_sin_perdidas` (`_conservado` devuelve False).
  m2  leer «Sin agente» de la portada en lugar del campo `agente` → `test_r1_agente_ninguno` (R1 no se dispararía
      con una ficha que solo figura en la portada).
  m3  admitir la portada para cualquier ficha → `tests/test_verificar_alcance_pr.py`
      (`test_la_portada_solo_entra_en_el_alcance_de_su_dueña`).
Sin base de datos y sin `import yaml`.
"""
import importlib.util
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def _cargar(nombre: str):
    spec = importlib.util.spec_from_file_location(nombre, RAIZ / "scripts" / f"{nombre}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[nombre] = mod
    spec.loader.exec_module(mod)
    return mod


mig = _cargar("migrar_reparto_ci31")
rep = _cargar("verificar_reparto")
git = _cargar("generar_indice_tareas")


def _ficha(tid, estado="pendiente", extra=""):
    return (f'+++\nid = "{tid}"\ntitulo = "t {tid}"\nola = "backlog"\nestado = "{estado}"\nsala = "s"\n'
            f'depende_de = []\npropiedad = ["{tid.lower()}.py"]\narbitro = "pytest"\n{extra}+++\n\n# {tid}\n')


def _brief(bl, tid, tanda, cita=""):
    return (f"### {bl} · {tid.lower()}  (tanda {tanda})\n\n**Contexto.** Sala(s): `s`. Depende de: ninguna.\n\n"
            f"**Objetivo** (en este orden):\n\n1. `{tid}` — t {tid}\n\n{cita}**Escribe** (lista exclusiva):\n\n"
            f"  - `{tid.lower()}.py`\n\n**No hagas:**\n\n- nada\n")


PORTADA_ANTES = (
    "# Briefs\n\n## Preámbulo\n\n- regla cita BL-10 una vez\n\n## Tandas de lanzamiento\n\n| Tanda | Bloques |\n"
    "| 1 | BL-10 |\n\n## Briefs\n\nNOTA\n\n## Sin agente (por asignar)\n\n"
    "- `C-1` (esperando a la sala; BL-5)\n- decisión del propietario sobre plazos (OPS-01, BL-27)\n\n"
    "### Subsección\n\ntexto\n\n## No verificado\n\n- nada\n")


def _arbol_antes():
    briefs = {"A-1": _brief("BL-10", "A-1", 1), "B-1": _brief("BL-11", "B-1", 2, "Ver BL-10.\n\n")}
    fichas = {"A-1": _ficha("A-1"), "B-1": _ficha("B-1"), "C-1": _ficha("C-1"), "D-1": _ficha("D-1", "hecha")}
    return PORTADA_ANTES, briefs, fichas


def _lineas_de_bloque(briefs: dict[str, str]) -> Counter:
    return Counter(l for t in briefs.values() for l in t.splitlines() if l.strip() and not l.startswith("### "))


def _conservado(antes: dict[str, str], despues: dict[str, str], citas: dict[str, str]) -> bool:
    """Multiconjunto de líneas de bloque, salvo la cabecera, con las citas de id cambiadas."""
    esperado = Counter()
    for linea, n in _lineas_de_bloque(antes).items():
        for bl, ident in citas.items():
            linea = linea.replace(bl, ident)
        esperado[linea] += n
    return esperado == _lineas_de_bloque(despues)


def test_migracion_sin_perdidas():
    portada, briefs, fichas = _arbol_antes()
    nueva, nuevos, cambiadas, _ = mig.migrar(portada, briefs, fichas)
    citas = {"BL-10": "A-1", "BL-11": "B-1"}
    assert _conservado(briefs, nuevos, citas)
    assert nuevos["A-1"].startswith("### A-1 · ") and nuevos["B-1"].startswith("### B-1 · ")
    assert "Ver A-1." in nuevos["B-1"]
    # la línea de «Sin agente» que cita una ficha va a su cuerpo, y la otra a «Decisiones del propietario»
    assert set(cambiadas) == {"C-1"}
    assert "**Sin agente.** `C-1` (esperando a la sala; BL-5)" in cambiadas["C-1"]
    assert git.leer_cabecera(cambiadas["C-1"])["agente"] == "ninguno"
    assert "## Sin agente" not in nueva and "| 1 | BL-10 |" not in nueva
    assert "- decisión del propietario sobre plazos (OPS-01)" in nueva.split("## Decisiones del propietario", 1)[1]
    assert not re.search(r"BL-\d", nueva)
    assert "### Subsección" in nueva
    # m1: perder una línea, o duplicarla, rompe la conservación
    perdida = dict(nuevos, **{"A-1": nuevos["A-1"].replace("- nada\n", "")})
    duplicada = dict(nuevos, **{"A-1": nuevos["A-1"] + "- nada\n"})
    assert not _conservado(briefs, perdida, citas)
    assert not _conservado(briefs, duplicada, citas)


def test_migracion_idempotente():
    portada, briefs, fichas = _arbol_antes()
    nueva, nuevos, cambiadas, _ = mig.migrar(portada, briefs, fichas)
    fichas2 = dict(fichas, **cambiadas)
    n2, b2, c2, _ = mig.migrar(nueva, nuevos, fichas2)
    assert (n2, b2, c2) == (nueva, nuevos, {})


def test_migracion_rechaza_cita_huerfana():
    portada, briefs, fichas = _arbol_antes()
    briefs["B-1"] = briefs["B-1"].replace("Ver BL-10.", "Ver BL-999.")
    try:
        mig.migrar(portada, briefs, fichas)
    except ValueError as exc:
        assert "BL-999" in str(exc)
    else:
        raise AssertionError("una cita BL sin brief debe detener la migración")


def test_ids_de_bloque_son_ids_de_ficha():
    portada = (RAIZ / "governance/apoyo/BRIEFS_POR_BLOQUE.md").read_text(encoding="utf-8")
    assert not re.search(r"BL-\d", portada)
    for ruta in sorted((RAIZ / "governance/apoyo/briefs").glob("*.md")):
        texto = ruta.read_text(encoding="utf-8")
        assert not re.search(r"BL-\d", texto), ruta.name
        cabeceras = rep._CABECERA.findall(texto)
        assert [c[0] for c in cabeceras] == [ruta.stem], ruta.name


def _tarea(tid, agente="asignable", estado="pendiente"):
    return git.Tarea(id=tid, titulo=tid, ola="A", estado=estado, sala="s", depende_de=(), propiedad=(f"{tid}.py",),
                     arbitro="pytest", agente=agente)


def _bloque(bid, tanda, tid):
    return (f"### {bid} · n  (tanda {tanda})\n\n**Objetivo** (en este orden):\n\n1. `{tid}` — x\n\n"
            f"**Rastro ¤**\n\n**Escribe** (lista):\n\n  - `{tid}.py`\n\n**No hagas:**\n\n")


def test_r1_agente_ninguno():
    sin_nada = rep.revisar("", [_tarea("A-1")], git)
    assert sin_nada == ["R1 A-1: debe figurar en un solo bloque y figura en 0"]
    assert rep.revisar("", [_tarea("A-1", "ninguno")], git) == []
    con_brief = _bloque("A-1", 1, "A-1")
    assert rep.revisar(con_brief, [_tarea("A-1")], git) == []
    ambas = rep.revisar(con_brief, [_tarea("A-1", "ninguno")], git)
    assert ambas == ['R1 A-1: debe figurar en un solo bloque y figura en 2 (A-1, agente "ninguno")']
    assert rep.revisar(con_brief, [_tarea("A-1", estado="hecha")], git) == ["R1 A-1: está hecha y figura en A-1"]
    # m2: la portada ya no cuenta; una ficha que solo figura en «## Sin agente» sigue fallando
    en_portada = "## Sin agente (x)\n\n- `A-1`\n"
    assert rep.revisar(en_portada, [_tarea("A-1")], git) == ["R1 A-1: debe figurar en un solo bloque y figura en 0"]


def _porcelana():
    return subprocess.run(["git", "status", "--porcelain"], cwd=RAIZ, capture_output=True, text=True,
                          encoding="utf-8", check=True).stdout


def test_vista_de_tandas_sin_archivos():
    antes = _porcelana()
    res = subprocess.run([sys.executable, str(RAIZ / "scripts" / "verificar_reparto.py"), "--tandas"],
                         cwd=RAIZ, capture_output=True, text=True, encoding="utf-8")
    assert res.returncode == 0, res.stdout[-800:]
    tandas = [int(m.group(1)) for m in re.finditer(r"(?m)^Tanda (\d+): ", res.stdout)]
    assert tandas and tandas == sorted(set(tandas))
    assert res.stdout.rstrip().splitlines()[-1].startswith("REPARTO OK: ")
    assert _porcelana() == antes
    # la vista sale de las cabeceras: dos bloques de una tanda se agrupan y las tandas van en orden
    bloques = rep.leer_bloques(_bloque("B-1", 7, "B-1") + _bloque("A-1", 7, "A-1") + _bloque("C-1", 2, "C-1"))
    assert rep.vista_de_tandas(bloques) == ["Tanda 2: C-1", "Tanda 7: A-1, B-1"]
