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

## Pruebas
1. Dos llamadas dejan una sola fila y ninguna invitación.
2. Con `APP_ENV` de producción, la compuerta lanza el error antes de cualquier consulta a la base.
3. La prueba de EP-03 «solo tenants y users» pasa a «ninguna tabla».

**Mutación:** emitir la invitación hace fallar la prueba 1.

**Validada por el Arquitecto ADPA (2026-11-08).** La lógica va en el engine; la compuerta solo la expone, con el cambio mínimo en `plataforma_service.py`.

**Antes del reparto:** pasa por Seguridad, porque es un alta sin invitación. Posee `plataforma_service.py` entero y solo agrega la función nueva; va después de ORG-20, que también lo toca.

## No hagas
- No te conectes a producción ni a Cloud SQL.
