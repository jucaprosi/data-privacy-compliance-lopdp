# ¤¤developer-architect
# ¤regulation-code
"""Centro de conocimiento (REG-02): consulta del corpus versionado y ayuda que siempre cita su fuente.

Solo lee el corpus de `regulacion_rag`; no genera texto (R2). Toda ayuda lleva cita completa
(fuente, artículo, versión) o no existe: el llamador responde 404 `SIN_FUENTE` (R1,
INV_LOPDP_AI_RAG_STRICT_CITATION).
"""
import re

from features.regulacion_rag.domain.corpus import CORPUS_NORMATIVO_OFICIAL, POR_ID
from features.regulacion_rag.domain.models import TipoNorma, UnidadNormativa
from features.regulacion_rag.services.implementation_guides import CONTROLES
from features.regulacion_rag.services.rag_engine import normalizar_consulta

_CAMPOS_CITA = ("fuente", "articulo", "version")
_TIPO_POR_FUENTE = {
    "lopdp": TipoNorma.LEY_ORGANICA,
    "ley": TipoNorma.LEY_ORGANICA,
    "reglamento": TipoNorma.REGLAMENTO_GENERAL,
}


# ¤numero-de-articulo
def _numero(unidad: UnidadNormativa) -> int:
    return int(re.sub(r"\D", "", unidad.articulo_o_seccion) or 0)


# ¤ordenar-corpus
def _ordenadas() -> list[UnidadNormativa]:
    return sorted(CORPUS_NORMATIVO_OFICIAL, key=lambda u: (u.tipo.value, _numero(u)))


# ¤proyectar-articulo
def _articulo(unidad: UnidadNormativa) -> dict:
    return {
        "fuente": unidad.numero_o_titulo,
        "articulo": unidad.articulo_o_seccion,
        "titulo": unidad.titulo,
        "texto": unidad.texto_oficial,
        "version": unidad.version,
    }


# ¤filtrar-por-fuente
def _coincide_fuente(unidad: UnidadNormativa, fuente: str) -> bool:
    buscada = normalizar_consulta(fuente)
    if not buscada:
        return True
    if buscada in _TIPO_POR_FUENTE:
        return unidad.tipo == _TIPO_POR_FUENTE[buscada]
    return buscada == normalizar_consulta(unidad.numero_o_titulo)


# ¤buscar-normativa
def listar_normativa(fuente: str = "", q: str = "") -> list[dict]:
    """Artículos del corpus, por fuente y artículo. `q` exige todas sus palabras en el artículo."""
    palabras = normalizar_consulta(q).split()
    resultado = []
    for unidad in _ordenadas():
        if not _coincide_fuente(unidad, fuente):
            continue
        pajar = normalizar_consulta(
            " ".join([unidad.titulo, unidad.texto_oficial, unidad.articulo_o_seccion, *unidad.palabras_clave])
        )
        if all(p in pajar for p in palabras):
            resultado.append(_articulo(unidad))
    return resultado


# ¤cita-completa
def _cita(unidad: UnidadNormativa) -> dict:
    return {
        "fuente": unidad.numero_o_titulo,
        "articulo": unidad.articulo_o_seccion,
        "version": unidad.version,
    }


def _cita_completa(cita: dict) -> bool:
    return all(str(cita.get(campo) or "").strip() for campo in _CAMPOS_CITA)


# ¤resolver-articulo
def _unidad_por_articulo(articulo: str) -> UnidadNormativa | None:
    """Acepta «7», «Art. 7», «L7», «R12» o «Art. 12 del Reglamento»; sin otra indicación, la LOPDP."""
    texto = normalizar_consulta(articulo)
    clave = re.fullmatch(r"([lr])\s*(\d+)", texto)
    if clave:
        return POR_ID.get(f"{clave.group(1).upper()}{clave.group(2)}")
    numero = re.search(r"\d+", texto)
    if not numero:
        return None
    prefijo = "R" if "reglamento" in texto else "L"
    return POR_ID.get(f"{prefijo}{int(numero.group())}")


# ¤resolver-control
def _unidad_por_control(control_ref: str) -> UnidadNormativa | None:
    """P<n> es la pregunta n del banco SGPDP; su fundamento sale del catálogo de implementación."""
    coincide = re.fullmatch(r"p(\d{1,3})", control_ref.strip().lower())
    registro = CONTROLES.get(int(coincide.group(1))) if coincide else None
    if registro is None:
        return None
    return next((POR_ID[c] for c in registro[3] if c in POR_ID), None)


# ¤ayuda-con-cita
def obtener_ayuda(control_ref: str = "", articulo: str = "") -> dict | None:
    """Texto del corpus con su cita, o `None` (404 SIN_FUENTE). Nunca texto sin cita completa."""
    unidad = _unidad_por_control(control_ref) if control_ref.strip() else _unidad_por_articulo(articulo)
    if unidad is None:
        return None
    cita = _cita(unidad)
    if not _cita_completa(cita) or not unidad.texto_oficial.strip():
        return None
    return {"texto": unidad.texto_oficial, "cita": cita}
