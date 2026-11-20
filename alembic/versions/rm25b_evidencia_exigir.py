# ¤¤security-engineer
"""RM-25b: la validación final de la evidencia exige la primera (paso «contraer» de RM-25a). ¤roadmap

Primera migración de la sala `roadmap` (CI-28): cuelga de `BASE_COMUN` y abre la etiqueta `roadmap`.
- `task_evidence.requiere_revalidacion`: marca las evidencias `approved` anteriores que no tienen primera
  validación. Antes de marcarlas imprime el recuento. No cambia su `validation_status` ni promueve ninguna.
- `ck_evidence_aprobada_con_primera`: una evidencia `approved` tiene primera validación o lleva la marca. Se crea
  `NOT VALID` y se valida aquí mismo: las filas históricas ya quedan cubiertas por la marca.
- `ck_evidence_validadores_distintos`: quien hace la validación final (la aprobación) no es quien hizo la primera.
  El rechazo no entra: sigue pudiendo hacerlo el coordinador en cualquiera de los dos pasos.
`lopdp_app` ya tiene UPDATE sobre toda la tabla (20261008_app_role_rls): no hay permisos que cambiar.
"""
from alembic import op
from sqlalchemy import text

revision = "rm25b_evidencia_exigir"
down_revision = "ret02_clave_objeto"  # BASE_COMUN de alembic/salas.py
branch_labels = ("roadmap",)
depends_on = None

SQL_RECUENTO = (
    "SELECT count(*) FROM task_evidence "
    "WHERE validation_status = 'approved' AND primera_validacion_por IS NULL"
)
SQL_MARCA = (
    "UPDATE task_evidence SET requiere_revalidacion = true "
    "WHERE validation_status = 'approved' AND primera_validacion_por IS NULL"
)

SQL_COLUMNA = "ALTER TABLE task_evidence ADD COLUMN requiere_revalidacion BOOLEAN NOT NULL DEFAULT false"

SQL_RESTRICCIONES = [
    "ALTER TABLE task_evidence ADD CONSTRAINT ck_evidence_aprobada_con_primera CHECK ("
    "validation_status <> 'approved' OR primera_validacion_por IS NOT NULL OR requiere_revalidacion) NOT VALID",
    "ALTER TABLE task_evidence VALIDATE CONSTRAINT ck_evidence_aprobada_con_primera",
    "ALTER TABLE task_evidence ADD CONSTRAINT ck_evidence_validadores_distintos CHECK ("
    "validation_status <> 'approved' OR validated_by IS NULL OR primera_validacion_por IS NULL "
    "OR validated_by <> primera_validacion_por) NOT VALID",
    "ALTER TABLE task_evidence VALIDATE CONSTRAINT ck_evidence_validadores_distintos",
]

SQL_DESCENDENTE = [
    "ALTER TABLE task_evidence DROP CONSTRAINT IF EXISTS ck_evidence_validadores_distintos",
    "ALTER TABLE task_evidence DROP CONSTRAINT IF EXISTS ck_evidence_aprobada_con_primera",
    "ALTER TABLE task_evidence DROP COLUMN IF EXISTS requiere_revalidacion",
]


def marcar_sin_promover(conexion) -> int:
    """Marca las `approved` sin primera validación y devuelve cuántas eran; su estado no cambia."""
    recuento = conexion.execute(text(SQL_RECUENTO)).scalar_one()
    print(f"[RM-25b] Evidencias aprobadas sin primera validación que quedan por revalidar: {recuento}")
    conexion.execute(text(SQL_MARCA))
    return recuento


def upgrade() -> None:
    op.execute(SQL_COLUMNA)
    marcar_sin_promover(op.get_bind())
    for sentencia in SQL_RESTRICCIONES:
        op.execute(sentencia)


def downgrade() -> None:
    for sentencia in SQL_DESCENDENTE:
        op.execute(sentencia)
