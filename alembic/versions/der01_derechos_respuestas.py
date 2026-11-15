"""DER-01 · identidad verificada, resultado y respuesta como evidencia en derechos_arco_solicitudes; derechos_modelos.

`¤evidencias` `¤rbac-tenant` `¤arbitro`

Contrato: governance/especificaciones/DER-01.md §1. Primera migración de la sala derechos_arco: cuelga de
BASE_COMUN con la etiqueta de su sala (governance/operaciones/FUSION_ALEMBIC.md §2).

- Columnas nuevas, todas NULL: una solicitud sin contestar no tiene identidad verificada ni respuesta.
  `evidencia_respuesta_hash` ya existe y no se toca.
- `ck_arco_contestada_con_evidencia` (`INV_ARCO_EVIDENCIA_E1`). La condición del hash va con `coalesce`: un CHECK
  que da NULL se acepta, y un hash NULL daría NULL en vez de falso; sin `coalesce` una CONTESTADA sin hash pasaría.
- **Guardia antes del CHECK.** Cuenta exactamente las filas que el CHECK rechazaría (con la misma condición) y, si
  hay alguna, aborta dando el recuento. Sin `UPDATE` silencioso: la corrección de esas filas la decide el
  propietario.
- `derechos_modelos`: por organización, sembrada con los 24 modelos de la especificación §4.1, RLS ENABLE y FORCE por `tenant_id`, `lopdp_app` con SELECT, INSERT y UPDATE.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "der01_derechos_respuestas"
down_revision: Union[str, Sequence[str], None] = "ret02_clave_objeto"  # BASE_COMUN (alembic/salas.py)
branch_labels: Union[str, Sequence[str], None] = ("derechos_arco",)
depends_on: Union[str, Sequence[str], None] = None

TABLA = "derechos_arco_solicitudes"
RESTRICCION = "ck_arco_contestada_con_evidencia"

# Una sola expresión para el CHECK y para el recuento previo: lo que uno rechaza, el otro lo cuenta.
CONDICION = (
    "estado::text <> 'CONTESTADA' "
    "OR (coalesce(evidencia_respuesta_hash ~ '^[0-9a-f]{64}$', false) AND respondida_en IS NOT NULL)"
)

# ¤arbitro — sentencia literal, sin valores dinámicos (test_sin_sql_interpolado).
SQL_GUARDIA = f"""
DO $$
DECLARE
    sin_evidencia bigint;
BEGIN
    SELECT count(*) INTO sin_evidencia FROM {TABLA} WHERE NOT ({CONDICION});
    IF sin_evidencia > 0 THEN
        RAISE EXCEPTION 'DER-01: % solicitud(es) ARCO en CONTESTADA sin hash de evidencia válido o sin '
            'respondida_en. La migración no cambia nada: decide el propietario.', sin_evidencia;
    END IF;
END $$;
"""

# Modelos de respuesta de governance/especificaciones/DER-01.md §4.1: copia literal; una prueba la compara con la del motor.
MODELOS: tuple[tuple[str, str, str], ...] = (
    ('ACCESO', 'concedido', "{organizacion} · Respuesta a la solicitud n.º {numero_solicitud}, presentada el {fecha_solicitud}.\nEstimado/a {nombre_titular}:\n\nAtendimos tu solicitud de acceso a tus datos personales (LOPDP, art. 13). {actuacion}\n\nSi tienes preguntas sobre esta respuesta, escríbenos a {contacto_dpo}.\n\n{organizacion} · {fecha_respuesta}"),
    ('ACCESO', 'denegado', "{organizacion} · Respuesta a la solicitud n.º {numero_solicitud}, presentada el {fecha_solicitud}.\nEstimado/a {nombre_titular}:\n\nNo podemos atender tu solicitud de acceso a tus datos personales (LOPDP, art. 13) por este motivo: {motivo}\n\nSi tienes preguntas sobre esta respuesta, escríbenos a {contacto_dpo}. Si no estás de acuerdo con esta respuesta, puedes acudir a la Autoridad de Protección de Datos Personales.\n\n{organizacion} · {fecha_respuesta}"),
    ('ACCESO', 'parcial', "{organizacion} · Respuesta a la solicitud n.º {numero_solicitud}, presentada el {fecha_solicitud}.\nEstimado/a {nombre_titular}:\n\nAtendimos en parte tu solicitud de acceso a tus datos personales (LOPDP, art. 13). {actuacion} No pudimos atender el resto por este motivo: {motivo}\n\nSi tienes preguntas sobre esta respuesta, escríbenos a {contacto_dpo}. Si no estás de acuerdo con esta respuesta, puedes acudir a la Autoridad de Protección de Datos Personales.\n\n{organizacion} · {fecha_respuesta}"),
    ('RECTIFICACION', 'concedido', "{organizacion} · Respuesta a la solicitud n.º {numero_solicitud}, presentada el {fecha_solicitud}.\nEstimado/a {nombre_titular}:\n\nAtendimos tu solicitud de rectificación y actualización de tus datos personales (LOPDP, art. 14). {actuacion}\n\nSi tienes preguntas sobre esta respuesta, escríbenos a {contacto_dpo}.\n\n{organizacion} · {fecha_respuesta}"),
    ('RECTIFICACION', 'denegado', "{organizacion} · Respuesta a la solicitud n.º {numero_solicitud}, presentada el {fecha_solicitud}.\nEstimado/a {nombre_titular}:\n\nNo podemos atender tu solicitud de rectificación y actualización de tus datos personales (LOPDP, art. 14) por este motivo: {motivo}\n\nSi tienes preguntas sobre esta respuesta, escríbenos a {contacto_dpo}. Si no estás de acuerdo con esta respuesta, puedes acudir a la Autoridad de Protección de Datos Personales.\n\n{organizacion} · {fecha_respuesta}"),
    ('RECTIFICACION', 'parcial', "{organizacion} · Respuesta a la solicitud n.º {numero_solicitud}, presentada el {fecha_solicitud}.\nEstimado/a {nombre_titular}:\n\nAtendimos en parte tu solicitud de rectificación y actualización de tus datos personales (LOPDP, art. 14). {actuacion} No pudimos atender el resto por este motivo: {motivo}\n\nSi tienes preguntas sobre esta respuesta, escríbenos a {contacto_dpo}. Si no estás de acuerdo con esta respuesta, puedes acudir a la Autoridad de Protección de Datos Personales.\n\n{organizacion} · {fecha_respuesta}"),
    ('CANCELACION', 'concedido', "{organizacion} · Respuesta a la solicitud n.º {numero_solicitud}, presentada el {fecha_solicitud}.\nEstimado/a {nombre_titular}:\n\nAtendimos tu solicitud de eliminación de tus datos personales (LOPDP, art. 15). {actuacion}\n\nSi tienes preguntas sobre esta respuesta, escríbenos a {contacto_dpo}.\n\n{organizacion} · {fecha_respuesta}"),
    ('CANCELACION', 'denegado', "{organizacion} · Respuesta a la solicitud n.º {numero_solicitud}, presentada el {fecha_solicitud}.\nEstimado/a {nombre_titular}:\n\nNo podemos atender tu solicitud de eliminación de tus datos personales (LOPDP, art. 15) por este motivo: {motivo}\n\nSi tienes preguntas sobre esta respuesta, escríbenos a {contacto_dpo}. Si no estás de acuerdo con esta respuesta, puedes acudir a la Autoridad de Protección de Datos Personales.\n\n{organizacion} · {fecha_respuesta}"),
    ('CANCELACION', 'parcial', "{organizacion} · Respuesta a la solicitud n.º {numero_solicitud}, presentada el {fecha_solicitud}.\nEstimado/a {nombre_titular}:\n\nAtendimos en parte tu solicitud de eliminación de tus datos personales (LOPDP, art. 15). {actuacion} No pudimos atender el resto por este motivo: {motivo}\n\nSi tienes preguntas sobre esta respuesta, escríbenos a {contacto_dpo}. Si no estás de acuerdo con esta respuesta, puedes acudir a la Autoridad de Protección de Datos Personales.\n\n{organizacion} · {fecha_respuesta}"),
    ('OPOSICION', 'concedido', "{organizacion} · Respuesta a la solicitud n.º {numero_solicitud}, presentada el {fecha_solicitud}.\nEstimado/a {nombre_titular}:\n\nAtendimos tu solicitud de oposición al tratamiento de tus datos personales (LOPDP, art. 16). {actuacion}\n\nSi tienes preguntas sobre esta respuesta, escríbenos a {contacto_dpo}.\n\n{organizacion} · {fecha_respuesta}"),
    ('OPOSICION', 'denegado', "{organizacion} · Respuesta a la solicitud n.º {numero_solicitud}, presentada el {fecha_solicitud}.\nEstimado/a {nombre_titular}:\n\nNo podemos atender tu solicitud de oposición al tratamiento de tus datos personales (LOPDP, art. 16) por este motivo: {motivo}\n\nSi tienes preguntas sobre esta respuesta, escríbenos a {contacto_dpo}. Si no estás de acuerdo con esta respuesta, puedes acudir a la Autoridad de Protección de Datos Personales.\n\n{organizacion} · {fecha_respuesta}"),
    ('OPOSICION', 'parcial', "{organizacion} · Respuesta a la solicitud n.º {numero_solicitud}, presentada el {fecha_solicitud}.\nEstimado/a {nombre_titular}:\n\nAtendimos en parte tu solicitud de oposición al tratamiento de tus datos personales (LOPDP, art. 16). {actuacion} No pudimos atender el resto por este motivo: {motivo}\n\nSi tienes preguntas sobre esta respuesta, escríbenos a {contacto_dpo}. Si no estás de acuerdo con esta respuesta, puedes acudir a la Autoridad de Protección de Datos Personales.\n\n{organizacion} · {fecha_respuesta}"),
    ('PORTABILIDAD', 'concedido', "{organizacion} · Respuesta a la solicitud n.º {numero_solicitud}, presentada el {fecha_solicitud}.\nEstimado/a {nombre_titular}:\n\nAtendimos tu solicitud de portabilidad de tus datos personales (LOPDP, art. 17). {actuacion}\n\nSi tienes preguntas sobre esta respuesta, escríbenos a {contacto_dpo}.\n\n{organizacion} · {fecha_respuesta}"),
    ('PORTABILIDAD', 'denegado', "{organizacion} · Respuesta a la solicitud n.º {numero_solicitud}, presentada el {fecha_solicitud}.\nEstimado/a {nombre_titular}:\n\nNo podemos atender tu solicitud de portabilidad de tus datos personales (LOPDP, art. 17) por este motivo: {motivo}\n\nSi tienes preguntas sobre esta respuesta, escríbenos a {contacto_dpo}. Si no estás de acuerdo con esta respuesta, puedes acudir a la Autoridad de Protección de Datos Personales.\n\n{organizacion} · {fecha_respuesta}"),
    ('PORTABILIDAD', 'parcial', "{organizacion} · Respuesta a la solicitud n.º {numero_solicitud}, presentada el {fecha_solicitud}.\nEstimado/a {nombre_titular}:\n\nAtendimos en parte tu solicitud de portabilidad de tus datos personales (LOPDP, art. 17). {actuacion} No pudimos atender el resto por este motivo: {motivo}\n\nSi tienes preguntas sobre esta respuesta, escríbenos a {contacto_dpo}. Si no estás de acuerdo con esta respuesta, puedes acudir a la Autoridad de Protección de Datos Personales.\n\n{organizacion} · {fecha_respuesta}"),
    ('SUSPENSION', 'concedido', "{organizacion} · Respuesta a la solicitud n.º {numero_solicitud}, presentada el {fecha_solicitud}.\nEstimado/a {nombre_titular}:\n\nAtendimos tu solicitud de suspensión del tratamiento de tus datos personales (LOPDP, art. 19). {actuacion}\n\nSi tienes preguntas sobre esta respuesta, escríbenos a {contacto_dpo}.\n\n{organizacion} · {fecha_respuesta}"),
    ('SUSPENSION', 'denegado', "{organizacion} · Respuesta a la solicitud n.º {numero_solicitud}, presentada el {fecha_solicitud}.\nEstimado/a {nombre_titular}:\n\nNo podemos atender tu solicitud de suspensión del tratamiento de tus datos personales (LOPDP, art. 19) por este motivo: {motivo}\n\nSi tienes preguntas sobre esta respuesta, escríbenos a {contacto_dpo}. Si no estás de acuerdo con esta respuesta, puedes acudir a la Autoridad de Protección de Datos Personales.\n\n{organizacion} · {fecha_respuesta}"),
    ('SUSPENSION', 'parcial', "{organizacion} · Respuesta a la solicitud n.º {numero_solicitud}, presentada el {fecha_solicitud}.\nEstimado/a {nombre_titular}:\n\nAtendimos en parte tu solicitud de suspensión del tratamiento de tus datos personales (LOPDP, art. 19). {actuacion} No pudimos atender el resto por este motivo: {motivo}\n\nSi tienes preguntas sobre esta respuesta, escríbenos a {contacto_dpo}. Si no estás de acuerdo con esta respuesta, puedes acudir a la Autoridad de Protección de Datos Personales.\n\n{organizacion} · {fecha_respuesta}"),
    ('DECISIONES_AUTOMATIZADAS', 'concedido', "{organizacion} · Respuesta a la solicitud n.º {numero_solicitud}, presentada el {fecha_solicitud}.\nEstimado/a {nombre_titular}:\n\nAtendimos tu solicitud de no ser objeto de una decisión basada en valoraciones automatizadas (LOPDP, art. 20). {actuacion}\n\nSi tienes preguntas sobre esta respuesta, escríbenos a {contacto_dpo}.\n\n{organizacion} · {fecha_respuesta}"),
    ('DECISIONES_AUTOMATIZADAS', 'denegado', "{organizacion} · Respuesta a la solicitud n.º {numero_solicitud}, presentada el {fecha_solicitud}.\nEstimado/a {nombre_titular}:\n\nNo podemos atender tu solicitud de no ser objeto de una decisión basada en valoraciones automatizadas (LOPDP, art. 20) por este motivo: {motivo}\n\nSi tienes preguntas sobre esta respuesta, escríbenos a {contacto_dpo}. Si no estás de acuerdo con esta respuesta, puedes acudir a la Autoridad de Protección de Datos Personales.\n\n{organizacion} · {fecha_respuesta}"),
    ('DECISIONES_AUTOMATIZADAS', 'parcial', "{organizacion} · Respuesta a la solicitud n.º {numero_solicitud}, presentada el {fecha_solicitud}.\nEstimado/a {nombre_titular}:\n\nAtendimos en parte tu solicitud de no ser objeto de una decisión basada en valoraciones automatizadas (LOPDP, art. 20). {actuacion} No pudimos atender el resto por este motivo: {motivo}\n\nSi tienes preguntas sobre esta respuesta, escríbenos a {contacto_dpo}. Si no estás de acuerdo con esta respuesta, puedes acudir a la Autoridad de Protección de Datos Personales.\n\n{organizacion} · {fecha_respuesta}"),
    ('QUEJA', 'concedido', "{organizacion} · Respuesta a la solicitud n.º {numero_solicitud}, presentada el {fecha_solicitud}.\nEstimado/a {nombre_titular}:\n\nRevisamos tu queja. {actuacion}\n\nSi tienes preguntas sobre esta respuesta, escríbenos a {contacto_dpo}.\n\n{organizacion} · {fecha_respuesta}"),
    ('QUEJA', 'denegado', "{organizacion} · Respuesta a la solicitud n.º {numero_solicitud}, presentada el {fecha_solicitud}.\nEstimado/a {nombre_titular}:\n\nRevisamos tu queja y no podemos atenderla por este motivo: {motivo}\n\nSi tienes preguntas sobre esta respuesta, escríbenos a {contacto_dpo}. Si no estás de acuerdo con esta respuesta, puedes acudir a la Autoridad de Protección de Datos Personales.\n\n{organizacion} · {fecha_respuesta}"),
    ('QUEJA', 'parcial', "{organizacion} · Respuesta a la solicitud n.º {numero_solicitud}, presentada el {fecha_solicitud}.\nEstimado/a {nombre_titular}:\n\nRevisamos tu queja en parte. {actuacion} Sobre el resto: {motivo}\n\nSi tienes preguntas sobre esta respuesta, escríbenos a {contacto_dpo}. Si no estás de acuerdo con esta respuesta, puedes acudir a la Autoridad de Protección de Datos Personales.\n\n{organizacion} · {fecha_respuesta}"),
)

SQL_COLUMNAS = (
    f"ALTER TABLE {TABLA} ADD COLUMN IF NOT EXISTS identidad_verificada_en TIMESTAMPTZ NULL",
    f"ALTER TABLE {TABLA} ADD COLUMN IF NOT EXISTS identidad_metodo VARCHAR(16) NULL "
    "CONSTRAINT ck_arco_identidad_metodo CHECK (identidad_metodo IN ('documento', 'correo', 'presencial'))",
    f"ALTER TABLE {TABLA} ADD COLUMN IF NOT EXISTS identidad_verificada_por VARCHAR NULL",
    f"ALTER TABLE {TABLA} ADD COLUMN IF NOT EXISTS resultado VARCHAR(10) NULL "
    "CONSTRAINT ck_arco_resultado CHECK (resultado IN ('concedido', 'denegado', 'parcial'))",
    f"ALTER TABLE {TABLA} ADD COLUMN IF NOT EXISTS respondida_en TIMESTAMPTZ NULL",
)

SQL_CHECK = f"ALTER TABLE {TABLA} ADD CONSTRAINT {RESTRICCION} CHECK ({CONDICION})"

SQL_MODELOS = (
    "CREATE TABLE derechos_modelos ("
    "id VARCHAR PRIMARY KEY, "
    "tenant_id VARCHAR NOT NULL REFERENCES tenants(id), "
    "derecho VARCHAR(32) NOT NULL, "
    "resultado VARCHAR(10) NOT NULL CONSTRAINT ck_derechos_modelos_resultado "
    "CHECK (resultado IN ('concedido', 'denegado', 'parcial')), "
    "texto TEXT NOT NULL, "
    "version INTEGER NOT NULL DEFAULT 1, "
    "CONSTRAINT uq_derechos_modelos UNIQUE (tenant_id, derecho, resultado, version))",
    "CREATE INDEX ix_derechos_modelos_tenant_derecho ON derechos_modelos (tenant_id, derecho, resultado)",
    "ALTER TABLE derechos_modelos ENABLE ROW LEVEL SECURITY",
    "ALTER TABLE derechos_modelos FORCE ROW LEVEL SECURITY",
    "CREATE POLICY tenant_isolation_derechos_modelos ON derechos_modelos "
    "USING (tenant_id = current_setting('app.current_tenant_id', true)) "
    "WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true))",
    "REVOKE ALL ON derechos_modelos FROM lopdp_app",
    "GRANT SELECT, INSERT, UPDATE ON derechos_modelos TO lopdp_app",
)


def upgrade() -> None:
    for sentencia in SQL_COLUMNAS:
        op.execute(sentencia)
    op.execute(SQL_GUARDIA)
    op.execute(SQL_CHECK)
    for sentencia in SQL_MODELOS:
        op.execute(sentencia)
    # Siembra para las organizaciones existentes; las posteriores la reciben al listar (asegurar_modelos).
    for derecho, resultado, texto in MODELOS:
        op.get_bind().execute(
            sa.text(
                "INSERT INTO derechos_modelos (id, tenant_id, derecho, resultado, texto, version) "
                "SELECT t.id || ':' || :d || ':' || :r, t.id, :d, :r, :x, 1 FROM tenants t"
            ),
            {"d": derecho, "r": resultado, "x": texto},
        )


SQL_DESCENDENTE = (
    "DROP TABLE IF EXISTS derechos_modelos",
    f"ALTER TABLE {TABLA} DROP CONSTRAINT IF EXISTS {RESTRICCION}",
    "ALTER TABLE derechos_arco_solicitudes DROP COLUMN IF EXISTS respondida_en",
    "ALTER TABLE derechos_arco_solicitudes DROP COLUMN IF EXISTS resultado",
    "ALTER TABLE derechos_arco_solicitudes DROP COLUMN IF EXISTS identidad_verificada_por",
    "ALTER TABLE derechos_arco_solicitudes DROP COLUMN IF EXISTS identidad_metodo",
    "ALTER TABLE derechos_arco_solicitudes DROP COLUMN IF EXISTS identidad_verificada_en",
)


def downgrade() -> None:
    for sentencia in SQL_DESCENDENTE:
        op.execute(sentencia)
