"""Dominio del cuestionario de garantías de encargados (TER-02).
`¤terceros` `¤seguridad` `¤evidencias`
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Literal

# Constante de SEC-12: el código devuelto para token no válido (404 por diseño)
CODIGO_ENLACE_NO_VALIDO: int = 404
VERSION_CUESTIONARIO: str = "TER-02.1"
DIAS_VIGENCIA_MIN: int = 1
DIAS_VIGENCIA_MAX: int = 30
DIAS_VIGENCIA_DEFAULT: int = 7
MAX_TAMANO_ARCHIVO_BYTES: int = 10 * 1024 * 1024  # 10 MB

TipoCampo = Literal["si_no", "si_no_evidencia", "texto", "fecha", "texto_evidencia"]
EstadoCuestionario = Literal["enviado", "respondido", "conforme", "correccion", "rechazado"]
DecisionRevision = Literal["conforme", "correccion", "rechazado"]


@dataclass(frozen=True)
class PreguntaCuestionario:
    id: str
    enunciado: str
    tipo: TipoCampo
    obligatoria: bool
    cita: str
    condicional: str | None = None

    def serializar(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "enunciado": self.enunciado,
            "tipo": self.tipo,
            "obligatoria": self.obligatoria,
            "cita": self.cita,
            "condicional": self.condicional,
        }


@dataclass
class Cuestionario:
    id: str
    tenant_id: str
    tercero_id: str
    token_hash: str
    caduca_en: datetime
    creado_por: str
    creado_en: datetime
    estado: EstadoCuestionario = "enviado"
    version_cuestionario: str = VERSION_CUESTIONARIO
    respuestas: dict[str, Any] | None = None
    evidencias: list[dict[str, Any]] | None = None
    revisado_por: str | None = None
    revisado_en: datetime | None = None
    comentario_revision: str | None = None
    informe_sha256: str | None = None
    proxima_revision: date | None = None


PREGUNTAS_TER_02_1: tuple[PreguntaCuestionario, ...] = (
    PreguntaCuestionario(
        id="G01",
        enunciado="¿Existe un contrato vigente con el responsable que regula el tratamiento de los datos personales?",
        tipo="si_no_evidencia",
        obligatoria=True,
        cita="LOPDP art. 34; Reglamento art. 41",
    ),
    PreguntaCuestionario(
        id="G02",
        enunciado="¿Trata los datos solo según las instrucciones del responsable y para la finalidad del contrato?",
        tipo="si_no",
        obligatoria=True,
        cita="LOPDP art. 34; Reglamento art. 41",
    ),
    PreguntaCuestionario(
        id="G03",
        enunciado="¿Todo el personal con acceso a los datos firmó un compromiso de confidencialidad?",
        tipo="si_no_evidencia",
        obligatoria=True,
        cita="LOPDP art. 47 num. 10",
    ),
    PreguntaCuestionario(
        id="G04",
        enunciado="¿Tiene documentadas las medidas técnicas y organizativas de seguridad que aplica a estos datos?",
        tipo="si_no_evidencia",
        obligatoria=True,
        cita="LOPDP art. 37; art. 10 lit. j); art. 47 num. 2",
    ),
    PreguntaCuestionario(
        id="G05",
        enunciado="Fecha de la última evaluación de la eficacia de esas medidas",
        tipo="fecha",
        obligatoria=True,
        cita="LOPDP art. 47 num. 3; art. 37",
    ),
    PreguntaCuestionario(
        id="G06",
        enunciado="¿Subcontrata a otros encargados (subencargados) para este tratamiento?",
        tipo="si_no",
        obligatoria=True,
        cita="Reglamento art. 45",
    ),
    PreguntaCuestionario(
        id="G07",
        enunciado="Subencargados (nombre, servicio y país de cada uno) y la cláusula del contrato o la autorización escrita del responsable que los permite",
        tipo="texto_evidencia",
        obligatoria=False,
        cita="Reglamento art. 45",
        condicional="G06",
    ),
    PreguntaCuestionario(
        id="G08",
        enunciado="¿Tiene un procedimiento para trasladar al responsable las solicitudes de los titulares y ayudarle a atenderlas?",
        tipo="si_no_evidencia",
        obligatoria=True,
        cita="Reglamento art. 42; LOPDP art. 47 num. 11",
    ),
    PreguntaCuestionario(
        id="G09",
        enunciado="¿Avisa al responsable de toda vulneración de seguridad dentro del término de dos días desde que la conoce?",
        tipo="si_no_evidencia",
        obligatoria=True,
        cita="LOPDP art. 43",
    ),
    PreguntaCuestionario(
        id="G10",
        enunciado="Contacto para avisos de vulneración (nombre, correo y teléfono)",
        tipo="texto",
        obligatoria=True,
        cita="LOPDP art. 43",
    ),
    PreguntaCuestionario(
        id="G11",
        enunciado="¿Devuelve o elimina los datos, con todas sus copias, al terminar el servicio y lo certifica por escrito?",
        tipo="si_no_evidencia",
        obligatoria=True,
        cita="LOPDP art. 34; Reglamento art. 46",
    ),
    PreguntaCuestionario(
        id="G12",
        enunciado="¿Permite auditorías o inspecciones del responsable o de un auditor acreditado?",
        tipo="si_no",
        obligatoria=True,
        cita="LOPDP art. 47 num. 14; Reglamento art. 47",
    ),
    PreguntaCuestionario(
        id="G13",
        enunciado="Fecha de la última auditoría externa de protección de datos o de seguridad",
        tipo="fecha",
        obligatoria=False,
        cita="LOPDP art. 47 num. 14; Reglamento art. 47",
    ),
    PreguntaCuestionario(
        id="G14",
        enunciado="¿Trata, almacena o accede a los datos desde fuera del Ecuador?",
        tipo="si_no",
        obligatoria=True,
        cita="LOPDP arts. 55, 56 y 57",
    ),
    PreguntaCuestionario(
        id="G15",
        enunciado="Países y garantía de cada transferencia (país con nivel adecuado o garantías adecuadas)",
        tipo="texto_evidencia",
        obligatoria=False,
        cita="LOPDP arts. 56 y 57",
        condicional="G14",
    ),
)
