# ¤entorno-pruebas ¤seguridad-tenant
"""Organizaciones ficticias y cuentas de quienes prueban (EP-03).

Cubre una micro y una mediana (reglas de tamaño, RM-16) y una de gran escala (MTGE). Nombre, sector y
RUC son visiblemente ficticios. Los roles se conceden por `organizacion_service.grant_role` y las áreas
por `organizacion_service.crear_area_estructura`; ninguna escritura de roles ni de áreas va a su tabla.

Las salas no exponen un alta idempotente de organización ni de persona: `plataforma_service` crea la
organización junto con una invitación y responde 409 si el RUC existe. Por eso `tenants` y `users` se
aseguran aquí con una inserción condicionada, igual que `scripts/crear_organizacion_dev.py`.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

from scripts.datos_sinteticos import DOMINIO_FICTICIO

ROLES_VALIDOS = ("admin_organizacion", "coordinador", "implementador", "responsable_area", "dpo")


@dataclass(frozen=True)
class OrganizacionFicticia:
    id: str
    nombre_comercial: str
    razon_social: str
    ruc: str
    sector: str
    tamano: str
    gran_escala: bool = False


ORGANIZACIONES: tuple[OrganizacionFicticia, ...] = (
    OrganizacionFicticia(
        id="ep-org-micro",
        nombre_comercial="FICTICIA Panadería El Ejemplo",
        razon_social="FICTICIA Panadería El Ejemplo Cía. Ltda. (datos de prueba)",
        ruc="9999999990001",
        sector="FICTICIO comercio minorista",
        tamano="micro",
    ),
    OrganizacionFicticia(
        id="ep-org-mediana",
        nombre_comercial="FICTICIA Clínica Modelo",
        razon_social="FICTICIA Clínica Modelo S.A. (datos de prueba)",
        ruc="9999999990002",
        sector="FICTICIO salud",
        tamano="mediana",
    ),
    OrganizacionFicticia(
        id="ep-org-gran-escala",
        nombre_comercial="FICTICIA Telecomunicaciones Andinas",
        razon_social="FICTICIA Telecomunicaciones Andinas S.A. (datos de prueba, MTGE)",
        ruc="9999999990003",
        sector="FICTICIO telecomunicaciones",
        tamano="corporativo",
        gran_escala=True,
    ),
)

# Personas ficticias de cada organización: (sufijo, rol). El DPO es una persona aparte (separación de funciones).
PERSONAS_FICTICIAS: tuple[tuple[str, str], ...] = (
    ("admin", "admin_organizacion"),
    ("coordinacion", "coordinador"),
    ("dpo", "dpo"),
)

CODIGO_ALTA_DIRECCION = "EP-ALTA-DIR"
CODIGO_UNIDAD_PRUEBAS = "EP-UNID-PRUEBAS"


@dataclass(frozen=True)
class CuentaDePrueba:
    correo: str
    rol: str
    organizacion: str


def correo_ficticio(org_id: str, sufijo: str) -> str:
    return f"{sufijo}.{org_id}@{DOMINIO_FICTICIO}"


def correos_ficticios() -> list[str]:
    return [correo_ficticio(o.id, s) for o in ORGANIZACIONES for s, _ in PERSONAS_FICTICIAS]


def id_de_usuario(correo: str) -> str:
    """Identificador estable derivado del correo: la segunda corrida encuentra el mismo usuario."""
    return "usr-ep-" + hashlib.sha256(correo.strip().lower().encode("utf-8")).hexdigest()[:16]


def leer_cuentas(texto: str) -> list[CuentaDePrueba]:
    """Lee `correo,rol,organización` por línea. Ignora las líneas vacías y las que empiezan por `#`.

    Los mensajes de error dan el número de línea, nunca el correo.
    """
    ids = {o.id for o in ORGANIZACIONES}
    cuentas: list[CuentaDePrueba] = []
    for numero, linea in enumerate(texto.splitlines(), start=1):
        linea = linea.strip()
        if not linea or linea.startswith("#"):
            continue
        partes = [p.strip() for p in linea.split(",")]
        if len(partes) != 3 or "@" not in partes[0]:
            raise ValueError(f"Línea {numero}: se espera correo,rol,organización.")
        correo, rol, org = partes
        if rol not in ROLES_VALIDOS:
            raise ValueError(f"Línea {numero}: rol desconocido «{rol}».")
        if org not in ids:
            raise ValueError(f"Línea {numero}: organización desconocida «{org}».")
        cuentas.append(CuentaDePrueba(correo.lower(), rol, org))
    return cuentas


async def _asegurar_tenant(session, org: OrganizacionFicticia, conteo) -> None:
    from sqlalchemy import text

    fila = await session.execute(
        text(
            "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion, sector, tamano, activo) "
            "VALUES (:id, :n, :r, :ruc, :sec, :tam, TRUE) ON CONFLICT (id) DO NOTHING RETURNING id"
        ),
        {"id": org.id, "n": org.nombre_comercial, "r": org.razon_social, "ruc": org.ruc,
         "sec": org.sector, "tam": org.tamano},
    )
    conteo("organizaciones", fila.first() is not None)


async def _asegurar_usuario(session, correo: str, nombre: str, conteo) -> str:
    from sqlalchemy import text

    uid = id_de_usuario(correo)
    existente = (await session.execute(
        text("SELECT id FROM users WHERE id = :id OR lower(email) = :e"), {"id": uid, "e": correo}
    )).first()
    if existente:
        conteo("personas", False)
        return existente[0]
    await session.execute(
        text("INSERT INTO users (id, email, nombre, activo) VALUES (:id, :e, :n, TRUE)"),
        {"id": uid, "e": correo, "n": nombre},
    )
    conteo("personas", True)
    return uid


async def _asegurar_area(session, tenant_id, codigo, nombre, nivel, padre, admin_uid, conteo) -> str:
    from sqlalchemy import text
    from features.organizacion import organizacion_service as org_srv

    fila = (await session.execute(
        text("SELECT id FROM areas WHERE tenant_id = :t AND codigo = :c AND deleted_at IS NULL"),
        {"t": tenant_id, "c": codigo},
    )).first()
    if fila:
        conteo("areas", False)
        return fila[0]
    area = await org_srv.crear_area_estructura(
        session=session, tenant_id=tenant_id, user_id=admin_uid,
        payload=org_srv.AreaEstructuraCreate(nombre=nombre, codigo=codigo, nivel=nivel, parent_area_id=padre),
    )
    conteo("areas", True)
    return area["id"]


async def _asegurar_rol(session, tenant_id, uid, rol, area_id, admin_uid, conteo) -> None:
    from sqlalchemy import text
    from features.organizacion import organizacion_service as org_srv

    fila = (await session.execute(
        text(
            "SELECT 1 FROM user_tenant_roles WHERE user_id = :u AND tenant_id = :t AND role = :r "
            "AND area_id IS NOT DISTINCT FROM CAST(:a AS TEXT) AND (valid_to IS NULL OR valid_to > now())"
        ),
        {"u": uid, "t": tenant_id, "r": rol, "a": area_id},
    )).first()
    if fila:
        conteo("roles", False)
        return
    await org_srv.grant_role(
        session=session, tenant_id=tenant_id, granted_by=admin_uid,
        payload=org_srv.RoleGrant(user_id=uid, role=org_srv.Role(rol), area_id=area_id),
    )
    conteo("roles", True)


async def sembrar_organizaciones(session, cuentas: list[CuentaDePrueba], conteo) -> None:
    """Crea o completa, sin duplicar, las organizaciones, sus personas ficticias, áreas y roles."""
    from features.organizacion import organizacion_service as org_srv

    for org in ORGANIZACIONES:
        await _asegurar_tenant(session, org, conteo)
        uids = {}
        for sufijo, rol in PERSONAS_FICTICIAS:
            correo = correo_ficticio(org.id, sufijo)
            uids[rol] = await _asegurar_usuario(session, correo, f"Persona ficticia {sufijo}", conteo)
        admin_uid = uids["admin_organizacion"]
        await _asegurar_rol(session, org.id, admin_uid, "admin_organizacion", None, admin_uid, conteo)
        alta = await _asegurar_area(session, org.id, CODIGO_ALTA_DIRECCION, "Dirección ficticia",
                                    org_srv.NivelArea.alta_direccion, None, admin_uid, conteo)
        unidad = await _asegurar_area(session, org.id, CODIGO_UNIDAD_PRUEBAS, "Unidad ficticia de pruebas",
                                      org_srv.NivelArea.unidad, alta, admin_uid, conteo)
        for rol, uid in uids.items():
            if rol != "admin_organizacion":
                await _asegurar_rol(session, org.id, uid, rol, None, admin_uid, conteo)
        for cuenta in (c for c in cuentas if c.organizacion == org.id):
            uid = await _asegurar_usuario(session, cuenta.correo, "Persona que prueba", conteo)
            area = unidad if cuenta.rol == "responsable_area" else None
            await _asegurar_rol(session, org.id, uid, cuenta.rol, area, admin_uid, conteo)
    await session.commit()
