# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤adpa ¤regulation-code ¤cita-verificada
# ¤¤developer-architect
"""Validación normativa de las plantillas (BIB-403): lógica pura, sin base ni archivos.

La validación no es personal: una plantilla es «validada» si cada cita atómica de su base legal y de su
cuerpo tiene una lectura `verificada` en fuente oficial (LEG-08) y, cuando el módulo de inteligencia
normativa conoce la fuente, esa lectura es de la última versión de la norma (huella igual).

Alcance (R7): acredita que la norma citada existe y dice lo citado en la versión leída. No acredita que
la cláusula aplique bien la norma a la organización ni que la plantilla esté completa.
"""
import re

LOPDP, REGLAMENTO = "LOPDP", "RLOPDP"
ESTADO_VERIFICADA = "verificada"

# Normas con un «fuente_id» propio; las resoluciones se identifican por año y número.
_NORMA = re.compile(
    r"(?P<lopdp>\bLOPDP\b)|(?P<reg>\bRGLOPDP\b|\bReglamento(?: General)?\b)"
    r"|(?:Resoluci[oó]n|Res\.?)\s*(?:SP[DS]P?-SP[DS]?P?-)?(?P<anio>\d{4})-(?P<num>\d{4})(?:-R)?",
)
_ELEMENTO = (r"\d+(?:\.\d+)?(?:(?:\s*[-–]\s*|\s+a\s+)\d+)?"
             r"(?:\s+[a-m](?![\wáéíóúñ])(?!\s+\d))?")
_ARTICULO = re.compile(r"\b(?:arts?\.|art[íi]culos?)\s*(?P<lista>" + _ELEMENTO + r"(?:(?:\s*,\s*|\s+y\s+)" + _ELEMENTO + r")*)",
                       re.IGNORECASE)
_ITEM = re.compile(r"(?P<a>\d+)(?:\.(?P<sub>\d+))?(?:(?:\s*[-–]\s*|\s+a\s+)(?P<b>\d+))?(?:\s+(?P<lit>[a-m]))?")
_REFORMA = re.compile(r"\bart(?:s?\.|[íi]culo) ?(?P<art>\d+),?\s+reformad[oa]\s+por\b[^)]*?\bRO\s*5S\s*(?P<ro>\d+)", re.IGNORECASE)
_PARENTESIS_SIN_ARTICULO = re.compile(r"\((?![^)]*art)[^)]*\)", re.IGNORECASE)
_SUFIJO = re.compile(r"\s*(?:de la|del)\s+(?P<n>LOPDP|RGLOPDP|Reglamento(?: General)?)")
_FRONTERA = re.compile(r";|(?<=[.:])\s+(?=[A-ZÁÉÍÓÚ])")
_ENCABEZADO = re.compile(r"^(#{2,3})\s+(.+?)\s*$", re.MULTILINE)


class CitaSinNorma(ValueError):
    """Un «art. N» cuya norma no se puede identificar en su contexto."""


def _norma_en(contexto: str, desde_atras: bool) -> str | None:
    marcas = list(_NORMA.finditer(contexto))
    if not marcas:
        return None
    m = marcas[-1] if desde_atras else marcas[0]
    if m.group("lopdp"):
        return LOPDP
    if m.group("reg"):
        return REGLAMENTO
    return f"RES-{m.group('anio')}-{m.group('num')}"


def _claves_de_lista(norma: str, lista: str) -> set[str]:
    claves: set[str] = set()
    for pieza in re.split(r"\s*(?:,|\by\b)\s*", lista.strip().rstrip(",")):
        m = _ITEM.fullmatch(pieza.strip())
        if not m:
            continue
        desde = int(m.group("a"))
        hasta = int(m.group("b") or desde)
        for art in range(desde, hasta + 1):
            claves.add(f"{norma}-art-{art}")
        if m.group("sub"):
            claves.add(f"{norma}-art-{desde}-num-{int(m.group('sub'))}")
        if m.group("lit"):
            claves.add(f"{norma}-art-{desde}-lit-{m.group('lit')}")
    return claves


# ¤adpa
def extraer_citas(texto: str) -> tuple[set[str], list[str]]:
    """Claves atómicas citadas en `texto` y las menciones «art. N» sin norma identificable.

    Claves: `LOPDP-art-N`, `LOPDP-art-N-num-M`, `LOPDP-art-N-lit-x`, `RLOPDP-art-N`, `RES-AAAA-NNNN-art-N`
    (la misma forma que DIAG-16/LEG-08). Un rango «arts. 55 a 60» da una clave por artículo.
    """
    claves: set[str] = set()
    sin_norma: list[str] = []
    texto = re.sub(r"\bRes\.\s*", "Resolución ", texto)
    for r in _REFORMA.finditer(texto):
        claves.add(f"{LOPDP}-art-{int(r.group('art'))}-reforma-RO-5S-{r.group('ro')}")
    texto = _REFORMA.sub("", texto)
    texto = _PARENTESIS_SIN_ARTICULO.sub("", texto)
    for m in _ARTICULO.finditer(texto):
        previo = texto[:m.start()]
        segmento = _FRONTERA.split(previo)[-1]
        # «art. 18 de la LOPDP»: la norma que sigue de inmediato manda sobre la que precede en la frase.
        propia = _SUFIJO.match(texto[m.end():m.end() + 40])
        norma = _norma_en(propia.group("n"), desde_atras=False) if propia else None
        if norma is None:
            norma = _norma_en(segmento, desde_atras=True)
        if norma is None:
            siguiente = texto[m.end():m.end() + 80]
            norma = _norma_en(_FRONTERA.split(siguiente)[0].split(")")[0], desde_atras=False)
        if norma is None:
            sin_norma.append(m.group(0).strip())
            continue
        claves |= _claves_de_lista(norma, m.group("lista"))
    return claves, sin_norma


# ¤adpa
def secciones(cuerpo: str) -> list[tuple[str, str]]:
    """(título, texto) de cada encabezado `##` o `###`, hasta el encabezado siguiente."""
    marcas = list(_ENCABEZADO.finditer(cuerpo))
    salida = []
    for i, m in enumerate(marcas):
        fin = marcas[i + 1].start() if i + 1 < len(marcas) else len(cuerpo)
        salida.append((m.group(2), cuerpo[m.end():fin]))
    return salida


# ¤adpa
def errores_informativas(cuerpo: str, informativas: list[str]) -> list[str]:
    """R8: cada título de `secciones_informativas` existe en el cuerpo y su sección no cita nada."""
    fallos: list[str] = []
    todas = secciones(cuerpo)
    titulos = [t for t, _ in todas]
    for titulo in informativas:
        if titulo not in titulos:
            fallos.append(f"secciones_informativas: el título «{titulo}» no existe en el cuerpo")
    for titulo, texto in todas:
        if titulo in informativas and extraer_citas(texto)[0]:
            fallos.append(f"sección informativa «{titulo}» con cita: tiene efecto jurídico")
    return fallos


# ¤adpa
def errores_secciones(cuerpo: str, informativas: list[str], verificadas: set[str]) -> list[str]:
    """R8: cada sección lleva una cita `verificada` o está declarada informativa (y entonces no cita)."""
    fallos = errores_informativas(cuerpo, informativas)
    for titulo, texto in secciones(cuerpo):
        if titulo not in informativas and not (extraer_citas(texto)[0] & verificadas):
            fallos.append(f"sección «{titulo}» sin cita verificada")
    return fallos


# ¤adpa
def errores_ida(claves: set[str], estados: dict[str, str]) -> list[str]:
    """Ida (R1): cada cita atómica tiene una fila `verificada` en el artefacto de LEG-08."""
    fallos = []
    for clave in sorted(claves):
        estado = estados.get(clave)
        if estado is None and clave.startswith("RES-"):
            # Una resolución se lee por artículo entero: «art. 4.10» queda cubierto por la fila del art. 4.
            estado = estados.get(re.sub(r"-num-\d+$", "", clave))
        if estado is None:
            fallos.append(f"cita sin fila en CITAS_PLANTILLAS_VERIFICADAS: {clave}")
        elif estado != ESTADO_VERIFICADA:
            fallos.append(f"cita {clave} con lectura «{estado}»")
    return fallos


# ¤adpa
def errores_vuelta(asignadas: set[str], citadas: set[str]) -> list[str]:
    """Vuelta (R1): cada clave asignada a la plantilla aparece en ella (y ninguna citada falta)."""
    return ([f"clave asignada y no citada en la plantilla: {c}" for c in sorted(asignadas - citadas)]
            + [f"clave citada y no asignada en citas.json: {c}" for c in sorted(citadas - asignadas)])


# ¤adpa
def validacion_normativa(claves: set[str], estados: dict[str, str], fuente_de: dict[str, str],
                         huellas_leidas: dict[str, str], versiones_modulo: dict[str, str]) -> str:
    """Valor de `validacion_legal` derivado (R2, R3): `validada`, `en_revision`, `pendiente`
    o `con_observaciones`. Nunca sale de un dictamen con nombre ni de un metadato.

    - `con_observaciones`: alguna cita `no_encontrada`.
    - `pendiente`: a la versión le falta alguna cita verificada (sin fila o `no_leida`).
    - `en_revision`: el módulo registra, para una fuente citada que conoce, otra huella que la leída.
    - `validada`: todo lo demás. Sin versión en el módulo (hoy no descarga) no hay control de versión.
    `versiones_modulo`: fuente_id -> archivo_sha256 de su última `normativa_versiones`.
    """
    if not claves:
        return "pendiente"
    lecturas = [estados.get(c) for c in claves]
    if "no_encontrada" in lecturas:
        return "con_observaciones"
    if any(e != ESTADO_VERIFICADA for e in lecturas):
        return "pendiente"
    for clave in claves:
        fuente = fuente_de.get(clave)
        registrada = versiones_modulo.get(fuente) if fuente else None
        if registrada is not None and registrada != huellas_leidas.get(fuente):
            return "en_revision"
    return "validada"
