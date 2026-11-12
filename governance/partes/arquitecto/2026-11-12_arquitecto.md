# Parte del Arquitecto ADPA · 2026-11-12

## Lo decidido
- **FE-25 (ficha resumen):**
  - Aprobado que sector y tamaño salgan del store, y que nombre, semáforos y contadores salgan de `GET /organizacion/cartera`.
  - No se usa `GET /organizacion/roles`: exige `admin_organizacion` y devuelve asignaciones completas. Para quien no es administrador, el DPO se oculta o se muestra «No disponible», nunca «Sin designar», porque sería falso.
  - RUC, naturaleza, nombres del DPO y del implementador (solo el nombre, sin correo) y los contadores de solicitudes y vulneraciones van en una ficha nueva de organización que amplía la fila de cartera, con los contadores por los pasillos.
- **DEMO-05c (políticas de purga, paso 5 del brief de DEMO-05):**
  - Política explícita para `purga_demo`, sin BYPASSRLS, por decisión del CTO.
  - Cada política exige el marcador `demo`. `tenants` excluye la plantilla y las organizaciones que no son demo, y el resto de tablas filtra por esos tenants.
  - El UPDATE de `demo_sesiones` solo permite poner a NULL.
  - Motivo: que la base falle cerrada aunque falle el Job.
  - No se usa `USING (true)`: propuse al CTO esta forma más estrecha y queda pendiente que la confirme.
  - Probado en un PostgreSQL 16 desechable: idempotente, sin INSERT y sin cambios para `lopdp_app`.
  - Guardia del Job: no borra nada si a alguna tabla con `tenant_id` le falta su política. Árbitro: prueba de CI con PostgreSQL efímera.
  - Descartada la migración condicionada al rol, porque correría en la cadena de producción.
- **DEMO-05d (purga frente a la inmutabilidad de la biblioteca):** opción (a), confirmada por el CTO.
  - Función `SECURITY DEFINER` que solo existe en la base de la demo. La crea el SQL del brief, nunca una migración.
  - Solo la ejecuta `purga_demo`. Exige el marcador `demo` y que el tenant no sea la plantilla.
  - Apaga una lista literal cerrada de triggers solo dentro de la transacción, con bloqueo exclusivo.
  - Descartada (c), un GUC que el trigger reconozca: el bypass llegaría al código de producción.
  - Descartada (b), el borrado lógico: las FK a `tenants` impiden borrar la demo, en contra de INVARIANTS_EVYDENTIA n.º 63. El costo de almacenamiento sería mínimo.
  - Descartado recrear la base de la demo.

## Lo que falta
- DEMO-05c: el CTO acepta o descarta la forma más estrecha frente a `USING (true)`. Después, el propietario ejecuta el paso 5 y entrega al Tech Lead la salida de las comprobaciones de solo lectura.
- DEMO-05d:
  - Medir en la PostgreSQL efímera si `biblioteca_versiones`, `biblioteca_revisiones` o el trigger AFTER `biblioteca_registrar_evento` también impiden el borrado, y cerrar la lista.
  - Medir si las tablas tienen FORCE RLS para su dueño.
  - Las dos mediciones las hace la ficha.
- Política de purga sobre `users`: espera a DEMO-05b, que debe fijar cómo se distinguen las personas ficticias.
- FE-25: el CTO decide quién ve el nombre del DPO. Mi propuesta es que lo vea cualquier miembro, pero sin una cita legal verificada.
- Ficha nueva de organización para ampliar la fila de cartera: la redacta el Tech Lead.

## Lo que no se toca
- La inmutabilidad de producción y de pruebas: ningún trigger de inmutabilidad cambia por la demo.
- La RLS de los roles de la aplicación: las políticas nuevas son solo `TO purga_demo`.
- La función de la demo y las políticas de purga no viajan por Alembic.
- ADPA: las salas no leen tablas ajenas; los datos llegan por la compuerta `_service.py` o por el pasillo de la sala dueña.
- No se cita ningún artículo legal sin texto verificado en `CITAS_LEGALES_VERIFICADAS.md`.
- Sin acciones en Google Cloud por parte de la IA: solo comandos de lectura, y los cambios los hace el propietario mediante el brief.
