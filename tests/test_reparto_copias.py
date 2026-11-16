"""REP-01: lo que cada bloque copia de sus fichas (Hecho si, Depende de, Objetivo y Sala(s)) coincide con ellas."""
import dataclasses
import importlib.util
import sys
from pathlib import Path

_RAIZ = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("verificar_reparto", _RAIZ / "scripts" / "verificar_reparto.py")
vr = importlib.util.module_from_spec(_spec)
sys.modules["verificar_reparto"] = vr
_spec.loader.exec_module(vr)
indice = vr._cargar_indice()


def _t(tid, sala="s", depende=(), estado="pendiente", arbitro="pytest tests/test_x.py", titulo=None):
    return indice.Tarea(id=tid, titulo=titulo or f"Título de {tid}", ola="A", estado=estado, sala=sala,
                        depende_de=tuple(depende), propiedad=(f"{tid}.py",), arbitro=arbitro)


def _bloque(bid, tanda, tareas, salas, depende, hecho=None):
    objetivo = "".join(f"{i}. `{t.id}` — {t.titulo}\n" for i, t in enumerate(tareas, 1))
    sala = "Sala(s): " + ", ".join(f"`{s}`" for s in salas)
    dep = ", ".join(f"`{d}` (pendiente)" for d in depende) or "ninguna"
    rutas = "".join(f"  - `{p}`\n" for t in tareas for p in t.propiedad)
    hecho = hecho if hecho is not None else [f"- `{t.id}`: {t.arbitro}\n" for t in tareas]
    return (f"### {bid} · nombre  (tanda {tanda})\n\n**Contexto.** {sala}. Depende de: {dep}. Especificaciones: `x.md`.\n\n"
            f"**Objetivo** (en este orden):\n\n{objetivo}\n**Rastro ¤**:\n\n**Escribe** (lista exclusiva):\n\n{rutas}\n"
            f"**No hagas:**\n\n- nada\n\n**Hecho si** (árbitro exógeno):\n\n{''.join(hecho)}"
            f"- `python scripts/generar_indice_tareas.py --verificar` con código 0.\n\n")


def _escenario():
    pend = _t("P-1", sala="pendiente")
    a = _t("A-1", sala="uno", depende=["P-1", "H-1"], arbitro="pytest tests/test_a.py; mutación 1")
    b = _t("A-2", sala="dos", depende=["A-1"], arbitro="pytest tests/test_b.py")
    hecha = _t("H-1", estado="hecha")
    tareas = [pend, a, b, hecha]
    briefs = (_bloque("BL-01", 0, [pend], ["pendiente"], [])
              + _bloque("BL-02", 1, [a, b], ["uno", "dos"], ["P-1"]))
    return briefs, tareas


def _cambia(tareas, i, **campos):
    """Las fichas son inmutables: devuelve una copia de la lista con la ficha i modificada."""
    return [dataclasses.replace(t, **campos) if k == i else t for k, t in enumerate(tareas)]


def _rN(briefs, tareas, regla):
    return [h for h in vr.revisar(briefs, tareas, indice) if h.startswith(regla)]


def test_el_escenario_correcto_no_da_hallazgos():
    briefs, tareas = _escenario()
    assert vr.revisar(briefs, tareas, indice) == []


def test_mutacion_1_cambiar_el_arbitro_sin_regenerar_falla_r6():
    briefs, tareas = _escenario()
    tareas = _cambia(tareas, 1, arbitro="pytest tests/test_a.py; mutación 2")
    assert _rN(briefs, tareas, "R6") == ["R6 BL-02: «Hecho si» de A-1 difiere del `arbitro` de su ficha"]


def test_mutacion_2_reintroducir_un_proveedor_retirado_falla_r6():
    briefs, tareas = _escenario()
    sucio = briefs.replace("pytest tests/test_b.py", "pytest tests/test_b.py contra una base remota de revisión")
    assert _rN(sucio, tareas, "R6") == ["R6 BL-02: «Hecho si» de A-2 difiere del `arbitro` de su ficha"]


def test_r6_falla_si_falta_o_sobra_una_linea():
    briefs, tareas = _escenario()
    sin = briefs.replace("- `A-2`: pytest tests/test_b.py\n", "")
    assert _rN(sin, tareas, "R6") == ["R6 BL-02: falta la línea «Hecho si» de A-2"]
    de_mas = briefs.replace("- `A-2`: pytest tests/test_b.py\n", "- `A-2`: pytest tests/test_b.py\n- `Z-9`: algo\n")
    assert _rN(de_mas, tareas, "R6") == ["R6 BL-02: «Hecho si» trae Z-9, que no está en el «Objetivo»"]


def test_r6_normaliza_espacios():
    briefs, tareas = _escenario()
    assert _rN(briefs.replace("pytest tests/test_b.py", "pytest   tests/test_b.py "), tareas, "R6") == []


def test_mutacion_3_quitar_una_dependencia_pendiente_falla_r7():
    briefs, tareas = _escenario()
    sin = briefs.replace("Depende de: `P-1` (pendiente).", "Depende de: ninguna.")
    assert _rN(sin, tareas, "R7") == ["R7 BL-02: «Depende de» no cita P-1, pendiente y ajena al bloque"]


def test_r7_no_exige_hechas_ni_las_del_mismo_bloque_y_citar_de_mas_solo_avisa():
    briefs, tareas = _escenario()
    assert _rN(briefs, tareas, "R7") == []  # H-1 hecha y A-1 en el mismo bloque no se exigen
    de_mas = briefs.replace("Depende de: `P-1` (pendiente).", "Depende de: `P-1` (pendiente), `H-1`.")
    assert _rN(de_mas, tareas, "R7") == []
    bloques = vr.leer_bloques(de_mas)
    _, avisos = vr.revisar_copias(bloques, {t.id: t for t in tareas})
    assert avisos == ["BL-02: «Depende de» cita H-1, que ninguna task del bloque necesita ahora"]


def test_mutacion_4_cambiar_el_titulo_en_la_ficha_falla_r8():
    briefs, tareas = _escenario()
    tareas = _cambia(tareas, 2, titulo="Otro título")
    assert _rN(briefs, tareas, "R8") == ["R8 BL-02: el título de A-2 en «Objetivo» difiere del de su ficha"]


def test_r8_las_salas_son_la_union_de_las_de_sus_tasks():
    briefs, tareas = _escenario()
    assert _rN(briefs.replace("`uno`, `dos`", "`uno`"), tareas, "R8")
    assert _rN(briefs.replace("`uno`, `dos`", "`uno`, `dos`, `tres`"), tareas, "R8")
    tareas = _cambia(_cambia(tareas, 1, sala="uno, dos"), 2, sala="uno")  # una ficha con dos salas en un campo
    assert _rN(briefs, tareas, "R8") == []


def test_mutacion_5_regenerar_deja_el_bloque_igual_al_arbitro_y_es_idempotente():
    briefs, tareas = _escenario()
    viejo = briefs.replace("pytest tests/test_b.py", "pytest tests/test_b.py contra la base remota").replace(
        "- `A-1`: pytest tests/test_a.py; mutación 1\n", "- `Z-9`: sobra\n")
    assert _rN(viejo, tareas, "R6")
    nuevo = vr.regenerar(viejo, tareas)
    assert _rN(nuevo, tareas, "R6") == []
    assert nuevo == briefs  # incluye la línea faltante, quita la sobrante y conserva la línea del verificador
    assert vr.regenerar(nuevo, tareas) == nuevo


def test_regenerar_conserva_los_saltos_de_linea_crlf():
    briefs, tareas = _escenario()
    crlf = briefs.replace("\n", "\r\n").replace("pytest tests/test_b.py", "viejo")
    nuevo = vr.regenerar(crlf, tareas)
    assert "\n" not in nuevo.replace("\r\n", "")
    assert "- `A-2`: pytest tests/test_b.py\r\n" in nuevo


def test_el_documento_real_regenerado_cumple_r6():
    tareas, errores = indice.cargar_tareas()
    assert errores == []
    crudo = vr.BRIEFS.read_bytes().decode("utf-8")
    nuevo = vr.regenerar(crudo, tareas)
    assert [h for h in vr.revisar(nuevo.replace("\r\n", "\n"), tareas, indice) if h.startswith("R6")] == []
    assert vr.regenerar(nuevo, tareas) == nuevo
