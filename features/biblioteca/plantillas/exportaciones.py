# ¤adpa
# ¤¤developer-architect
"""PLA-01 y RAT-01 frente a sus módulos canónicos (BIB-208): reglas puras, sin BD.

- PLA: instantánea del plan existente con sus IDs reales y fecha de corte. R (control de cierre) y S
  (alerta temporal) son derivados. «crítica» y «bloqueada» no tienen equivalente en la plantilla: se
  conservan como «sin equivalencia» y quedan pendientes. No se crea ni se importa ninguna acción.
- RAT: la fila conserva el ID del tratamiento existente y sus finalidades, bases y retención; lo que la
  captura difiere o añade es una propuesta documental. Nada se escribe en el RAT por esta ruta.
"""
from collections.abc import Mapping, Sequence
from datetime import date, datetime, timezone
from uuid import uuid4
from pydantic import Field
from api.errores import ErrorNegocio
from features.biblioteca.plantillas.captura import (
    Celda, EntradaFicha, Pendiente, ResultadoFicha, Valor, _Modelo, evaluar_tabla, texto, vacio,
)
from features.biblioteca.plantillas.mapas import MapaFicha

PRIORIDADES = {"alta": "Alta", "media": "Media"}
ESTADOS = {"pendiente": "Pendiente", "en_progreso": "En curso", "completada": "Cerrada"}
SIN_EQUIVALENCIA = "Sin equivalencia"
RAT_CANONICO = {"nombre_de_actividad": "nombre", "finalidades": "finalidad", "bases_legitimadoras_motivadas": "base_legal",
                "retencion_evento_y_fundamento": "plazo_conservacion", "categorias_de_datos": "categorias_datos"}


# ¤adpa
class InstantaneaPlan(_Modelo):
    instantanea_id: str
    codigo: str = "PLA-01"
    fecha_corte: date
    generada_en: datetime
    conteo: int
    ids: list[str]
    filas: list[dict[str, str]]
    celdas: list[Celda]
    pendientes: list[Pendiente]
    aceptada: bool


# ¤adpa
class PropuestaRAT(_Modelo):
    tratamiento_id: str
    campo: str
    valor_canonico: str
    valor_propuesto: str


# ¤adpa
class ResultadoRAT(_Modelo):
    ficha: ResultadoFicha
    propuestas: list[PropuestaRAT] = Field(default_factory=list)
    escrituras_rat: int = 0


def _fecha(valor) -> date | None:
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    try:
        return date.fromisoformat(str(valor)) if valor not in (None, "", 0, "0") else None
    except ValueError:
        return None


# ¤adpa
def control_de_cierre(estado: str, evidencias_aprobadas: int) -> str:
    if estado == "Cerrada":
        return "Cierre con evidencia" if evidencias_aprobadas > 0 else "Cierre bloqueado"
    return "Abierta"


# ¤adpa
def alerta_temporal(estado: str, objetivo: date | None, corte: date) -> str:
    if objetivo is None:
        return "Fecha inválida"
    if estado == "Cerrada":
        return "Cerrada"
    return "Vencida" if objetivo < corte else "En plazo"


def _fila_plan(accion: Mapping, corte: date, numero: int, pendientes: list[Pendiente]) -> dict[str, str]:
    def falta(campo: str, motivo: str) -> None:
        pendientes.append(Pendiente(campo=campo, fila=numero, motivo=motivo))

    estado = ESTADOS.get(str(accion.get("status")), SIN_EQUIVALENCIA)
    prioridad = PRIORIDADES.get(str(accion.get("priority")), SIN_EQUIVALENCIA)
    objetivo = _fecha(accion.get("end_date"))
    evidencias = [str(e) for e in accion.get("evidencias_aprobadas") or []]
    if estado == SIN_EQUIVALENCIA:
        falta("estado_declarado", f"El estado «{accion.get('status')}» no tiene equivalente en PLA-01.")
    if prioridad == SIN_EQUIVALENCIA:
        falta("prioridad", f"La prioridad «{accion.get('priority')}» no tiene equivalente en PLA-01.")
    if objetivo is None:
        falta("fecha_objetivo", "La acción no tiene una fecha objetivo real.")
    if vacio(accion.get("hallazgo_id")):
        falta("brecha_id", "El plan no enlaza esta acción con una brecha.")
    falta("tratamiento_id", "El plan canónico no guarda el tratamiento de la acción.")
    falta("requiere_eficacia", "El plan canónico no registra si la acción requiere eficacia.")
    if vacio(accion.get("deliverable")):
        falta("criterio_de_aceptacion", "La acción no declara su entregable verificable.")
    fila = {
        "accion_id": str(accion["id"]), "brecha_id": texto(accion.get("hallazgo_id") or ""),
        "requisito_id": texto(accion.get("control_ref") or ""), "accion_concreta": texto(accion.get("title") or ""),
        "prioridad": prioridad, "responsable_por_rol": texto(accion.get("owner") or ""),
        "fecha_objetivo": objetivo.isoformat() if objetivo else "", "estado_declarado": estado,
        "criterio_de_aceptacion": texto(accion.get("deliverable") or ""), "evidencia_ids": "; ".join(evidencias),
        "control_de_cierre": control_de_cierre(estado, len(evidencias)),
        "alerta_temporal": alerta_temporal(estado, objetivo, corte),
    }
    return fila


# ¤adpa
def exportar_plan(mapa: MapaFicha, acciones: Sequence[Mapping], corte: date) -> InstantaneaPlan:
    """Una fila por acción existente, en el orden del plan; comprueba que no aparece ni falta ninguna."""
    pendientes: list[Pendiente] = []
    filas = [_fila_plan(a, corte, n, pendientes) for n, a in enumerate(acciones, start=1)]
    origen = [str(a["id"]) for a in acciones]
    ids = [f["accion_id"] for f in filas]
    if len(ids) != len(origen) or set(ids) != set(origen) or len(set(ids)) != len(ids):
        raise ErrorNegocio("BIB_FICHA_INICIAL_EXPORTACION_ALTERADA")
    celdas = [Celda(hoja=c.hoja, fila=c.primera_fila + i, columna=c.columna, clave=c.clave, valor=f[c.clave])
              for i, f in enumerate(filas) for c in mapa.campos
              if c.hoja and c.columna and c.primera_fila and f.get(c.clave)]
    return InstantaneaPlan(
        instantanea_id=str(uuid4()), fecha_corte=corte, generada_en=datetime.now(timezone.utc), conteo=len(filas),
        ids=ids, filas=filas, celdas=celdas, pendientes=pendientes, aceptada=not pendientes,
    )


def _plano(valor) -> str:
    if isinstance(valor, (list, tuple)):
        return "; ".join(str(getattr(v, "value", v)) for v in valor)
    return str(getattr(valor, "value", valor) or "")


# ¤adpa
def proponer_rat(mapa: MapaFicha, entrada: EntradaFicha, actividades: Sequence[Mapping]) -> ResultadoRAT:
    """La fila RAT-01 se ancla en un tratamiento existente; lo distinto queda como propuesta documental."""
    canonicas = {str(a["id"]): a for a in actividades}
    filas: list[dict[str, Valor]] = []
    propuestas: list[PropuestaRAT] = []
    sin_ancla: list[Pendiente] = []
    for numero, fila in enumerate(entrada.filas, start=1):
        ident = texto(fila.get("tratamiento_id") or "")
        actividad = canonicas.get(ident)
        if actividad is None:
            sin_ancla.append(Pendiente(campo="tratamiento_id", fila=numero,
                                       motivo="Registre primero la actividad en el RAT; aquí no se crea."))
            continue
        conservada = dict(fila)
        for clave, origen in RAT_CANONICO.items():
            canonico, capturado = _plano(actividad.get(origen)), fila.get(clave)
            if canonico:
                conservada[clave] = canonico
            if not vacio(capturado) and texto(capturado) != canonico:
                propuestas.append(PropuestaRAT(tratamiento_id=ident, campo=clave, valor_canonico=canonico,
                                               valor_propuesto=texto(capturado)))
        filas.append(conservada)
    ficha = evaluar_tabla(mapa, entrada.model_copy(update={"filas": filas}), frozenset(canonicas))
    if sin_ancla:
        ficha = ficha.model_copy(update={"pendientes": sin_ancla + ficha.pendientes, "aceptada": False})
    return ResultadoRAT(ficha=ficha, propuestas=propuestas)
