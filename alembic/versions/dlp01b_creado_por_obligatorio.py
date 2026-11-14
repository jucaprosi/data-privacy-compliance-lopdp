# ¤¤security-engineer
"""DLP-01b: todo escaneo muestreado tiene autor. ¤dlp-muestreo ¤seguridad-tenant

Revision ID: dlp01b_creado_por_obligatorio
Revises: rat07_consentimientos

`creado_por` pasa a NOT NULL y no vacío (validación del Arquitecto ADPA, 2026-11-13): sale siempre del token
del usuario autenticado. `creado_en` ya era NOT NULL con DEFAULT now() en dlp01_escaneos_muestreados y no
cambia. La migración ya fusionada no se edita.

Filas existentes sin autor: la migración FALLA con un mensaje claro y no rellena nada. Un autor inventado
falsearía la auditoría del escaneo; si aparece una fila así, se revisa a mano antes de migrar. Hoy no debe
haber ninguna fuera de las bases locales.
"""
from alembic import op

revision = "dlp01b_creado_por_obligatorio"
down_revision = "rat07_consentimientos"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM dlp_escaneos_muestreados
                WHERE creado_por IS NULL OR length(trim(creado_por)) = 0
            ) THEN
                RAISE EXCEPTION 'DLP-01b: hay escaneos sin autor (creado_por nulo o vacío); revíselos antes de migrar';
            END IF;
        END
        $$;
        ALTER TABLE dlp_escaneos_muestreados ALTER COLUMN creado_por SET NOT NULL;
        ALTER TABLE dlp_escaneos_muestreados
            ADD CONSTRAINT ck_dlp_creado_por_no_vacio CHECK (length(trim(creado_por)) >= 1);
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE dlp_escaneos_muestreados DROP CONSTRAINT IF EXISTS ck_dlp_creado_por_no_vacio;
        ALTER TABLE dlp_escaneos_muestreados ALTER COLUMN creado_por DROP NOT NULL;
        """
    )
