+++
id = "DIAG-16"
titulo = "Citas normativas del banco de preguntas contrastadas con el texto oficial (corrige P73)"
ola = "backlog"
estado = "en_curso"
sala = "diagnostico, frontend"
depende_de = ["DIAG-02", "RM-19"]
propiedad = ["features/diagnostico/domain/banco_preguntas.json", "frontend/src/lib/bancoPreguntas/bloque1.ts", "frontend/src/lib/bancoPreguntas/bloque2.ts", "frontend/src/lib/bancoPreguntas/bloque3.ts", "tests/test_banco_preguntas.py", "tests/test_diag16_referencias_normativas.py", "governance/apoyo/CONTRASTE_REFERENCIAS_BANCO.md", "governance/artefactos/CITAS_LEGALES_VERIFICADAS.md"]
crea = ["tests/test_diag16_referencias_normativas.py", "governance/apoyo/CONTRASTE_REFERENCIAS_BANCO.md", "governance/artefactos/CITAS_LEGALES_VERIFICADAS.md"]
arbitro = "pytest tests/test_diag16_referencias_normativas.py tests/test_banco_preguntas.py (test_referencias_backend_igual_frontend, test_sin_art47_num3_capacitacion, test_contraste_cubre_todas) + tsc --noEmit; mutación: volver a poner Art. 47 numeral 3 (Capacitación)"
rastros = ["¤diagnostico"]
+++

# DIAG-16 · Citas normativas del banco de preguntas contrastadas con el texto oficial (corrige P73)

Hallazgo del Arquitecto ADPA (2026-11-13) al contrastar P73 con el texto oficial de la LOPDP (5.º Suplemento del R.O. 459, 26-V-2021), por pedido del CTO.

## Hallazgo
`features/diagnostico/domain/banco_preguntas.json` cita para P73 «LOPDP Art. 47 numeral 3 (Capacitación)», y la cadena aparece 3 veces. El art. 47 tiene 15 numerales y ninguno trata de la capacitación del personal: el num. 3 es la verificación y la valoración periódica de la eficacia de las medidas; el num. 2, las herramientas administrativas, técnicas, físicas, organizativas y jurídicas; el num. 10, los contratos de confidencialidad con el personal. En la ley, la capacitación aparece en el art. 50 num. 3 (capacitar al delegado), en los arts. 23 y 24 (educación digital) y en el art. 77.

## Entrega
- Corregir las 3 referencias de P73 a la base que valide el abogado. Propuesta, ESTIMADA: art. 47 num. 2 como medida organizativa, más el art. 10 (responsabilidad proactiva) y, si se verifica en el texto oficial, el art. 36 del Reglamento.
- Hacer el mismo contraste en **todo** el banco: cada cita normativa, contra el texto oficial del corpus, con su fuente y fecha. Las que no casen se corrigen o quedan marcadas para el abogado.
- Ninguna cita de memoria. Las citas verificadas quedan en `governance/artefactos/CITAS_LEGALES_VERIFICADAS.md`.
- La pregunta al abogado, por escrito, en el parte del día.

## Prueba
Una prueba que recorre el banco y falla si una cita normativa no está en `CITAS_LEGALES_VERIFICADAS.md`. Mutación: volver a poner «Art. 47 numeral 3 (Capacitación)» → falla.

La propiedad concreta la mide el Arquitecto. Dueños del banco: DIAG-02 y RM-19, las dos hechas.

**Nota del Arquitecto.** El corpus del proyecto no tiene el texto literal: `features/regulacion_rag/domain/corpus.py` guarda el art. 47 resumido en una línea, sin numerales. El texto del num. 3 se leyó en la LOPDP oficial (5.º Supl. R.O. 459). Si el contraste de todo el banco necesita el texto literal dentro del proyecto, depende de NORM-01 (corpus normativo con el original custodiado) o de cargarlo a mano en `CITAS_LEGALES_VERIFICADAS.md`, con su fuente.

## Condiciones del CTO (2026-11-13; prioridad alta)
- La base propuesta (art. 47 num. 2 + art. 10) entra marcada como ESTIMADA en el dato y no se muestra al cliente como cita firme hasta que el abogado la confirme. Mientras tanto, P73 muestra en la interfaz una referencia sin numeral equivocado, o ninguna, antes que una falsa.
- El contraste cubre **todas** las citas del banco contra el texto oficial (LOPDP, R.O. 459, 5.º Supl., y el Reglamento si se cita). Cada una queda en `CITAS_LEGALES_VERIFICADAS.md` con artículo, numeral, texto literal breve, fuente y fecha de lectura.
- La prueba falla si una cita del banco no está en ese archivo.
- La pregunta al abogado va por escrito en esta ficha, con la lista de citas dudosas. La decisión legal es del propietario y su abogado.
- Se lista dónde se repiten las mismas citas fuera del banco (plantillas del RAT, textos de la interfaz, PRD). Esas se corrigen en fichas de sus dueños.

## Regla de carga a mano (CTO, 2026-11-13)
- El texto literal de cada cita sale de la fuente oficial (Registro Oficial o publicación de la SPDP). En `CITAS_LEGALES_VERIFICADAS.md` va la URL o el archivo exacto y la página.
- Si la sesión no puede leer la fuente, la cita queda «pendiente de verificar» y no se escribe de memoria.
- Cuando NORM-01 tenga corpus custodiado, el archivo pasará a apuntar al objeto del corpus (sha256) en una ficha posterior.


## Ortogonalidad ADPA y Desacoplamiento Entre Salas (Doctrina ZERAG)

- **Prohibición de imports laterales directos (`ImportsCruzados = ∅`)**: Esta tarea **nunca** debe importar `features.<otra_sala>.*` directamente. Toda consulta o invocación hacia otra sala se realiza exclusivamente a través del pasillo tipado `app_core/pasillo/<otra_sala>.py#DIAG-16` (ADR 0001).
