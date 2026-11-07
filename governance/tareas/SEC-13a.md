+++
id = "SEC-13a"
titulo = "Tope total de generaciones de IA por organización, configurable por tenant"
ola = "D"
estado = "pendiente"
sala = "pasillo_central"
depende_de = ["SEC-13"]
propiedad = ["app_core/limites/tope_organizacion.py", "api/middleware/limite_peticiones.py#SEC-13a", "app_core/errors.py#SEC-13a", "alembic/versions/20261120_ia_tope_organizacion.py", "tests/test_sec13a_tope_ia_organizacion.py"]
arbitro = "pytest tests/test_sec13a_tope_ia_organizacion.py + tests/test_sec13_limite_peticiones.py + tests/test_alembic_una_cabeza.py + tests/test_rls_todas_las_tablas.py en verde"
rastros = ["¤seguridad", "¤seguridad-tenant", "¤copiloto-ia"]
+++

# SEC-13a · Tope total de generaciones de IA por organización

**Proyecto:** EVYDENTIA (Google Cloud). **Sala dueña:** `pasillo_central`. Hija de `SEC-13`. Tanda 52.

**Por qué.** Decisión del CTO del 2026-11-07. El propietario fijó un techo de 5 generaciones de IA por organización demo (PRD §5.6.7), y un tope total por organización también hace falta en la reventa, para controlar el costo por tenant. Va en el limitador común y no en la sala demo: si la demo interceptara las llamadas de IA de otras salas, sería un cruce prohibido por ADPA.

## Entrega
- Migración `20261120_ia_tope_organizacion.py`: tabla `ia_tope_organizacion` (`tenant_id` como clave primaria, `tope` entero **nulable**, `usadas` entero no nulo, por defecto 0), con RLS forzada por `tenant_id`. `lopdp_app` con SELECT, INSERT y UPDATE, sin DELETE. Nulo, o sin fila, significa sin tope. Se encadena tras la cabeza vigente de Alembic.
- `app_core/limites/tope_organizacion.py`: `consumir_generacion(session, tenant_id)` incrementa `usadas` de forma atómica (`UPDATE … WHERE usadas < tope RETURNING`) y lanza `IA_TOPE_ORGANIZACION` si ya se llegó al tope.
- La sección `SEC-13a` de `api/middleware/limite_peticiones.py` llama a `consumir_generacion` en el mismo punto donde se aplica la política de IA de las ventanas deslizantes, después de que esa política deje pasar.
- La sección `SEC-13a` de `app_core/errors.py` define `IA_TOPE_ORGANIZACION` (429) con cuerpo `{codigo, mensaje}` y el mensaje «Tu organización alcanzó su límite de generaciones con IA».

## Pruebas (`tests/test_sec13a_tope_ia_organizacion.py`)
- Con tope 5, la 5.ª generación pasa y la 6.ª responde 429 `IA_TOPE_ORGANIZACION`.
- Sin tope (nulo o sin fila), no se niega nada.
- El consumo de una organización no afecta a otra.
- Dos generaciones concurrentes con `usadas = tope − 1`: solo una pasa.
- Las ventanas deslizantes de SEC-13 siguen igual.

## Límites
- No cambies las firmas ni el comportamiento de SEC-13 fuera de tus secciones.
- No escribas el valor 5: lo siembra DEMO-03 en la plantilla de la demo.
- Nunca uses la base de producción: solo tu rama Neon de prueba.

## Fuentes
- `governance/artefactos/PRD_EVYDENTIA_REVENTA_NUBE.md` §5.6.7 (decisión del propietario: «techo de 5 por demo»).
- Decisión del CTO del 2026-11-07: se amplía SEC-13; no lo cuenta la demo.
- `governance/tareas/SEC-13.md`.
