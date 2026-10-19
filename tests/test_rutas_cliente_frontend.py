"""Contrato estático entre las llamadas HTTP del frontend y el OpenAPI real.

No ejecuta el frontend ni el servidor. Inspecciona los clientes TypeScript y compara
sus pares método/ruta con ``app.openapi()``. Las expresiones que no pueden resolverse
sin ejecutar JavaScript se informan como advertencias, pero no producen un falso fallo.
"""

from __future__ import annotations

import re
import warnings
from dataclasses import dataclass
from pathlib import Path

from main import app


RAIZ = Path(__file__).resolve().parent.parent
FRONTEND_SRC = RAIZ / "frontend" / "src"
METODOS_OPENAPI = {"get", "post", "put", "patch", "delete", "options", "head"}
AYUDANTES_API = {"fetchJson", "requestJson", "solicitar"}

# Deuda conocida: declarativa, localizada y con motivo. No se ocultan directorios ni
# patrones completos; cada excepción identifica exactamente el método y la ruta.
EXCEPCIONES: dict[tuple[str, str], str] = {
    (
        "GET",
        "/api/v1/terceros",
    ): "TercerosModule conserva la ruta anterior; el backend publica /terceros/encargados.",
    (
        "POST",
        "/api/v1/niif18/exportar/{ruta}",
    ): "El despachador recibe solo excel, pdf o informe; las tres rutas constan en OpenAPI.",
}


@dataclass(frozen=True, order=True)
class Llamada:
    archivo: str
    metodo: str
    ruta: str


@dataclass(frozen=True, order=True)
class NoResuelta:
    archivo: str
    expresion: str


PATRON_LLAMADA = re.compile(
    r"\b(?P<funcion>fetchAutenticado|fetchJson|requestJson|solicitar|fetch)\s*\(\s*"
    r"(?P<argumento>`(?:[^`\\]|\\.)*`|\"(?:[^\"\\]|\\.)*\"|'(?:[^'\\]|\\.)*'|[A-Za-z_$][\w$.[\]]*)",
    re.DOTALL,
)
PATRON_METODO = re.compile(r"\bmethod\s*:\s*['\"](?P<metodo>[A-Za-z]+)['\"]")
PATRON_PLANTILLA = re.compile(r"\$\{(?P<expresion>[^}]+)\}")


def _nombre_parametro(expresion: str) -> str:
    """Convierte una interpolación TS en un parámetro comparable con OpenAPI."""
    identificadores = re.findall(r"[A-Za-z_$][\w$]*", expresion)
    ignorados = {"encodeURIComponent", "String", "toString"}
    candidatos = [nombre for nombre in identificadores if nombre not in ignorados]
    return candidatos[-1] if candidatos else "param"


def _normalizar_ruta(ruta: str) -> str:
    ruta = PATRON_PLANTILLA.sub(
        lambda coincidencia: "{" + _nombre_parametro(coincidencia.group("expresion")) + "}",
        ruta,
    )
    ruta = ruta.split("?", 1)[0]
    ruta = re.sub(r"/+", "/", ruta)
    return ruta if ruta == "/" else ruta.rstrip("/")


def _firma_ruta(ruta: str) -> str:
    """Ignora el nombre local del parámetro, pero no su posición en la ruta."""
    return re.sub(r"\{[^/{}]+\}", "{}", _normalizar_ruta(ruta))


def _literal(argumento: str) -> str | None:
    if argumento[:1] not in {'"', "'", "`"}:
        return None
    return argumento[1:-1]


def _metodo_en_invocacion(texto: str, fin_argumento: int) -> str:
    # El límite evita atribuir a una llamada el método de otra invocación posterior.
    cola = texto[fin_argumento : fin_argumento + 800]
    cierre = cola.find(");")
    if cierre >= 0:
        cola = cola[:cierre]
    encontrado = PATRON_METODO.search(cola)
    return encontrado.group("metodo").upper() if encontrado else "GET"


def extraer_llamadas(raiz: Path = FRONTEND_SRC) -> tuple[list[Llamada], list[NoResuelta]]:
    llamadas: set[Llamada] = set()
    no_resueltas: set[NoResuelta] = set()
    for archivo in sorted((*raiz.rglob("*.ts"), *raiz.rglob("*.tsx"))):
        if archivo.name.endswith((".test.ts", ".test.tsx", ".spec.ts", ".spec.tsx")):
            continue
        relativo = archivo.relative_to(RAIZ).as_posix()
        texto = archivo.read_text(encoding="utf-8")
        for coincidencia in PATRON_LLAMADA.finditer(texto):
            funcion = coincidencia.group("funcion")
            argumento = coincidencia.group("argumento")
            if funcion == "solicitar" and relativo != "frontend/src/lib/preanalisis/cliente.ts":
                continue
            ruta = _literal(argumento)
            if ruta is None:
                if funcion in AYUDANTES_API or argumento.startswith("API_BASE_URL"):
                    no_resueltas.add(NoResuelta(relativo, f"{funcion}({argumento})"))
                continue

            if funcion in AYUDANTES_API:
                ruta = f"/api/v1{ruta}"
            elif ruta.startswith("${API_BASE_URL}"):
                ruta = "/api/v1" + ruta.removeprefix("${API_BASE_URL}")

            # Estas son las implementaciones de los propios ayudantes; su argumento
            # se resuelve en cada invocación literal que también inspeccionamos.
            if ruta in {"/api/v1${endpoint}", "/api/v1${ruta}"}:
                no_resueltas.add(NoResuelta(relativo, f"{funcion}({argumento})"))
                continue

            # Fetches externos, rutas internas de Next y URLs firmadas no pertenecen
            # al contrato FastAPI solicitado por TEST-04.
            if not ruta.startswith("/api/v1"):
                continue
            llamadas.add(
                Llamada(
                    archivo=relativo,
                    metodo=_metodo_en_invocacion(texto, coincidencia.end()),
                    ruta=_normalizar_ruta(ruta),
                )
            )
    return sorted(llamadas), sorted(no_resueltas)


def rutas_backend(esquema: dict | None = None) -> set[tuple[str, str]]:
    esquema = esquema or app.openapi()
    return {
        (metodo.upper(), _firma_ruta(ruta))
        for ruta, operaciones in esquema.get("paths", {}).items()
        for metodo in operaciones
        if metodo in METODOS_OPENAPI
    }


def faltantes(
    llamadas: list[Llamada],
    disponibles: set[tuple[str, str]],
    excepciones: dict[tuple[str, str], str] | None = None,
) -> list[Llamada]:
    excepciones = EXCEPCIONES if excepciones is None else excepciones
    return [
        llamada
        for llamada in llamadas
        if (llamada.metodo, _firma_ruta(llamada.ruta)) not in disponibles
        and (llamada.metodo, llamada.ruta) not in excepciones
    ]


def _mensaje_faltantes(errores: list[Llamada]) -> str:
    detalle = "\n".join(
        f"- {error.archivo}: {error.metodo} {error.ruta}" for error in errores
    )
    return "El frontend llama rutas que el backend no expone:\n" + detalle


def test_todas_las_rutas_estaticas_del_frontend_existen_en_openapi():
    llamadas, no_resueltas = extraer_llamadas()
    assert llamadas, "No se extrajo ninguna llamada API de frontend/src; el detector está roto."

    if no_resueltas:
        detalle = "\n".join(
            f"- {item.archivo}: {item.expresion}" for item in no_resueltas
        )
        warnings.warn(
            "Llamadas que no se pueden resolver de forma estática (no bloquean):\n" + detalle,
            stacklevel=1,
        )

    errores = faltantes(llamadas, rutas_backend())
    assert not errores, _mensaje_faltantes(errores)


def test_mutacion_de_ruta_falla_con_archivo_metodo_y_ruta():
    """Prueba negativa: altera una copia, nunca código del frontend ni OpenAPI."""
    llamadas, _ = extraer_llamadas()
    original = next(
        llamada
        for llamada in llamadas
        if (llamada.metodo, llamada.ruta) not in EXCEPCIONES
    )
    mutada = Llamada(original.archivo, original.metodo, original.ruta + "-ruta-rota")

    errores = faltantes([mutada], rutas_backend(), excepciones={})
    mensaje = _mensaje_faltantes(errores)

    assert errores == [mutada]
    assert original.archivo in mensaje
    assert original.metodo in mensaje
    assert mutada.ruta in mensaje
