+++
id = "RM-25c"
titulo = "Panel de evidencia: «Primera validación» del Coordinador y «Validación final» del DPO, con el rol en el historial"
ola = "backlog"
estado = "pendiente"
sala = "roadmap, frontend"
depende_de = ["RM-25a", "FE-01", "FE-04", "FE-07", "FE-15", "FE-18", "ORG-00", "ORG-08", "ORG-12", "RM-20"]
propiedad = ["frontend/src/components/modules/roadmap/evidencia/EvidenciaPanel.tsx", "frontend/src/lib/roadmap/cliente.ts", "frontend/src/lib/roadmap/cliente.mock.test.ts", "frontend/src/app/harness-roadmap/evidencia/HarnessEvidencia.tsx", "frontend/tests/roadmap/doble-validacion.spec.ts"]
crea = ["frontend/tests/roadmap/doble-validacion.spec.ts"]
arbitro = "Playwright frontend/tests/roadmap/doble-validacion.spec.ts (el coordinador ve «Primera validación»; el DPO ve «Validación final», activa solo si ya hay primera validación; el rol se muestra en el historial) + cliente.mock.test.ts + tsc --noEmit + npm run build; antes, git grep de los specs que buscan «Validar» y de HarnessEvidencia.tsx; mutación documentada: dejar activo el botón del DPO sin primera validación hace fallar el spec"
rastros = ["¤roadmap"]
+++

# RM-25c · Panel de evidencia: «Primera validación» del Coordinador y «Validación final» del DPO, con el rol en el historial

Diseño del Arquitecto ADPA, 2026-11-11 (doble validación de la evidencia: primera validación del Coordinador, validación final del DPO o Auditor; invariante 14 de EVY), medido leyendo origin/main; no se ejecutaron pruebas. DIAG-12 entra con «dpo o auditor, distinto de quien subió»; la primera validación llega después y endurece esa consulta sin cambiar la regla.

## Entrega
- El coordinador ve «Primera validación» y el DPO ve «Validación final», solo activo si ya hay primera validación; el rol se muestra en el historial. El botón del coordinador depende de RM-25a; el cambio del DPO entra con RM-25b o después.
- Antes de escribir: `git grep` de los specs que buscan «Validar» y de `HarnessEvidencia.tsx`; si una prueba ajena fija el texto y no es tuya, para y avisa al Tech Lead.
- Los textos nuevos pasan por UX/UI.

**Ajuste 2026-11-11 (decisiones del CTO, aplicadas por el Arquitecto):** el panel muestra «Pendiente de validación final» en las evidencias con `requiere_revalidacion`; el texto pasa por UX/UI.

## Textos cerrados por UX/UI (2026-11-13)
- Botón del coordinador: «Primera validación». Botón del DPO: «Validación final», con `aria-disabled` y la línea «Disponible cuando el coordinador haga la primera validación» mientras no la haya.
- Etiqueta «Pendiente de validación final», con `role="status"`.
- Historial: «{Nombre} · {Rol} · Primera validación» y «{Nombre} · {Rol} · Validación final», con fecha.
- Errores por código del catálogo, nunca el texto del servidor.
- Si la ficha cambia, UX/UI vuelve a confirmar por escrito.
