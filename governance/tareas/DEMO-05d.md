+++
id = "DEMO-05d"
titulo = "Purga de la demo frente a los triggers de inmutabilidad de la biblioteca: función SECURITY DEFINER solo en la base de la demo"
ola = "backlog"
estado = "pendiente"
sala = "demo"
depende_de = ["DEMO-05", "DEMO-05b", "DEMO-05c", "SEC-20"]
propiedad = ["jobs/purga_demo/politicas_purga.sql", "jobs/purga_demo/purga.py", "jobs/purga_demo/guardias.py", "tests/test_demo05d_purga_inmutables.py"]
crea = ["tests/test_demo05d_purga_inmutables.py"]
arbitro = "pytest tests/test_demo05d_purga_inmutables.py contra la PostgreSQL efímera del CI (sin producción ni Cloud SQL): una demo con biblioteca queda con 0 filas tras la purga; al terminar tgenabled = 'O' en los triggers de inmutabilidad; la función falla sin marcador, con la plantilla y con un tenant que no es demo; lopdp_app no puede ejecutarla; ninguna migración define la función; la guardia del Job sale con 1 sin borrar nada si falta la función o su lista no cubre todo trigger que lance excepción en DELETE sobre una tabla con tenant_id; mutaciones documentadas, una por prueba"
rastros = ["¤demo"]
+++

# DEMO-05d · Purga de la demo frente a los triggers de inmutabilidad

Diseño del Arquitecto ADPA (2026-11-12) a petición del CTO, a partir del hallazgo de la sesión de DEMO-02: con datos reales de biblioteca la purga falla con `no se pudo vaciar por claves foráneas: biblioteca_documentos, biblioteca_documentos_historial`. Medido leyendo el código; **no se ejecutó nada**. Diseño completo en la conversación del Arquitecto; lo que sigue es la entrega.

## Qué falla hoy
Tres triggers impiden siempre el DELETE: sobre `biblioteca_documentos_historial`, `biblioteca_descargas` y `biblioteca_eventos_documento`. Ninguno reconoce un GUC y lanzan 23514, que la purga trata como `IntegrityError`: reintenta y al final revierte, así que una demo con biblioteca nunca se purga. **Sin medir:** si `biblioteca_versiones`, `biblioteca_revisiones` o el AFTER `biblioteca_registrar_evento` también bloquean; lo mide esta ficha en la PostgreSQL efímera.

## Decisión (opción a)
Una función `SECURITY DEFINER`, `purga_demo_borrar_inmutables(tenant)`:
- Existe **solo en la base de la demo**: la crea `politicas_purga.sql` (DEMO-05c), **nunca una migración** (la cadena de Alembic también corre en producción).
- Solo el rol `purga_demo` puede ejecutarla (`EXECUTE` solo a ese rol).
- Exige el marcador `demo`, que el tenant sea `es_demo` y que no sea la plantilla.
- Con una **lista cerrada de triggers**: `DISABLE TRIGGER`, el `DELETE` del tenant y `ENABLE`, todo dentro de la transacción del Job. El bloqueo exclusivo impide que otra sesión escriba mientras tanto, y un rollback deja el trigger encendido.
- No usa `session_replication_role`.
- Descartadas: (c) el GUC (el bypass llegaría al código de producción y cualquier sesión puede fijar un GUC `app.*`); (b) el borrado lógico (las claves foráneas a `tenants` impiden borrar la organización, lo que contradice el invariante 63 de EVY; el costo en espacio no era el problema: menos de 1 MB por demo).

## Entrega
1. `jobs/purga_demo/politicas_purga.sql`: la función y su `EXECUTE` solo para `purga_demo`.
2. `jobs/purga_demo/purga.py`: llama a la función y añade su lista a `TABLAS_EXENTAS`.
3. `jobs/purga_demo/guardias.py`: **guardia del Job**: la función tiene que existir y su lista tiene que cubrir todo trigger que lance excepción en DELETE sobre una tabla con `tenant_id`; si no, el Job sale con 1 sin borrar nada.
4. `tests/test_demo05d_purga_inmutables.py`, cada prueba con su mutación: una demo con biblioteca queda con 0 filas; al terminar `tgenabled = 'O'`; falla sin marcador, con la plantilla y con un tenant que no es demo; `lopdp_app` no puede ejecutarla; ninguna migración define la función.
- **Pendiente de medir:** si esas tablas tienen FORCE RLS para su dueño; en ese caso la función fija `app.current_tenant_id` y la RLS no se toca.
- **El CTO tiene que confirmar** el modelo de apagar triggers dentro de la transacción antes de lanzar la ficha.

## Orden (Tech Lead)
Depende de DEMO-05c (el SQL y la guardia de políticas) y, como esa, de que se decida si DEMO-05, dueña entera de `jobs/purga_demo/**`, pasa a `hecha`.
