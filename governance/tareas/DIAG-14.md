+++
id = "DIAG-14"
titulo = "Diagnóstico: con un rol que no es DPO, los controles de nivel y de evidencia se muestran deshabilitados y explican por qué"
ola = "C"
estado = "en_curso"
sala = "diagnostico, frontend"
depende_de = ["ADPA-11", "DIAG-03", "DIAG-09", "FE-16"]
propiedad = ["frontend/src/components/DiagnosticCanvas.tsx#DIAG-14", "frontend/src/components/diagnostico/NotaSoloDpo.tsx", "frontend/tests/diagnostico/solo-dpo.spec.ts"]
crea = ["frontend/src/components/diagnostico/NotaSoloDpo.tsx", "frontend/tests/diagnostico/solo-dpo.spec.ts"]
arbitro = "npx playwright test tests/diagnostico/solo-dpo.spec.ts + tsc --noEmit + npm run build; mutación documentada"
rastros = ["¤frontend-ide", "¤rbac-tenant"]
+++

# DIAG-14 · Solo el DPO asigna el nivel

**Origen.** Brief de UX/UI aprobado por el CTO y revisado por el Arquitecto (2026-11-08). **Validada por el Arquitecto ADPA (2026-11-08).**

## Entrega
- Con un rol que no es DPO, los botones de nivel y de evidencia se ven deshabilitados (`aria-disabled`, sin hover).
- Junto a cada control aparece «Solo el DPO puede asignar el nivel. Estás viendo como <rol>.» (`NotaSoloDpo.tsx`).
- En la demo se añade un enlace a la persona DPO. `lib/demo` solo se lee.
- Escribe solo dentro de la sección `#DIAG-14`, que siembra ADPA-11.

## Pruebas (`frontend/tests/diagnostico/solo-dpo.spec.ts`)
1. Con un rol que no es DPO: los botones de nivel y de evidencia tienen `aria-disabled`, la nota aparece junto a cada control y nombra el rol, y un clic no cambia el estado derivado.
2. Con el DPO: los controles siguen funcionando y la nota no aparece.
3. En la demo, el enlace lleva a la persona DPO.

**Mutación:** quitar `aria-disabled` hace fallar la prueba 1. Las capturas van como evidencia en el PR, no como árbitro.
