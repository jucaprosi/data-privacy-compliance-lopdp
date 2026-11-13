# ¤¤qa-engineer
# ¤diagnostico
"""DIAG-16: cada cita normativa del banco de preguntas está contrastada con el texto oficial.

Árbitros:
- `test_referencias_backend_igual_frontend`: la referencia de cada pregunta es la misma en el JSON del
  servidor y en los bloques TypeScript del frontend.
- `test_sin_art47_num3_capacitacion`: ninguna pregunta cita el art. 47 numeral 3 (verificación de la
  eficacia de las medidas) como base de la capacitación del personal, ni la cadena de P73 vuelve.
- `test_citas_atomicas_en_citas_verificadas`: cada artículo (y numeral) de la LOPDP citado en el banco
  tiene su fila en `governance/artefactos/CITAS_LEGALES_VERIFICADAS.md`.
- `test_contraste_cubre_todas`: cada referencia del banco aparece literal en
  `governance/apoyo/CONTRASTE_REFERENCIAS_BANCO.md`.

Mutación: volver a poner «LOPDP Art. 47 numeral 3 (Capacitación) y Art. 10 (Responsabilidad Proactiva)»
en P73 (bloque3.ts y el JSON) pone en rojo `test_sin_art47_num3_capacitacion` y `test_contraste_cubre_todas`.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
RUTA_JSON = RAIZ / "features" / "diagnostico" / "domain" / "banco_preguntas.json"
RUTAS_TS = [RAIZ / "frontend" / "src" / "lib" / "bancoPreguntas" / f"bloque{i}.ts" for i in (1, 2, 3)]
RUTA_CITAS = RAIZ / "governance" / "artefactos" / "CITAS_LEGALES_VERIFICADAS.md"
RUTA_CONTRASTE = RAIZ / "governance" / "apoyo" / "CONTRASTE_REFERENCIAS_BANCO.md"

_ART = re.compile(r"Art\.\s*(\d+)(?:\s+numeral\s+(\d+))?(?:\s+al\s+(\d+))?")
_TS_PREGUNTA = re.compile(
    r"id:\s*(\d+),.*?referenciaNormativa:\s*\"((?:[^\"\\]|\\.)*)\"", re.DOTALL
)
_CLAVE_CITA = re.compile(r"`(LOPDP-art-\d+(?:-num-\d+)?)`")


def _banco() -> list[dict]:
    return json.loads(RUTA_JSON.read_text(encoding="utf-8"))


def _referencias_ts() -> dict[int, str]:
    refs: dict[int, str] = {}
    for ruta in RUTAS_TS:
        for m in _TS_PREGUNTA.finditer(ruta.read_text(encoding="utf-8")):
            refs[int(m.group(1))] = json.loads(f'"{m.group(2)}"')
    return refs


def claves_lopdp(referencia: str) -> set[str]:
    """Citas atómicas de la LOPDP en una referencia: `LOPDP-art-N` y `LOPDP-art-N-num-M`."""
    claves: set[str] = set()
    for m in _ART.finditer(referencia):
        desde, numeral, hasta = int(m.group(1)), m.group(2), m.group(3)
        for art in range(desde, int(hasta or desde) + 1):
            claves.add(f"LOPDP-art-{art}")
        if numeral:
            claves.add(f"LOPDP-art-{desde}-num-{numeral}")
    return claves


def test_referencias_backend_igual_frontend():
    ts = _referencias_ts()
    banco = _banco()
    assert len(ts) == len(banco) == 80
    distintas = [p["id"] for p in banco if ts.get(p["id"]) != p["referenciaNormativa"]]
    assert not distintas, f"Referencias distintas entre servidor y frontend: {distintas}"


def test_sin_art47_num3_capacitacion():
    textos = [p["referenciaNormativa"] for p in _banco()] + list(_referencias_ts().values())
    culpables = [t for t in textos if re.search(r"Art\.\s*47\s+numeral\s+3\b", t)]
    assert not culpables, f"El art. 47 num. 3 no trata de la capacitación: {culpables}"


def test_citas_atomicas_en_citas_verificadas():
    registradas = set(_CLAVE_CITA.findall(RUTA_CITAS.read_text(encoding="utf-8")))
    faltan = sorted(
        {c for p in _banco() for c in claves_lopdp(p["referenciaNormativa"])} - registradas
    )
    assert not faltan, f"Citas del banco sin fila en CITAS_LEGALES_VERIFICADAS.md: {faltan}"


def test_contraste_cubre_todas():
    contraste = RUTA_CONTRASTE.read_text(encoding="utf-8")
    faltan = [p["id"] for p in _banco() if p["referenciaNormativa"] not in contraste]
    assert not faltan, f"Preguntas sin contraste en CONTRASTE_REFERENCIAS_BANCO.md: {faltan}"


def test_extractor_de_claves():
    assert claves_lopdp("LOPDP Art. 22 al 24 y Art. 30") == {
        "LOPDP-art-22", "LOPDP-art-23", "LOPDP-art-24", "LOPDP-art-30"
    }
    assert claves_lopdp("LOPDP Art. 7 numeral 8 (Interés legítimo)") == {
        "LOPDP-art-7", "LOPDP-art-7-num-8"
    }
