# ¤dlp-muestreo ¤rat ¤seguridad-tenant
"""Compuerta pública de la sala Descubrimiento DLP Muestreado."""
# === DLP-01 ===
import uuid
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from features.dlp_discovery.domain.errores import (
    ActividadRatNoEncontrada,
    AdaptadorDlpDesactivado,
    CategoriaNoDetectada,
    ErrorDlp,
    EscaneoInexistente,
    InfotypeNoPermitido,
    MuestraExcedeLimite,
)
from features.dlp_discovery.models import EscaneoMuestreado
from features.dlp_discovery.schemas import EscaneoSalida, SolicitudEscaneo, SolicitudVinculo
from features.dlp_discovery.services.cloud_dlp_sampler import (
    INFOTYPES_PERMITIDOS,
    LIMITE_MAXIMO,
    LIMITE_POR_DEFECTO,
    ClienteDlp,
    ClienteDlpDesactivado,
    cedula_valida,
    muestrear,
    obtener_cliente_dlp,
    ruc_valido,
    validar_limite,
)

__all__ = [
    "ActividadRatNoEncontrada", "AdaptadorDlpDesactivado", "CategoriaNoDetectada", "ClienteDlp",
    "ClienteDlpDesactivado", "ErrorDlp", "EscaneoMuestreado", "EscaneoInexistente", "EscaneoSalida",
    "INFOTYPES_PERMITIDOS", "InfotypeNoPermitido", "LIMITE_MAXIMO", "LIMITE_POR_DEFECTO", "MuestraExcedeLimite",
    "ROLES_ESCANEO", "ROLES_CONSULTA", "ROLES_VINCULO", "SolicitudEscaneo", "SolicitudVinculo",
    "CATEGORIA_RAT", "cedula_valida", "escanear_muestra", "listar_escaneos", "obtener_cliente_dlp",
    "ruc_valido", "validar_limite", "vincular_al_rat",
]

# Escanean quienes pueden ver el dato de origen; el DPO solo lee; al RAT escribe el coordinador (como en RAT).
ROLES_ESCANEO: tuple[str, ...] = ("admin_organizacion", "coordinador", "implementador")
# El auditor lee los escaneos de su organización (solo tipos y conteos); no lanza ni vincula (decisión del CTO).
ROLES_CONSULTA: tuple[str, ...] = ROLES_ESCANEO + ("dpo", "auditor")
ROLES_VINCULO: tuple[str, ...] = ("coordinador",)

# Nombre de la categoría de datos que se agrega a la actividad del RAT.
CATEGORIA_RAT: dict[str, str] = {
    "EC_CEDULA_MOD10": "Número de cédula de identidad",
    "EC_RUC": "Número de RUC",
    "EMAIL": "Correo electrónico",
    "PHONE": "Número de teléfono",
    "SALUD": "Datos de salud",
}


def a_salida(e: EscaneoMuestreado, filas_evaluadas: int | None = None) -> EscaneoSalida:
    return EscaneoSalida(
        id=str(e.id), fuente_nombre=e.fuente_nombre, limite_muestra=e.limite_muestra,
        filas_evaluadas=filas_evaluadas, infotypes_detectados=dict(e.infotypes_detectados),
        contiene_datos_sensibles=e.contiene_datos_sensibles, actividad_rat_id=e.actividad_rat_id,
        creado_por=e.creado_por, creado_en=e.creado_en,
    )


async def escanear_muestra(
    session: AsyncSession, tenant_id: str, user_id: str | None, fuente_nombre: str,
    limite_muestra: int, filas: Sequence[str], cliente: ClienteDlp,
) -> EscaneoSalida:
    """Cuenta los tipos de datos de la muestra y guarda solo los conteos. La muestra no sale de esta llamada."""
    resultado = muestrear(filas, limite_muestra, cliente)
    escaneo = EscaneoMuestreado(
        id=uuid.uuid4(), tenant_id=tenant_id, fuente_nombre=fuente_nombre.strip(),
        limite_muestra=limite_muestra, infotypes_detectados=resultado.infotypes_detectados,
        contiene_datos_sensibles=resultado.contiene_datos_sensibles, creado_por=user_id,
    )
    session.add(escaneo)
    await session.flush()
    await session.refresh(escaneo)
    salida = a_salida(escaneo, resultado.filas_evaluadas)
    await session.commit()
    return salida


async def listar_escaneos(session: AsyncSession, tenant_id: str, limite: int = 50) -> list[EscaneoSalida]:
    filas = await session.execute(
        select(EscaneoMuestreado)
        .where(EscaneoMuestreado.tenant_id == tenant_id)
        .order_by(EscaneoMuestreado.creado_en.desc())
        .limit(limite)
    )
    return [a_salida(e) for e in filas.scalars()]


async def vincular_al_rat(
    session: AsyncSession, tenant_id: str, user_id: str | None, escaneo_id: str,
    actividad_rat_id: str, infotypes: Sequence[str],
) -> dict:
    """Agrega a la actividad del RAT las categorías confirmadas (solo las encontradas en el escaneo)."""
    from app_core.pasillo import rat as pasillo_rat

    try:
        clave = uuid.UUID(escaneo_id)
    except ValueError:
        raise EscaneoInexistente() from None
    escaneo = (
        await session.execute(
            select(EscaneoMuestreado).where(
                EscaneoMuestreado.id == clave, EscaneoMuestreado.tenant_id == tenant_id
            )
        )
    ).scalar_one_or_none()
    if escaneo is None:
        raise EscaneoInexistente()
    elegidos = list(dict.fromkeys(infotypes))
    if not elegidos or any(escaneo.infotypes_detectados.get(t, 0) <= 0 for t in elegidos):
        raise CategoriaNoDetectada()
    nombre = await pasillo_rat.agregar_categorias_datos(
        session, tenant_id, actividad_rat_id, [CATEGORIA_RAT[t] for t in elegidos], user_id
    )
    if nombre is None:
        raise ActividadRatNoEncontrada()
    escaneo.actividad_rat_id = actividad_rat_id
    await session.commit()
    return {"escaneo_id": str(escaneo.id), "actividad_rat_id": actividad_rat_id, "actividad_nombre": nombre,
            "categorias": [CATEGORIA_RAT[t] for t in elegidos]}
# === fin DLP-01 ===
