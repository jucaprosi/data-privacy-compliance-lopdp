# Fusión de migraciones de Alembic con varias tareas en paralelo

Desde el 2026-11-05 no hay ramas `dev/<persona>`: cada tarea nace de `origin/main` y abre su PR directo a `main`. Varias sesiones pueden añadir migraciones a la vez, cada una en su worktree. Este documento fija qué se hace cuando eso produce más de una cabeza. No depende de dónde esté alojada la base (Neon hoy, Cloud SQL después de GCP-01 a GCP-04): habla de **base personal** y **base compartida**.

## 1. Qué es una cabeza

Una **cabeza** es una migración sin hijas: ninguna otra la nombra en su `down_revision`. La base guarda una sola revisión, la última aplicada, y `alembic upgrade head` recorre la cadena desde ahí hasta la cabeza. Con dos cabezas, `upgrade head` no sabe a cuál ir y falla.

Las cabezas salen de los archivos de `alembic/versions/`, es decir, de Git. Cambiar de proveedor de base no las cambia.

## 2. Por qué aparecen

Cuatro tareas que parten de la misma cabeza `D` añaden cada una su migración con `down_revision = "D"`:

```
D ─┬─ E1   (tarea 1)
   ├─ E2   (tarea 2)
   ├─ E3   (tarea 3)
   └─ E4   (tarea 4)
```

Git no ve conflicto, porque son archivos distintos. Alembic sí: cuatro cabezas.

## 3. Quién ajusta

La primera tarea que se fusiona no hace nada: `main` pasa a `E1`. **Cada tarea posterior ajusta en su turno**, dentro de su propio PR y antes de fusionar. Si dos están listas a la vez, la segunda vuelve a traer `main` cuando entra la primera.

Pasos de quien ajusta:

1. Traer `main` a la rama de la tarea:
   ```bash
   git fetch origin
   git merge origin/main
   ```
2. Ver las cabezas:
   ```bash
   alembic heads
   ```
   Una sola: no hay nada que hacer. Dos o más: elegir la opción A o B.

## 4. Opción A: reencadenar (por defecto)

**Cuándo:** la migración de la tarea solo se ha aplicado en la base personal de esa tarea y en ninguna base compartida.

**Qué se hace:** cambiar el `down_revision` de la migración propia de la cabeza vieja (`D`) a la cabeza actual de `main` (`E1`). La cadena queda en línea recta y no se añaden archivos.

```
D ─ E1 ─ E2
```

**Efecto en la base personal:** esa base ya tiene aplicada `E2` y su `alembic_version` apunta a `E2`, cuyo padre ahora es `E1`, que nunca se aplicó. Hay que rehacer la base personal desde la compartida de pruebas (`test-main`) y migrar hasta la cabeza. Con ramas Neon es crear la rama de nuevo; con una base efímera (contenedor o base creada al vuelo) es rehacerla.

## 5. Opción B: migración de fusión

**Cuándo:** la migración de la tarea ya se aplicó en una base compartida (`test-main`, staging o producción). Editar su `down_revision` dejaría esa base con una revisión que no encaja en la cadena.

**Qué se hace:** añadir una migración vacía, sin cambios de esquema, cuyo `down_revision` lista las dos cabezas:

```bash
alembic merge heads -m "fusion <id-tarea>"
```

```
D ─┬─ E1 ─┐
   └─ E2 ─┴─ F
```

`upgrade()` y `downgrade()` quedan vacíos (`pass`). Precedente: `alembic/versions/20261118_merge_heads_cierre_dev.py`.

## 6. Elegir entre A y B

| Pregunta | Sí | No |
|---|---|---|
| ¿Mi migración está aplicada en una base compartida? | B | A |

Mientras la migración no haya salido de tu base personal, usa A: la cadena no acumula migraciones vacías.

## 7. Qué lo hace cumplir

- **Árbitro:** `tests/test_alembic_una_cabeza.py` falla si `get_heads()` devuelve más de una. Corre en todo PR sobre la fusión de prueba con `main`, y de nuevo tras cada fusión en `main`.
- **Pruebas de una tarea:** una prueba de migración no debe exigir que *su* migración sea la cabeza (la próxima fusión la desmentiría). Debe exigir «una sola cabeza y mi revisión existe en la cadena» (precedente: `tests/test_bib_401_plantillas_cuenta.py`).
- **Despliegue:** el paso que ejecuta `alembic upgrade head` (hoy el flujo de Neon, después el despliegue a Cloud SQL) falla con más de una cabeza. Por eso la prueba va primero.

## 8. Registro

Toda migración aplicada a mano en una base compartida o en producción consta en `REGISTRO_MIGRACIONES_MANUALES.md`, incluida la de una migración de fusión.

## 9. Resumen para el brief de una tarea con migración

> Tu `down_revision` es la cabeza de `main` cuando creas la rama. Antes de fusionar, `git merge origin/main` y `alembic heads`. Si hay más de una cabeza, reencadena (A) o añade una migración de fusión (B) según `governance/operaciones/FUSION_ALEMBIC.md`. Avisa en el PR de que la tarea trae migración.
