+++
id = "LEG-08b"
titulo = "Lectura oficial de las citas de las plantillas que LEG-08 no leyó, en el mismo artefacto"
ola = "backlog"
estado = "hecha"
tanda = 101
sala = "gobernanza"
depende_de = ["LEG-08"]
propiedad = ["governance/artefactos/CITAS_PLANTILLAS_VERIFICADAS.md"]
crea = []
arbitro = "Revisión del CTO: cada fila nueva con fuente oficial, página, texto literal breve y huella SHA-256 del PDF leído; ninguna completada de memoria. Después, BIB-403 corre scripts/verificar_citas_plantillas.py."
rastros = ["¤regulation-code", "¤arbitro", "¤cita-verificada"]
+++

# LEG-08b · Citas de las plantillas que LEG-08 no leyó

**Contrato:** `governance/especificaciones/LEG-08b.md` (manda sobre esta ficha).

**Origen.** Pedido del CTO (2026-11-24). El árbitro de BIB-403 (`verificar_citas_plantillas.py`) encontró citas de las plantillas sin fila o con lectura `no_leida` en `CITAS_PLANTILLAS_VERIFICADAS.md`, y BIB-403 se bloquea por su R1.

## Entrega
- Filas nuevas, o filas `no_leida` actualizadas, en `CITAS_PLANTILLAS_VERIFICADAS.md` para las claves de la especificación §1, con el método y el formato de LEG-08.
- La lectura la hace el CTO; la ficha la deja en el artefacto.

## Límites
- Solo el artefacto. Las plantillas, `citas.json` y las secciones sin cita las cambia BIB-403, que también quita lo que quede sin verificar.
- Lo que no se lee queda `no_leida`, y lo que no está en la fuente, `no_encontrada`.
