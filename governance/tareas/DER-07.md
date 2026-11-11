+++
id = "DER-07"
titulo = "Textos legales de la interfaz de derechos ARCO: plazo legal estimado y sin Art. 37, laborables, SLA ni 72h"
ola = "backlog"
estado = "en_curso"
sala = "frontend"
depende_de = ["BIB-118", "DER-05", "FE-28"]
propiedad = ["frontend/src/types/arco.ts", "frontend/src/components/modules/ArcoModule.tsx", "frontend/src/components/CommandPalette.tsx", "frontend/tests/derechos/arco-plazo-aviso.spec.ts", "tests/test_der07_textos_legales.py"]
crea = ["frontend/tests/derechos/arco-plazo-aviso.spec.ts", "tests/test_der07_textos_legales.py"]
arbitro = "python scripts/verificar_citas_legales.py + pytest tests/test_der07_textos_legales.py + npx playwright test frontend/tests/derechos/arco-plazo-aviso.spec.ts + tsc --noEmit + build; mutaciones documentadas"
rastros = ["¤regulation-code", "¤frontend-ide", "¤arbitro"]
+++

# DER-07 · Textos legales de la interfaz de derechos ARCO: plazo legal estimado y sin Art. 37, laborables, SLA ni 72h

Diseño del Arquitecto ADPA (2026-11-09) y redacción de UX/UI (2026-11-09). **Pasa por UX/UI antes de repartir.** Plazos por tipo de solicitud: 15 días (arts. 13 a 16: acceso, rectificación, eliminación, oposición) y 10 días (art. 62: portabilidad, suspensión, decisiones automatizadas y quejas), validado por un abogado local, comunicado por el propietario el 2026-11-09; el documento del abogado no consta en el repositorio. Fuente: PR #557 y #558 de Aleczandra. La unidad (hábiles o corridos) sigue pendiente y la regla provisional son días corridos, marcada como estimada. La interfaz solo muestra lo que llega en `plazo_dias`, `plazo_unidad` y `plazo_estimado`, que fija DER-05 en el backend.

## Propiedad de los archivos
`CommandPalette.tsx` lo comparte con BIB-118, que abre la sección `#BIB-118`; DER-07 va después de BIB-118 y no la toca. `ArcoModule.tsx` y `CommandPalette.tsx` tuvieron a FE-28 como dueña (hecha).

## Medido
`arco.ts:23` y `:32` dicen «Art. 37 LOPDP… 15 días laborables» (artículo y unidad equivocados; el art. 37 es de seguridad). `CommandPalette.tsx:499` «SLA 72h» y `:525` «SLA 15 días laborables».

## Textos (UX/UI)
- **Plazo legal estimado:** «Plazo legal estimado: {plazo_dias} días {unidad}», con la unidad de `plazo_unidad` («hábiles», «naturales» o «por confirmar»). Con «por confirmar» se muestra «{plazo_dias} días» sin unidad.
- **Aviso provisional** (`role="note"`, `data-testid` `aviso-plazo-provisional`, `text-xs` con `--ui-texto-suave`, o icono (i) con `aria-label` «Cómo se calcula el plazo»): «Criterio provisional: la ley fija el plazo en días, pero la forma de contarlos (hábiles o naturales) está pendiente de confirmación legal. Mientras tanto contamos días corridos, que es la lectura más estricta.» Desaparece cuando `plazo_unidad` deja de ser «por confirmar».
- `ArcoModule.tsx:79`: «Gestión de las solicitudes de los titulares. Cada solicitud muestra su plazo legal estimado y los días que quedan.» `:114` «SLA Normativo» pasa a «Plazo legal estimado», y debajo del contador «{plazo_dias} días {unidad} · vence el {fecha}» (es-EC, dd/mm/aaaa). `:118` «Gestionar Expediente» se queda.
- `types/arco.ts:23` y `:32` (comentarios): «LOPDP, arts. 13 a 16 (15 días) y art. 62 (10 días); unidad pendiente».
- `CommandPalette.tsx:525`: «Solicitudes de los titulares: acceso, rectificación, eliminación, oposición y más · con plazo legal estimado» (sin cifra; «Cancelación» pasa a «eliminación», que es el término de la ley, arts. 14 a 16).
- **Ayuda contextual:** «LOPDP, arts. 13 a 16: acceso, rectificación y actualización, eliminación y oposición se atienden en 15 días. Art. 62: portabilidad, suspensión del tratamiento, decisiones automatizadas y quejas, 10 días.» **Advertencia:** `CITAS_LEGALES_VERIFICADAS.md` solo respalda, del art. 62, el término de 10 días para contestar el requerimiento directo del titular; la asignación a portabilidad, suspensión y decisiones automatizadas viene del trabajo de Aleczandra y de la validación del abogado local comunicada por el propietario (2026-11-09), sin documento en el repositorio.
- **Incidentes:** `CommandPalette.tsx:499` pasa a «Ir al Playbook de Incidentes» y se quita la palabra clave «72h» (l. 489). Sin cifra en la paleta: CITAS tiene como `verificado` el término de 5 días a la Autoridad y los de 2 y 3 días de los arts. 43 y 46, pero su unidad no está verificada.

## Accesibilidad y pruebas
- «Vencido por N días» ya lleva texto; se añade el icono `ShieldAlert` con `aria-hidden`.
- Con `plazo_unidad` = «por confirmar» aparece el aviso; con «hábiles» o «naturales» desaparece.
- Ningún texto visible del módulo contiene «Art. 37», «laborables», «SLA» ni «72h» (se busca `\bSLA\b` y `72 ?h`). Mutación: reponer cada uno.
- `scripts/verificar_citas_legales.py` sobre esos tres archivos, sin filas `no verificado`.
- Sin tokens de gobernanza ni nombres internos en pantalla; las citas salen de las filas `verificado`.
