+++
id = "SEC-12"
titulo = "Diseño de seguridad de los portales externos (titulares y encargados) antes de implementarlos"
ola = "D"
estado = "pendiente"
sala = "gobernanza"
depende_de = []
propiedad = ["governance/apoyo/DISENO_PORTALES_EXTERNOS.md"]
arbitro = "Revisión del propietario sobre el documento; python scripts/generar_indice_tareas.py --verificar con código 0"
rastros = ["¤seguridad", "¤portales-externos"]
+++

# SEC-12 · Diseño de seguridad de los portales externos (titulares y encargados) antes de implementarlos

**Origen.** Conflicto D-7 de `governance/apoyo/ESTRUCTURA_FUNCIONAL_EVYDENTIA.md`: portal público de solicitudes de titulares y portal de encargados son una superficie pública nueva sin diseño de seguridad.

## Entrega
- `governance/apoyo/DISENO_PORTALES_EXTERNOS.md`: amenazas, verificación proporcional de identidad del titular, enlaces que caducan y de un solo uso, ninguna exposición de datos de otros titulares, límites de abuso y CAPTCHA o alternativa accesible, registro de auditoría, aislamiento por organización (RLS, sin `BYPASSRLS`), datos mínimos (Doctrina 8), DLP en toda subida (Doctrina 7).
- Para cada control: base legal o norma técnica con fuente verificada, o «(*) por verificar» si no la hay (LEG-03).
- Lista de las tareas de implementación que abriría, sin fichas todavía.

## Límites
- Solo diseño: ni código, ni rutas públicas, ni fichas de implementación.
