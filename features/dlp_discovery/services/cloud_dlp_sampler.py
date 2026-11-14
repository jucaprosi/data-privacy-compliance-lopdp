# ¤dlp-muestreo ¤seguridad-tenant
"""Motor de muestreo DLP-01: validador Módulo 10 local + puerto hacia Sensitive Data Protection (Cloud DLP).

R1 · Ningún escaneo evalúa más de `limite_muestra` filas (tope absoluto 1000) ni más infoTypes que la lista
blanca. R2 · Del motor solo sale el tipo de hallazgo y su conteo: la muestra vive en memoria durante la
llamada y nunca se registra, se persiste ni se copia a un mensaje de error
(INV_LOPDP_DLP_ECUADORIAN_CEDULA_MODULO10).

El adaptador real hacia Cloud DLP no se entrega en esta ficha: el cliente por defecto falla cerrado. Enviar
datos personales a un servicio externo exige el brief del propietario y la confirmación del CTO sobre la
región y el encargo del tratamiento (governance/operaciones/BRIEF_PROPIETARIO_DLP-01.md).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Mapping, Protocol, Sequence

from features.dlp_discovery.domain.errores import (
    AdaptadorDlpDesactivado,
    InfotypeNoPermitido,
    MuestraExcedeLimite,
)

LIMITE_MAXIMO = 1000
LIMITE_POR_DEFECTO = 250
INFOTYPES_PERMITIDOS: tuple[str, ...] = ("EC_CEDULA_MOD10", "EC_RUC", "EMAIL", "PHONE", "SALUD")
# Los que valida la plataforma sin salir de memoria; el resto se delega al puerto.
INFOTYPES_LOCALES: tuple[str, ...] = ("EC_CEDULA_MOD10", "EC_RUC")
INFOTYPES_DELEGADOS: tuple[str, ...] = ("EMAIL", "PHONE", "SALUD")
INFOTYPES_SENSIBLES: frozenset[str] = frozenset({"SALUD"})

_DIEZ_DIGITOS = re.compile(r"(?<!\d)\d{10}(?!\d)")
_TRECE_DIGITOS = re.compile(r"(?<!\d)\d{13}(?!\d)")


def cedula_valida(cedula: str) -> bool:
    """Módulo 10 de la cédula ecuatoriana: provincia 01-24 o 30, tercer dígito < 6 y dígito verificador."""
    if len(cedula) != 10 or not cedula.isdigit():
        return False
    provincia = int(cedula[:2])
    if not (1 <= provincia <= 24 or provincia == 30) or int(cedula[2]) >= 6:
        return False
    suma = 0
    for i, digito in enumerate(cedula[:9]):
        producto = int(digito) * (2 if i % 2 == 0 else 1)
        suma += producto - 9 if producto > 9 else producto
    return (10 - suma % 10) % 10 == int(cedula[9])


def _modulo11(digitos: str, coeficientes: Sequence[int], verificador: str) -> bool:
    resto = sum(int(d) * c for d, c in zip(digitos, coeficientes)) % 11
    esperado = 0 if resto == 0 else 11 - resto
    return esperado < 10 and esperado == int(verificador)


def ruc_valido(ruc: str) -> bool:
    """RUC de persona natural (cédula + establecimiento), sociedad privada (9) o entidad pública (6)."""
    if len(ruc) != 13 or not ruc.isdigit():
        return False
    provincia = int(ruc[:2])
    if not (1 <= provincia <= 24 or provincia == 30):
        return False
    tercero = int(ruc[2])
    if tercero < 6:
        return cedula_valida(ruc[:10]) and int(ruc[10:]) >= 1
    if tercero == 9:
        return int(ruc[10:]) >= 1 and _modulo11(ruc[:9], (4, 3, 2, 7, 6, 5, 4, 3, 2), ruc[9])
    if tercero == 6:
        return int(ruc[9:]) >= 1 and _modulo11(ruc[:8], (3, 2, 7, 6, 5, 4, 3, 2), ruc[8])
    return False


class ClienteDlp(Protocol):
    """Puerto hacia Sensitive Data Protection. Devuelve solo conteos por infoType, nunca los hallazgos."""

    def inspeccionar(self, fragmentos: Sequence[str], infotypes: Sequence[str]) -> Mapping[str, int]: ...


class ClienteDlpDesactivado:
    """Cliente por defecto: falla cerrado antes de enviar nada."""

    def inspeccionar(self, fragmentos: Sequence[str], infotypes: Sequence[str]) -> Mapping[str, int]:
        raise AdaptadorDlpDesactivado()


def obtener_cliente_dlp() -> ClienteDlp:
    """Esta ficha solo entrega el puerto: no hay configuración que encienda el adaptador real."""
    return ClienteDlpDesactivado()


@dataclass(frozen=True)
class ResultadoMuestreo:
    infotypes_detectados: dict[str, int]
    filas_evaluadas: int

    @property
    def contiene_datos_sensibles(self) -> bool:
        return any(self.infotypes_detectados.get(t, 0) > 0 for t in INFOTYPES_SENSIBLES)


def validar_limite(limite_muestra: int, filas: int) -> None:
    if limite_muestra < 1 or limite_muestra > LIMITE_MAXIMO or filas > limite_muestra:
        raise MuestraExcedeLimite()


def _conteos_locales(filas: Sequence[str]) -> dict[str, int]:
    cedulas = rucs = 0
    for fila in filas:
        cedulas += sum(1 for m in _DIEZ_DIGITOS.finditer(fila) if cedula_valida(m.group()))
        rucs += sum(1 for m in _TRECE_DIGITOS.finditer(fila) if ruc_valido(m.group()))
    return {"EC_CEDULA_MOD10": cedulas, "EC_RUC": rucs}


def _conteos_delegados(cliente: ClienteDlp, filas: Sequence[str]) -> dict[str, int]:
    devueltos = cliente.inspeccionar(list(filas), INFOTYPES_DELEGADOS)
    conteos: dict[str, int] = {}
    for infotype, cantidad in dict(devueltos).items():
        # Lista blanca y solo enteros: un cliente que devuelva otra cosa (p. ej. el hallazgo) se rechaza.
        if infotype not in INFOTYPES_DELEGADOS or isinstance(cantidad, bool) or not isinstance(cantidad, int):
            raise InfotypeNoPermitido()
        if cantidad < 0:
            raise InfotypeNoPermitido()
        conteos[infotype] = cantidad
    return conteos


def muestrear(filas: Sequence[str], limite_muestra: int, cliente: ClienteDlp) -> ResultadoMuestreo:
    """Valida el tope antes de leer, cuenta y descarta la muestra. Solo devuelve tipos con conteo > 0."""
    validar_limite(limite_muestra, len(filas))
    conteos = {**_conteos_locales(filas), **_conteos_delegados(cliente, filas)}
    return ResultadoMuestreo(
        infotypes_detectados={t: conteos[t] for t in INFOTYPES_PERMITIDOS if conteos.get(t, 0) > 0},
        filas_evaluadas=len(filas),
    )
