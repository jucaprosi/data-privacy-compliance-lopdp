# ¤adpa
# ¤¤developer-architect
"""Validación en servidor de las respuestas `contexto.*` y de la entrada a revisión (BIB-201).

El cliente puede mostrar avisos, pero esta es la regla que cuenta: se valida contra el esquema de campos
que declara la plantilla, nunca contra lo que el cliente diga de sí mismo.
"""
from app_core.errors import ErrorNegocio
from features.biblioteca.domain.esquemas import CampoContexto, Valor
import features.biblioteca.domain.errores  # noqa: F401  registra los códigos de Biblioteca al importarse

MAX_TEXTO = 2000
MAX_ITEMS = 50


# ¤adpa
def _normalizar(campo: CampoContexto, valor: Valor) -> Valor:
    if campo.tipo == "lista":
        if not isinstance(valor, list) or len(valor) > MAX_ITEMS or any(not isinstance(v, str) for v in valor):
            raise ErrorNegocio("BIB_CONTEXTO_INVALIDO", f"{campo.clave}: se espera una lista de textos.")
        limpios = [v.strip() for v in valor if v.strip()]
        if any(len(v) > MAX_TEXTO for v in limpios):
            raise ErrorNegocio("BIB_CONTEXTO_INVALIDO", f"{campo.clave}: un elemento es demasiado largo.")
        return limpios
    if not isinstance(valor, str):
        raise ErrorNegocio("BIB_CONTEXTO_INVALIDO", f"{campo.clave}: se espera un texto.")
    limpio = valor.strip()
    if len(limpio) > MAX_TEXTO:
        raise ErrorNegocio("BIB_CONTEXTO_INVALIDO", f"{campo.clave}: supera {MAX_TEXTO} caracteres.")
    if campo.tipo == "si_no" and limpio not in ("", "si", "no"):
        raise ErrorNegocio("BIB_CONTEXTO_INVALIDO", f"{campo.clave}: responde «si» o «no».")
    return limpio


# ¤adpa
def validar_contexto(campos: list[CampoContexto], contexto: dict[str, Valor]) -> dict[str, Valor]:
    """Respuestas normalizadas. Una clave no declarada o generada por el servidor se rechaza.

    Un valor vacío es válido (guardar incompleto): simplemente no se conserva y la variable queda faltante.
    """
    por_clave = {c.clave: c for c in campos}
    resultado: dict[str, Valor] = {}
    for clave, valor in contexto.items():
        campo = por_clave.get(clave)
        if campo is None or campo.origen != "captura":
            raise ErrorNegocio("BIB_CONTEXTO_INVALIDO", f"{clave}: no es un campo de captura de esta plantilla.")
        normalizado = _normalizar(campo, valor)
        if normalizado:
            resultado[clave] = normalizado
    return resultado


# ¤adpa
def es_revisable(faltantes: list[str]) -> bool:
    return not faltantes


# ¤adpa
def exigir_revisable(faltantes: list[str]) -> None:
    """Compuerta de `borrador → en_revision` (la transición la ejecuta BIB-107): sin faltantes."""
    if faltantes:
        raise ErrorNegocio("BIB_VARIABLES_FALTANTES", "Faltan: " + ", ".join(faltantes[:20]))
