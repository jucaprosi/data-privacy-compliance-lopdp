# Migraciones de Alembic con una rama por sala

Desde CI-28 cada sala tiene su propia rama de Alembic: varias tareas de salas distintas añaden migraciones a la vez sin serializarse ni re-colgarse de la cabeza de `main`. Este documento fija cómo se cuelga una migración. No depende de dónde esté alojada la base (contenedor local o Cloud SQL).

Especificación: `governance/especificaciones/CI-28.md`. Código: `alembic/salas.py` (`BASE_COMUN`, `TABLAS_POR_SALA`), árbitro `tests/test_alembic_cabeza_por_sala.py`.

## 1. El grafo

```
… historia anterior … ─ BASE_COMUN ─┬─ roadmap_1 ─ roadmap_2        (etiqueta «roadmap»)
                                    ├─ diagnostico_1                (etiqueta «diagnostico»)
                                    └─ firma_1 ─ firma_2            (etiqueta «firma_electronica»)
```

- **`BASE_COMUN`** es la cabeza que tenía `main` al fusionar CI-28. La historia anterior no se reescribe.
- La **etiqueta** de una rama es el nombre de la carpeta de su sala en `features/`.
- Una **cabeza** es una migración sin hijas en su rama. Hay una por sala, más `BASE_COMUN` mientras nadie cuelga de ella.

## 2. Cómo se cuelga una migración

| Caso | `down_revision` | `branch_labels` |
|---|---|---|
| Primera migración de la sala | `BASE_COMUN` (de `alembic/salas.py`) | `("<sala>",)` |
| Siguientes migraciones de la sala | la cabeza de su sala: `alembic revision --head <sala>@head` | no se declara: se hereda |

Ninguna migración nueva tiene un `down_revision` con revisiones de dos salas (sin merges entre salas).

## 3. Dependencias entre salas

Si una migración de la sala X crea una FK hacia una tabla de la sala Y, o lee, altera o rellena una tabla de Y, declara `depends_on` con la revisión de Y que creó o cambió esa tabla. En ningún otro caso hay orden entre salas. El árbitro lo detecta por las tablas de `TABLAS_POR_SALA` y por las que crean las migraciones de cada sala: llamadas `op.*`, `sa.ForeignKey` y los nombres de tabla dentro del SQL en texto de `op.execute`.

## 4. Despliegue

Todo lo que migra usa `alembic upgrade heads` (todas las cabezas): el paso de migración del pipeline, los scripts de entorno de pruebas y los comandos de los briefs. `alembic upgrade head` (sin `s`) falla con más de una cabeza. Para comprobar una base: el conjunto de `alembic current` debe ser igual al de `alembic heads` (`scripts/verificar_cloudsql_conexion.py`, comprobación 5).

## 5. Qué hace una tarea con migración

1. Traer `origin/main` y ver las cabezas: `alembic heads`.
2. Colgar la migración según el §2 y declarar `depends_on` si toca tablas de otra sala (§3).
3. Correr `pytest tests/test_alembic_cabeza_por_sala.py`.

Ya no se pide re-colgarse de la cabeza de `main` ni añadir migraciones de fusión: dos tareas de salas distintas no compiten por la misma cabeza. Solo queda una carrera: dos tareas **de la misma sala** (o dos primeras migraciones colgando de `BASE_COMUN` con la misma etiqueta) producen dos cabezas en esa rama. La segunda en fusionarse trae `main` y re-cuelga su migración de la cabeza de su sala, una vez, en su propia sesión.

## 6. Transición (R9)

Ninguna migración abierta en otro PR se reescribe por CI-28. Si su PR se fusiona después de CI-28, cambia una vez su `down_revision` a `BASE_COMUN` (o a la cabeza de su sala) y añade `branch_labels` con su sala. Mientras CI-28 no esté en `main`, rige la regla lineal de una sola cabeza.

## 7. Qué lo hace cumplir

- **Árbitro:** `tests/test_alembic_cabeza_por_sala.py`: una cabeza por etiqueta, toda migración posterior a `BASE_COMUN` con sala, etiquetas que son carpetas de `features/`, sin merges entre salas, `depends_on` entre salas y `test_despliegue_usa_heads`.
- **Pruebas de una tarea:** una prueba de migración no debe exigir que *su* migración sea la cabeza. Debe exigir «una cabeza de mi sala (`cabeza_de_sala("<sala>")`, de `tests/_alembic_salas.py`) y mi revisión existe en la cadena».
- **`BASE_COMUN` y `TABLAS_POR_SALA`:** viven en `alembic/salas.py`.

## 8. Registro

Toda migración aplicada a mano en una base compartida o en producción consta en `REGISTRO_MIGRACIONES_MANUALES.md`.

## 9. Resumen para el brief de una tarea con migración

> Tu migración cuelga de la cabeza de tu sala (`alembic revision --head <sala>@head`), o de `BASE_COMUN` con `branch_labels = ("<sala>",)` si es la primera de la sala. Si tocas tablas de otra sala, declara `depends_on`. Despliega con `alembic upgrade heads`. Avisa en el PR de que la tarea trae migración. Guía: `governance/operaciones/FUSION_ALEMBIC.md`.
