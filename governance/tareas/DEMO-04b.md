+++
id = "DEMO-04b"
titulo = "Ver como: la línea del responsable de área ya no promete cargar evidencia antes del sello"
ola = "backlog"
estado = "en_curso"
sala = "demo"
depende_de = ["DEMO-04", "EVI-01"]
propiedad = ["frontend/src/lib/demo/contrato.ts", "governance/apoyo/UX_DEMO_EVYDENTIA.md", "frontend/tests/demo/demo.spec.ts"]
crea = []
arbitro = "Playwright frontend/tests/demo/demo.spec.ts: el selector «Ver como» con las seis personas muestra la línea nueva del responsable de área y la compara con la regla (sin diagnóstico real sellado no sube evidencia); el texto antiguo («sus tareas y carga la evidencia», sin la condición del sello) ya no aparece en frontend/ ni en governance/apoyo/UX_DEMO_EVYDENTIA.md; tsc --noEmit y npm run build; mutación documentada: volver a la línea antigua hace fallar la prueba"
rastros = ["¤demo"]
+++

# DEMO-04b · Ver como: la línea del responsable de área ya no promete cargar evidencia antes del sello

**Origen.** Propuesta de UX/UI (2026-11-11), aprobada por el CTO. Corrige una promesa falsa en el texto de la demo: EVI-01 (invariantes 58 y 59) no deja subir evidencia antes del sello del diagnóstico real, y la línea del responsable de área en «Ver como» decía que «carga la evidencia» sin condición.

**Motivo que se anota (aviso del CTO al propietario).** El texto que el propietario validó el 2026-11-07 cambia, pero no cambia una decisión de producto: solo se corrige lo que la pantalla permite hoy. El CTO informa al propietario.

## Entrega
- La línea de `responsable_area` en `LINEA_DE_ROL` (`frontend/src/lib/demo/contrato.ts`, línea 41) pasa a: «Responde los dominios de su unidad, ejecuta sus tareas y, con el diagnóstico real sellado, carga la evidencia.»
- La misma línea en la tabla de `governance/apoyo/UX_DEMO_EVYDENTIA.md` (línea 48).
- La prueba de Playwright del selector «Ver como» con las seis personas (`frontend/tests/demo/demo.spec.ts`) muestra la línea nueva del responsable de área y la compara con la regla: antes del sello del real, el responsable de área no sube evidencia (EVI-01); después, sí. Las demás líneas de rol no cambian.
- No toca backend.

## Pruebas
- La línea nueva aparece en el selector; el texto antiguo ya no aparece en `frontend/` ni en la tabla de la especificación (la ficha DEMO-04 menciona el texto antiguo como historia y se actualiza en el PR de gobernanza que crea esta ficha).
- Mutación: volver a la línea antigua en `contrato.ts` hace fallar la prueba.
