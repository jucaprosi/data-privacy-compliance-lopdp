# SEC-25 · Cabecera `Cache-Control: no-store` por defecto en `/api/v1`
`¤sdd` `¤seguridad-tenant`

## 1. Datos

Sin tablas ni migraciones. Un middleware nuevo en `app_core/seguridad/no_store.py`, registrado en la sección `SEC-25` de `main.py` (ya sembrada, líneas 253 a 255). Usa la constante `CABECERA_NO_STORE` de `app_core/cache`, que entregó GCP-06.

## 2. API

Ninguna ruta cambia de contrato. Cambia una cabecera de respuesta:

| Respuesta | Antes | Después |
| :--- | :--- | :--- |
| Ruta de `/api/v1/*` que no fija `Cache-Control` | sin la cabecera | `Cache-Control: no-store` |
| Ruta de `/api/v1/*` que fija su propio `Cache-Control` (descargas de biblioteca y de evidencias) | el suyo | el suyo, sin cambio |
| Rutas fuera de `/api/v1` (`/health`, estáticos) | sin cambio | sin cambio |

## 3. Reglas

- **R1 · Por defecto, no se guarda.** Toda respuesta de `/api/v1/*` sale con `no-store`, también las de error (401, 403, 404, 422 y 500).
- **R2 · No se pisa.** Si la ruta ya puso un `Cache-Control`, el middleware no lo cambia.
- **R3 · Solo `/api/v1`.** El prefijo se compara con la ruta de la petición, no con una subcadena: `/api/v10` o `/otra/api/v1` no cuentan.
- **R4 · Una sola fuente del valor.** El middleware usa `CABECERA_NO_STORE`; no escribe la cadena.
- **R5 · Sin estado.** El middleware no lee la organización, no abre sesión de base y no registra el cuerpo.
- **R-ADPA · Ortogonalidad ZERAG (`SEC-25`).** Vive en `app_core`; no importa de ninguna sala.

## 4. Interfaz

No aplica: no hay pantalla.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** una ruta de `/api/v1` que no fija la cabecera, **entonces** la respuesta trae `Cache-Control: no-store`. Mutación: quitar el middleware hace fallar la prueba. | `test_api_sin_cabecera_recibe_no_store` |
| **Dado** una respuesta de error de `/api/v1` (401 y 404), **entonces** también trae `no-store`. | `test_errores_con_no_store` |
| **Dado** una descarga que fija su propio `Cache-Control`, **entonces** lo conserva. Mutación: pisarlo hace fallar la prueba. | `test_cabecera_propia_se_respeta` |
| **Dado** `/health` y una ruta `/api/v10/x`, **entonces** no reciben la cabecera. | `test_solo_el_prefijo_api_v1` |
| **Dado** el módulo del middleware, **entonces** no contiene la cadena `no-store`: la toma de `app_core.cache`. | `test_usa_la_constante_comun` |

Todas en `tests/test_sec25_no_store.py`, sin base de datos y sin `import yaml`.

## 6. Trazabilidad

- Ficha: `governance/tareas/SEC-25.md`. Especificación de referencia: `governance/especificaciones/README.md`.
- Pedida por el CTO el 2026-11-13: GCP-06 deja fuera el backend. Depende de GCP-06 (en curso) y MARCA-01 (hecha).
- Propiedad, medida en `origin/main` 4eca5af2: `app_core/seguridad/no_store.py` y `tests/test_sec25_no_store.py` son nuevos; la carpeta `app_core/seguridad/` no existe todavía. `main.py` lo comparten por sección BOV-01 y DLP-01 (en curso) y CCTV-01 y CON-01 (pendientes): cada una escribe solo entre sus marcas.
- Fuera de esta ficha: la política de contenido en modo informe no declara `frame-src blob:`, y el visor de NORM-02 usa un blob. Va en la ficha que configure esa política.
