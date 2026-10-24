+++
id = "MTGE-01"
titulo = "Cálculo de gran escala conforme al texto vinculante de la Res. SPDP-SPD-2026-0005-R"
ola = "D"
estado = "pendiente"
sala = "riesgos_mtge, frontend"
depende_de = ["FE-06", "FE-07", "LEG-01", "SEC-02", "SEC-08", "RAT-01"]
propiedad = ["features/riesgos_mtge/services/mtge_calculator.py", "features/riesgos_mtge/domain/models.py", "api/routers/riesgos_mtge.py", "tests/test_mtge_engine.py", "tests/test_mtge_resolucion_0005.py", "tests/test_api_gateway.py", "frontend/src/lib/api.ts", "frontend/src/types/index.ts", "frontend/src/app/actions/mtgeActions.ts", "frontend/src/components/modules/MtgeRelacionalModule.tsx", "frontend/src/components/modules/MtgeModule.tsx", "frontend/tests/legal/citas.spec.ts", "frontend/tests/mtge/**"]
arbitro = "pytest tests/test_mtge_resolucion_0005.py tests/test_mtge_engine.py tests/test_api_gateway.py + suite completa + Playwright de frontend/tests/mtge + tsc --noEmit; prueba de mutación documentada"
rastros = ["¤mtge-granescala"]
+++

# MTGE-01 · Gran escala según la norma

**Fuente vinculante (leída el 2026-10-23).** Resolución Nº SPDP-SPD-2026-0005-R, «Norma General sobre el Tratamiento de Datos Personales a Gran Escala», dada en Quito el 2 de febrero de 2026, vigente desde su publicación en el Registro Oficial (número de Registro Oficial **no verificado**; copia en PDF aportada por el equipo consultor SALUDATA, guardada fuera del repositorio).

**Hallazgo.** La plataforma tiene tres cálculos y ninguno sigue la norma:
- `mtge_calculator.py`: escala propia de 100 puntos, cuatro variables con pesos sin fuente y dos supuestos directos citando un «art. 12».
- `frontend/src/lib/api.ts` (`evaluarMTGE`): si el backend falla, calcula en el navegador con otra fórmula, en silencio.
- `frontend/src/app/actions/mtgeActions.ts`: suma los titulares de toda la organización contra un umbral de 10.000. La norma calcula **por tratamiento** (arts. 3.8 y 7).

## Lo que dice la norma
- **Art. 8 · puntajes:**
  - **Titulares en 12 meses, contados una vez (art. 3.8):** 0-1.000 → 1; 1.001-10.000 → 2; 10.001-100.000 → 3; desde 101.000 → 4.
  - **Tipos de datos por titular:** hasta 10 → 0,5; 11-30 → 1; 31-100 → 2; 101 o más → 3.
  - **Categorías:** solo básicas → 0,5; una categoría especial → 2; más de una categoría especial, grupos vulnerables o datos penales → 3.
  - **Frecuencia:** puntual → 0,5; periódica o recurrente → 1; continua o en tiempo real → 2.
  - **Permanencia (art. 3.10-3.12):** ocasional → 0,5; temporal, menos de 3 años → 1; prolongada, desde 3 años → 2.
  - **Alcance (art. 3.1-3.5):** local → 1; nacional → 2; global o transfronterizo → 3.
- **Art. 9:** P = suma de las seis variables.
- **Art. 10:** gran escala si **P ≥ 6**.
- **Art. 12 · efectos vinculantes:** EIPD previa, DPO obligatorio, inclusión en el RAT y medidas reforzadas.
- **Art. 14 · calificación directa sin MTGE:**
  - 14.1 salud y otras categorías especiales o datos sensibles;
  - 14.2 perfilamiento automatizado con efectos jurídicos;
  - 14.3 videovigilancia sistemática en zonas de acceso público;
  - 14.4 biométricos o geolocalización;
  - 14.5 crédito, solvencia y riesgo económico;
  - 14.5 (bis) niñas, niños y adolescentes;
  - 14.6 transferencias sistemáticas;
  - 14.7 mensajería y courier.

## Decisiones asumidas (defectos del texto; aprobadas por el propietario el 2026-10-24)
- **Hueco en el art. 8.1.1-8.1.4:** de 100.001 a 100.999 titulares no hay tramo. Se asignan **4 puntos**, porque superan el tramo de 3 («hasta 100.000»). Constante con comentario que cita esta ficha.
- **Numeral 14.5 duplicado:** en el código se nombran `14.5.a` (crédito) y `14.5.b` (menores), con el texto literal en el comentario.

## Entrega
- `mtge_calculator.py` y `models.py`: las seis variables como enumeraciones con el puntaje del art. 8, el umbral del art. 10 y los supuestos del art. 14. Cada constante cita su artículo. El resultado indica el camino (supuesto directo con su numeral, o puntaje por variable) y los cuatro efectos del art. 12.
- `api/routers/riesgos_mtge.py`: contrato nuevo con las seis variables y la lista de supuestos directos. Una entrada inválida responde 422; nunca se toma un valor por defecto que cambie el resultado.
- **Frontend:**
  - se retira el cálculo de respaldo de `api.ts`: si el backend falla, se muestra el error, no un resultado inventado;
  - `mtgeActions.ts` y `MtgeRelacionalModule.tsx` calculan por tratamiento con el backend y muestran el desglose por variable.
- **Pruebas:**
  - un caso por cada supuesto directo;
  - los bordes de cada tramo del art. 8, incluido el hueco de 100.001;
  - el umbral (5,5 no es gran escala, 6 sí);
  - los dos ejemplos del art. 11 (11.1 supera el umbral; 11.2 no lo alcanza «en condiciones ordinarias»);
  - Playwright del formulario con el desglose.
- **Prueba de mutación documentada:** cambiar el umbral a 6,5 y comprobar que la prueba de borde falla.

## Límites
- No persiste el resultado en el RAT (RAT-01) ni crea la EIPD (RAT-03); deja el resultado listo para que lo guarden.

## Hecho cuando
- Su árbitro pasa, la suite completa pasa y los checks del PR están en verde. No modificó ningún archivo fuera de su propiedad.

## Corrección del coordinador al implementar (2026-10-24)
- **Cinco cálculos, no tres.** Además de los de la lista, `MtgeModule.tsx` (la calculadora visible) calculaba en el navegador con la escala de 100 puntos: pasa a la propiedad de esta tarea y ahora envía las seis variables al servidor. `frontend/src/app/actions/ratActions.ts` tiene otro cálculo de 100 puntos sobre un RAT guardado en `frontend/data/rat_master.json`, pero ninguna pantalla lo usa: queda fuera, como hallazgo para su propia tarea.
- **Vista de la organización.** `mtgeActions.ts` sumaba los titulares de todo el RAT contra 10.000 y escribía banderas «irreversibles» en el archivo local: se elimina, y `MtgeRelacionalModule.tsx` explica que el cálculo es por tratamiento.
- **Titulares y tipos de datos se reciben como cifras**, y el motor aplica los tramos del art. 8 (incluido el hueco de 100.001 a 100.999); no se aceptan tramos ya elegidos.
- **Art. 11.2:** el ejemplo vale para «prolongado **o** nacional» por separado; con las dos condiciones juntas el puntaje es 6,5 y sí es gran escala. Las pruebas lo fijan así.
- **Citas de LEG-01** (`frontend/tests/legal/citas.spec.ts`): la etiqueta «DPO Obligatorio (Art. 48):» sigue en la calculadora, en el resultado de un tratamiento de gran escala; la nota «No puede revertirse…» desaparece con la bandera irreversible.
