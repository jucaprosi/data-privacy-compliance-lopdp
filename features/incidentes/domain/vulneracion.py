# ¤incidentes ¤hallazgos
"""Asistente de vulneración en ocho secciones (INC-02): reglas puras, sin base de datos.

Cada sección se guarda como una versión nueva (R6); la vigente es la última. Aquí se valida el cuerpo
de cada sección, el orden (R1), la decisión de notificar con justificación (R2) y qué informes pide
la decisión. Ningún plazo se calcula (R5): las fechas se guardan tal cual y no se comparan con nada.

Contenido mínimo de la comunicación a los titulares: Res. SPDP-SPD-2026-0040-R, art. 10.1 (verificado
en LEG-02, governance/apoyo/NORMA_TECNICA_VULNERACIONES.md). El del informe para la Autoridad remite al
Reglamento General (arts. 64-67 según LEG-02), cuyo texto no está verificado: los campos que se usan
salen de la especificación R3 y quedan pendientes de revisión legal.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

SECCIONES: dict[int, str] = {
    1: "Identificación",
    2: "Tratamientos afectados",
    3: "Titulares y datos",
    4: "Descripción y tipo",
    5: "Efectos y medidas",
    6: "Resolución",
    7: "Decisión de notificar",
    8: "Informes y notificación",
}
SECCION_DECISION = 7
SECCION_INFORMES = 8
SECCIONES_PREVIAS = tuple(range(1, SECCION_DECISION))
JUSTIFICACION_MINIMA = 20
TIPOS = ("confidencialidad", "integridad", "disponibilidad")
DECISIONES = ("spdp", "titulares", "ambos", "ninguno")
DESTINOS = ("spdp", "titulares")
TEXTO_MAXIMO = 5000
LISTA_MAXIMA = 50

# Roles (decisión del CTO 2026-11-13, ficha INC-02): implementador y coordinador completan 1 a 6;
# dpo e implementador, 7 y 8 y los informes; el coordinador ve 7 y 8 sin escribir.
ROLES_LECTURA: tuple[str, ...] = ("implementador", "coordinador", "dpo", "admin_organizacion")
ROLES_SECCIONES_PREVIAS: tuple[str, ...] = ("implementador", "coordinador")
ROLES_DECISION: tuple[str, ...] = ("implementador", "dpo")
ROLES_INFORMES: tuple[str, ...] = ("implementador", "dpo")


class SeccionInvalida(ValueError):
    """El cuerpo de la sección no cumple su forma; `faltan` dice qué campos faltan."""

    def __init__(self, mensaje: str, faltan: list[str] | None = None) -> None:
        super().__init__(mensaje)
        self.faltan = faltan or []


class DecisionSinJustificacion(ValueError):
    """Sección 7 con justificación de menos de 20 caracteres (R2), también con «ninguno»."""


class SeccionAnteriorIncompleta(ValueError):
    """Se intenta una sección o un informe sin completar las anteriores (R1)."""

    def __init__(self, seccion: int) -> None:
        super().__init__(f"Falta completar la sección {seccion}.")
        self.seccion = seccion


class RolNoAutorizado(PermissionError):
    """El rol no puede escribir esta sección."""


def roles_de_escritura(seccion: int) -> tuple[str, ...]:
    return ROLES_SECCIONES_PREVIAS if seccion in SECCIONES_PREVIAS else ROLES_DECISION


def exigir_rol(seccion: int, rol: str) -> None:
    if rol not in roles_de_escritura(seccion):
        raise RolNoAutorizado(f"El rol {rol!r} no escribe la sección {seccion}.")


def _texto(datos: dict, campo: str, faltan: list[str], obligatorio: bool = True) -> str | None:
    valor = datos.get(campo)
    if valor is None or (isinstance(valor, str) and not valor.strip()):
        if obligatorio:
            faltan.append(campo)
        return None
    if not isinstance(valor, str) or len(valor) > TEXTO_MAXIMO:
        raise SeccionInvalida(f"El campo {campo} debe ser un texto de hasta {TEXTO_MAXIMO} caracteres.")
    return valor.strip()


def _lista_textos(datos: dict, campo: str, faltan: list[str], minimo: int = 1) -> list[str]:
    valor = datos.get(campo) or []
    if not isinstance(valor, list) or len(valor) > LISTA_MAXIMA or not all(isinstance(x, str) for x in valor):
        raise SeccionInvalida(f"El campo {campo} debe ser una lista de textos.")
    limpios = [x.strip() for x in valor if x.strip()]
    if len(limpios) < minimo:
        faltan.append(campo)
    return limpios


def _entero(datos: dict, campo: str, faltan: list[str]) -> int | None:
    valor = datos.get(campo)
    if valor is None:
        faltan.append(campo)
        return None
    if isinstance(valor, bool) or not isinstance(valor, int) or valor < 0:
        raise SeccionInvalida(f"El campo {campo} debe ser un número entero no negativo.")
    return valor


def _fecha(datos: dict, campo: str, faltan: list[str]) -> str | None:
    valor = _texto(datos, campo, faltan)
    if valor is None:
        return None
    try:
        datetime.fromisoformat(valor.replace("Z", "+00:00"))
    except ValueError as exc:
        raise SeccionInvalida(f"El campo {campo} debe ser una fecha ISO 8601.") from exc
    return valor


def normalizar_seccion(seccion: int, datos: Any) -> dict[str, Any]:
    """Valida el cuerpo de una sección 1 a 7 y devuelve lo que se guarda. La 8 no se guarda aquí."""
    if seccion not in SECCIONES or seccion == SECCION_INFORMES:
        raise SeccionInvalida(f"Sección {seccion} no admitida.")
    if not isinstance(datos, dict):
        raise SeccionInvalida("El cuerpo de la sección debe ser un objeto.")
    faltan: list[str] = []
    salida: dict[str, Any]
    if seccion == 1:
        salida = {
            "fecha_conocimiento": _fecha(datos, "fecha_conocimiento", faltan),
            "detectado_por": _texto(datos, "detectado_por", faltan),
            "contacto_dpo": _texto(datos, "contacto_dpo", faltan),
        }
    elif seccion == 2:
        salida = {"tratamiento_ids": _lista_textos(datos, "tratamiento_ids", faltan)}
    elif seccion == 3:
        salida = {
            "titulares_aproximados": _entero(datos, "titulares_aproximados", faltan),
            "registros_aproximados": _entero(datos, "registros_aproximados", faltan),
            "categorias_datos": _lista_textos(datos, "categorias_datos", faltan),
        }
    elif seccion == 4:
        tipo = datos.get("tipo")
        if tipo is None:
            faltan.append("tipo")
        elif tipo not in TIPOS:
            raise SeccionInvalida("Tipo de vulneración no admitido.")
        salida = {"descripcion": _texto(datos, "descripcion", faltan), "tipo": tipo}
    elif seccion == 5:
        salida = {
            "efectos": _texto(datos, "efectos", faltan),
            "medidas": _texto(datos, "medidas", faltan),
            "recomendaciones_titulares": _texto(datos, "recomendaciones_titulares", faltan),
        }
    elif seccion == 6:
        salida = {
            "resolucion": _texto(datos, "resolucion", faltan),
            "lecciones": _lista_textos(datos, "lecciones", faltan, minimo=0),
        }
    else:
        decision = datos.get("decision")
        if decision not in DECISIONES:
            raise SeccionInvalida("Decisión no admitida.", ["decision"])
        justificacion = datos.get("justificacion")
        if not isinstance(justificacion, str) or len(justificacion.strip()) < JUSTIFICACION_MINIMA:
            raise DecisionSinJustificacion("Explica tu decisión con al menos 20 caracteres.")
        if len(justificacion) > TEXTO_MAXIMO:
            raise SeccionInvalida(f"La justificación admite hasta {TEXTO_MAXIMO} caracteres.")
        salida = {"decision": decision, "justificacion": justificacion.strip()}
    if faltan:
        raise SeccionInvalida("Completa este paso antes de continuar.", faltan)
    return salida


def destinos_de(decision: str | None) -> tuple[str, ...]:
    """Informes que pide la decisión; «ninguno» no pide informes."""
    return {"spdp": ("spdp",), "titulares": ("titulares",), "ambos": DESTINOS}.get(decision or "", ())


@dataclass(frozen=True)
class EstadoAsistente:
    """Lo que el asistente sabe de un incidente: última versión de cada sección, informes y notificaciones."""

    secciones: dict[int, dict[str, Any]]
    informes: frozenset[str]
    notificados: frozenset[str]

    @property
    def decision(self) -> str | None:
        datos = self.secciones.get(SECCION_DECISION)
        return datos.get("decision") if datos else None

    def completa(self, seccion: int) -> bool:
        if seccion in SECCIONES_PREVIAS or seccion == SECCION_DECISION:
            return seccion in self.secciones
        if SECCION_DECISION not in self.secciones:
            return False
        pedidos = set(destinos_de(self.decision))
        return pedidos <= set(self.informes) and pedidos <= set(self.notificados)

    @property
    def seccion_actual(self) -> int:
        """Primera sección sin completar; 8 si todas lo están."""
        for numero in SECCIONES:
            if not self.completa(numero):
                return numero
        return SECCION_INFORMES

    def exigir_previas(self, hasta: int) -> None:
        for numero in range(1, hasta):
            if not self.completa(numero):
                raise SeccionAnteriorIncompleta(numero)

    def a_salida(self) -> dict[str, Any]:
        return {
            "seccion_actual": self.seccion_actual,
            "decision": self.decision,
            "secciones": [
                {"id": n, "nombre": SECCIONES[n], "completa": self.completa(n), "datos": self.secciones.get(n)}
                for n in SECCIONES
            ],
            "informes": sorted(self.informes),
            "notificados": sorted(self.notificados),
        }


def informe_texto(destino: str, titulo: str, secciones: dict[int, dict[str, Any]]) -> str:
    """Informe en texto plano desde la última versión de cada sección (R3). Sin cifras de plazo."""
    s1, s3, s4, s5 = (secciones.get(n, {}) for n in (1, 3, 4, 5))
    if destino == "spdp":
        bloques = [
            "INFORME DE VULNERACIÓN DE SEGURIDAD DE DATOS PERSONALES PARA LA AUTORIDAD",
            f"Incidente: {titulo}",
            "",
            "1. Naturaleza de la vulneración",
            f"Tipo: {s4.get('tipo', '')}",
            f"Descripción: {s4.get('descripcion', '')}",
            f"Fecha en que se tuvo conocimiento: {s1.get('fecha_conocimiento', '')}",
            "",
            "2. Categorías y número aproximado de titulares y registros afectados",
            f"Categorías de datos: {', '.join(s3.get('categorias_datos', []))}",
            f"Titulares afectados (aproximado): {s3.get('titulares_aproximados', '')}",
            f"Registros afectados (aproximado): {s3.get('registros_aproximados', '')}",
            "",
            "3. Posibles consecuencias y medidas adoptadas",
            f"Efectos: {s5.get('efectos', '')}",
            f"Medidas: {s5.get('medidas', '')}",
            "",
            "4. Contacto del delegado de protección de datos",
            f"{s1.get('contacto_dpo', '')}",
            "",
            "Presenta este informe en el SISPDP (servicios.spdp.gob.ec).",
        ]
    else:
        bloques = [
            "COMUNICACIÓN A LOS TITULARES SOBRE UNA VULNERACIÓN DE SUS DATOS PERSONALES",
            "",
            "1. Qué ocurrió",
            f"{s4.get('descripcion', '')}",
            "",
            "2. Cuándo se detectó",
            f"{s1.get('fecha_conocimiento', '')}",
            "",
            "3. Qué medidas tomamos",
            f"{s5.get('medidas', '')}",
            "",
            "4. Qué te recomendamos",
            f"{s5.get('recomendaciones_titulares', '')}",
            "",
            "5. Contacto",
            f"{s1.get('contacto_dpo', '')}",
        ]
    return "\n".join(bloques) + "\n"


SECCIONES_MINIMAS_INFORME: dict[str, tuple[str, ...]] = {
    "spdp": (
        "1. Naturaleza de la vulneración",
        "2. Categorías y número aproximado de titulares y registros afectados",
        "3. Posibles consecuencias y medidas adoptadas",
        "4. Contacto del delegado de protección de datos",
    ),
    "titulares": ("1. Qué ocurrió", "2. Cuándo se detectó", "3. Qué medidas tomamos", "4. Qué te recomendamos"),
}
