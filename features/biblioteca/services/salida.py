# ¤adpa
# ¤¤developer-architect
"""Salida de uso (BIB-205): lo que entra en el archivo y lo que se queda en la guía.

Funciones puras. La plantilla puede llevar instrucciones y ejemplos entre `<!-- instruccion -->` …
`<!-- /instruccion -->` y `<!-- ejemplo -->` … `<!-- /ejemplo -->`; van a la guía descargable, nunca al
documento. Cualquier otro comentario HTML se descarta. Los datos del usuario se tratan siempre como texto:
no se interpretan como Markdown activo, HTML, fórmula ni código.
"""
import re
import zipfile
from dataclasses import dataclass, field
from io import BytesIO

GUIA = re.compile(r"<!--\s*(instruccion|ejemplo)\s*-->(.*?)<!--\s*/\1\s*-->", re.S)
COMENTARIO = re.compile(r"<!--.*?-->", re.S)
FALTA = re.compile(r"⟦falta: ([^⟧]+)⟧")
PENDIENTE = re.compile(r"⟦pendiente: [^⟧]+⟧")
RESIDUO = re.compile(r"⟦|⟧|\[FALTA:|\{\{[#/]si|\{\{#sino\}\}")  # marcas del sistema, nunca datos del usuario
LINEA_FIRMA = "______________________"
ARRANQUE_FORMULA = ("=", "+", "-", "@", "\t", "\r")
FECHA_ZIP = (1980, 1, 1, 0, 0, 0)


# ¤adpa
@dataclass(frozen=True)
class Bloque:
    tipo: str  # titulo | parrafo | lista | cita | tabla
    texto: str = ""
    nivel: int = 0
    filas: list[list[str]] = field(default_factory=list)


# ¤adpa
def separar_guia(cuerpo: str) -> tuple[str, str]:
    """(cuerpo de uso, guía). La guía junta instrucciones y ejemplos en el orden en que aparecen."""
    partes = [f"### {'Instrucción' if m.group(1) == 'instruccion' else 'Ejemplo'}\n\n{m.group(2).strip()}"
              for m in GUIA.finditer(cuerpo)]
    uso = COMENTARIO.sub("", GUIA.sub("", cuerpo))
    return re.sub(r"\n{3,}", "\n\n", uso).strip("\n"), "\n\n".join(partes)


# ¤adpa
def preparar(contenido: str, faltantes: list[str], opcionales: set[str], borrador: bool) -> tuple[str, list[str]]:
    """Texto final y faltantes que bloquean la revisión.

    Borrador: cada faltante se ve como `[FALTA: x]`. Revisión: un opcional vacío desaparece y los campos
    que se completan al aprobar quedan como línea de firma.
    """
    bloqueantes = [f for f in faltantes if f not in opcionales]

    def marca(m: re.Match) -> str:
        return f"[FALTA: {m.group(1)}]" if borrador and m.group(1) not in opcionales else ""
    texto = PENDIENTE.sub(LINEA_FIRMA, FALTA.sub(marca, contenido))
    return texto, bloqueantes


# ¤adpa
def residuos(texto: str) -> list[str]:
    """Restos de plantilla en un texto que debería estar resuelto."""
    return sorted({m.group(0) for m in RESIDUO.finditer(texto)})


# ¤adpa
def _celdas(linea: str) -> list[str]:
    return [c.strip() for c in linea.strip().strip("|").split("|")]


# ¤adpa
def bloques(markdown: str) -> list[Bloque]:
    """Markdown de las plantillas del PMV (títulos, párrafos, listas, citas y tablas) en bloques."""
    resultado: list[Bloque] = []
    lineas = markdown.splitlines()
    i = 0
    while i < len(lineas):
        linea = lineas[i].rstrip()
        if not linea.strip():
            i += 1
            continue
        titulo = re.match(r"^(#{1,6})\s+(.*)$", linea)
        if titulo:
            resultado.append(Bloque("titulo", titulo.group(2).strip(), len(titulo.group(1))))
        elif linea.lstrip().startswith("|"):
            filas = []
            while i < len(lineas) and lineas[i].lstrip().startswith("|"):
                if not re.fullmatch(r"\|?[\s:|-]+\|?", lineas[i].strip()):
                    filas.append(_celdas(lineas[i]))
                i += 1
            resultado.append(Bloque("tabla", filas=filas))
            continue
        elif re.match(r"^\s*[-*]\s+", linea):
            resultado.append(Bloque("lista", re.sub(r"^\s*[-*]\s+", "", linea)))
        elif linea.startswith(">"):
            resultado.append(Bloque("cita", linea.lstrip("> ").strip()))
        else:
            parrafo = [linea.strip()]
            while (i + 1 < len(lineas) and lineas[i + 1].strip()
                   and not re.match(r"^(#{1,6}\s|\s*[-*]\s+|\||>)", lineas[i + 1])):
                i += 1
                parrafo.append(lineas[i].strip())
            resultado.append(Bloque("parrafo", "\n".join(parrafo)))
        i += 1
    return resultado


# ¤adpa
def tramos(texto: str) -> list[tuple[str, bool]]:
    """Texto en tramos (contenido, negrita) según `**…**`; nada más se interpreta."""
    partes = texto.split("**")
    if len(partes) % 2 == 0:  # negrita sin cerrar: todo literal
        return [(texto, False)]
    return [(p, i % 2 == 1) for i, p in enumerate(partes) if p]


# ¤adpa
def es_formula(valor: str) -> bool:
    return valor.startswith(ARRANQUE_FORMULA)


# ¤adpa
def zip_determinista(entradas: list[tuple[str, bytes]]) -> bytes:
    """ZIP con fecha y orden fijos: la misma entrada da siempre los mismos bytes."""
    salida = BytesIO()
    with zipfile.ZipFile(salida, "w", zipfile.ZIP_DEFLATED) as archivo:
        for nombre, datos in entradas:
            info = zipfile.ZipInfo(nombre, FECHA_ZIP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o600 << 16
            archivo.writestr(info, datos)
    return salida.getvalue()
