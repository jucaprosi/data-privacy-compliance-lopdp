# -*- coding: utf-8 -*-
# ¤gemini-vertex ¤arbitro
"""IA-11: conjunto fijo de evaluación de prompts y modelos.

Uso (compuerta humana del propietario; gasta Vertex y usa sus credenciales de GCP, el CI nunca lo ejecuta):

    python scripts/evaluar_ia.py <prompt_id> <version> <modelo> --org-id <organizacion_de_evaluacion> --confirmar

Los casos viven en `evaluacion/ia/casos/<prompt_id>.json` (ficticios, sin datos personales). El resultado se escribe en
`evaluacion/ia/resultados/<prompt_id>_v<n>_<modelo>.json` con puntaje, fecha y `modelo_version`. La llamada pasa
siempre por la compuerta `inferencia_service.generar_trazado` y consume el tope de la organización indicada.

Las funciones puras de abajo (descubrimiento, puntaje y comprobación de resultados) las usa también la prueba del CI,
que no llama a Vertex.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import importlib.util
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from pydantic import BaseModel, ConfigDict  # noqa: E402

CASOS = Path("evaluacion") / "ia" / "casos"
RESULTADOS = Path("evaluacion") / "ia" / "resultados"
_CITA = re.compile(r"\b(?:art\.?|artículo|articulo)\s*\d+", re.IGNORECASE)
_NUMERO = re.compile(r"\d+(?:[.,]\d+)?")


class RespuestaLibre(BaseModel):
    """Esquema por omisión: acepta cualquier objeto JSON; los criterios del caso son los que puntúan."""

    model_config = ConfigDict(extra="allow")


# --------------------------------------------------------------------------- descubrimiento

def modulos_de_prompts(raiz: Path) -> list[tuple[str, object]]:
    """(sala, módulo) de cada `<raiz>/features/<sala>/ai/prompts.py`."""
    salida = []
    for archivo in sorted((raiz / "features").glob("*/ai/prompts.py")):
        sala = archivo.parent.parent.name
        spec = importlib.util.spec_from_file_location(f"_ia11_prompts_{sala}_{abs(hash(str(raiz)))}", archivo)
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)
        salida.append((sala, modulo))
    return salida


def vigentes(raiz: Path) -> list[tuple[str, int]]:
    """(prompt_id, versión) de cada `VIGENTE` declarado. `VIGENTE` puede ser una versión o un dict `{id: versión}`."""
    encontrados: list[tuple[str, int]] = []
    for _, modulo in modulos_de_prompts(raiz):
        versiones = getattr(modulo, "VERSIONES", {})
        vigente = getattr(modulo, "VIGENTE", None)
        if isinstance(vigente, dict):
            encontrados.extend((str(i), int(v)) for i, v in vigente.items())
        elif isinstance(vigente, int) and vigente in versiones:
            encontrados.append((versiones[vigente].id, vigente))
    return sorted(set(encontrados))


def buscar_prompt(raiz: Path, prompt_id: str, version: int):
    """(PromptVersionado, esquema) de `(prompt_id, version)` o None."""
    for _, modulo in modulos_de_prompts(raiz):
        for p in getattr(modulo, "VERSIONES", {}).values():
            if p.id == prompt_id and p.version == version:
                esquemas = getattr(modulo, "ESQUEMAS", {})
                return p, esquemas.get(prompt_id, RespuestaLibre)
    return None


# --------------------------------------------------------------------------- casos y puntaje

def ruta_casos(raiz: Path, prompt_id: str) -> Path:
    return raiz / CASOS / f"{prompt_id}.json"


def huella_casos(raiz: Path, prompt_id: str) -> str:
    return hashlib.sha256(ruta_casos(raiz, prompt_id).read_bytes()).hexdigest()


def cargar_casos(raiz: Path, prompt_id: str) -> list[dict]:
    datos = json.loads(ruta_casos(raiz, prompt_id).read_text(encoding="utf-8"))
    if datos.get("prompt_id") != prompt_id or not datos.get("casos"):
        raise ValueError(f"casos de {prompt_id} mal formados")
    return datos["casos"]


def _textos(valor) -> list[str]:
    if isinstance(valor, str):
        return [valor]
    if isinstance(valor, dict):
        return [t for v in valor.values() for t in _textos(v)]
    if isinstance(valor, (list, tuple)):
        return [t for v in valor for t in _textos(v)]
    if isinstance(valor, bool) or valor is None:
        return []
    return [str(valor)]


def _numeros(valor) -> set[str]:
    return {n.replace(",", ".") for t in _textos(valor) for n in _NUMERO.findall(t)}


def puntuar_caso(caso: dict, salida: dict | None) -> float:
    """Fracción de criterios cumplidos (0..1). Sin salida válida, 0."""
    if not isinstance(salida, dict):
        return 0.0
    criterios = caso.get("criterios", {})
    pruebas: list[bool] = []
    obligatorios = criterios.get("campos_obligatorios", [])
    if obligatorios:
        pruebas.append(all(salida.get(c) not in (None, "", [], {}) for c in obligatorios))
    if criterios.get("cita_presente"):
        pruebas.append(any(_CITA.search(t) for t in _textos(salida)))
    if criterios.get("sin_cifras_inventadas"):
        permitidas = _numeros(caso.get("valores", {})) | {str(c) for c in criterios.get("cifras_permitidas", [])}
        pruebas.append(_numeros(salida) <= permitidas)
    return sum(pruebas) / len(pruebas) if pruebas else 0.0


def puntuar(casos: list[dict], salidas: list[dict | None]) -> float:
    return round(sum(puntuar_caso(c, s) for c, s in zip(casos, salidas)) / len(casos), 4)


# --------------------------------------------------------------------------- resultados

def ruta_resultado(raiz: Path, prompt_id: str, version: int, modelo: str) -> Path:
    return raiz / RESULTADOS / f"{prompt_id}_v{version}_{modelo}.json"


def leer_resultado(raiz: Path, prompt_id: str, version: int, modelo: str) -> dict | None:
    ruta = ruta_resultado(raiz, prompt_id, version, modelo)
    return json.loads(ruta.read_text(encoding="utf-8")) if ruta.is_file() else None


def problemas_de_resultados(raiz: Path, modelos: frozenset[str]) -> list[str]:
    """Incumplimientos de IA-11 sin red: resultado faltante, puntaje menor al anterior o casos cambiados."""
    problemas: list[str] = []
    for prompt_id, version in vigentes(raiz):
        usados = sorted(
            m for m in modelos if any(ruta_resultado(raiz, prompt_id, v, m).is_file() for v in range(1, version + 1))
        )
        if not usados:
            problemas.append(f"{prompt_id}@{version}: sin ningún resultado de evaluación")
            continue
        for modelo in usados:
            actual = leer_resultado(raiz, prompt_id, version, modelo)
            if actual is None:
                problemas.append(f"{prompt_id}@{version} {modelo}: falta el resultado")
                continue
            if ruta_casos(raiz, prompt_id).is_file() and actual.get("huella_casos") != huella_casos(raiz, prompt_id):
                problemas.append(f"{prompt_id}@{version} {modelo}: los casos cambiaron desde la evaluación")
            previas = [
                r for v in range(version - 1, 0, -1) if (r := leer_resultado(raiz, prompt_id, v, modelo)) is not None
            ]
            if previas and actual.get("puntaje", 0) < previas[0].get("puntaje", 0):
                problemas.append(f"{prompt_id}@{version} {modelo}: puntaje menor que el de la versión anterior")
    return problemas


# --------------------------------------------------------------------------- corrida contra Vertex

async def evaluar(raiz: Path, prompt_id: str, version: int, modelo: str, org_id: str) -> dict:
    """Corre los casos por la compuerta de inferencia (traza y tope incluidos) y devuelve el resultado."""
    from features.inferencia import inferencia_service as gate

    hallado = buscar_prompt(raiz, prompt_id, version)
    if hallado is None:
        raise SystemExit(f"No existe el prompt {prompt_id} en la versión {version}.")
    prompt, esquema = hallado
    casos = cargar_casos(raiz, prompt_id)
    salidas: list[dict | None] = []
    versiones: set[str] = set()
    for caso in casos:
        try:
            resultado, traza = await gate.generar_trazado(
                prompt, caso["valores"], esquema, modelo=modelo, org_id=org_id
            )
            salidas.append(resultado.model_dump())
            versiones.add(traza.modelo_version)
        except gate.InferenciaNoDisponible:
            salidas.append(None)
    if len(versiones) != 1:
        raise SystemExit("Vertex no devolvió una única modelo_version; no se escribe resultado.")
    return {
        "prompt_id": prompt_id,
        "version": version,
        "modelo": modelo,
        "modelo_version": versiones.pop(),
        "puntaje": puntuar(casos, salidas),
        "casos_evaluados": len(casos),
        "huella_casos": huella_casos(raiz, prompt_id),
        "fecha": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def main(argv: list[str] | None = None, raiz: Path = RAIZ) -> int:
    from features.inferencia.domain.modelos_permitidos import MODELOS_PERMITIDOS

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("prompt_id")
    ap.add_argument("version", type=int)
    ap.add_argument("modelo")
    ap.add_argument("--org-id", required=True, help="organización de evaluación cuyo tope se consume")
    ap.add_argument("--confirmar", action="store_true", help="acepta gastar las generaciones anunciadas")
    args = ap.parse_args(argv)
    if args.modelo not in MODELOS_PERMITIDOS:
        print(f"Modelo no permitido: {args.modelo}. Permitidos: {', '.join(sorted(MODELOS_PERMITIDOS))}")
        return 2
    casos = cargar_casos(raiz, args.prompt_id)
    print(f"Va a gastar {len(casos)} generaciones del tope de la organización {args.org_id} con {args.modelo}.")
    if not args.confirmar:
        print("Sin --confirmar no se llama a Vertex.")
        return 2
    resultado = asyncio.run(evaluar(raiz, args.prompt_id, args.version, args.modelo, args.org_id))
    destino = ruta_resultado(raiz, args.prompt_id, args.version, args.modelo)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Escrito {destino} con puntaje {resultado['puntaje']}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
