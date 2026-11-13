# ¤¤security-engineer
"""RM-25a: primera validación del Coordinador y rol de la validación final en `task_evidence`. ¤roadmap

Expandir, sin exigir: cinco columnas nulas.
- `primera_validacion_por`, `primera_validacion_en`, `primera_validacion_rol`: quién, cuándo y con qué rol
  hizo la primera validación (el `coordinador`). Las tres van juntas o ninguna; quien valida primero no es quien subió.
- `validado_rol`: rol de quien hizo la validación final (la guarda el PATCH existente).
- `nivel_acreditado`: nivel de evidencia (0 a 4) que acredita el soporte; lo fija la validación final.
`lopdp_app` ya tiene UPDATE sobre toda la tabla (20261008_app_role_rls): no hay permisos que cambiar.
"""
from alembic import op

revision = "rm25a_evidencia_doble_validacion"
down_revision = "20261031_evidencias_vigencia"
branch_labels = None
depends_on = None

SQL_ASCENDENTE = [
    "ALTER TABLE task_evidence ADD COLUMN primera_validacion_por VARCHAR NULL REFERENCES users(id)",
    "ALTER TABLE task_evidence ADD COLUMN primera_validacion_en TIMESTAMPTZ NULL",
    "ALTER TABLE task_evidence ADD COLUMN primera_validacion_rol VARCHAR(40) NULL",
    "ALTER TABLE task_evidence ADD COLUMN validado_rol VARCHAR(40) NULL",
    "ALTER TABLE task_evidence ADD COLUMN nivel_acreditado SMALLINT NULL",
    "ALTER TABLE task_evidence ADD CONSTRAINT ck_evidence_nivel_acreditado "
    "CHECK (nivel_acreditado BETWEEN 0 AND 4)",
    "ALTER TABLE task_evidence ADD CONSTRAINT ck_evidence_primera_validacion_completa CHECK ("
    "(primera_validacion_por IS NULL AND primera_validacion_en IS NULL AND primera_validacion_rol IS NULL) OR "
    "(primera_validacion_por IS NOT NULL AND primera_validacion_en IS NOT NULL AND primera_validacion_rol IS NOT NULL))",
    "ALTER TABLE task_evidence ADD CONSTRAINT ck_evidence_primera_validacion_cuatro_ojos "
    "CHECK (primera_validacion_por IS NULL OR uploaded_by IS NULL OR primera_validacion_por <> uploaded_by)",
]

SQL_DESCENDENTE = [
    "ALTER TABLE task_evidence DROP CONSTRAINT IF EXISTS ck_evidence_primera_validacion_cuatro_ojos",
    "ALTER TABLE task_evidence DROP CONSTRAINT IF EXISTS ck_evidence_primera_validacion_completa",
    "ALTER TABLE task_evidence DROP CONSTRAINT IF EXISTS ck_evidence_nivel_acreditado",
    "ALTER TABLE task_evidence DROP COLUMN IF EXISTS nivel_acreditado",
    "ALTER TABLE task_evidence DROP COLUMN IF EXISTS validado_rol",
    "ALTER TABLE task_evidence DROP COLUMN IF EXISTS primera_validacion_rol",
    "ALTER TABLE task_evidence DROP COLUMN IF EXISTS primera_validacion_en",
    "ALTER TABLE task_evidence DROP COLUMN IF EXISTS primera_validacion_por",
]


def upgrade() -> None:
    for sentencia in SQL_ASCENDENTE:
        op.execute(sentencia)


def downgrade() -> None:
    for sentencia in SQL_DESCENDENTE:
        op.execute(sentencia)
