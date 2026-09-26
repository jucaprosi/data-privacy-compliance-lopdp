# ¤¤frontend-architect
"""Búsqueda determinista en el corpus cerrado y versionado."""
import re
import unicodedata
from features.regulacion_rag.domain.corpus import CORPUS_NORMATIVO_OFICIAL, fundamento
from features.regulacion_rag.domain.models import ConsultaRAGInput, RespuestaRAGOutput, UnidadNormativa

# ¤normalizar-consulta
def normalizar_consulta(texto: str) -> str:
    return " ".join("".join(c for c in unicodedata.normalize("NFD", texto.lower())
        if unicodedata.category(c) != "Mn").split())

# ¤buscar-unidades
def buscar_unidades(query: str, limite: int = 6) -> list[UnidadNormativa]:
    consulta = normalizar_consulta(query)
    palabras = {p for p in re.findall(r"[a-z0-9]+", consulta) if len(p) >= 4}
    puntuadas = []
    for norma in CORPUS_NORMATIVO_OFICIAL:
        claves = {normalizar_consulta(k) for k in norma.palabras_clave}
        texto = normalizar_consulta(norma.titulo + " " + norma.texto_oficial + " " + " ".join(norma.palabras_clave))
        score = sum(4 for clave in claves if clave in consulta)
        score += sum(1 for palabra in palabras if palabra in texto)
        # Una palabra genérica aislada no basta para convertir una consulta
        # ajena en orientación jurídica. Se exige una frase catalogada o una
        # coincidencia temática compuesta.
        if score >= 3:
            puntuadas.append((score, norma.id, norma))
    puntuadas.sort(key=lambda item: (-item[0], item[1]))
    return [norma for _, _, norma in puntuadas[:limite]]

# ¤buscar-fundamentos
def buscar_fundamentos(query: str) -> list[dict]:
    return [fundamento(norma.id) for norma in buscar_unidades(query)]

# ¤motor-rag-cerrado
class RAGCopilotEngine:
    def __init__(self, strict_citation_mode: bool = True):
        self.strict_citation_mode = strict_citation_mode

    def search(self, query: str) -> list[UnidadNormativa]:
        return buscar_unidades(query)

    def query(self, input_data: ConsultaRAGInput) -> RespuestaRAGOutput:
        coincidencias = self.search(input_data.pregunta)
        if not coincidencias:
            return RespuestaRAGOutput(
                respuesta="No puedo responder esto basándome en la normativa indexada.",
                citas_normativas=[], confianza=0.0, fuente_oficial_verificada=False,
            )
        citas = [f"{n.numero_o_titulo} ({n.articulo_o_seccion.replace('Art.', 'Artículo')}, {n.titulo}, versión {n.version})"
                 for n in coincidencias]
        respuesta = "Fuentes aplicables del corpus cerrado:\n" + "\n".join(
            f"• {n.numero_o_titulo}, {n.articulo_o_seccion} — {n.titulo}: {n.texto_oficial}"
            for n in coincidencias)
        return RespuestaRAGOutput(
            respuesta=respuesta, citas_normativas=citas,
            confianza=min(0.95, 0.70 + len(coincidencias) * 0.04),
            fuente_oficial_verificada=all(bool(n.fuente_url and n.version) for n in coincidencias),
        )

# ¤responder-consulta-normativa
def responder_consulta_normativa(input_data: ConsultaRAGInput) -> RespuestaRAGOutput:
    return RAGCopilotEngine(strict_citation_mode=True).query(input_data)
