+++
id = "INC-03"
titulo = "Estado del incidente (abierto o cerrado) como eventos que solo se agregan, y contador de abiertos"
ola = "backlog"
estado = "pendiente"
sala = "incidentes"
depende_de = ["INC-01", "ADPA-06"]
propiedad = ["alembic/versions/inc03_incidentes_estado.py", "features/incidentes/domain/estado.py", "features/incidentes/services/estado_engine.py", "features/incidentes/incidentes_service.py#INC-03", "features/incidentes/domain/errores.py#INC-03", "app_core/pasillo/incidentes.py#INC-03", "api/routers/incidentes_estado.py", "api/routers/incidentes.py", "tests/test_inc03_estado_incidente.py", "tests/matriz/INC-03.py"]
crea = ["alembic/versions/inc03_incidentes_estado.py", "features/incidentes/domain/estado.py", "features/incidentes/services/estado_engine.py", "api/routers/incidentes_estado.py", "tests/test_inc03_estado_incidente.py", "tests/matriz/INC-03.py"]
arbitro = "pytest tests/test_inc03_estado_incidente.py + tests/test_incidentes.py + tests/test_matriz_permisos.py contra PostgreSQL 16 local con lopdp_app (RLS); mutaciones m1 a m8"
rastros = ["¤incidentes", "¤rbac-tenant"]
+++

# INC-03 · Estado del incidente (abierto o cerrado) como eventos que solo se agregan, y contador de abiertos

Diseño del Arquitecto ADPA (2026-11-12), pedido del CTO. **Motivo:** la ficha de la organización (ORG-24) no puede decir «vulneraciones abiertas» porque `incidentes` no guarda estado; hasta esta ficha cuenta `vulneraciones_registradas`.

**Cambio de fondo: no hay columna de estado.** `incidentes` es inmutable por diseño: INC-01 dice «un incidente registrado no se edita ni se borra», tiene huella SHA-256 encadenada por organización y `lopdp_app` solo tiene `SELECT, INSERT` (`20261028_bitacora_incidentes.py`). Una columna de estado obligaría a dar `UPDATE` y rompería esa garantía. El estado es una **tabla de eventos que solo se agregan**; el estado actual es el del último evento.

## Datos (migración `inc03_incidentes_estado.py`, sin fecha)
- `down_revision` = la cabeza de `main` al implementar; una sola cabeza (FUSION_ALEMBIC).
- Tabla `incidentes_eventos_estado`: `id`, `tenant_id`, `incidente_id`, `secuencia`, `tipo` CHECK IN (`cierre`, `reapertura`), `motivo` TEXT NOT NULL CHECK (`length(trim(motivo)) >= 10`), `registrado_por`, `registrado_en`.
- `UNIQUE (incidente_id, secuencia)`: dos cierres simultáneos del mismo incidente chocan y el segundo recibe 409.
- FK compuesta `(incidente_id, tenant_id)` → `incidentes(id, tenant_id)`; para eso se agrega a `incidentes` `uq_incidentes_id_tenant UNIQUE (id, tenant_id)` (DDL, no toca filas).
- RLS `ENABLE` y `FORCE` con `USING` y `WITH CHECK` por `tenant_id`; `GRANT SELECT, INSERT` a `lopdp_app`, sin `UPDATE` ni `DELETE`.
- **Sin backfill ni recuento:** un incidente sin eventos está abierto, que es la verdad para todos los de hoy. Nada se reescribe. La huella de `incidentes` no cambia: el estado no entra en `contenido()`.

## Transiciones y roles
- abierto → cerrado con un evento `cierre`; cerrado → abierto con un evento `reapertura`. Cerrar algo cerrado o reabrir algo abierto → 409 con código del catálogo.
- Roles: `ROLES_REGISTRO` de INC-01 (`admin_organizacion`, `coordinador`, `responsable_area`, `implementador`). El DPO consulta y no cambia el estado, por la misma razón por la que no registra (art. 49, ORG-01). Con ORG-22, el auditor solo consulta.
- **Plazos: ninguno.** No se calcula ni se exige plazo para cerrar; eso es de REG-01.
- **Pregunta abierta al CTO (ESTIMADO):** ¿un incidente con `afecta_datos_personales` puede cerrarse antes de que INC-02 registre la decisión de notificar? Se recomienda que sí por ahora; cuando INC-02 exista, ella agrega esa precondición en su propia sección, sin tocar INC-03.

## API
`POST /api/v1/incidentes/{id}/cerrar` y `/reabrir` (router propio `incidentes_estado.py`, `AUTO_REGISTRO = True`; cuerpo con `motivo`, `extra="forbid"`); identidad y organización del token, nunca del cuerpo. El `GET` de la lista de `api/routers/incidentes.py` suma `estado`. El pasillo `app_core/pasillo/incidentes.py#INC-03` expone `contar_abiertos(tenant)`, que usa ORG-24b.

## Propiedad y siembra
Las secciones `INC-03` de `incidentes_service.py`, `domain/errores.py` y `pasillo/incidentes.py` no existían: el PR de gobernanza las siembra (`# === INC-03 ===` / `# === fin INC-03 ===`, solo comentarios). `api/routers/incidentes.py` es de INC-01 (hecha) y INC-02 no lo posee, por eso entra entero. Frente a INC-02 no hay archivos en común (cada una tiene su sección y su router), salvo `api/routers/incidentes.py`, que ORG-23 toca solo en su tupla `ROLES_CONSULTA`: por eso ORG-23 depende de INC-03 (INC-03 va primero); `app_core/pasillo/incidentes.py` es de ADPA-06 (hecha), de ahí la dependencia. **Las dos traen migración: no van en la misma tanda**, o una aplica FUSION_ALEMBIC sobre la otra.

## Pruebas (cada una con su mutación)
- **m1:** cerrar → cerrado; reabrir → abierto; `contar_abiertos` sigue los cambios. Mutación: calcular el estado con el primer evento en vez del último → rojo.
- **m2:** cerrar dos veces → 409. Mutación: quitar la comprobación de transición → rojo.
- **m3:** dos cierres concurrentes → uno pasa y el otro 409 por la `UNIQUE`. Mutación: quitar la `UNIQUE` → rojo.
- **m4:** `UPDATE` o `DELETE` sobre `incidentes_eventos_estado` con `lopdp_app` → permiso denegado. Mutación: `GRANT UPDATE` → rojo.
- **m5:** el DPO cierra → 403. Mutación: sumar `dpo` a los roles → rojo.
- **m6:** la huella de un incidente cerrado es igual a la de antes de cerrarlo y la cadena sigue íntegra. Mutación: meter el estado en `contenido()` → rojo.
- **m7:** un evento con el incidente de otro tenant → rechazado por la FK compuesta y por RLS. Mutación: dejar la FK solo a `incidentes(id)` → rojo.
- **m8:** motivo vacío o de menos de 10 caracteres → 422. Mutación: quitar el CHECK → rojo.

## Límites
- Sin plazos (REG-01). El frontend (insignia abierto/cerrado, botones Cerrar y Reabrir con motivo en `IncidentPlaybook.tsx`, sin tocar `frontend/src/components/incidentes/**` de INC-02) es una ficha aparte, `INC-03f`, que pasa por UX/UI; backend primero. Pruebas contra PostgreSQL 16 local; nunca producción.
- El paso de ORG-24 de «registradas» a «abiertas» es `ORG-24b`, no esta ficha.
