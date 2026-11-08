+++
id = "PLAT-01"
titulo = "Alta idempotente de organizaciones sintéticas en plataforma_service, sin invitación"
ola = "indep"
estado = "pendiente"
sala = "plataforma"
depende_de = ["EP-03", "ORG-11", "ORG-20"]
propiedad = ["features/plataforma/plataforma_service.py", "features/plataforma/services/organizacion_sintetica_engine.py", "scripts/datos_sinteticos/organizaciones.py", "tests/test_plat01_organizacion_sintetica.py", "tests/test_ep03_sembrar_entorno.py"]
crea = ["features/plataforma/services/organizacion_sintetica_engine.py", "tests/test_plat01_organizacion_sintetica.py"]
arbitro = "pytest tests/test_plat01_organizacion_sintetica.py tests/test_ep03_sembrar_entorno.py + suite completa; mutación documentada; revisión de Seguridad antes del reparto"
rastros = ["¤seguridad-tenant", "¤adpa"]
+++

# PLAT-01 · Alta idempotente de organizaciones sintéticas

**Origen.** Validación del Arquitecto a EP-03 (2026-11-08). La siembra escribe directo en `tenants` y `users` porque el alta de `plataforma_service` responde 409 y emite una invitación. Esta ficha crea la compuerta que retira esa excepción.

## Entrega
- `asegurar_organizacion_sintetica(datos)` en `plataforma_service.py`, con la lógica en `services/organizacion_sintetica_engine.py`:
  - es idempotente: crea la organización o devuelve la existente;
  - no emite invitación ni correo;
  - solo se permite con `APP_ENV` en `pruebas` o `demo`; en cualquier otro entorno lanza un error.
- `scripts/datos_sinteticos/organizaciones.py` usa la compuerta y deja de escribir en `tenants` y `users`.
- Se retira la excepción de tablas y su anotación en la ficha EP-03.

## Revisión de Seguridad (2026-11-08)
1. **Una sola lectura del entorno.** La compuerta usa `entorno_actual()` y `validar_arranque()` de `app_core/entorno/guardias.py`, nunca `os.environ`. Lista cerrada `{pruebas, demo}`: `development`, `test`, `production`, vacío o desconocido dan error. También falla si el servicio corre en el proyecto de producción o si `DATABASE_URL` tiene su huella.
2. **No apropiarse de una organización real.** La organización lleva una marca sintética (por ejemplo, RUC reservado 9999…). Si existe una fila con esa clave sin la marca, error y no se toca.
3. **Usuarios sin invitación:** solo correos de dominio reservado (`.invalid` o `example.org`, RFC 2606), sin credenciales, nunca con rol de plataforma ni de superadministrador; los roles salen de una lista cerrada de la organización.
4. **Sin superficie HTTP:** ningún router de `api/` importa `asegurar_organizacion_sintetica`. Si DEMO-02 la llama, lo hace desde su orquestador con su propia autorización, declarado en DEMO-02.
5. **Carrera:** idempotente también con dos llamadas concurrentes, con restricción única, `ON CONFLICT DO NOTHING` y relectura, nunca SELECT seguido de INSERT. Conecta con `lopdp_app` (sin BYPASSRLS), con la RLS fijada al tenant creado.
6. **Auditoría:** el alta se registra con origen «sintética» y el entorno, sin datos personales.

## Pruebas
1. Dos llamadas dejan una sola fila y ninguna invitación.
2. Con una sesión que falla en cualquier `execute()`, el error de entorno sale antes de la primera consulta:
   - 2a: por cada valor de `APP_ENV` fuera de `{pruebas, demo}`;
   - 2b: `APP_ENV=demo` con la huella de producción en `DATABASE_URL`.
3. La prueba de EP-03 «solo tenants y users» pasa a «ninguna tabla».
4. Una organización con la misma clave y sin la marca sintética da error y queda intacta.
5. Un correo de dominio real o un rol de plataforma dan error.
6. Ningún archivo de `api/` importa la compuerta (AST o grep).
7. Dos llamadas concurrentes (`asyncio.gather`) dejan una sola fila.
8. El alta queda en la auditoría con origen «sintética», sin datos personales.

**Mutaciones:**
- M1: emitir la invitación hace fallar la prueba 1.
- M2: quitar la comprobación de la marca hace fallar la prueba 4.

**Validada por el Arquitecto ADPA (2026-11-08)** y **revisada por Seguridad (2026-11-08)**: apta para el reparto con los puntos 1 a 6. La lógica va en el engine; la compuerta solo la expone, con el cambio mínimo en `plataforma_service.py`.

## No hagas
- No te conectes a producción ni a Cloud SQL.
