# RAT-08 · Área responsable del tratamiento como referencia al área de la organización
`¤sdd` `¤rat`

## 1. Datos

Migración `alembic/versions/rat08_area_id.py` (sin fecha; su `down_revision` es la cabeza de `main` al crear la rama, `FUSION_ALEMBIC.md`):

| Objeto | Definición |
| :--- | :--- |
| `areas` | `uq_areas_id_tenant UNIQUE (id, tenant_id)`, aditiva, el mismo patrón que `uq_bib_documentos_id_tenant` |
| `rat_actividades.area_id` | `String NULL` |
| `fk_rat_area` | `FOREIGN KEY (area_id, tenant_id) REFERENCES areas (id, tenant_id)` |
| `ix_rat_actividades_area` | índice sobre `(tenant_id, area_id)` |
| `rat_actividades.area_responsable` | `Text NOT NULL`; texto de respaldo: el escrito por el responsable o el último nombre guardado del área |

**Emparejado de datos.** La migración pone `area_id` cuando `lower(trim(area_responsable))` coincide con `lower(trim(nombre))` de exactamente un área viva (`deleted_at IS NULL`) del mismo tenant. Si no coincide con ninguna o coincide con varias, deja `NULL` y conserva el texto. Al terminar imprime tres recuentos: emparejadas, sin emparejar y ambiguas. `downgrade` borra el índice, la FK, la columna y la restricción única.

Hecho medido en `origin/main` 3554924e:
- `rat_actividades.area_responsable` es `Text NOT NULL` (`20261024_rat_actividades.py`), y `ActividadRAT.area_responsable` es `str = ""` (`features/rat/domain/models.py:53`);
- `areas` tiene clave primaria `id` y no tiene `UNIQUE (id, tenant_id)` (`20261006_user_tenant_roles.py`);
- las áreas se leen con `app_core/pasillo/organizacion.py::listar_areas` y, desde el frontend, con `GET /api/v1/organizacion/areas` (`frontend/src/lib/roadmap/cliente.ts`).

## 2. API

`api/routers/rat.py`:
- La entrada de crear y editar acepta `area_id: str | None`. Con `area_id`, el servidor comprueba por `app_core/pasillo/organizacion.py` que el área existe, está viva y es del tenant; si no, responde **422 `AREA_NO_VALIDA`**. Además rellena `area_responsable` con el `nombre` del área.
- Sin `area_id`, `area_responsable` (texto) sigue siendo obligatorio.
- La salida incluye `area_id` (nulo o id) y `area_responsable`. Con `area_id` de un área viva, `area_responsable` es el nombre actual del área, leído por el pasillo. Sin `area_id`, o con un área borrada, es el texto guardado.

## 3. Reglas

- **R1 · Referencia, no texto.** Un tratamiento nuevo o editado con área elegida guarda `area_id`. `area_responsable` guarda el nombre del área en el momento de guardar, como respaldo.
- **R2 · Emparejado sin inventar.** La migración solo empareja coincidencias únicas tras normalizar mayúsculas y espacios de los extremos. Nunca crea un área ni elige entre varias.
- **R3 · Texto conservado.** `area_responsable` es el respaldo de las filas sin `area_id` y de las que referencian un área borrada. La migración no lo borra ni lo vacía.
- **R4 · Mismo tenant.** La FK compuesta impide referenciar un área de otro tenant. La comprobación de §2 da el error de dominio antes de llegar a la base.
- **R5 · Nombre resuelto al leer.** Cuando `area_id` apunta a un área viva, el listado y la exportación muestran su nombre actual, leído por `app_core/pasillo/organizacion.py` (`listar_areas` para el listado, `area_del_tenant` para una fila). Un área borrada no se ofrece en el selector ni se acepta en §2; las filas que la referencian muestran su `area_responsable`. Renombrar un área no escribe en `rat_actividades`: la sala de organización no escribe en las filas del RAT.
- **R6 · Exportación.** `exportacion_engine.py` muestra en «Área responsable» el nombre actual del área enlazada y, sin área enlazada viva, `area_responsable`.
- **R-ADPA · Ortogonalidad ZERAG (`RAT-08`).** `features/rat` lee las áreas solo con `app_core/pasillo/organizacion.py` (sección `#RAT-08` para la comprobación de §2: `area_del_tenant(session, tenant_id, area_id) -> dict | None`). No importa `features.organizacion` (`ImportsCruzados = ∅`).

## 4. Interfaz

`frontend/src/components/modules/RatModule.tsx`, con el tipo de `frontend/src/types/rat_area.ts` (`area_id?: string | null`, que extiende `ActividadRAT`):
- El campo «Área responsable» es un selector con las áreas de `GET /api/v1/organizacion/areas`, ordenadas por nombre. Su valor es `area_id`.
- Si el tratamiento no tiene `area_id` y la organización tiene áreas, el campo muestra «Área registrada: {area_responsable}» con el botón «Elegir un área de la organización», que abre el selector.
- Si la organización no tiene áreas, el campo es de texto, con una nota que indica que las áreas se crean en la estructura de la organización.
- La tabla muestra el `area_responsable` que devuelve la API (§2), que ya es el nombre actual cuando hay área enlazada.
- El valor inicial de ejemplo del formulario es vacío, no un área inventada.
- Textos sin jerga técnica; el error 422 se muestra como «El área elegida ya no está disponible. Elige otra.» y la lista de áreas se recarga.

El diseño visual lo revisa UX/UI antes de lanzar la ficha.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** filas con «Contabilidad » y «contabilidad» y un área «Contabilidad», **cuando** corre la migración, **entonces** las dos quedan con su `area_id`. Mutación m1: emparejar sin normalizar mayúsculas hace fallar la prueba. | `tests/test_rat08_area_id.py` |
| **Dado** una fila con un texto que no casa, o que casa con dos áreas, **entonces** queda con `area_id` nulo y su texto intacto, y no se crea ningún área. Mutación m2: inventar o elegir un área hace fallar la prueba. | `tests/test_rat08_area_id.py` |
| **Dado** filas sin emparejar, **entonces** `area_responsable` conserva su texto tras la migración. Mutación m3: vaciar o borrar la columna hace fallar la prueba. | `tests/test_rat08_area_id.py` |
| **Dado** un `area_id` de otro tenant o borrado, **cuando** se crea un tratamiento, **entonces** la respuesta es 422 `AREA_NO_VALIDA` y no se escribe nada. | `tests/test_rat08_area_id.py` |
| **Dado** un `area_id` válido, **entonces** la fila guarda `area_id` y `area_responsable` con el nombre del área. | `tests/test_rat08_area_id.py` |
| **Dado** un tratamiento con `area_id` y un área renombrada, **cuando** se lista el RAT y se exporta, **entonces** ambos muestran el nombre nuevo y `rat_actividades` queda sin cambios (mismo `area_responsable` y misma fila). Mutación m4: leer `area_responsable` en lugar del nombre del área hace fallar la prueba. | `tests/test_rat08_area_id.py` |
| **Dado** un tratamiento cuyo área se borró, **entonces** el listado y la exportación muestran su `area_responsable` guardado. | `tests/test_rat08_area_id.py` |
| **Dado** el grafo de Alembic, **entonces** tiene una sola cabeza y `downgrade` deja el esquema anterior. | `tests/test_alembic_una_cabeza.py` y `tests/test_rat08_area_id.py` |
| **Dado** el frontend, **entonces** `tsc --noEmit` pasa. | `tsc --noEmit` |

## 6. Trazabilidad

- Ficha: `governance/tareas/RAT-08.md`. Especificación de referencia: `governance/especificaciones/README.md`.
- Depende de RAT-07, que toca los mismos archivos del RAT, y de RAT-06 y CORE-01, dueñas anteriores de `exportacion_engine.py`.
- FOR-01, o una ficha hija, puede usar `area_id` para el denominador de la cobertura por área.
- Pruebas contra el PostgreSQL 16 local, con `exigir_base_de_pruebas()`.
