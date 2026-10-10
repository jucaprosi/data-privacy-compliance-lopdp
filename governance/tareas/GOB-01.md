+++
id = "GOB-01"
titulo = "Promover los rastros nuevos al VPA"
ola = "indep"
estado = "pendiente"
sala = "gobernanza"
depende_de = []
propiedad = ["governance/artefactos/data/CANDIDATOS_VPA.json"]
arbitro = "los rastros aparecen en el VPA servido por el MCP"
rastros = ["¤vpa"]
+++

# GOB-01 · Promover los rastros nuevos al VPA

**Objetivo.** Indexar `¤roadmap` y `¤rbac-tenant` con `mcp_promote_vpa_candidate`; el `VPA_MAP` lo sirve el MCP y no se edita a mano.

## Entrega
- Promover los dos rastros desde los candidatos.

## Hecho cuando
- Su árbitro pasa, la suite completa pasa y el check `Arnés Físico Determinista` del PR está en verde. No modificó ningún archivo fuera de su propiedad y dejó `estado = "hecha"` en esta especificación.
