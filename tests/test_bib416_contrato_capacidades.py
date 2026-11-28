# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤arbitro
# ¤¤qa-engineer
"""Árbitro BIB-416 R3: el cliente de las capacidades editoriales cumple el contrato del backend.

Lee las llamadas de `frontend/src/lib/plataforma/capacidadesEditoriales.ts` (ruta, método y parámetros de consulta) y
las compara con `app.openapi()` importado en el proceso, sin red ni base. Cada ruta existe con su método y cada
parámetro `required: true` de la operación aparece en la llamada.

Mutación m1: quitar `?usuario_id=...` de `listarHistorial` hace fallar `test_cada_llamada_lleva_sus_parametros_obligatorios`.
"""
import re
from pathlib import Path

from main import app

CLIENTE = Path(__file__).resolve().parent.parent / "frontend" / "src" / "lib" / "plataforma" / "capacidadesEditoriales.ts"
PREFIJO_API = "/api/v1"


def _llamadas() -> list[dict]:
    """Cada `httpBiblioteca<...>(ruta, opciones?)` del cliente: método, ruta con marcadores y parámetros de consulta."""
    fuente = CLIENTE.read_text(encoding="utf-8")
    base = re.search(r'const BASE = "([^"]+)"', fuente).group(1)
    acciones = re.findall(r'"(\w+)"', re.search(r"cambiar\(accion:\s*((?:\"\w+\"\s*\|?\s*)+)", fuente).group(1))
    llamadas = []
    for trozo in fuente.split("httpBiblioteca<")[1:]:
        sentencia = trozo.split(";")[0]
        primero = re.search(r"\(\s*(`[^`]*`|BASE)\s*[,)]", sentencia)
        plantilla = base if primero.group(1) == "BASE" else primero.group(1).strip("`").replace("${BASE}", base)
        metodo = re.search(r'method:\s*"(\w+)"', sentencia)
        variantes = [plantilla.replace("${accion}", a) for a in acciones] if "${accion}" in plantilla else [plantilla]
        for v in variantes:
            ruta, _, consulta = v.partition("?")
            llamadas.append({
                "metodo": (metodo.group(1) if metodo else "GET").lower(),
                "ruta": re.sub(r"\$\{encodeURIComponent\((\w+)\)\}", r"{\1}", ruta),
                "consulta": set(re.findall(r"(?:^|&)(\w+)=", consulta)),
            })
    return llamadas


def _operacion(ruta: str, metodo: str) -> dict | None:
    """La operación de OpenAPI de esa ruta; si hay una literal y otra con marcador, gana la literal."""
    segmentos = (PREFIJO_API + ruta).split("/")
    candidatas = []
    for publicada, operaciones in app.openapi()["paths"].items():
        otros = publicada.split("/")
        if metodo in operaciones and len(otros) == len(segmentos) and all(
                a == b or (a.startswith("{") and b.startswith("{")) for a, b in zip(otros, segmentos)):
            candidatas.append((sum(a.startswith("{") for a in otros), operaciones[metodo]))
    return min(candidatas, key=lambda c: c[0])[1] if candidatas else None


def test_el_cliente_tiene_las_cuatro_llamadas():
    llamadas = _llamadas()
    assert sorted((c["metodo"], c["ruta"]) for c in llamadas) == sorted([
        ("get", "/biblioteca/capacidades/equipo"),
        ("get", "/biblioteca/capacidades/equipo/historial"),
        ("post", "/biblioteca/capacidades/equipo/{usuarioId}/conceder"),
        ("post", "/biblioteca/capacidades/equipo/{usuarioId}/retirar"),
    ])


def test_cada_ruta_del_cliente_existe_con_su_metodo():
    for c in _llamadas():
        assert _operacion(c["ruta"], c["metodo"]) is not None, f"{c['metodo'].upper()} {c['ruta']} no está en app.openapi()"


def test_cada_llamada_lleva_sus_parametros_obligatorios():
    for c in _llamadas():
        operacion = _operacion(c["ruta"], c["metodo"])
        assert operacion is not None, f"{c['metodo'].upper()} {c['ruta']} no está en app.openapi()"
        obligatorios = {p["name"] for p in operacion.get("parameters", []) if p["in"] == "query" and p.get("required")}
        faltan = obligatorios - c["consulta"]
        assert not faltan, f"{c['metodo'].upper()} {c['ruta']} no manda {sorted(faltan)} (required: true en OpenAPI)"
