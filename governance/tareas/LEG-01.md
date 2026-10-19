+++
id = "LEG-01"
titulo = "Citas normativas de la interfaz coherentes con la LOPDP"
ola = "D"
estado = "hecha"
sala = "frontend"
depende_de = []
propiedad = ["frontend/src/components/modules/DpoCockpitModule.tsx", "frontend/src/components/modules/MtgeRelacionalModule.tsx", "frontend/tests/legal/**"]
arbitro = "npx playwright test tests/legal + tsc --noEmit y next build"
rastros = ["¤frontend-ide", "¤arbitro"]
+++

# LEG-01 · Citas normativas de la interfaz coherentes con la LOPDP

**Objetivo.** Dos textos de la interfaz atribuyen al Art. 48 de la LOPDP lo que dicen los Art. 49 y 50. El Art. 48 solo enumera los casos en que hay que designar delegado de protección de datos; las funciones del delegado (supervisar el cumplimiento, asesorar, ser punto de contacto con la Autoridad) están en el Art. 49 y las garantías de su independencia en el Art. 50. Las citas del Art. 48 para la **obligatoriedad de designar** delegado (MTGE, copiloto, banco de preguntas) son correctas y no se tocan.

## Entrega
- `DpoCockpitModule.tsx`: la «supervisión independiente» cita los Art. 49 y 50, no el 48.
- `MtgeRelacionalModule.tsx`: la separación de funciones del DPO cita el Art. 50 (conflicto de intereses), no el 48.
- Una prueba que fija esas citas, y otra que comprueba que las citas del Art. 48 que hablan de designación obligatoria siguen intactas.

## Límites
- **El plazo de notificación de vulneraciones queda fuera por ahora**, por decisión del propietario hasta cerrar la gobernanza. No se toca, pero conviene recordar que hoy la interfaz muestra «72h» y el texto oficial de la ley (Art. 43) habla de un término de cinco días: está anotado para cuando se traten los plazos.
- No toca el backend: la cita de `app_core/security.py` es de SEC-03 (ya integrada) y la de `domain/roles.py` es de ORG-01.

## Hecho cuando
- Su árbitro pasa, la suite completa pasa y el check `Arnés Físico Determinista` del PR está en verde. No modificó ningún archivo fuera de su propiedad y dejó `estado = "hecha"` en esta especificación.
