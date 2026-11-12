+++
id = "PMV-01"
titulo = "El PRD del PMV declara Neon como su base de datos y separa lo que es de EVYDENTIA (Google Cloud)"
ola = "indep"
estado = "hecha"
sala = "gobernanza"
depende_de = []
propiedad = ["governance/tareas/PMV-01.md"]
arbitro = "scripts/verificar_bom_huellas.py y scripts/verificar_especificaciones.py sin hallazgos; lectura del diff del PRD (sección 7, Módulo 8 y sección 9)"
rastros = ["¤arbitro"]
+++

# PMV-01 · El PRD del PMV declara Neon como su base de datos y separa lo que es de EVYDENTIA

**Decisión de la propietaria (2026-11-12).** El PMV es el espacio de control de calidad de la aplicación: usa PostgreSQL 16 en Neon, con una rama de pruebas por persona (`test-<persona>`). Google Cloud (Cloud Run, Cloud SQL, Cloud Storage, Vertex AI) pertenece a EVYDENTIA. Lo que se prueba en el PMV se implementa después en EVYDENTIA.

## Entrega
- Sección 7 del PRD: apartado «Base de datos del PMV» con esa decisión.
- Módulo 8: la nota de aislamiento aclara que el módulo es de EVYDENTIA y que el PMV sigue sobre Neon.
- Sección 9: nota de alcance antes del criterio 19; los criterios 19 a 25 son de EVYDENTIA.

## Límites
- No mueve ni borra texto de EVYDENTIA; no toca `PRD_EVYDENTIA_REVENTA_NUBE.md`.
- Pendiente de decisión (sin tarea abierta): marcar como de EVYDENTIA las invariantes de nube de `INVARIANTS.md` y los rastros de nube del PRD.
