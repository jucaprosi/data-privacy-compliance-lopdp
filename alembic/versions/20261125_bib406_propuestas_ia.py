# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤adpa ¤cita-verificada
# ¤¤developer-architect
"""BIB-406: versiones de plantilla redactadas por la IA, sin usuario de sistema.

Añade las columnas de origen a `biblioteca_versiones` y redefine `biblioteca_validar_version` partiendo de
la definición de BIB-403 (`20261124_bib403_publicacion_normativa.py`), con los cambios de la especificación:
- INSERT: si `redactada_por = 'ia'`, `autores = ["ia"]` y `responsable_id = actor` (quien disparó, que queda
  en el origen y no como autor).
- `en_revision -> retirada` (descartar) con `nota_descarte` no vacía y la capacidad `editor`,
  `revisor_tecnico` o `publicador`.
- R5b: una versión de la IA no se edita (el UPDATE sin cambio de estado se rechaza) y las columnas de
  origen no cambian después del alta.
El resto no cambia. El `downgrade` restaura la definición de BIB-403 y quita las columnas.
"""
import importlib.util
from pathlib import Path

from alembic import op

revision = "20261125_bib406_propuestas_ia"
down_revision = "20261124_bib403_publicacion"
branch_labels = None
depends_on = None


def _bib403():
    ruta = Path(__file__).with_name("20261124_bib403_publicacion_normativa.py")
    especificacion = importlib.util.spec_from_file_location("_bib403_publicacion", ruta)
    modulo = importlib.util.module_from_spec(especificacion)
    especificacion.loader.exec_module(modulo)
    return modulo


_ALTA_PERSONA = """                IF NEW.estado<>'en_revision' OR NEW.generacion<>1 OR NOT public.biblioteca_puede('editor')
                   OR NEW.responsable_id<>actor OR NEW.autores<>jsonb_build_array(actor) THEN
                    RAISE EXCEPTION 'BIB_ALTA_DENEGADA' USING ERRCODE='23514';
                END IF;"""
_ALTA_IA = """                IF NEW.redactada_por='ia' THEN
                    IF NEW.estado<>'en_revision' OR NEW.generacion<>1 OR NEW.responsable_id<>actor
                       OR NEW.autores<>'["ia"]'::jsonb OR NEW.nota_descarte IS NOT NULL
                       OR NEW.descartada_por IS NOT NULL OR NEW.descartada_en IS NOT NULL
                       OR NOT (NEW.origen_ia='resolucion' OR public.biblioteca_puede('editor')
                               OR public.biblioteca_puede('revisor_tecnico')) THEN
                        RAISE EXCEPTION 'BIB_ALTA_DENEGADA' USING ERRCODE='23514';
                    END IF;
                ELSIF NEW.estado<>'en_revision' OR NEW.generacion<>1 OR NOT public.biblioteca_puede('editor')
                   OR NEW.responsable_id<>actor OR NEW.autores<>jsonb_build_array(actor) THEN
                    RAISE EXCEPTION 'BIB_ALTA_DENEGADA' USING ERRCODE='23514';
                END IF;"""
_IDENTIDAD = """                   OR NEW.sustituye_id IS DISTINCT FROM OLD.sustituye_id OR NEW.creada_en<>OLD.creada_en THEN"""
_IDENTIDAD_IA = """                   OR NEW.sustituye_id IS DISTINCT FROM OLD.sustituye_id OR NEW.creada_en<>OLD.creada_en
                   OR NEW.redactada_por<>OLD.redactada_por OR NEW.modelo_ia IS DISTINCT FROM OLD.modelo_ia
                   OR NEW.origen_ia IS DISTINCT FROM OLD.origen_ia
                   OR NEW.id_resolucion IS DISTINCT FROM OLD.id_resolucion
                   OR NEW.motivo_ia IS DISTINCT FROM OLD.motivo_ia
                   OR NEW.cambios_ia IS DISTINCT FROM OLD.cambios_ia THEN"""
_MISMO_ESTADO = """                IF NEW.estado=OLD.estado THEN
                    IF OLD.estado<>'en_revision'"""
_MISMO_ESTADO_IA = """                IF NEW.estado=OLD.estado THEN
                    IF OLD.redactada_por='ia' THEN
                        RAISE EXCEPTION 'BIB_VERSION_IA_NO_EDITABLE' USING ERRCODE='23514';
                    END IF;
                    IF OLD.estado<>'en_revision'"""
_TRANSICION = """                ELSE
                    IF NOT public.biblioteca_puede('publicador') OR OLD.autores ? actor"""
_TRANSICION_DESCARTE = """                ELSIF OLD.estado='en_revision' AND NEW.estado='retirada' THEN
                    IF NOT (public.biblioteca_puede('editor') OR public.biblioteca_puede('revisor_tecnico')
                            OR public.biblioteca_puede('publicador'))
                       OR length(trim(COALESCE(NEW.nota_descarte,'')))=0
                       OR NEW.descartada_por IS DISTINCT FROM actor OR NEW.descartada_en IS NULL
                       OR (to_jsonb(NEW)-'estado'-'motivo'-'nota_descarte'-'descartada_por'-'descartada_en')
                          IS DISTINCT FROM
                          (to_jsonb(OLD)-'estado'-'motivo'-'nota_descarte'-'descartada_por'-'descartada_en') THEN
                        RAISE EXCEPTION 'BIB_TRANSICION_DENEGADA' USING ERRCODE='23514';
                    END IF;
                ELSE
                    IF NOT public.biblioteca_puede('publicador') OR OLD.autores ? actor"""


def _cambiar(cuerpo: str, antes: str, despues: str) -> str:
    if cuerpo.count(antes) != 1:
        raise RuntimeError("BIB-406: la definición de BIB-403 no tiene la forma esperada")
    return cuerpo.replace(antes, despues)


# ¤adpa
def definicion_nueva() -> str:
    """La definición de BIB-403 con los cambios de BIB-406 (la prueba la lee sin base)."""
    bib403 = _bib403()
    cuerpo = bib403._NUEVO
    for antes, despues in ((_ALTA_PERSONA, _ALTA_IA), (_IDENTIDAD, _IDENTIDAD_IA),
                           (_MISMO_ESTADO, _MISMO_ESTADO_IA), (_TRANSICION, _TRANSICION_DESCARTE)):
        cuerpo = _cambiar(cuerpo, antes, despues)
    return bib403._definicion(cuerpo)


_COLUMNAS = """
    ALTER TABLE biblioteca_versiones
        ADD COLUMN redactada_por varchar NOT NULL DEFAULT 'persona'
            CONSTRAINT biblioteca_versiones_redactada_por_check CHECK (redactada_por IN ('persona','ia')),
        ADD COLUMN modelo_ia varchar,
        ADD COLUMN origen_ia varchar
            CONSTRAINT biblioteca_versiones_origen_ia_check CHECK (origen_ia IN ('resolucion','peticion')),
        ADD COLUMN id_resolucion varchar,
        ADD COLUMN motivo_ia text,
        ADD COLUMN cambios_ia jsonb,
        ADD COLUMN nota_descarte text,
        ADD COLUMN descartada_por varchar REFERENCES users(id),
        ADD COLUMN descartada_en timestamptz,
        ADD CONSTRAINT biblioteca_versiones_autoria_ia_check CHECK (
            (redactada_por='ia') = (autores='["ia"]'::jsonb)
            AND (redactada_por<>'ia' OR (modelo_ia IS NOT NULL AND origen_ia IS NOT NULL AND cambios_ia IS NOT NULL))
            AND (origen_ia IS DISTINCT FROM 'resolucion' OR id_resolucion IS NOT NULL));
"""
_QUITAR = """
    ALTER TABLE biblioteca_versiones
        DROP CONSTRAINT biblioteca_versiones_autoria_ia_check,
        DROP COLUMN descartada_en, DROP COLUMN descartada_por, DROP COLUMN nota_descarte,
        DROP COLUMN cambios_ia, DROP COLUMN motivo_ia, DROP COLUMN id_resolucion,
        DROP COLUMN origen_ia, DROP COLUMN modelo_ia, DROP COLUMN redactada_por;
"""


# ¤adpa
def upgrade() -> None:
    op.execute(_COLUMNAS)
    op.execute(definicion_nueva())


# ¤adpa
def downgrade() -> None:
    bib403 = _bib403()
    op.execute(bib403._definicion(bib403._NUEVO))
    op.execute(_QUITAR)
