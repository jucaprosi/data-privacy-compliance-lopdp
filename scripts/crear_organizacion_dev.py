"""Script para crear organización de demostración y usuarios de desarrollo (DEV-01).

Permite probar en físico la plataforma rol por rol en modo desarrollo (`AUTH_MODE=headers`).
Crea:
- Organización de demostración (tamaño 'mediana').
- Un usuario por cada rol: admin_organizacion, coordinador, implementador, responsable_area, dpo.
- Estructura orgánica mínima (Alta Dirección, Unidad Operaciones con jefatura, Unidad Tecnología con vacante).
- Designación formal del Delegado de Protección de Datos (DPD).
- Idempotente: ejecutarlo múltiples veces no duplica registros ni falla.
- Fallo cerrado contra producción: rechaza si el host es de producción o AUTH_MODE != headers.
"""
from __future__ import annotations

import asyncio
from datetime import date
import os
import sys
from urllib.parse import urlparse

# Asegurar importación desde la raíz del proyecto
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

HOST_PRODUCCION = "ep-late-hall-b50bpbk5"

# Identificadores fijos para idempotencia y facilidad de configuración
DEMO_TENANT_ID = "tenant-corp-demo"
DEMO_TENANT_NOMBRE = "Organización Demo LOPDP 360"
DEMO_TENANT_RAZON = "Organización Demo S.A."
DEMO_TENANT_RUC = "1790000000001"
DEMO_TENANT_TAMANO = "mediana"
DEMO_TENANT_SECTOR = "privado"

USUARIOS_DEMO = {
    "admin_organizacion": {
        "id": "usr-demo-admin",
        "email": "admin@example.test",
        "nombre": "Admin Demo",
    },
    "coordinador": {
        "id": "usr-demo-coordinador",
        "email": "coordinador@example.test",
        "nombre": "Coordinador Demo",
    },
    "implementador": {
        "id": "usr-demo-implementador",
        "email": "implementador@example.test",
        "nombre": "Implementador Demo",
    },
    "responsable_area": {
        "id": "usr-demo-responsable",
        "email": "responsable@example.test",
        "nombre": "Responsable Área Demo",
    },
    "dpo": {
        "id": "usr-demo-dpo",
        "email": "dpo@example.test",
        "nombre": "Delegado DPO Demo",
    },
}


def sanitizar_host(url: str) -> str:
    """Extrae el host de la URL de conexión sin revelar usuario ni contraseña."""
    if not url:
        return "<desconocido>"
    try:
        parsed = urlparse(url)
        return parsed.hostname or "<sin-host>"
    except Exception:
        return "<invalido>"


def validar_entorno(database_url: str, auth_mode: str) -> str:
    """Valida precondiciones duras de entorno:
    - Base de datos no vacía.
    - No apunta al host de producción.
    - AUTH_MODE configurado exactamente en 'headers'.
    Retorna el hostname validado.
    """
    if not database_url or not database_url.strip():
        raise RuntimeError(
            "TEST_DATABASE_URL (o DATABASE_URL) no está definida. "
            "Se requiere una base de desarrollo para ejecutar este script."
        )

    host = sanitizar_host(database_url)

    if HOST_PRODUCCION in host or HOST_PRODUCCION in database_url:
        raise RuntimeError(
            f"Fallo cerrado de seguridad: el host '{host}' contiene el host de PRODUCCIÓN "
            f"({HOST_PRODUCCION}). Ejecución cancelada."
        )

    modo = (auth_mode or "").strip().lower()
    if modo != "headers":
        raise RuntimeError(
            f"Fallo cerrado de seguridad: AUTH_MODE debe ser 'headers', pero es '{auth_mode}'. "
            "Este script solo se ejecuta en modo de pruebas en desarrollo."
        )

    return host


async def crear_organizacion_dev(
    session,
    tenant_id: str = DEMO_TENANT_ID,
    tamano: str = DEMO_TENANT_TAMANO,
) -> dict:
    """Crea o asegura de forma idempotente:
    1. Tenant con tamaño y sector válidos.
    2. Cinco usuarios independientes (@example.test) asignados a sus roles correspondientes.
    3. Estructura orgánica (Alta Dirección + Operaciones + Tecnología).
    4. Jefatura de Operaciones asignada al responsable_area y jefatura de Tecnología vacante.
    5. Designación formal del DPD cumpliendo Art. 49 del Reglamento.
    """
    from sqlalchemy import text
    from features.organizacion import organizacion_service
    from features.organizacion.organizacion_service import (
        AreaEstructuraCreate,
        CargoCreate,
        DesignacionCreate,
        NivelArea,
        Role,
        RoleGrant,
        TipoCargo,
        TipoDesignacion,
        VinculoDesignacion,
    )

    # 1. Asegurar Tenant
    res_tenant = await session.execute(
        text("SELECT id, tamano FROM tenants WHERE id = :t"),
        {"t": tenant_id},
    )
    tenant_existente = res_tenant.mappings().first()
    if not tenant_existente:
        await session.execute(
            text(
                "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion, sector, tamano, activo) "
                "VALUES (:id, :n, :r, :ruc, :sec, :tam, TRUE)"
            ),
            {
                "id": tenant_id,
                "n": DEMO_TENANT_NOMBRE,
                "r": DEMO_TENANT_RAZON,
                "ruc": DEMO_TENANT_RUC,
                "sec": DEMO_TENANT_SECTOR,
                "tam": tamano,
            },
        )
    else:
        if tenant_existente["tamano"] != tamano:
            await session.execute(
                text("UPDATE tenants SET tamano = :tam WHERE id = :id"),
                {"tam": tamano, "id": tenant_id},
            )

    # 2. Asegurar Usuarios
    for rol_name, u_info in USUARIOS_DEMO.items():
        res_u = await session.execute(
            text("SELECT id, email FROM users WHERE id = :id OR email = :email"),
            {"id": u_info["id"], "email": u_info["email"]},
        )
        usr = res_u.mappings().first()
        if not usr:
            await session.execute(
                text(
                    "INSERT INTO users (id, email, nombre, activo) "
                    "VALUES (:id, :email, :nombre, TRUE)"
                ),
                {
                    "id": u_info["id"],
                    "email": u_info["email"],
                    "nombre": u_info["nombre"],
                },
            )

    admin_uid = USUARIOS_DEMO["admin_organizacion"]["id"]

    # Fijar RLS para el tenant y admin
    await session.execute(
        text("SELECT set_config('app.current_tenant_id', :t, true)"),
        {"t": tenant_id},
    )
    await session.execute(
        text("SELECT set_config('app.current_user_id', :u, true)"),
        {"u": admin_uid},
    )

    # 3. Estructura Orgánica (Compuerta organizacion_service)
    # A) Alta Dirección
    res_ad = await session.execute(
        text("SELECT id, nombre FROM areas WHERE tenant_id = :t AND nivel = 'alta_direccion' AND deleted_at IS NULL"),
        {"t": tenant_id},
    )
    ad_row = res_ad.mappings().first()
    if not ad_row:
        area_ad = await organizacion_service.crear_area_estructura(
            session=session,
            tenant_id=tenant_id,
            payload=AreaEstructuraCreate(
                nombre="Gerencia General y Directorio",
                codigo="ALTA-DIR",
                nivel=NivelArea.alta_direccion,
            ),
            user_id=admin_uid,
        )
        alta_dir_id = area_ad["id"]
    else:
        alta_dir_id = ad_row["id"]

    # B) Unidad Operaciones
    res_op = await session.execute(
        text("SELECT id FROM areas WHERE tenant_id = :t AND codigo = 'UNID-OPER' AND deleted_at IS NULL"),
        {"t": tenant_id},
    )
    op_row = res_op.mappings().first()
    if not op_row:
        area_op = await organizacion_service.crear_area_estructura(
            session=session,
            tenant_id=tenant_id,
            payload=AreaEstructuraCreate(
                nombre="Unidad de Operaciones y Procesos",
                codigo="UNID-OPER",
                nivel=NivelArea.unidad,
                parent_area_id=alta_dir_id,
            ),
            user_id=admin_uid,
        )
        operaciones_id = area_op["id"]
    else:
        operaciones_id = op_row["id"]

    # C) Unidad Tecnología
    res_tec = await session.execute(
        text("SELECT id FROM areas WHERE tenant_id = :t AND codigo = 'UNID-TEC' AND deleted_at IS NULL"),
        {"t": tenant_id},
    )
    tec_row = res_tec.mappings().first()
    if not tec_row:
        area_tec = await organizacion_service.crear_area_estructura(
            session=session,
            tenant_id=tenant_id,
            payload=AreaEstructuraCreate(
                nombre="Unidad de Tecnología y Sistemas",
                codigo="UNID-TEC",
                nivel=NivelArea.unidad,
                parent_area_id=alta_dir_id,
            ),
            user_id=admin_uid,
        )
        tecnologia_id = area_tec["id"]
    else:
        tecnologia_id = tec_row["id"]

    # D) Cargos y Jefaturas
    resp_uid = USUARIOS_DEMO["responsable_area"]["id"]

    # Jefatura de Operaciones (titular: responsable_area)
    res_jef_op = await session.execute(
        text("SELECT id, titular_user_id FROM cargos_organicos WHERE area_id = :a AND es_jefatura = TRUE AND valid_to IS NULL"),
        {"a": operaciones_id},
    )
    jef_op_row = res_jef_op.mappings().first()
    if not jef_op_row:
        await organizacion_service.crear_cargo(
            session=session,
            tenant_id=tenant_id,
            payload=CargoCreate(
                area_id=operaciones_id,
                nombre="Jefe de Operaciones",
                tipo_cargo=TipoCargo.otro,
                es_jefatura=True,
                titular_user_id=resp_uid,
            ),
            user_id=admin_uid,
        )
    elif jef_op_row["titular_user_id"] != resp_uid:
        await session.execute(
            text("UPDATE cargos_organicos SET titular_user_id = :u WHERE id = :id"),
            {"u": resp_uid, "id": jef_op_row["id"]},
        )

    # Jefatura de Tecnología (vacante)
    res_jef_tec = await session.execute(
        text("SELECT id, titular_user_id FROM cargos_organicos WHERE area_id = :a AND es_jefatura = TRUE AND valid_to IS NULL"),
        {"a": tecnologia_id},
    )
    jef_tec_row = res_jef_tec.mappings().first()
    if not jef_tec_row:
        await organizacion_service.crear_cargo(
            session=session,
            tenant_id=tenant_id,
            payload=CargoCreate(
                area_id=tecnologia_id,
                nombre="Jefe de Sistemas y Ciberseguridad",
                tipo_cargo=TipoCargo.otro,
                es_jefatura=True,
                titular_user_id=None,
            ),
            user_id=admin_uid,
        )

    # 4. Roles RBAC y SoD (Compuerta organizacion_service)
    # admin_organizacion
    res_r_admin = await session.execute(
        text("SELECT id FROM user_tenant_roles WHERE user_id = :u AND tenant_id = :t AND role = 'admin_organizacion' AND (valid_to IS NULL OR valid_to > now())"),
        {"u": admin_uid, "t": tenant_id},
    )
    if not res_r_admin.first():
        await organizacion_service.grant_role(
            session=session,
            tenant_id=tenant_id,
            granted_by=admin_uid,
            payload=RoleGrant(user_id=admin_uid, role=Role.admin_organizacion),
        )

    # coordinador
    coord_uid = USUARIOS_DEMO["coordinador"]["id"]
    res_r_coord = await session.execute(
        text("SELECT id FROM user_tenant_roles WHERE user_id = :u AND tenant_id = :t AND role = 'coordinador' AND (valid_to IS NULL OR valid_to > now())"),
        {"u": coord_uid, "t": tenant_id},
    )
    if not res_r_coord.first():
        await organizacion_service.grant_role(
            session=session,
            tenant_id=tenant_id,
            granted_by=admin_uid,
            payload=RoleGrant(user_id=coord_uid, role=Role.coordinador),
        )

    # implementador
    impl_uid = USUARIOS_DEMO["implementador"]["id"]
    res_r_impl = await session.execute(
        text("SELECT id FROM user_tenant_roles WHERE user_id = :u AND tenant_id = :t AND role = 'implementador' AND (valid_to IS NULL OR valid_to > now())"),
        {"u": impl_uid, "t": tenant_id},
    )
    if not res_r_impl.first():
        await organizacion_service.grant_role(
            session=session,
            tenant_id=tenant_id,
            granted_by=admin_uid,
            payload=RoleGrant(user_id=impl_uid, role=Role.implementador),
        )

    # responsable_area (acotado al área de Operaciones)
    res_r_resp = await session.execute(
        text("SELECT id FROM user_tenant_roles WHERE user_id = :u AND tenant_id = :t AND role = 'responsable_area' AND area_id = :a AND (valid_to IS NULL OR valid_to > now())"),
        {"u": resp_uid, "t": tenant_id, "a": operaciones_id},
    )
    if not res_r_resp.first():
        await organizacion_service.grant_role(
            session=session,
            tenant_id=tenant_id,
            granted_by=admin_uid,
            payload=RoleGrant(user_id=resp_uid, role=Role.responsable_area, area_id=operaciones_id),
        )

    # dpo (sin ningún otro rol ni cargo incompatible)
    dpo_uid = USUARIOS_DEMO["dpo"]["id"]
    res_r_dpo = await session.execute(
        text("SELECT id FROM user_tenant_roles WHERE user_id = :u AND tenant_id = :t AND role = 'dpo' AND (valid_to IS NULL OR valid_to > now())"),
        {"u": dpo_uid, "t": tenant_id},
    )
    if not res_r_dpo.first():
        await organizacion_service.grant_role(
            session=session,
            tenant_id=tenant_id,
            granted_by=admin_uid,
            payload=RoleGrant(user_id=dpo_uid, role=Role.dpo),
        )

    # 5. Designación Formal del DPD (ORG-06 vía organizacion_service)
    res_desig = await session.execute(
        text(
            "SELECT id FROM designaciones_formales WHERE tenant_id = :t AND tipo = 'dpd' "
            "AND revocada_at IS NULL AND (valid_to IS NULL OR valid_to > now())"
        ),
        {"t": tenant_id},
    )
    if not res_desig.first():
        await organizacion_service.crear_designacion_formal(
            session=session,
            tenant_id=tenant_id,
            admin_user_id=admin_uid,
            payload=DesignacionCreate(
                tipo=TipoDesignacion.dpd,
                user_id=dpo_uid,
                representante_nombre="Gerente General Demo",
                representante_identificacion="1790000000001",
                representante_cargo="Representante Legal Demo",
                fecha_designacion=date.today(),
                doc_referencia="ACTA-DIR-DEMO-2026-001",
                vinculo=VinculoDesignacion.relacion_dependencia,
            ),
        )

    await session.commit()

    return {
        "tenant_id": tenant_id,
        "alta_dir_id": alta_dir_id,
        "operaciones_id": operaciones_id,
        "tecnologia_id": tecnologia_id,
        "usuarios": USUARIOS_DEMO,
    }


def imprimir_instrucciones_desarrollo(resultado: dict) -> None:
    """Imprime los identificadores para frontend/.env.local y cabeceras de prueba."""
    tenant_id = resultado["tenant_id"]
    print("\n" + "=" * 70)
    print(" ORGANIZACIÓN DE DESARROLLO PREPARADA EXITOSAMENTE (DEV-01)")
    print("=" * 70)
    print(f"TENANT_ID: {tenant_id}")
    print("\nPara configurar en `frontend/.env.local`:")
    print("----------------------------------------------------------------------")
    print("NEXT_PUBLIC_AUTH_MODE=headers")
    print(f"NEXT_PUBLIC_TENANT_ID={tenant_id}")
    print("# Elige uno de los siguientes usuarios y roles según tu prueba:")
    for rol, datos in resultado["usuarios"].items():
        print(f"# {rol.upper()}:")
        print(f"# NEXT_PUBLIC_USER_ID={datos['id']}")
        print(f"# NEXT_PUBLIC_USER_ROLE={rol}")
    print("----------------------------------------------------------------------")

    print("\nCabeceras HTTP para modo headers (cURL / Postman / Swagger / Fetch):")
    print("----------------------------------------------------------------------")
    for rol, datos in resultado["usuarios"].items():
        print(f"[{rol}]:")
        print(f'  X-Tenant-ID: {tenant_id}')
        print(f'  X-User-ID:   {datos["id"]}')
        print(f'  X-Role:      {rol}')
        print(f'  Email:       {datos["email"]}')
        print()
    print("=" * 70 + "\n")


async def main() -> None:
    db_url = os.environ.get("TEST_DATABASE_URL") or os.environ.get("DATABASE_URL") or ""
    auth_mode = os.environ.get("AUTH_MODE", "headers")

    host = validar_entorno(db_url, auth_mode)
    print(f"[DEV-01] Validando conexión segura a base de desarrollo: host='{host}'...")

    # El motor de la aplicación conecta con DATABASE_URL (y app_core.config carga el .env, cuya
    # DATABASE_URL es la de producción): se fija explícitamente a la URL validada y, ya creado el
    # motor, se vuelve a validar el host al que de verdad conectará.
    os.environ["DATABASE_URL"] = db_url

    from app_core.db.session import async_session_factory, engine

    validar_entorno(engine.url.render_as_string(hide_password=True), auth_mode)

    try:
        async with async_session_factory() as session:
            resultado = await crear_organizacion_dev(session)
        imprimir_instrucciones_desarrollo(resultado)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    if sys.platform == "win32":
        from app_core.bucle_eventos import configurar_bucle_eventos
        configurar_bucle_eventos()
    asyncio.run(main())
