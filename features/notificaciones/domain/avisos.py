# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤notificaciones ¤adpa
"""NOTIF-02: textos exactos (R2, R3) y calendario de recordatorios de los avisos de versiones por revisar.

Esta es la única fuente de los textos: el correo de NOTIF-03 los reutiliza. Sin base de datos ni reloj propio.
"""
import re
from datetime import date, datetime, timedelta, timezone

ENLACE_TEXTO = "Revisar la versión"
TEXTO_FIN = "Ya no está pendiente"
LIMITE_PETICION = 200
_ECUADOR = timezone(timedelta(hours=-5))  # sin horario de verano
_MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre",
          "noviembre", "diciembre"]


def hoy_ecuador(ahora: datetime) -> date:
    return ahora.astimezone(_ECUADOR).date()


def fecha_larga(d: date) -> str:
    return f"{d.day} de {_MESES[d.month - 1]} de {d.year}"


def titulo(plantilla: str) -> str:
    return f"Versión por revisar: {plantilla}"


def _plano(texto: str | None) -> str:
    limpio = re.sub(r"[*_`#>\[\]()]", "", texto or "")
    return re.sub(r"\s+", " ", limpio).strip()


def motivo(*, origen: str, hoy: date, norma: str | None = None, articulo: str | None = None,
           vigencia: date | None = None, nombre: str | None = None, texto: str | None = None) -> str:
    if origen == "peticion":
        cuerpo = _plano(texto)
        if len(cuerpo) > LIMITE_PETICION:
            cuerpo = cuerpo[:LIMITE_PETICION] + "…"
        quien = f"Motivo del cambio: petición de {_plano(nombre)}" if _plano(nombre) else "Motivo del cambio: petición"
        return f"{quien}: «{cuerpo}»." if cuerpo else f"{quien}."
    base = f"Motivo del cambio: {_plano(norma)}"
    if _plano(articulo):
        base += f", {_plano(articulo)}"
    if vigencia is None:
        return f"{base}. La norma no indica fecha de vigencia."
    if vigencia > hoy:
        return f"{base}, que entra en vigencia el {fecha_larga(vigencia)}."
    if vigencia == hoy:
        return f"{base}, que entra en vigencia hoy."
    return f"{base}, que entró en vigencia el {fecha_larga(vigencia)}."


def programa(creado: date, vigencia: date | None) -> list[date]:
    """Fechas de los recordatorios: 7 y 1 día antes de una vigencia futura; si no, 5 y 10 días tras la creación."""
    if vigencia is not None and vigencia > creado:
        return [d for d in (vigencia - timedelta(days=7), vigencia - timedelta(days=1)) if d > creado]
    return [creado + timedelta(days=5), creado + timedelta(days=10)]


def recordatorio(*, vigencia: date | None, hoy: date, creado: date | None = None) -> str:
    if vigencia is not None and vigencia >= hoy:
        if vigencia == hoy:
            return "La norma que motiva el cambio entra en vigencia hoy."
        n = (vigencia - hoy).days
        faltan = "(falta 1 día)" if n == 1 else f"(faltan {n} días)"
        return f"La norma que motiva el cambio entra en vigencia el {fecha_larga(vigencia)} {faltan}."
    n = (hoy - (creado or hoy)).days
    return f"Sigue sin revisión técnica desde hace {'1 día' if n == 1 else f'{n} días'}."
