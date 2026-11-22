+++
id = "NORM-03b"
titulo = "Pestaña «Impacto» en el panel de una resolución de NORM-02"
ola = "backlog"
estado = "pendiente"
sala = "frontend"
depende_de = ["NORM-02", "NORM-03"]
propiedad = ["frontend/src/components/normativa/PanelResolucion.tsx", "frontend/src/components/normativa/CentroVigilancia.tsx", "frontend/tests/normativa_impacto/impacto.spec.ts"]
crea = []
arbitro = "Playwright frontend/tests/normativa_impacto/impacto.spec.ts + tsc --noEmit + npm run build; mutación m1."
rastros = ["¤frontend-ide"]
agente = "ninguno"
+++

# NORM-03b · Pestaña «Impacto» en el panel de una resolución de NORM-02

**Contrato:** `governance/especificaciones/NORM-03b.md` (manda sobre esta ficha).

**Origen.** Pedido del CTO (2026-11-21). Medido: los componentes de NORM-03 (`PestanaImpacto.tsx`) no se usan fuera de su carpeta, y el router de impacto ya está montado por `AUTO_REGISTRO`. UX/UI cerró la interfaz el 2026-11-21.

## Entrega
- La pestaña «Impacto» en `PanelResolucion.tsx`, con los roles leídos de `/organizacion/me/roles`.
