# ¤¤backend-developer
"""NORM-01: tablas globales del corpus normativo de la SPDP. ¤inteligencia-normativa ¤vigilancia-spdp

Revision ID: norm01_inteligencia_normativa
Revises: 20261112_ia10_trazas_ia

El corpus es público y común a todas las organizaciones: sin `tenant_id` y sin RLS. `lopdp_app` solo lee.
Escribe el proceso de monitoreo con un rol propio, que concede el brief de despliegue del propietario.
`normativa_versiones` es inmutable: un disparador rechaza UPDATE y DELETE.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "norm01_inteligencia_normativa"
down_revision: Union[str, Sequence[str], None] = "20261112_ia10_trazas_ia"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE normativa_resoluciones (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            numero_resolucion VARCHAR(100) NOT NULL,
            anio_emision INTEGER NOT NULL,
            titulo VARCHAR(500) NOT NULL,
            organo_emisor VARCHAR(200),
            materia VARCHAR(200),
            fecha_publicacion DATE,
            url_fuente VARCHAR(1000) NOT NULL,
            seccion_fuente VARCHAR(30) NOT NULL
                CHECK (seccion_fuente IN ('resoluciones', 'marco_normativo', 'consultas_absueltas')),
            archivo_sha256 VARCHAR(64) NOT NULL CHECK (archivo_sha256 ~ '^[0-9a-f]{64}$'),
            ruta_original VARCHAR(500) NOT NULL,
            tamano_bytes BIGINT NOT NULL CHECK (tamano_bytes > 0),
            estado VARCHAR(30) NOT NULL DEFAULT 'pendiente_revision'
                CHECK (estado IN ('pendiente_revision', 'homologada', 'observada', 'vigente', 'reformada', 'derogada')),
            detectada_en TIMESTAMPTZ NOT NULL DEFAULT now(),
            revisada_por VARCHAR,
            revisada_en TIMESTAMPTZ,
            CONSTRAINT uq_normativa_numero_anio UNIQUE (numero_resolucion, anio_emision)
        );
        CREATE TABLE normativa_versiones (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            resolucion_id UUID NOT NULL REFERENCES normativa_resoluciones(id),
            archivo_sha256 VARCHAR(64) NOT NULL CHECK (archivo_sha256 ~ '^[0-9a-f]{64}$'),
            ruta_original VARCHAR(500) NOT NULL,
            detectada_en TIMESTAMPTZ NOT NULL DEFAULT now(),
            motivo VARCHAR(30) NOT NULL CHECK (motivo IN ('republicacion', 'fe_de_erratas', 'cambio_en_fuente'))
        );
        CREATE INDEX ix_normativa_versiones_resolucion ON normativa_versiones (resolucion_id);
        CREATE TABLE normativa_monitoreo_logs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            inicio TIMESTAMPTZ NOT NULL,
            fin TIMESTAMPTZ,
            origen VARCHAR(20) NOT NULL CHECK (origen IN ('programado', 'manual')),
            documentos_vistos INTEGER NOT NULL DEFAULT 0,
            nuevos INTEGER NOT NULL DEFAULT 0,
            versiones_nuevas INTEGER NOT NULL DEFAULT 0,
            errores INTEGER NOT NULL DEFAULT 0,
            estado VARCHAR(20) NOT NULL CHECK (estado IN ('ok', 'parcial', 'fallida')),
            codigos_error JSONB NOT NULL DEFAULT '[]'::jsonb
        );
        CREATE FUNCTION normativa_versiones_inmutable() RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'normativa_versiones es inmutable: no admite UPDATE ni DELETE';
        END;
        $$ LANGUAGE plpgsql;
        CREATE TRIGGER trg_normativa_versiones_inmutable
            BEFORE UPDATE OR DELETE ON normativa_versiones
            FOR EACH ROW EXECUTE FUNCTION normativa_versiones_inmutable();
        REVOKE ALL ON normativa_resoluciones, normativa_versiones, normativa_monitoreo_logs FROM lopdp_app;
        GRANT SELECT ON normativa_resoluciones, normativa_versiones, normativa_monitoreo_logs TO lopdp_app;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TABLE IF EXISTS normativa_monitoreo_logs;
        DROP TABLE IF EXISTS normativa_versiones;
        DROP FUNCTION IF EXISTS normativa_versiones_inmutable();
        DROP TABLE IF EXISTS normativa_resoluciones;
        """
    )
