# ¤adpa
# ¤¤developer-architect
"""Rellenado determinista de plantillas Markdown (docs/biblioteca-pmv.md, apartados a y f).

Funciones puras: sin base de datos, sin red, sin reloj implícito. Las variables se sustituyen en una sola
pasada por tabla de valores: el texto insertado no se vuelve a interpretar, así que un dato con `{{…}}`
nunca ejecuta ni expande nada. Una variable sin valor queda como `⟦falta: x⟧`; las de la rama que no
aplica de una parte condicional no se evalúan.
"""
import re
from collections.abc import Mapping
from datetime import date, datetime
from features.biblioteca.domain.esquemas import Plantilla, Valor, leer_plantilla

BLOQUE = re.compile(r"\{\{#si ([^{}]*)\}\}(.*?)(?:\{\{#sino\}\}(.*?))?\{\{/si\}\}", re.S)
VARIABLE = re.compile(r"\{\{([a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)?)\}\}")
MARCA_FALTA = re.compile(r"⟦falta: ([^⟧]+)⟧")
# Se completan al aprobar (BIB-107): en el borrador no son datos que falten.
AL_APROBAR = frozenset({"documento.aprobado_por", "documento.fecha_aprobacion"})
CONDICION_DPO = "dpo.designado"


# ¤adpa
def _meses(inicio: date, meses: int) -> date:
    indice = inicio.year * 12 + inicio.month - 1 + meses
    anio, mes = divmod(indice, 12)
    mes += 1
    ultimo = (date(anio + (mes == 12), mes % 12 + 1, 1) - date(anio, mes, 1)).days
    return date(anio, mes, min(inicio.day, ultimo))


# ¤adpa
def datos_del_documento(plantilla: Plantilla, fecha_emision: date) -> dict[str, str]:
    """Variables que salen de la propia plantilla y de la fecha de emisión."""
    meses = int(str(plantilla.meta.get("revision_meses", 12)))
    return {
        "documento.codigo": plantilla.codigo, "documento.nombre": str(plantilla.meta["nombre"]),
        "documento.version": plantilla.version, "fecha_emision": fecha_emision.isoformat(),
        "documento.proxima_revision": _meses(fecha_emision, meses).isoformat(),
    }


# ¤adpa
def _item(valor: object) -> str:
    return str(getattr(valor, "value", valor)).strip()


# ¤adpa
def _en_linea(valor: object) -> str:
    """Lista como una sola línea (para celdas de tabla); un escalar, tal cual."""
    if isinstance(valor, (list, tuple)):
        return "; ".join(i for i in map(_item, valor) if i)
    return "" if valor is None else _item(valor)


# ¤adpa
def _texto(valor: object) -> str:
    if valor is None:
        return ""
    if isinstance(valor, (list, tuple)):
        return "\n".join(f"- {i}" for i in map(_item, valor) if i)
    if isinstance(valor, (date, datetime)):
        return valor.isoformat()
    if isinstance(valor, bool):
        return "sí" if valor else "no"
    return _item(valor)


# ¤adpa
def _condicion(nombre: str, organizacion: Mapping, contexto: Mapping) -> bool | None:
    """True/False según el dato; None si aún no se respondió (la condición queda como faltante)."""
    if nombre.strip() == CONDICION_DPO:
        return bool(organizacion.get(CONDICION_DPO))
    respuesta = contexto.get(nombre.strip())
    return {"si": True, "no": False}.get(respuesta) if isinstance(respuesta, str) else None


# ¤adpa
def rellenar(plantilla: Plantilla | str, organizacion: Mapping, contexto: Mapping[str, Valor]) -> tuple[str, list[str]]:
    """Devuelve (contenido, variables faltantes) sin tocar la plantilla.

    `organizacion` trae las variables de ámbito organizacion, representante, dpo, documento, tratamiento y
    fecha_emision (más `dpo.designado`); `contexto`, las respuestas del formulario y las generadas.
    """
    plantilla = leer_plantilla(plantilla) if isinstance(plantilla, str) else plantilla

    def rama(m: re.Match) -> str:
        elegida = _condicion(m.group(1), organizacion, contexto)
        if elegida is None:
            return f"⟦falta: {m.group(1).strip()}⟧"
        return (m.group(2) if elegida else m.group(3) or "").strip("\n")

    def valor(m: re.Match) -> str:
        clave = m.group(1)
        encontrado = _texto(contexto.get(clave) if clave.startswith("contexto.") else organizacion.get(clave))
        if encontrado:
            return encontrado
        return f"⟦pendiente: {clave}⟧" if clave in AL_APROBAR else f"⟦falta: {clave}⟧"

    contenido = VARIABLE.sub(valor, BLOQUE.sub(rama, plantilla.cuerpo))
    return contenido, list(dict.fromkeys(MARCA_FALTA.findall(contenido)))


# ¤adpa
def fichas_de_actividades(actividades: list[Mapping]) -> str:
    """Una ficha por actividad del RAT con los nueve contenidos del art. 38 del Reglamento (solo lectura).

    Un dato ausente en el RAT sale como `⟦falta: contexto.actividades[CODIGO].campo⟧`.
    """
    fichas = []
    for a in actividades:
        codigo = str(a.get("codigo") or a.get("id") or "sin-codigo")

        def dato(campo: str, valor: object) -> str:
            return _en_linea(valor) or f"⟦falta: contexto.actividades[{codigo}].{campo}⟧"

        transferencia = (dato("pais_transferencia", a.get("pais_transferencia"))
                         if a.get("transferencia_internacional") else "No se realizan")
        filas = [
            ("1. Responsable, corresponsable si lo hay, y delegado",
             f"Los del apartado 2 · Encargados: {_en_linea(a.get('encargados')) or 'ninguno registrado'}"),
            ("2. Fines del tratamiento", dato("finalidad", a.get("finalidad"))),
            ("3. Categorías de destinatarios", dato("destinatarios", a.get("destinatarios"))),
            ("4. Titulares y categorías de datos",
             f"Titulares: {dato('categorias_titulares', a.get('categorias_titulares'))} · "
             f"Datos: {dato('categorias_datos', a.get('categorias_datos'))} · "
             f"¿Categorías especiales?: {'sí' if a.get('datos_sensibles') else 'no'}"),
            ("5. Uso de perfiles", "Sí" if a.get("decisiones_automatizadas") else "No"),
            ("6. Transferencias internacionales", transferencia),
            ("7. Base de legitimación", dato("base_legal", getattr(a.get("base_legal"), "value", a.get("base_legal")))),
            ("8. Plazo de conservación", dato("plazo_conservacion", a.get("plazo_conservacion"))),
            ("9. Medidas técnicas, jurídicas, administrativas y organizativas",
             dato("medidas_seguridad", a.get("medidas_seguridad"))),
        ]
        cuerpo = "\n".join(f"| {k} | {v.replace('|', '/')} |" for k, v in filas)
        fichas.append(f"### Actividad: {str(a.get('nombre') or codigo).replace(chr(10), ' ')}\n\n"
                      f"| Contenido (Reglamento art. 38) | Detalle |\n|---|---|\n{cuerpo}")
    return "\n\n".join(fichas)


# ¤adpa
def datos_de_tratamiento(actividades: list[Mapping]) -> dict[str, str]:
    """`tratamiento.*` agregado desde el RAT; vacío si el RAT no tiene actividades."""
    def unir(campo: str) -> list[str]:
        vistos: dict[str, None] = {}
        for a in actividades:
            valor = a.get(campo)
            for v in (valor if isinstance(valor, (list, tuple)) else [valor]):
                if _item(v) and v is not None:
                    vistos[_item(v)] = None
        return list(vistos)

    def lista(campo: str) -> str:
        return _texto(unir(campo))
    return {"tratamiento.finalidades": lista("finalidad"), "tratamiento.categorias_datos": lista("categorias_datos"),
            "tratamiento.plazo_conservacion": "; ".join(unir("plazo_conservacion")),
            "tratamiento.destinatarios": lista("destinatarios")}
