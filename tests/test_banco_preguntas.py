"""Test de validación del banco canónico de 80 preguntas del SGPDP (DIAG-02).

Invariantes validadas:
- 80 identificadores únicos del 1 al 80 correlativos.
- Distribución canónica de preguntas en las 10 dimensiones (D01 a D10).
- Criticidad en rango 1 a 5 para todas las preguntas.
- Tallas mínimas válidas dentro del vocabulario ('micro', 'pequena', 'mediana', 'corporativo').
- Exactamente los 4 controles estructurales habilitadores (9, 10, 13, 28) marcados.
- Ningún texto requerido vacío (control, enunciado, referenciaNormativa, evidenciaEsperada, ejemplo).
- Sincronización exacta con el script exportador y el banco del frontend.
"""
import json
import subprocess
from pathlib import Path

from features.diagnostico.services.engine import cargar_banco_preguntas_raw, normalizar_tamano
from features.diagnostico.services.dimensiones_sgpdp import obtener_controles_estructurales

RUTA_BANCO_JSON = (
    Path(__file__).resolve().parent.parent
    / "features"
    / "diagnostico"
    / "domain"
    / "banco_preguntas.json"
)

TALLAS_VALIDAS = {"micro", "pequena", "mediana", "corporativo"}
DIMENSIONES_VALIDAS = {f"D{i:02d}" for i in range(1, 11)}


def test_banco_preguntas_json_existe_y_tiene_80_preguntas():
    assert RUTA_BANCO_JSON.exists(), f"El archivo {RUTA_BANCO_JSON} no existe."
    banco = cargar_banco_preguntas_raw()
    assert isinstance(banco, list), "El banco debe ser una lista JSON."
    assert len(banco) == 80, f"El banco debe contener exactamente 80 preguntas, tiene {len(banco)}."


def test_ids_unicos_y_correlativos_1_a_80():
    banco = cargar_banco_preguntas_raw()
    ids = [p["id"] for p in banco]
    assert len(ids) == len(set(ids)), "Existen identificadores duplicados en el banco."
    assert ids == list(range(1, 81)), "Los ids deben ser enteros correlativos del 1 al 80."


def test_distribucion_preguntas_por_dimension():
    banco = cargar_banco_preguntas_raw()
    conteo_dimensiones = {}
    for p in banco:
        dim = p.get("dimensionId")
        assert dim in DIMENSIONES_VALIDAS, f"Dimensión inválida: {dim} en pregunta {p.get('id')}"
        conteo_dimensiones[dim] = conteo_dimensiones.get(dim, 0) + 1

    assert len(conteo_dimensiones) == 10, "Deben existir exactamente 10 dimensiones D01-D10."
    # D03 tiene 6 preguntas y D04 tiene 10 preguntas; las demás tienen 8 preguntas cada una. Total = 80.
    for dim, cantidad in conteo_dimensiones.items():
        assert cantidad >= 6, f"La dimensión {dim} tiene una cantidad sospechosamente baja: {cantidad}"
    assert conteo_dimensiones["D03"] == 6
    assert conteo_dimensiones["D04"] == 10
    for d in ["D01", "D02", "D05", "D06", "D07", "D08", "D09", "D10"]:
        assert conteo_dimensiones[d] == 8, f"Dimensión {d} se esperaba con 8 preguntas, tiene {conteo_dimensiones[d]}"


def test_criticidad_y_tallas_validas():
    banco = cargar_banco_preguntas_raw()
    for p in banco:
        crit = p.get("criticidad")
        assert isinstance(crit, int) and 1 <= crit <= 5, (
            f"Pregunta {p.get('id')} tiene criticidad inválida: {crit}"
        )

        talla = p.get("tamanoMinimo")
        assert talla in TALLAS_VALIDAS, (
            f"Pregunta {p.get('id')} tiene talla mínima inválida: {talla}"
        )


def test_controles_estructurales_habilitadores():
    banco = cargar_banco_preguntas_raw()
    estructurales_banco = {p["id"] for p in banco if p.get("esEstructural")}
    
    # Del catálogo oficial en backend
    estructurales_cat = {c.pregunta_id for c in obtener_controles_estructurales()}
    assert estructurales_cat == {9, 10, 13, 28}, "Los estructurales deben ser 9, 10, 13 y 28."
    assert estructurales_banco == {9, 10, 13, 28}, (
        f"Controles estructurales en banco difieren: {estructurales_banco} vs {estructurales_cat}"
    )


def test_textos_requeridos_no_vacios():
    banco = cargar_banco_preguntas_raw()
    campos_requeridos = [
        "control",
        "enunciado",
        "referenciaNormativa",
        "evidenciaEsperada",
        "ejemplo",
    ]
    for p in banco:
        for campo in campos_requeridos:
            val = p.get(campo)
            assert isinstance(val, str) and val.strip(), (
                f"Campo {campo} vacío o no string en pregunta {p.get('id')}"
            )


def test_script_verificador_exportar_banco_preguntas_exitoso():
    script_path = Path(__file__).resolve().parent.parent / "scripts" / "exportar_banco_preguntas.mjs"
    res = subprocess.run(
        ["node", str(script_path), "--verificar"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, f"node exportar_banco_preguntas.mjs --verificar falló:\n{res.stderr}\n{res.stdout}"
    assert "80 controles" in res.stdout
