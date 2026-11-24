+++
id = "LEG-08"
titulo = "Lectura oficial de las citas de las 12 plantillas de la Biblioteca, con la huella del documento leído"
ola = "backlog"
estado = "hecha"
tanda = 101
sala = "gobernanza"
depende_de = ["DIAG-16", "LEG-03"]
propiedad = ["governance/artefactos/CITAS_PLANTILLAS_VERIFICADAS.md"]
crea = ["governance/artefactos/CITAS_PLANTILLAS_VERIFICADAS.md"]
arbitro = "Revisión del CTO: cada fila con fuente oficial, página, texto literal breve y huella SHA-256 del PDF leído; ninguna fila completada de memoria."
rastros = ["¤regulation-code", "¤arbitro"]
+++

# LEG-08 · Lectura oficial de las citas de las 12 plantillas

**Contrato:** `governance/especificaciones/LEG-08.md` (manda sobre esta ficha).

**Origen.** Decisión del propietario (2026-11-24): las plantillas se validan contra la normativa vigente, no por una persona. Brief del CTO `ARQUITECTO_BIBLIOTECA_PUBLICACION_Y_DEMO.v2.md`, medido en `origin/main` a80da616.

## Entrega
- Un artefacto nuevo, `governance/artefactos/CITAS_PLANTILLAS_VERIFICADAS.md`, con una fila por cita atómica de las 12 plantillas, leída en la fuente oficial, y la huella SHA-256 del documento leído.
- Para cada marca «PENDIENTE VALIDACIÓN» de las plantillas, la resolución con la fuente oficial o la constancia de que no la tiene.

## Límites
- Solo el artefacto nuevo. Las plantillas las cambia BIB-403.
- Lo que no se lee queda como no leído y no se marca verificado.
