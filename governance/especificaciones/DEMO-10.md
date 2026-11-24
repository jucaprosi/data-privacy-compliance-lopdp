# DEMO-10 · El procedimiento de la web de demo comprueba el permiso de lectura y vuelve atrás sin revisión fija
`¤sdd` `¤demo` `¤arbitro`

## 1. Datos

Sin tablas ni migraciones. Estado final:

| Archivo | Estado final |
| :--- | :--- |
| `governance/operaciones/DEMO_COMERCIAL.md` | §5.2 abre con la comprobación de R1 y fija la etiqueta `anterior` (R2); §5.3 vuelve con `--to-tags=anterior=100`; ninguna revisión escrita a mano en §5 |
| `tests/test_demo09_web_demo.py` | las pruebas de DEMO-09 siguen igual y se añaden las dos de §5 (m5 y m6) |

Hecho medido en `origin/main` aceee6f7 (revisión del Tech Lead de DEMO-09, #1000; lo confirmé en el texto):
- §5.1 manda la comprobación del permiso al brief del propietario, y §5.2 publica sin comprobarlo. DEMO-09 R2 pedía que el procedimiento empezara por esa comprobación.
- §5.2, paso 2, anota `$ANTERIOR` desde Cloud Run, pero §5.3 lo vuelve a escribir: `$ANTERIOR = "evydentia-web-demo-00005-8f5"`. Desde la segunda publicación, volver atrás llevaría a una revisión vieja.
- §5.2 dice que cada bloque define sus variables, así que §5.3 no puede heredar `$ANTERIOR` del paso 2.

## 2. API

Sin rutas.

## 3. Reglas

- **R1 · Comprobar el permiso antes de publicar.** El primer bloque de §5.2, antes de cualquier `gcloud run deploy`:
  1. calcula el agente de servicio a partir del número del proyecto, sin escribirlo a mano: `$NUMERO = (gcloud projects describe evydentia-demo --format="value(projectNumber)").Trim()` y `$AGENTE = "service-$NUMERO@serverless-robot-prod.iam.gserviceaccount.com"`;
  2. lee, solo con lectura, la política del repositorio: `gcloud artifacts repositories get-iam-policy evydentia-containers --project=evydentia --location=us-central1`, filtrada por `roles/artifactregistry.reader` y `serviceAccount:$AGENTE`;
  3. si no aparece, se detiene con `throw` y un mensaje que remite a §5.1. No publica nada.
  - La comprobación es del repositorio, no del proyecto: un permiso sobre todo `evydentia` no cuenta (DEMO-09 R2, mínimo privilegio).
- **R2 · Volver atrás con una etiqueta de Cloud Run, no con una constante.**
  - **Decisión:** la revisión anterior se guarda en el propio servicio, como etiqueta de tráfico `anterior`. No se usa un archivo local ni una variable que se herede entre bloques.
  - En el paso 2 de §5.2, después de leer `$ANTERIOR` de `status.latestReadyRevisionName`, se ejecuta `gcloud run services update-traffic evydentia-web-demo … --update-tags="anterior=$ANTERIOR"`. La etiqueta se mueve en cada publicación, así que siempre señala la revisión que servía justo antes.
  - §5.3 vuelve con `gcloud run services update-traffic evydentia-web-demo … --to-tags="anterior=100"`. No define `$ANTERIOR` ni nombra ninguna revisión.
  - Razones:
    - cada bloque sigue siendo independiente;
    - la etiqueta sobrevive al cierre de la sesión, a otro equipo y a otra persona, y un archivo local no;
    - se puede leer con `gcloud run services describe` (`status.traffic`).
  - Coste aceptado: la revisión anterior conserva una URL con etiqueta. La demo ya es pública (`allUsers`), así que no expone nada nuevo.
- **R3 · Ninguna revisión escrita a mano.** En toda §5 no aparece un nombre de revisión (`evydentia-web-demo-` seguido de cinco cifras). Las revisiones se leen de Cloud Run.
- **R4 · Límites.** Solo los dos archivos de la propiedad. No toca la nube ni usa gcloud: el procedimiento lo sigue el propietario. Las pruebas leen el texto, sin red y sin `import yaml`.
- **Supuesto del nombre del agente de servicio (DEMO-09 R2).** No cambia el diseño y R1 lo hace seguro.
  - Si el nombre no fuera ese, la comprobación no encontraría el permiso y se detendría antes de publicar. El fallo cerrado nunca da un falso verde.
  - El único coste es un falso rojo, y §5.1 ya pide confirmar la cuenta con `gcloud projects get-iam-policy evydentia-demo`.
  - Calcular `$AGENTE` a partir del número del proyecto quita el último literal del número.
- **R-ADPA · Ortogonalidad ZERAG (`DEMO-10`).** Solo la propiedad.

## 4. Interfaz

No aplica.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** §5.2, **entonces** el primer bloque `powershell` contiene, antes de la primera aparición de `gcloud run deploy`: `get-iam-policy evydentia-containers`, `roles/artifactregistry.reader`, `serverless-robot-prod.iam.gserviceaccount.com`, `projectNumber` y `throw`; y no contiene el número `517105327086`. Mutación m5: quitar el `throw` o mover la comprobación después del `deploy` da rojo. | `test_el_procedimiento_comprueba_el_permiso_antes_de_publicar` |
| **Dado** §5, **entonces** no contiene ningún `evydentia-web-demo-\d{5}-`; §5.2 contiene `--update-tags="anterior=` antes de `gcloud run deploy`, y §5.3 contiene `--to-tags="anterior=100"` y no asigna `$ANTERIOR`. Mutación m6: volver a escribir `$ANTERIOR = "evydentia-web-demo-00005-8f5"` en §5.3 da rojo. | `test_volver_atras_usa_la_etiqueta_anterior` |
| **Dado** las pruebas de DEMO-09 (m1 a m4), **entonces** siguen en verde. | `tests/test_demo09_web_demo.py` |

## 6. Trazabilidad

- Ficha: `governance/tareas/DEMO-10.md`. Especificación de referencia: `governance/especificaciones/README.md`.
- Revisión del Tech Lead de DEMO-09 (#1000, `aceee6f7`, 2026-11-24): dos desvíos de §5 frente a DEMO-09 R2 y R3.
- Completa DEMO-09 R2 (la comprobación) y R3, paso 5 (volver atrás).
- Depende de DEMO-09, dueña de los dos archivos mientras siga `en_curso`. DEMO-10 se lanza cuando DEMO-09 se cierre.
