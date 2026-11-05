# SEC-14 · El frontend no publica mapas de fuente ni secretos en variables públicas
`¤sdd` `¤seguridad` `¤arbitro`

## 1. Datos

Sin tablas. Entradas: las configuraciones de Next (`frontend/next.config*.ts`), los nombres `NEXT_PUBLIC_*` que aparecen en `frontend/src` y, tras compilar, la carpeta `frontend/.next/static`.

Nombre de secreto: un nombre que contiene `SECRET`, `PASSWORD`, `PRIVATE`, `TOKEN` o termina en `_KEY`.

Forma de credencial en el paquete: `sk-` seguido de 20 o más caracteres alfanuméricos, `-----BEGIN` y `postgres://` o `postgresql://` con contraseña.

## 2. API

Sin API. `python scripts/verificar_bundle_frontend.py [carpeta]` termina con código 0 si el paquete está limpio y con 1 si no, listando cada archivo y motivo sin imprimir el valor hallado.

## 3. Reglas

- **R1 · Sin mapas de fuente en producción.** Ninguna configuración de Next fija `productionBrowserSourceMaps: true`.
- **R2 · Sin secretos públicos.** Ninguna variable `NEXT_PUBLIC_*` tiene nombre de secreto.
- **R3 · Paquete limpio.** `frontend/.next/static` no contiene `.map`, ni `sourceMappingURL`, ni cadenas con forma de credencial.
- **R4 · Sin filtrar lo que encuentra.** El informe nombra archivo y regla, nunca el valor.

## 4. Interfaz

Sin interfaz de usuario.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** la configuración actual de Next, **cuando** corre la prueba, **entonces** no hay hallazgos. | `test_configuracion_actual_sin_mapas` |
| **Dado** una configuración con `productionBrowserSourceMaps: true`, **cuando** se revisa, **entonces** hay un hallazgo R1. | `test_detecta_mapas_activados` |
| **Dado** un archivo de `frontend/src` que usa `NEXT_PUBLIC_STRIPE_SECRET`, **cuando** se revisa, **entonces** hay un hallazgo R2 y `NEXT_PUBLIC_GOOGLE_CLIENT_ID` no lo produce. | `test_detecta_secreto_publico` |
| **Dado** una carpeta de compilación con `app.js.map` y una cadena `sk-` de prueba, **cuando** corre el script, **entonces** termina con 1 y el informe no contiene la cadena. | `test_script_detecta_mapa_y_credencial_sin_imprimirla` |

## 6. Trazabilidad

- `PRD_EVYDENTIA_REVENTA_NUBE.md` §5.3 (frontend en Cloud Run, GCP-03); requisito 1 de la revisión del 2026-11-04.
