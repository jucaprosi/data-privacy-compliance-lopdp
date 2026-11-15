# RET-10 · Comentarios de las migraciones aplicadas
`¤sdd` `¤arbitro`

## 1. Datos

Sin tablas nuevas ni migraciones nuevas. Cambian solo los comentarios y docstrings de dos migraciones ya aplicadas:

- `alembic/versions/20261008_app_role_rls.py`
- `alembic/versions/20261108_biblioteca_capacidades_propietario.py`

Hecho medido: Alembic 1.20.0 identifica cada migración por su revisión. `alembic_version` guarda solo `version_num` y no calcula ninguna suma del contenido. Cambiar comentarios no altera las cabezas ni las bases ya migradas.

## 2. API

No aplica.

## 3. Reglas

- **R1 · Solo texto.** Los comentarios y docstrings describen el rol de aplicación, la RLS y las capacidades de la biblioteca en términos de Cloud SQL para PostgreSQL y del PostgreSQL 16 local.
- **R2 · Código idéntico.** `upgrade`, `downgrade`, `revision`, `down_revision`, `branch_labels` y `depends_on` no cambian.
- **R3 · Árbitro AST.** Para cada archivo, el AST con los docstrings quitados es idéntico al de `origin/main` (`ast.dump` de los dos árboles). Los comentarios `#` no están en el AST. La comprobación la corre el revisor una vez, con el script del PR, y no queda como prueba permanente.
- **R4 · Esquema vivo fuera.** Las columnas que todavía nombran un almacén anterior son esquema vivo; las renombra la migración nueva de RET-02.
- **R-ADPA · Ortogonalidad ZERAG (`RET-10`).** Solo los dos archivos de §1.

## 4. Interfaz

No aplica.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** cada archivo de §1, **entonces** su AST sin docstrings es idéntico al de `origin/main`. | comprobación AST de R3, con su salida en el PR |
| **Dado** el grafo de Alembic, **entonces** sigue con una cabeza y las revisiones no cambian. | `tests/test_alembic_una_cabeza.py` |
| **Dado** el árbol con la ficha fusionada, **entonces** la suite completa pasa. | la suite existente |

## 6. Trazabilidad

- Ficha: `governance/tareas/RET-10.md`. Especificación de referencia: `governance/especificaciones/README.md`.
- Mapa del programa: `governance/partes/arquitecto/2026-11-14_COBERTURA_PLATAFORMA_UNICA.md`, §4.
- Depende de BIB-117, que posee la segunda migración.
