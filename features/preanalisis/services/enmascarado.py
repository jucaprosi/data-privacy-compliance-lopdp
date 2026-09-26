"""DLP de la sala: enmascarado PARCIAL de datos personales de Ecuador antes de enviar texto a un modelo."""
from __future__ import annotations

import re
import unicodedata

from app_core.dlp_sanitizer import validar_cedula_ecuatoriana

_ESP = r"[ \u00a0\t]"
_EMAIL = re.compile(rf"(?<![\w.+-])[\w.+-]+{_ESP}*@{_ESP}*[\w-]+(?:\.[\w-]+)+")
# Secuencia de grupos de dígitos separados por espacio, punto, guion o paréntesis (máx. 2 separadores seguidos).
_RUN = re.compile(r"\d+(?:[ .\-()]{1,2}\d+)*")
_GRUPO = re.compile(r"\d+")
_TELEFONO = re.compile(r"(?:(?:00)?593[2-7]\d{7}|(?:00)?5939\d{8}|0[2-7]\d{7}|09\d{8})")
_DECIMAL = re.compile(r"[.,]\d{1,2}(?!\d)")
_MAX_GRUPOS_VENTANA = 16


def _es_ruc(valor: str) -> bool:
    provincia = int(valor[:2])
    if not (1 <= provincia <= 24 or provincia == 30) or valor[10:] == "000":
        return False
    return validar_cedula_ecuatoriana(valor[:10]) or valor[2] in "69"


def _clasificar(d: str) -> str | None:
    if len(d) == 10 and validar_cedula_ecuatoriana(d):
        return "[CEDULA_ENMASCARADA]"
    if len(d) == 13 and _es_ruc(d):
        return "[RUC_ENMASCARADO]"
    if _TELEFONO.fullmatch(d):
        return "[TELEFONO_ENMASCARADO]"
    return None


def _es_formato_miles(texto_ventana: str) -> bool:
    """1.234.567.890 (miles con punto): es un importe, no un identificador."""
    partes = texto_ventana.split(".")
    return (
        len(partes) >= 3
        and partes[0].isdigit()
        and 1 <= len(partes[0]) <= 3
        and all(p.isdigit() and len(p) == 3 for p in partes[1:])
    )


def enmascarar_pii(texto: str) -> tuple[str, int]:
    """Devuelve ``(texto_enmascarado, cantidad_de_reemplazos)``. Parcial: no detecta nombres propios.

    El texto se normaliza NFKC (anchos completos, NBSP) antes de detectar.
    """
    if not texto:
        return texto, 0
    texto = unicodedata.normalize("NFKC", texto)
    cuenta = 0

    def _correo(_m: re.Match[str]) -> str:
        nonlocal cuenta
        cuenta += 1
        return "[CORREO_ENMASCARADO]"

    t = _EMAIL.sub(_correo, texto)

    def _secuencia(m: re.Match[str]) -> str:
        nonlocal cuenta
        run = m.group(0)
        grupos = list(_GRUPO.finditer(run))
        salida: list[str] = []
        pos = 0
        i = 0
        while i < len(grupos):
            hallado = False
            for j in range(min(len(grupos) - 1, i + _MAX_GRUPOS_VENTANA - 1), i - 1, -1):
                ini, fin = grupos[i].start(), grupos[j].end()
                marca = _clasificar("".join(g.group(0) for g in grupos[i : j + 1]))
                if marca is None:
                    continue
                ventana = run[ini:fin]
                if _es_formato_miles(ventana):
                    continue
                if _DECIMAL.match(t, m.start() + fin):
                    continue
                # Absorbe signo "+" o "(" de apertura y ")" de cierre adyacentes.
                if ini > pos and run[ini - 1] in "+(":
                    ini -= 1
                elif ini == 0 and m.start() > 0 and t[m.start() - 1] in "+(":
                    salida.append("\0")  # marca: retroceder un carácter del prefijo
                if fin < len(run) and run[fin] == ")":
                    fin += 1
                salida.append(run[pos:ini])
                salida.append(marca)
                pos = fin
                cuenta += 1
                i = j + 1
                hallado = True
                break
            if not hallado:
                i += 1
        salida.append(run[pos:])
        return "".join(salida)

    # Se procesa con un pase simple: el prefijo "+"/"(" previo al run se absorbe en un segundo paso.
    t = _RUN.sub(_secuencia, t)
    t = t.replace("+\0", "").replace("(\0", "").replace("\0", "")
    return t, cuenta
