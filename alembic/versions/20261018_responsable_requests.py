"""Flujo de alta de responsables de área: area_responsable_requests y user_tenant_roles.request_id.

Revision ID: 20261018_responsable_requests
Revises: 20261017_encargado_resp_trigger
Create Date: 2026-10-18 10:00:00.000000

RM-10 (PRD §5.3.1): el encargado solicita, el implementador aprueba o rechaza y ejecuta. Ningún rol
completa el flujo solo ni se salta pasos, y cada transición queda registrada.

Tres capas: esta migración pone la de base de datos (RLS forzado por tenant, estados cerrados y un
trigger que solo admite las transiciones válidas y exige que cada paso deje a su actor); el servicio y la
API están en `solicitud_responsable_engine.py` y `api/routers/areas_responsable_requests.py`.

El SQL vive en las constantes del módulo y `upgrade()`/`downgrade()` solo lo ejecutan: así la prueba
(`tests/test_responsable_requests.py`) puede instalar exactamente este SQL dentro de una transacción
que se revierte, sin copiarlo ni depender de que la migración ya esté aplicada.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "20261018_responsable_requests"
down_revision: Union[str, None] = "20261017_encargado_resp_trigger"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

APP_ROLE = "lopdp_app"
TABLA = "area_responsable_requests"

SQL_ASCENDENTE: tuple[str, ...] = (
    """
    CREATE TABLE area_responsable_requests (
        id VARCHAR NOT NULL PRIMARY KEY,
        tenant_id VARCHAR NOT NULL REFERENCES tenants(id),
        target_user_id VARCHAR NOT NULL REFERENCES users(id),
        area_id VARCHAR NULL REFERENCES areas(id),
        area_nombre VARCHAR(255) NULL,
        motivo TEXT NULL,
        estado VARCHAR(20) NOT NULL DEFAULT 'pendiente',
        requested_by VARCHAR NOT NULL REFERENCES users(id),
        decided_by VARCHAR NULL REFERENCES users(id),
        decided_at TIMESTAMPTZ NULL,
        decision_notes TEXT NULL,
        executed_by VARCHAR NULL REFERENCES users(id),
        executed_at TIMESTAMPTZ NULL,
        assignment_id VARCHAR NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        CONSTRAINT ck_arr_estado CHECK (estado IN ('pendiente', 'aprobada', 'rechazada', 'cancelada', 'ejecutada')),
        CONSTRAINT ck_arr_area CHECK (area_id IS NOT NULL OR area_nombre IS NOT NULL)
    )
    """,
    "CREATE INDEX ix_arr_tenant_estado ON area_responsable_requests (tenant_id, estado)",
    # Una persona no puede tener dos solicitudes abiertas para la misma área.
    """
    CREATE UNIQUE INDEX uq_arr_abierta_por_usuario_area ON area_responsable_requests (tenant_id, target_user_id, area_id)
    WHERE area_id IS NOT NULL AND estado IN ('pendiente', 'aprobada')
    """,
    "ALTER TABLE area_responsable_requests ENABLE ROW LEVEL SECURITY",
    "ALTER TABLE area_responsable_requests FORCE ROW LEVEL SECURITY",
    """
    CREATE POLICY tenant_isolation_area_responsable_requests ON area_responsable_requests
    USING (tenant_id = current_setting('app.current_tenant_id', true))
    """,
    # Sin DELETE: las solicitudes son un registro; se cierran, no se borran.
    "GRANT SELECT, INSERT, UPDATE ON area_responsable_requests TO lopdp_app",
    # Trazabilidad: qué solicitud originó cada asignación de rol.
    "ALTER TABLE user_tenant_roles ADD COLUMN request_id VARCHAR NULL REFERENCES area_responsable_requests(id)",
    """
    CREATE OR REPLACE FUNCTION fn_arr_transiciones() RETURNS trigger
    LANGUAGE plpgsql AS $$
    BEGIN
        IF TG_OP = 'INSERT' THEN
            IF NEW.estado <> 'pendiente' THEN
                RAISE EXCEPTION 'RESPONSABLE_REQUEST_TRANSITION: una solicitud nace pendiente, no %', NEW.estado
                    USING ERRCODE = 'check_violation';
            END IF;
            RETURN NEW;
        END IF;
        IF OLD.estado IN ('rechazada', 'cancelada', 'ejecutada') THEN
            RAISE EXCEPTION 'RESPONSABLE_REQUEST_TRANSITION: la solicitud % esta % y no admite cambios', OLD.id, OLD.estado
                USING ERRCODE = 'check_violation';
        END IF;
        IF NEW.tenant_id <> OLD.tenant_id OR NEW.target_user_id <> OLD.target_user_id
           OR NEW.requested_by <> OLD.requested_by THEN
            RAISE EXCEPTION 'RESPONSABLE_REQUEST_TRANSITION: no se puede cambiar el tenant, el destinatario ni quien solicita'
                USING ERRCODE = 'check_violation';
        END IF;
        IF NEW.estado <> OLD.estado AND NOT (
               (OLD.estado = 'pendiente' AND NEW.estado IN ('aprobada', 'rechazada', 'cancelada'))
            OR (OLD.estado = 'aprobada' AND NEW.estado = 'ejecutada')
        ) THEN
            RAISE EXCEPTION 'RESPONSABLE_REQUEST_TRANSITION: de % a % no esta permitido', OLD.estado, NEW.estado
                USING ERRCODE = 'check_violation';
        END IF;
        IF NEW.estado IN ('aprobada', 'rechazada', 'cancelada') AND NEW.decided_by IS NULL THEN
            RAISE EXCEPTION 'RESPONSABLE_REQUEST_TRANSITION: el paso % debe registrar quien lo decide', NEW.estado
                USING ERRCODE = 'check_violation';
        END IF;
        IF NEW.estado = 'ejecutada' AND (NEW.executed_by IS NULL OR NEW.assignment_id IS NULL) THEN
            RAISE EXCEPTION 'RESPONSABLE_REQUEST_TRANSITION: ejecutar debe registrar quien ejecuta y la asignacion creada'
                USING ERRCODE = 'check_violation';
        END IF;
        RETURN NEW;
    END;
    $$
    """,
    """
    CREATE TRIGGER trg_arr_transiciones BEFORE INSERT OR UPDATE ON area_responsable_requests
    FOR EACH ROW EXECUTE FUNCTION fn_arr_transiciones()
    """,
)

SQL_DESCENDENTE: tuple[str, ...] = (
    "DROP TRIGGER IF EXISTS trg_arr_transiciones ON area_responsable_requests",
    "DROP FUNCTION IF EXISTS fn_arr_transiciones()",
    "ALTER TABLE user_tenant_roles DROP COLUMN IF EXISTS request_id",
    "REVOKE SELECT, INSERT, UPDATE ON area_responsable_requests FROM lopdp_app",
    "DROP POLICY IF EXISTS tenant_isolation_area_responsable_requests ON area_responsable_requests",
    "DROP TABLE IF EXISTS area_responsable_requests",
)


def upgrade() -> None:
    for sentencia in SQL_ASCENDENTE:
        op.execute(sentencia)


def downgrade() -> None:
    for sentencia in SQL_DESCENDENTE:
        op.execute(sentencia)
