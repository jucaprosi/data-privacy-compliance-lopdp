"""Alta de la organización en siete pasos (sala ADPA: Organización). ¤rbac-tenant ¤alta-organizacion

ORG-16. Cada paso se guarda en el servidor por la compuerta de su sala; el estado del asistente
se deriva de los datos (R2): no se guarda un `isConfigured`. La organización y la identidad llegan
del contexto de la sesión; los cuerpos no las admiten. Los catálogos de sugerencias son solo
estructura (D-5): ningún dato de otra organización.
"""
from __future__ import annotations

import unicodedata
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, ValidationError
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from api.errores import ErrorNegocio
from app_core.audit import registrar_evento
from app_core.errors import TENANT_SIZE_NOT_CONFIGURED, CodigoErrorNegocio
from features.organizacion.domain.models import AreaCreate, AreaUpdate
from features.organizacion.services.areas_engine import create_area, list_areas, update_area
from features.organizacion.services.configuracion_engine import (
    actualizar_perfil_tenant,
    get_tenant_config,
)
from features.organizacion.services.contexto_tenant import fijar_tenant
from features.organizacion.services.datos_documentales_engine import (
    DatosDocumentalesPatch,
    actualizar_datos_documentales,
)
from features.organizacion.services.invitaciones_personas_engine import (
    contar_personas_clave,
    registrar_personas_clave,
)

PASO_DESCONOCIDO = CodigoErrorNegocio(
    codigo="PASO_DESCONOCIDO",
    status_code=422,
    mensaje_defecto="El paso del alta no existe.",
    action_required=None,
)
PASO_PREVIO_INCOMPLETO = CodigoErrorNegocio(
    codigo="PASO_PREVIO_INCOMPLETO",
    status_code=409,
    mensaje_defecto="Faltan los pasos obligatorios (perfil y áreas) para completar el resumen.",
    action_required=None,
)
PASO_NO_DISPONIBLE = CodigoErrorNegocio(
    codigo="PASO_NO_DISPONIBLE",
    status_code=501,
    mensaje_defecto="Este paso aún no se puede guardar en el servidor; puede saltarse.",
    action_required=None,
)
PASO_INVALIDO = CodigoErrorNegocio(
    codigo="PASO_INVALIDO",
    status_code=422,
    mensaje_defecto="Los datos del paso no son válidos.",
    action_required=None,
)

PASOS: tuple[str, ...] = ("perfil", "sedes", "areas", "tratamientos", "terceros", "personas", "resumen")

_PREFIJO_ORIGEN = "plantilla:alta-"


# ------------------------------------------------------------------------- cuerpos de cada paso

class _Cuerpo(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PasoPerfil(_Cuerpo):
    razon_social: str = Field(min_length=1, max_length=255)
    nombre_comercial: Optional[str] = Field(default=None, max_length=255)
    ruc: str = Field(pattern=r"^[0-9]{13}$")
    sector: str = Field(min_length=1, max_length=100)
    tamano: Literal["micro", "pequena", "mediana", "corporativo"]
    naturaleza: Literal["publica", "privada", "mixta"]
    rol_datos: Literal["responsable", "encargado", "ambos"]
    actividades_riesgo: list[str] = Field(default_factory=list, max_length=30)


class PasoSedes(_Cuerpo):
    domicilio: str = Field(min_length=1, max_length=300)
    ciudad: str = Field(min_length=1, max_length=120)
    provincia: str = Field(min_length=1, max_length=120)


class _AreaAlta(_Cuerpo):
    nombre: str = Field(min_length=1, max_length=255)
    codigo: Optional[str] = Field(default=None, max_length=50)


class PasoAreas(_Cuerpo):
    areas: list[_AreaAlta] = Field(min_length=1, max_length=60)


class _Ajuste(_Cuerpo):
    indice: int = Field(ge=0)
    nombre: Optional[str] = Field(default=None, min_length=1, max_length=255)
    finalidad: Optional[str] = Field(default=None, min_length=1, max_length=500)


class PasoTratamientos(_Cuerpo):
    aceptados: list[int] = Field(default_factory=list, max_length=60)
    ajustes: list[_Ajuste] = Field(default_factory=list, max_length=60)


class PasoTerceros(_Cuerpo):
    aceptados: list[int] = Field(default_factory=list, max_length=60)


class _PersonaClave(_Cuerpo):
    nombre: str = Field(min_length=1, max_length=200)
    cargo: str = Field(min_length=1, max_length=150)
    area_id: Optional[str] = Field(default=None, max_length=64)
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", max_length=254)
    rol: Literal["coordinador", "responsable_area", "dpo"]


class PasoPersonas(_Cuerpo):
    personas: list[_PersonaClave] = Field(min_length=1, max_length=40)


class PasoResumen(_Cuerpo):
    pass


_MODELOS: dict[str, type[BaseModel]] = {
    "perfil": PasoPerfil,
    "sedes": PasoSedes,
    "areas": PasoAreas,
    "tratamientos": PasoTratamientos,
    "terceros": PasoTerceros,
    "personas": PasoPersonas,
    "resumen": PasoResumen,
}


# ----------------------------------------------------------------------- catálogo (solo estructura)

_GENERAL = {
    "tratamientos": [
        {"nombre": "Gestión de clientes", "finalidad": "Atender y dar seguimiento a clientes.", "base_legal": "CUMPLIMIENTO_CONTRATO"},
        {"nombre": "Gestión de personal", "finalidad": "Administrar la relación laboral.", "base_legal": "CUMPLIMIENTO_CONTRATO"},
        {"nombre": "Gestión de proveedores", "finalidad": "Contratar y pagar a proveedores.", "base_legal": "CUMPLIMIENTO_CONTRATO"},
    ],
    "terceros": [
        {"tipo": "Proveedor de nube", "descripcion": "Aloja información de la organización."},
        {"tipo": "Contabilidad externa", "descripcion": "Procesa información tributaria y de nómina."},
    ],
}

SUGERENCIAS_POR_SECTOR: dict[str, dict[str, list[dict[str, str]]]] = {
    "salud": {
        "tratamientos": [
            {"nombre": "Admisión de pacientes", "finalidad": "Identificar al paciente y abrir su ficha.", "base_legal": "OBLIGACION_LEGAL"},
            {"nombre": "Historia clínica", "finalidad": "Registrar la atención y el seguimiento del paciente.", "base_legal": "OBLIGACION_LEGAL"},
            {"nombre": "Agendamiento de citas", "finalidad": "Gestionar y recordar citas.", "base_legal": "CUMPLIMIENTO_CONTRATO"},
        ],
        "terceros": [
            {"tipo": "Laboratorio clínico", "descripcion": "Recibe órdenes y devuelve resultados."},
            {"tipo": "Software médico", "descripcion": "Aloja la historia clínica electrónica."},
        ],
    },
    "educacion": {
        "tratamientos": [
            {"nombre": "Matrícula de estudiantes", "finalidad": "Inscribir y administrar la matrícula.", "base_legal": "CUMPLIMIENTO_CONTRATO"},
            {"nombre": "Registro académico", "finalidad": "Registrar calificaciones y asistencia.", "base_legal": "OBLIGACION_LEGAL"},
        ],
        "terceros": [{"tipo": "Plataforma de aula virtual", "descripcion": "Aloja actividades y calificaciones."}],
    },
    "financiero": {
        "tratamientos": [
            {"nombre": "Alta de socios o clientes", "finalidad": "Conocer al cliente y abrir productos.", "base_legal": "OBLIGACION_LEGAL"},
            {"nombre": "Gestión de crédito", "finalidad": "Evaluar y administrar operaciones de crédito.", "base_legal": "CUMPLIMIENTO_CONTRATO"},
        ],
        "terceros": [{"tipo": "Buró de crédito", "descripcion": "Consulta de historial crediticio."}],
    },
    "comercio": {
        "tratamientos": [
            {"nombre": "Ventas y facturación", "finalidad": "Emitir comprobantes y cobrar.", "base_legal": "OBLIGACION_LEGAL"},
            {"nombre": "Marketing directo", "finalidad": "Enviar promociones a quien lo autoriza.", "base_legal": "CONSENTIMIENTO"},
        ],
        "terceros": [{"tipo": "Pasarela de pago", "descripcion": "Procesa cobros con tarjeta."}],
    },
    "general": _GENERAL,
}


def _clave_sector(sector: Optional[str]) -> Optional[str]:
    """None sin sector; la clave del catálogo si el sector coincide; «general» en otro caso."""
    if not sector or not sector.strip():
        return None
    base = unicodedata.normalize("NFKD", sector.strip().lower()).encode("ascii", "ignore").decode()
    for clave in SUGERENCIAS_POR_SECTOR:
        if clave != "general" and clave in base:
            return clave
    return "general"


async def obtener_sugerencias(session: AsyncSession, tenant_id: str) -> dict[str, list[dict[str, Any]]]:
    """Catálogo de estructura según el sector del paso 1; sin sector, listas vacías."""
    clave = _clave_sector((await get_tenant_config(session, tenant_id))["sector"])
    if clave is None:
        return {"tratamientos": [], "terceros": []}
    catalogo = SUGERENCIAS_POR_SECTOR[clave]
    return {
        "tratamientos": [{"indice": i, **t} for i, t in enumerate(catalogo["tratamientos"])],
        "terceros": [{"indice": i, **t} for i, t in enumerate(catalogo["terceros"])],
    }


# ---------------------------------------------------------------------------- estado derivado (R2)

def _rat():
    """Compuerta de RAT, importada al usarla: RAT importa esta sala y un import de módulo sería circular."""
    from features.rat import rat_service
    return rat_service


async def obtener_estado_alta(session: AsyncSession, tenant_id: str) -> dict[str, Any]:
    await fijar_tenant(session, tenant_id)
    fila = (await session.execute(
        text("SELECT tamano, nombre_comercial, direccion FROM tenants WHERE id = :t"),
        {"t": tenant_id},
    )).mappings().one_or_none()
    if fila is None:
        raise ErrorNegocio("ORGANIZACION_NO_ENCONTRADA", "Organización no encontrada.", status_code=404)
    areas = await list_areas(session, tenant_id)
    actividades = await _rat().listar_actividades_rat(session, tenant_id)
    personas = await contar_personas_clave(session, tenant_id)

    completo = {
        "perfil": fila["tamano"] is not None and bool((fila["nombre_comercial"] or "").strip()),
        "sedes": bool((fila["direccion"] or "").strip()),
        "areas": bool(areas),
        "tratamientos": any((a.origen or "").startswith(_PREFIJO_ORIGEN) for a in actividades),
        "terceros": False,
        "personas": personas > 0,
    }
    completo["resumen"] = completo["perfil"] and completo["areas"]
    return {
        "pasos": [{"id": paso, "completo": completo[paso]} for paso in PASOS],
        "completo": completo["resumen"],
    }


# --------------------------------------------------------------------------------- guardar un paso

async def _guardar_perfil(session, tenant_id, user_id, c: PasoPerfil) -> None:
    await actualizar_perfil_tenant(session, tenant_id, user_id, {
        "razon_social": c.razon_social.strip(),
        "nombre_comercial": (c.nombre_comercial or c.razon_social).strip(),
        "ruc": c.ruc,
        "sector": c.sector.strip(),
        "tamano": c.tamano,
        "naturaleza": c.naturaleza,
        "rol_datos": c.rol_datos,
        "actividades_riesgo": [a.strip() for a in c.actividades_riesgo if a.strip()],
    })


async def _guardar_sedes(session, tenant_id, user_id, c: PasoSedes) -> None:
    # Domicilio y ciudad: columnas documentales de ORG-14, por su compuerta. La provincia es solo un dato
    # de la sede principal que el alta guarda y muestra: no es un campo documental ni variable de plantilla.
    await actualizar_datos_documentales(
        session, tenant_id, user_id,
        DatosDocumentalesPatch(direccion=c.domicilio, ciudad=c.ciudad),
    )
    await session.execute(
        text("UPDATE tenants SET provincia = :provincia, updated_at = now() WHERE id = :t"),
        {"provincia": c.provincia.strip(), "t": tenant_id},
    )


async def _guardar_areas(session, tenant_id, user_id, c: PasoAreas) -> None:
    existentes = await list_areas(session, tenant_id)
    for entrada in c.areas:
        nombre = entrada.nombre.strip()
        codigo = (entrada.codigo or "").strip() or None
        previa = next(
            (
                a for a in existentes
                if (codigo and a.get("codigo") == codigo) or a["nombre"].casefold() == nombre.casefold()
            ),
            None,
        )
        if previa:
            await update_area(session, tenant_id, previa["id"], AreaUpdate(nombre=nombre, codigo=codigo))
        else:
            creada = await create_area(session, tenant_id, AreaCreate(nombre=nombre, codigo=codigo))
            existentes.append(creada)


async def _guardar_tratamientos(session, tenant_id, user_id, c: PasoTratamientos) -> None:
    from features.rat.domain.models import ActividadRAT, BaseLegitimacion

    rat_service = _rat()
    clave = _clave_sector((await get_tenant_config(session, tenant_id))["sector"])
    if clave is None:
        raise ErrorNegocio(PASO_INVALIDO, "Completa el perfil (sector) antes de elegir tratamientos.")
    catalogo = SUGERENCIAS_POR_SECTOR[clave]["tratamientos"]
    ajustes = {a.indice: a for a in c.ajustes}
    for indice in sorted(set(c.aceptados) | set(ajustes)):
        if indice >= len(catalogo):
            raise ErrorNegocio(PASO_INVALIDO, f"El índice {indice} no existe en el catálogo.")
    existentes = {
        a.codigo: a for a in await rat_service.listar_actividades_rat(session, tenant_id)
    }
    for indice in sorted(set(c.aceptados)):
        modelo, ajuste = catalogo[indice], ajustes.get(indice)
        codigo = f"ALTA-{clave.upper()}-{indice + 1:02d}"
        nombre = (ajuste.nombre if ajuste and ajuste.nombre else modelo["nombre"])
        finalidad = (ajuste.finalidad if ajuste and ajuste.finalidad else modelo["finalidad"])
        if codigo in existentes:
            await rat_service.editar_actividad_rat(
                session, tenant_id, existentes[codigo].id,
                {"nombre": nombre, "finalidad": finalidad}, user_id,
            )
        else:
            await rat_service.registrar_actividad_rat(session, ActividadRAT(
                tenant_id=tenant_id, codigo=codigo, nombre=nombre, finalidad=finalidad,
                base_legal=BaseLegitimacion(modelo["base_legal"]),
                origen=f"{_PREFIJO_ORIGEN}{clave}",
            ), user_id)


async def _guardar_terceros(session, tenant_id, user_id, c: PasoTerceros) -> None:
    # `terceros_service` y `transferencias_service` solo exponen lectura; `pais_destino` y
    # `nivel_proteccion` son obligatorios y un catálogo de estructura no los trae.
    raise ErrorNegocio(PASO_NO_DISPONIBLE)


async def _guardar_personas(session, tenant_id, user_id, c: PasoPersonas) -> None:
    if (await get_tenant_config(session, tenant_id))["tamano"] is None:
        raise ErrorNegocio(TENANT_SIZE_NOT_CONFIGURED)
    await registrar_personas_clave(session, tenant_id, user_id, [p.model_dump() for p in c.personas])


async def _guardar_resumen(session, tenant_id, user_id, c: PasoResumen) -> None:
    if not (await obtener_estado_alta(session, tenant_id))["completo"]:
        raise ErrorNegocio(PASO_PREVIO_INCOMPLETO)


_GUARDADORES = {
    "perfil": _guardar_perfil,
    "sedes": _guardar_sedes,
    "areas": _guardar_areas,
    "tratamientos": _guardar_tratamientos,
    "terceros": _guardar_terceros,
    "personas": _guardar_personas,
    "resumen": _guardar_resumen,
}


async def guardar_paso(
    session: AsyncSession, tenant_id: str, user_id: str, paso_id: str, cuerpo: dict[str, Any],
) -> dict[str, Any]:
    """Valida y guarda un paso por la compuerta de su sala; audita sin copiar valores (R6)."""
    if paso_id not in _MODELOS:
        raise ErrorNegocio(PASO_DESCONOCIDO)
    try:
        validado = _MODELOS[paso_id].model_validate(cuerpo)
    except ValidationError as exc:
        campos = sorted({".".join(str(p) for p in e["loc"]) for e in exc.errors()})
        raise ErrorNegocio(PASO_INVALIDO, f"Campos no válidos: {', '.join(campos)}") from exc
    await fijar_tenant(session, tenant_id, user_id)
    await _GUARDADORES[paso_id](session, tenant_id, user_id, validado)
    await registrar_evento(
        session=session,
        tenant_id=tenant_id,
        entity_type="organizacion_alta",
        entity_id=tenant_id,
        action=f"paso_{paso_id}",
        user_id=user_id,
        payload={"paso": paso_id},
    )
    return {"paso": paso_id, "completo": True}
