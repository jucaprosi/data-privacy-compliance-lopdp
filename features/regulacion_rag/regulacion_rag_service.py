"""Compuerta pública de la sala ADPA: Regulación y Copiloto RAG."""
from features.regulacion_rag.domain.models import ConsultaRAGInput, RespuestaRAGOutput
from features.regulacion_rag.services.rag_engine import responder_consulta_normativa
from features.regulacion_rag.domain.corpus import CORPUS_VERSION
from features.regulacion_rag.services.implementation_guides import obtener_guia_brecha
from features.regulacion_rag.services.rag_engine import buscar_fundamentos

def consultar_corpus_spdp(consulta: ConsultaRAGInput) -> RespuestaRAGOutput:
    """Ejecuta una consulta sobre el corpus oficial garantizando citas y ausencia de alucinaciones."""
    return responder_consulta_normativa(consulta)

# === REG-02 ===
from features.regulacion_rag.services.conocimiento_engine import listar_normativa, obtener_ayuda
# === fin REG-02 ===

# === REG-01 ===
# ¤paquete-normativo
from features.regulacion_rag.domain.paquete import (
    CLAVES_MINIMAS,
    DetallePaquete,
    Impacto,
    Paquete,
    Parametro,
    ParametroEntrada,
    Publicacion,
    VersionEntrada,
)
from features.regulacion_rag.domain.errores import NO_ES_OPERADOR
from features.regulacion_rag.services import paquetes_engine as _paquetes
from features.regulacion_rag.services.paquetes_diff_engine import impacto_de_publicar

listar_paquetes = _paquetes.listar_paquetes
detalle_paquete = _paquetes.detalle_paquete
parametros_publicados = _paquetes.parametros_publicados
crear_version_paquete = _paquetes.crear_version
fijar_parametro_paquete = _paquetes.fijar_parametro


async def publicar_paquete(session, operador_id: str, paquete_id: str) -> Publicacion:
    """Publica el borrador (R1, R2) y devuelve el impacto del cambio (R3)."""
    paquete, anterior = await _paquetes.publicar(session, operador_id, paquete_id)
    return Publicacion(paquete=paquete, impacto=impacto_de_publicar(paquete, anterior))
# === fin REG-01 ===

# === REG-03 ===
# ¤vertex-cache
from features.regulacion_rag.domain.corpus import CORPUS_NORMATIVO_OFICIAL, fundamento as _fundamento
from features.regulacion_rag.services import vertex_context_cache as _cache_vertex


async def vectorizar_fragmentos(textos, modelo):
    """Vectores por el pasillo de inferencia (IA-12); sin inferencia propaga el error al llamador."""
    from app_core.pasillo import inferencia

    return await inferencia.vectorizar(textos, modelo)


def obtener_o_crear_cache_normativo(modelo):
    """Descriptor de la caché de contexto del corpus oficial; sin inferencia lanza VTX_CACHE_NO_DISPONIBLE."""
    return _cache_vertex.obtener_o_crear(modelo, corpus=CORPUS_NORMATIVO_OFICIAL)


def regenerar_cache_normativo(corpus_sha256: str) -> None:
    """Si el hash difiere de la caché vigente, vacía el registro para que la próxima llamada cree otra."""
    _cache_vertex.regenerar_si_difiere(corpus_sha256)


def corpus_citable() -> dict[str, dict]:
    """{clave: fundamento} de cada unidad del corpus oficial (el mismo de la caché)."""
    return {norma.id: _fundamento(norma.id) for norma in CORPUS_NORMATIVO_OFICIAL}
# === fin REG-03 ===
