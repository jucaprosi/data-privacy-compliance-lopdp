+++
id = "LEG-05"
titulo = "Citas legales: transferencia internacional en el Reglamento General y tratamiento de datos en Vertex AI"
ola = "indep"
estado = "en_curso"
sala = "gobernanza"
depende_de = ["LEG-03", "LEG-04"]
propiedad = ["governance/apoyo/CITAS_LEGALES_VERIFICADAS.md#LEG-05"]
arbitro = "python scripts/verificar_citas_legales.py + pytest tests/test_leg03_citas_legales.py + python scripts/generar_indice_tareas.py --verificar; mutación sobre las filas nuevas"
rastros = ["¤regulation-code"]
+++

# LEG-05 · Transferencia internacional y uso de Vertex AI

Propuesta del Arquitecto ADPA y del CTO (2026-11-09). Sin dependencias abiertas. **No bloquea a IA-03:** esa ficha solo necesita la nota con el pendiente en `FUENTES_Y_BIBLIOGRAFIA.md`.

## Entrega
- Lectura del texto oficial de los artículos del Reglamento General (Decreto 904) sobre transferencia internacional, y su cita en `CITAS_LEGALES_VERIFICADAS.md`. Hoy figura «texto no leído en LEG-03» y `no verificado`.
- Lectura de la fuente oficial de Google sobre el tratamiento de datos en Vertex AI, con su URL.
- Cada fila queda `verificado` o `no verificado`, sin afirmar una base legal. La aprobación del contenido y el dictamen son del propietario.

## Propiedad
`governance/apoyo/CITAS_LEGALES_VERIFICADAS.md#LEG-05`: la sección, con su marca, la siembra este PR de gobernanza. Antes de repartir, comprobar con el verificador del reparto que ninguna ficha viva sea dueña del archivo entero.

## Árbitro
El de LEG-03, extendido a las filas nuevas: artículo literal, fuente con URL oficial y estado. Mutación: una fila con estado `verificado` sin URL oficial deja la prueba en rojo.
