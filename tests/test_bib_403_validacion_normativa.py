# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤adpa ¤regulation-code ¤cita-verificada ¤arbitro
# ¤¤qa-engineer
"""BIB-403: validación normativa de las plantillas. Parte pura (sin base de datos).

Cubre R1 (ida y vuelta), R2/R3 (validación derivada de la huella) y R8 (cita por sección). Lo que necesita
PostgreSQL (compuerta R4 en el flujo editorial, carga con ficha R6) va en el bloque marcado más abajo y
corre en el CI.

Mutaciones (una a una, con el archivo restaurado):
- m1: añadir «LOPDP art. 99» a un cuerpo da rojo en `test_m1_cita_sin_fila_falla_la_ida`.
- m2: asignar una clave a una plantilla que no la cita da rojo en `test_m2_clave_asignada_y_no_citada_falla_la_vuelta`.
- m3: tratar `no_leida` como verificada da rojo en `test_m3_no_leida_no_es_verificada`.
- m4: ignorar la huella da rojo en `test_m4_otra_huella_del_modulo_pasa_a_en_revision`.
- m9: contar las citas de toda la plantilla en vez de por sección da rojo en `test_m9_seccion_sin_cita_falla`.
- m10: no comprobar que el título informativo exista da rojo en `test_m10_titulo_informativo_inexistente_falla`.
"""
from __future__ import annotations

from features.biblioteca.domain.validacion import (
    errores_ida, errores_secciones, errores_vuelta, extraer_citas, secciones, validacion_normativa,
)

ESTADOS = {
    "LOPDP-art-7": "verificada", "LOPDP-art-8": "verificada", "LOPDP-art-10": "verificada",
    "LOPDP-art-10-lit-i": "verificada", "RLOPDP-art-8": "verificada", "RLOPDP-art-9": "verificada",
    "RES-2025-0006-art-4": "verificada", "RES-2025-0028-art-10": "no_leida",
}
VERIFICADAS = {c for c, e in ESTADOS.items() if e == "verificada"}
FUENTE_DE = {"LOPDP-art-7": "LOPDP-RO459", "LOPDP-art-8": "LOPDP-RO459", "RLOPDP-art-8": "RGLOPDP-RO435"}
LEIDAS = {"LOPDP-RO459": "aa", "RGLOPDP-RO435": "bb"}


def test_extrae_claves_atomicas_de_las_formas_de_las_plantillas():
    claves, sin_norma = extraer_citas("(LOPDP art. 10 i ; Reglamento arts. 8 y 9)")
    assert claves == {"LOPDP-art-10", "LOPDP-art-10-lit-i", "RLOPDP-art-8", "RLOPDP-art-9"} and not sin_norma
    claves, _ = extraer_citas("LOPDP arts. 55 a 60")
    assert claves == {f"LOPDP-art-{n}" for n in range(55, 61)}
    claves, _ = extraer_citas("(Resolución SPDP-SPD-2025-0006-R, art. 4.10)")
    assert claves == {"RES-2025-0006-art-4", "RES-2025-0006-art-4-num-10"}
    claves, _ = extraer_citas("términos del art. 62 de la LOPDP")
    assert claves == {"LOPDP-art-62"}
    claves, _ = extraer_citas("(Res. 2025-0041, arts. 4 y 5)")
    assert claves == {"RES-2025-0041-art-4", "RES-2025-0041-art-5"}


def test_art_sin_norma_se_informa():
    claves, sin_norma = extraer_citas("Se notifica en los plazos del art. 43.")
    assert not claves and sin_norma == ["art. 43"]


def test_la_reforma_del_art_43_es_su_propia_clave():
    claves, _ = extraer_citas("LOPDP (RO 5S 459; art. 43 reformado por la Ley X, RO 5S 290, 2026) arts. 7, 43")
    assert "LOPDP-art-43-reforma-RO-5S-290" in claves and {"LOPDP-art-7", "LOPDP-art-43"} <= claves


def test_ida_pasa_con_filas_verificadas():
    assert errores_ida({"LOPDP-art-7", "RLOPDP-art-8", "RES-2025-0006-art-4-num-10"}, ESTADOS) == []


def test_m1_cita_sin_fila_falla_la_ida():
    claves, _ = extraer_citas("Aplica la LOPDP art. 99.")
    assert errores_ida(claves, ESTADOS) == ["cita sin fila en CITAS_PLANTILLAS_VERIFICADAS: LOPDP-art-99"]


def test_m3_no_leida_no_es_verificada():
    claves, _ = extraer_citas("(Resolución SPDP-SPD-2025-0028-R, art. 10)")
    assert errores_ida(claves, ESTADOS) == ["cita RES-2025-0028-art-10 con lectura «no_leida»"]


def test_m2_clave_asignada_y_no_citada_falla_la_vuelta():
    assert errores_vuelta({"LOPDP-art-7", "LOPDP-art-99"}, {"LOPDP-art-7"}) == [
        "clave asignada y no citada en la plantilla: LOPDP-art-99"]
    assert errores_vuelta({"LOPDP-art-7"}, {"LOPDP-art-7", "LOPDP-art-8"}) == [
        "clave citada y no asignada en citas.json: LOPDP-art-8"]
    assert errores_vuelta({"LOPDP-art-7"}, {"LOPDP-art-7"}) == []


CUERPO = """# Título

## 1. Datos de contacto
Teléfono y correo.

## 2. Base
Se trata con consentimiento (LOPDP art. 8).

### 2.1 Conservación
Se elimina al cumplirse la finalidad (Reglamento art. 8).
"""


def test_secciones_por_encabezado():
    assert [t for t, _ in secciones(CUERPO)] == ["1. Datos de contacto", "2. Base", "2.1 Conservación"]


def test_r8_pasa_con_la_informativa_declarada():
    assert errores_secciones(CUERPO, ["1. Datos de contacto"], VERIFICADAS) == []


def test_m9_seccion_sin_cita_falla():
    # Aunque la plantilla cite en otras secciones, la sección sin cita y no declarada falla.
    assert errores_secciones(CUERPO, [], VERIFICADAS) == ["sección «1. Datos de contacto» sin cita verificada"]


def test_r8_una_cita_no_leida_no_cuenta_para_la_seccion():
    cuerpo = "## 1. Delegado\nNo se designa (Resolución SPDP-SPD-2025-0028-R, art. 10).\n"
    assert errores_secciones(cuerpo, [], VERIFICADAS) == ["sección «1. Delegado» sin cita verificada"]


def test_m10_titulo_informativo_inexistente_falla():
    assert errores_secciones(CUERPO, ["1. Datos de contacto", "9. No existe"], VERIFICADAS) == [
        "secciones_informativas: el título «9. No existe» no existe en el cuerpo"]


def test_r8_una_seccion_informativa_con_cita_falla():
    assert errores_secciones(CUERPO, ["1. Datos de contacto", "2. Base"], VERIFICADAS) == [
        "sección informativa «2. Base» con cita: tiene efecto jurídico"]


def test_r3_validada_con_todas_verificadas_y_sin_version_en_el_modulo():
    claves = {"LOPDP-art-7", "RLOPDP-art-8"}
    assert validacion_normativa(claves, ESTADOS, FUENTE_DE, LEIDAS, {}) == "validada"
    assert validacion_normativa(claves, ESTADOS, FUENTE_DE, LEIDAS, {"LOPDP-RO459": "aa"}) == "validada"


def test_m4_otra_huella_del_modulo_pasa_a_en_revision():
    claves = {"LOPDP-art-7", "RLOPDP-art-8"}
    assert validacion_normativa(claves, ESTADOS, FUENTE_DE, LEIDAS, {"LOPDP-RO459": "zz"}) == "en_revision"


def test_r3_pendiente_si_falta_una_cita_verificada():
    assert validacion_normativa({"LOPDP-art-7", "RES-2025-0028-art-10"}, ESTADOS, FUENTE_DE, LEIDAS, {}) == "pendiente"
    assert validacion_normativa({"LOPDP-art-99"}, ESTADOS, FUENTE_DE, LEIDAS, {}) == "pendiente"
    assert validacion_normativa(set(), ESTADOS, FUENTE_DE, LEIDAS, {}) == "pendiente"


def test_r3_con_observaciones_por_cita_no_encontrada():
    estados = {**ESTADOS, "LOPDP-art-77": "no_encontrada"}
    assert validacion_normativa({"LOPDP-art-7", "LOPDP-art-77"}, estados, FUENTE_DE, LEIDAS, {}) == "con_observaciones"


def test_validar_plantilla_md_rechaza_informativas_mal_declaradas():
    from features.biblioteca.domain.plantillas_md import validar_plantilla_md
    from pathlib import Path
    texto = Path("data/biblioteca/pmv/BIB-007.md").read_bytes().decode("utf-8")
    marca = "quedan marcas de borrador"  # BIB-007 conserva la marca 7 de LEG-08 hasta decidirla
    assert [f for f in validar_plantilla_md(texto, "BIB-007") if f != marca] == []
    inexistente = texto.replace("  - titulo: 1. Objeto\n", "  - titulo: 9. No existe\n")
    assert any("no existe en el cuerpo" in f for f in validar_plantilla_md(inexistente, "BIB-007"))
    con_cita = texto.replace("  - titulo: 1. Objeto\n", "  - titulo: 1. Objeto\n  - titulo: 2. Derechos que se pueden ejercer\n")
    assert [f for f in validar_plantilla_md(con_cita, "BIB-007") if f != marca] == [
        "sección informativa «2. Derechos que se pueden ejercer» con cita: tiene efecto jurídico"]


def test_m7_pendiente_validacion_es_marca_de_borrador():
    from features.biblioteca.domain.plantillas_md import MARCAS_BORRADOR, validar_plantilla_md
    from pathlib import Path
    assert "PENDIENTE VALIDACIÓN" in MARCAS_BORRADOR
    texto = Path("data/biblioteca/pmv/BIB-007.md").read_bytes().decode("utf-8")
    assert "quedan marcas de borrador" in validar_plantilla_md(texto, "BIB-007")  # conserva la marca 7 (LEG-08)
    limpio = texto.replace("PENDIENTE VALIDACIÓN", "x")
    assert "quedan marcas de borrador" not in validar_plantilla_md(limpio, "BIB-007")


def test_r6_fichas_json_cubre_las_doce_con_el_contrato_ficha():
    from pathlib import Path
    from features.biblioteca.services.plantillas_md import CODIGOS, leer_fichas
    fichas = leer_fichas(Path("."))
    assert set(fichas) == set(CODIGOS)
    assert all(f["restricciones"] and f["fecha_revision"] for f in fichas.values())


def test_r6_script_de_carga_pasa_la_ficha_m8():
    # m8: si _aplicar dejara de pasar la ficha, publicar daría BIB_PUBLICACION_INCOMPLETA (el flujo con base va al CI).
    import inspect
    from features.biblioteca.services import plantillas_md
    assert "ficha=paso[\"ficha\"]" in inspect.getsource(plantillas_md._aplicar)


def test_r6_entorno_produccion_con_url_local_es_codigo_2(monkeypatch, capsys):
    import importlib
    cargar = importlib.import_module("scripts.cargar_plantillas_pmv")
    monkeypatch.setenv("BIB109_DATABASE_URL", "postgresql+asyncpg://u:p@localhost:5432/x")
    codigo = cargar.main(["--cargar", "--actor", "u", "--entorno", "produccion", "--confirmar-entorno"])
    assert codigo == 2 and "localhost" not in capsys.readouterr().out
    codigo = cargar.main(["--cargar", "--actor", "u", "--entorno", "local"])
    assert codigo == 2  # sin --confirmar-entorno
