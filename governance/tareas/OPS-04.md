+++
id = "OPS-04"
titulo = "Rama de Neon por agente"
ola = "indep"
estado = "pendiente"
sala = "operaciones"
depende_de = []
propiedad = ["governance/operaciones/RAMAS_NEON_POR_AGENTE.md"]
arbitro = "un agente conecta a su rama test-<agente> y comprueba que el rol lopdp_app existe"
rastros = ["¤seguridad", "¤ci-cd"]
+++

# OPS-04 · Rama de Neon por agente

**Objetivo.** Decisión D-8: cada agente prueba y migra en su propia rama hija de Neon, nunca en la rama `test` compartida.

## Entrega
- Procedimiento por escrito: crear la rama hija desde `test` con el nombre `test-<agente>` (consola de Neon, sección Branches), copiar sus cadenas de conexión a las variables `TEST_DATABASE_URL` y `TEST_MIGRATION_DATABASE_URL` del `.env` local del agente (nunca al repositorio), aplicar las migraciones, comprobar que `lopdp_app` existe y borrar la rama al terminar.
- Límites del plan gratuito (documentación de Neon): 10 ramas por proyecto, 2 en uso hoy, y 100 horas de cómputo al mes en total.

## Límites
- Las cadenas de conexión son secretos: las crea y las entrega el usuario.

## Hecho cuando
- Su árbitro pasa, la suite completa pasa y el check `Arnés Físico Determinista` del PR está en verde. No modificó ningún archivo fuera de su propiedad y dejó `estado = "hecha"` en esta especificación.
