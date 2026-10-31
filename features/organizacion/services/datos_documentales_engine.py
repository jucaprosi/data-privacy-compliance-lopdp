"""Motor de los datos de la organización para documentos (sala ADPA: Organización). ¤rbac-tenant

ORG-14. Guarda en `tenants` el domicilio, los contactos y el representante legal que las plantillas
de Biblioteca necesitan para rellenar `{{organizacion.*}}` y `{{representante.*}}`
(`docs/biblioteca-pmv.md`, apartado a). Todos los campos son opcionales: una organización sin
ellos sigue funcionando y Biblioteca los muestra como faltantes.

El tenant llega siempre del contexto de la sesión (lo resuelve el router); este motor no lo lee
de ningún cuerpo de petición. Los valores inválidos se rechazan con `ErrorNegocio`. La auditoría
registra qué campos cambiaron, no sus valores: el nombre y la cédula del representante son datos
personales y no se copian a `audit_events`.
"""
from __future__ import annotations

import re
from typing import Any, Optional
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from api.errores import ErrorNegocio
from app_core.audit import registrar_evento
from app_core.errors import CodigoErrorNegocio

DATOS_DOCUMENTALES_INVALIDOS = CodigoErrorNegocio(
    codigo="DATOS_DOCUMENTALES_INVALIDOS",
    status_code=422,
    mensaje_defecto="Uno de los datos de la organización para documentos no es válido.",
    action_required=None,
)
ORGANIZACION_NO_ENCONTRADA = CodigoErrorNegocio(
    codigo="ORGANIZACION_NO_ENCONTRADA",
    status_code=404,
    mensaje_defecto="Organización no encontrada.",
    action_required=None,
)

# Columna de `tenants` → longitud máxima (la misma que fija la migración).
CAMPOS_DOCUMENTALES: dict[str, int] = {
    "direccion": 300,
    "ciudad": 120,
    "provincia": 120,
    "telefono": 30,
    "correo_contacto": 254,
    "correo_privacidad": 254,
    "sitio_web": 300,
    "representante_legal_nombre": 200,
    "representante_legal_identificacion": 13,
    "representante_legal_cargo": 150,
}

# Variable de plantilla → columna de `tenants` (docs/biblioteca-pmv.md, apartado a).
VARIABLES_DOCUMENTALES: dict[str, str] = {
    "organizacion.razon_social": "razon_social",
    "organizacion.nombre_comercial": "nombre_comercial",
    "organizacion.ruc": "ruc_identificacion",
    "organizacion.sector": "sector",
    "organizacion.tamano": "tamano",
    "organizacion.direccion": "direccion",
    "organizacion.ciudad": "ciudad",
    "organizacion.telefono": "telefono",
    "organizacion.correo_contacto": "correo_contacto",
    "organizacion.correo_privacidad": "correo_privacidad",
    "organizacion.sitio_web": "sitio_web",
    "representante.nombre": "representante_legal_nombre",
    "representante.identificacion": "representante_legal_identificacion",
    "representante.cargo": "representante_legal_cargo",
}

_CORREO = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_TELEFONO = re.compile(r"^\+?[0-9 ()\-]{7,30}$")
_HOST = re.compile(r"^(?=.{1,253}$)([a-z0-9]([a-z0-9\-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$", re.IGNORECASE)


class DatosDocumentalesPatch(BaseModel):
    """Cambios a los datos para documentos. Campo ausente: no cambia; null o vacío: se borra."""

    model_config = ConfigDict(extra="forbid")

    direccion: Optional[str] = None
    ciudad: Optional[str] = None
    provincia: Optional[str] = None
    telefono: Optional[str] = None
    correo_contacto: Optional[str] = None
    correo_privacidad: Optional[str] = None
    sitio_web: Optional[str] = None
    representante_legal_nombre: Optional[str] = None
    representante_legal_identificacion: Optional[str] = None
    representante_legal_cargo: Optional[str] = None


def _invalido(campo: str, detalle: str) -> ErrorNegocio:
    return ErrorNegocio(DATOS_DOCUMENTALES_INVALIDOS, f"{campo}: {detalle}")


def es_cedula_valida(cedula: str) -> bool:
    """Cédula ecuatoriana: 10 dígitos, provincia 01-24 o 30, tercer dígito < 6 y dígito verificador módulo 10."""
    if not re.fullmatch(r"[0-9]{10}", cedula):
        return False
    provincia, tercero = int(cedula[:2]), int(cedula[2])
    if not (1 <= provincia <= 24 or provincia == 30) or tercero >= 6:
        return False
    suma = 0
    for i, digito in enumerate(cedula[:9]):
        producto = int(digito) * (2 if i % 2 == 0 else 1)
        suma += producto - 9 if producto > 9 else producto
    return (10 - suma % 10) % 10 == int(cedula[9])


def es_identificacion_valida(valor: str) -> bool:
    """Cédula, o RUC de persona natural (cédula válida seguida de un establecimiento distinto de 000)."""
    if len(valor) == 13:
        return es_cedula_valida(valor[:10]) and valor[10:].isdigit() and valor[10:] != "000"
    return es_cedula_valida(valor)


def normalizar_dato_documental(campo: str, valor: Optional[str]) -> Optional[str]:
    """Recorta, convierte el vacío en None y valida el formato del campo. Lanza ErrorNegocio."""
    if valor is None:
        return None
    valor = valor.strip()
    if not valor:
        return None
    if len(valor) > CAMPOS_DOCUMENTALES[campo]:
        raise _invalido(campo, f"admite hasta {CAMPOS_DOCUMENTALES[campo]} caracteres.")
    if campo in ("correo_contacto", "correo_privacidad"):
        if not _CORREO.fullmatch(valor):
            raise _invalido(campo, "no es un correo electrónico válido.")
        return valor.lower()
    if campo == "sitio_web":
        partes = urlparse(valor)
        if partes.scheme not in ("http", "https") or not _HOST.fullmatch(partes.hostname or ""):
            raise _invalido(campo, "debe ser una dirección web completa, p. ej. https://organizacion.ec.")
        return valor
    if campo == "telefono":
        if not _TELEFONO.fullmatch(valor) or sum(c.isdigit() for c in valor) < 7:
            raise _invalido(campo, "solo admite dígitos, espacios, guiones, paréntesis y un + inicial.")
        return valor
    if campo == "representante_legal_identificacion":
        if not es_identificacion_valida(valor):
            raise _invalido(campo, "no es una cédula ni un RUC de persona natural válidos.")
        return valor
    return valor


_SQL_LEER = """
SELECT
    id, razon_social, nombre_comercial, ruc_identificacion, sector, tamano,
    direccion,
    ciudad,
    provincia,
    telefono,
    correo_contacto,
    correo_privacidad,
    sitio_web,
    representante_legal_nombre,
    representante_legal_identificacion,
    representante_legal_cargo
FROM tenants
WHERE id = :tenant_id
"""

# Sentencia estática: columnas literales y valores enlazados; `:p_<campo>` dice si la columna se escribe.
_SQL_ACTUALIZAR = """
UPDATE tenants
SET direccion = CASE WHEN :p_direccion THEN CAST(:v_direccion AS varchar) ELSE direccion END,
    ciudad = CASE WHEN :p_ciudad THEN CAST(:v_ciudad AS varchar) ELSE ciudad END,
    provincia = CASE WHEN :p_provincia THEN CAST(:v_provincia AS varchar) ELSE provincia END,
    telefono = CASE WHEN :p_telefono THEN CAST(:v_telefono AS varchar) ELSE telefono END,
    correo_contacto = CASE WHEN :p_correo_contacto THEN CAST(:v_correo_contacto AS varchar) ELSE correo_contacto END,
    correo_privacidad = CASE WHEN :p_correo_privacidad THEN CAST(:v_correo_privacidad AS varchar) ELSE correo_privacidad END,
    sitio_web = CASE WHEN :p_sitio_web THEN CAST(:v_sitio_web AS varchar) ELSE sitio_web END,
    representante_legal_nombre = CASE WHEN :p_representante_legal_nombre THEN CAST(:v_representante_legal_nombre AS varchar) ELSE representante_legal_nombre END,
    representante_legal_identificacion = CASE WHEN :p_representante_legal_identificacion THEN CAST(:v_representante_legal_identificacion AS varchar) ELSE representante_legal_identificacion END,
    representante_legal_cargo = CASE WHEN :p_representante_legal_cargo THEN CAST(:v_representante_legal_cargo AS varchar) ELSE representante_legal_cargo END,
    updated_at = now()
WHERE id = :tenant_id
RETURNING
    id, razon_social, nombre_comercial, ruc_identificacion, sector, tamano,
    direccion,
    ciudad,
    provincia,
    telefono,
    correo_contacto,
    correo_privacidad,
    sitio_web,
    representante_legal_nombre,
    representante_legal_identificacion,
    representante_legal_cargo
"""


async def _leer_fila(session: AsyncSession, tenant_id: str) -> dict[str, Any]:
    fila = (await session.execute(
        text(_SQL_LEER),
        {"tenant_id": tenant_id},
    )).mappings().one_or_none()
    if fila is None:
        raise ErrorNegocio(ORGANIZACION_NO_ENCONTRADA)
    return dict(fila)


def _respuesta(fila: dict[str, Any]) -> dict[str, Any]:
    datos = {campo: fila[campo] for campo in CAMPOS_DOCUMENTALES}
    return {
        "tenant_id": fila["id"],
        **datos,
        "faltantes": [campo for campo, valor in datos.items() if valor is None],
    }


async def obtener_datos_documentales(session: AsyncSession, tenant_id: str) -> dict[str, Any]:
    """Datos para documentos del tenant, con la lista de campos aún sin registrar."""
    return _respuesta(await _leer_fila(session, tenant_id))


async def obtener_variables_documentales(session: AsyncSession, tenant_id: str) -> dict[str, Any]:
    """Solo consulta, para Biblioteca (BIB-201): valor de cada variable de plantilla y las faltantes.

    Devuelve `{"valores": {"organizacion.direccion": "…" | None, …}, "faltantes": [...]}`.
    """
    fila = await _leer_fila(session, tenant_id)
    valores = {variable: fila[columna] for variable, columna in VARIABLES_DOCUMENTALES.items()}
    return {
        "valores": valores,
        "faltantes": [variable for variable, valor in valores.items() if valor in (None, "")],
    }


async def actualizar_datos_documentales(
    session: AsyncSession,
    tenant_id: str,
    user_id: str,
    cambios: DatosDocumentalesPatch,
) -> dict[str, Any]:
    """Aplica los campos enviados, valida su formato y registra qué campos cambiaron en audit_events."""
    enviados = {campo: getattr(cambios, campo) for campo in cambios.model_fields_set}
    normalizados = {campo: normalizar_dato_documental(campo, valor) for campo, valor in enviados.items()}

    actual = await _leer_fila(session, tenant_id)
    cambiados = sorted(campo for campo, valor in normalizados.items() if actual[campo] != valor)
    if not cambiados:
        return _respuesta(actual)

    params: dict[str, Any] = {"tenant_id": tenant_id}
    for campo in CAMPOS_DOCUMENTALES:
        params[f"p_{campo}"] = campo in cambiados
        params[f"v_{campo}"] = normalizados.get(campo)
    fila = (await session.execute(
        text(_SQL_ACTUALIZAR),
        params,
    )).mappings().one()

    await registrar_evento(
        session=session,
        tenant_id=tenant_id,
        entity_type="tenant",
        entity_id=tenant_id,
        action="datos_documentales_updated",
        user_id=user_id,
        payload={"campos": cambiados},
    )
    return _respuesta(dict(fila))
