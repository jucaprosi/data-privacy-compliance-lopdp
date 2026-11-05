# SEC-14 · Empaquetado seguro del frontend: sin mapas de fuente públicos y sin secretos en el paquete del navegador
`¤sdd` `¤empaquetado-seguro` `¤grado-productivo` `¤seguridad` `¤frontend-ide`

## 1. Datos

Lista blanca `variables_publicas.json` (`{"NEXT_PUBLIC_API_URL": "motivo"}`). Hallazgo `HallazgoEmpaquetado` (`archivo: str`, `tipo: mapa_fuente | variable_no_declarada | secreto`, `detalle: str`).

## 2. API

- Sin rutas: árbitro de compilación ejecutable como `python scripts/verificar_empaquetado_frontend.py [--salida frontend/.next]` con código 1 si hay hallazgos.

## 3. Reglas

- **R1 · Sin mapas de fuente públicos (`INV_FRONTEND_NO_PUBLIC_SOURCE_MAPS_NO_SECRETS`).** La configuración de producción no activa `productionBrowserSourceMaps` y ningún `*.map` queda servible.
- **R2 · Lista blanca de variables públicas.** Solo las variables declaradas en `variables_publicas.json` pueden aparecer en el paquete del navegador.
- **R3 · Cero secretos en el navegador.** Las claves viven en Secret Manager y solo las lee el servidor.

## 4. Interfaz

Sin cambios visibles: la interfaz es la misma, servida sin mapas de fuente.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** una compilación de ejemplo con un archivo `.map` bajo `/_next/static/`, **cuando** se ejecuta el verificador, **entonces** devuelve código 1 con un hallazgo `mapa_fuente`. | `test_detecta_mapa_de_fuente` |
| **Dado** un paquete que contiene una variable `NEXT_PUBLIC_*` no declarada o una clave privada, **cuando** se ejecuta el verificador, **entonces** devuelve código 1 con el hallazgo correspondiente. | `test_detecta_variable_y_secreto` |
| **Dado** la configuración real del repositorio, **cuando** se ejecuta el verificador, **entonces** no hay hallazgos. | `test_configuracion_real_limpia` |

## 6. Trazabilidad

- PRD_EVYDENTIA_REVENTA_NUBE §5.4 pilar 1 y criterio 27; invariante `INV_FRONTEND_NO_PUBLIC_SOURCE_MAPS_NO_SECRETS`.
