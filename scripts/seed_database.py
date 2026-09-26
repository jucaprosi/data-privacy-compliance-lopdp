import sys
import os
import asyncio
from datetime import datetime, timezone, timedelta
import uuid

# Asegurar que el PYTHONPATH incluya el directorio raíz del proyecto
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import delete
from app_core.database import async_session_factory, engine, current_tenant_id, set_db_tenant_context, Base
from features.derechos_arco.domain.models import SolicitudARCO, TipoSolicitud, EstadoSolicitud
from features.transferencias.services.encargados_service import TerceroEncargado, RolTercero, NivelProteccion

# Asegurar que las tablas existan creando el schema basado en los modelos
async def init_db():
    async with engine.begin() as conn:
        # Importante: para que detecte las tablas, deben estar importadas las clases Base (lo cual ya hacemos arriba).
        await conn.run_sync(Base.metadata.create_all)

async def seed_data():
    TENANT_ID = uuid.UUID("123e4567-e89b-12d3-a456-426614174000")
    
    print("Inicializando base de datos y creando tablas si no existen...")
    await init_db()

    # Inyectar el context var para simular el request RLS
    current_tenant_id.set(str(TENANT_ID))

    async with async_session_factory() as session:
        # Seteamos el tenant_id en la base de datos de PostgreSQL
        await set_db_tenant_context(session, str(TENANT_ID))
        
        print(f"Limpiando datos previos para el Tenant {TENANT_ID} (Idempotencia)...")
        await session.execute(delete(SolicitudARCO).where(SolicitudARCO.tenant_id == TENANT_ID))
        await session.execute(delete(TerceroEncargado).where(TerceroEncargado.tenant_id == TENANT_ID))
        
        now = datetime.now(timezone.utc)
        
        # --- ARCO Solicitudes ---
        print("Insertando solicitudes ARCO...")
        arco_vencida = SolicitudARCO(
            tenant_id=TENANT_ID,
            tipo_solicitud=TipoSolicitud.ACCESO,
            estado=EstadoSolicitud.VENCIDA,
            cedula_solicitante="0999999999",
            nombre_solicitante="Juan Perez",
            fecha_recepcion=now - timedelta(days=20),
            fecha_vencimiento=now - timedelta(days=5)
        )
        
        arco_al_dia = SolicitudARCO(
            tenant_id=TENANT_ID,
            tipo_solicitud=TipoSolicitud.RECTIFICACION,
            estado=EstadoSolicitud.EN_ANALISIS,
            cedula_solicitante="1710034065",
            nombre_solicitante="Maria Gomez",
            fecha_recepcion=now - timedelta(days=5),
            fecha_vencimiento=now + timedelta(days=10)
        )
        
        arco_contestada = SolicitudARCO(
            tenant_id=TENANT_ID,
            tipo_solicitud=TipoSolicitud.CANCELACION,
            estado=EstadoSolicitud.CONTESTADA,
            cedula_solicitante="1101234567",
            nombre_solicitante="Carlos Ruiz",
            fecha_recepcion=now - timedelta(days=15),
            fecha_vencimiento=now,
            evidencia_respuesta_hash="abcdef123456"
        )
        
        session.add_all([arco_vencida, arco_al_dia, arco_contestada])
        
        # --- Transferencias a terceros ---
        print("Insertando transferencias a terceros...")
        trans_adecuada = TerceroEncargado(
            tenant_id=TENANT_ID,
            nombre="AWS us-east-1",
            rol=RolTercero.ENCARGADO,
            pais_destino="Estados Unidos",
            nivel_proteccion=NivelProteccion.ADECUADO,
            clausulas_firmadas=True
        )
        
        trans_estandar = TerceroEncargado(
            tenant_id=TENANT_ID,
            nombre="Agencia de Marketing Local",
            rol=RolTercero.DESTINATARIO,
            pais_destino="Ecuador",
            nivel_proteccion=NivelProteccion.ESTANDAR,
            clausulas_firmadas=True
        )
        
        # Registro que dispara Poka-Yoke
        trans_poka_yoke = TerceroEncargado(
            tenant_id=TENANT_ID,
            nombre="Servicio de CallCenter Offshore",
            rol=RolTercero.SUBENCARGADO,
            pais_destino="País No Reconocido",
            nivel_proteccion=NivelProteccion.NO_ADECUADO,
            clausulas_firmadas=False
        )
        
        session.add_all([trans_adecuada, trans_estandar, trans_poka_yoke])
        
        await session.commit()
        print(f"Data seedeada con éxito en la base de datos para Tenant {TENANT_ID}.")

if __name__ == "__main__":
    asyncio.run(seed_data())
