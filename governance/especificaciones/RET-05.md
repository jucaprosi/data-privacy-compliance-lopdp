# RET-05 · Una sola entrada de la API y despliegue en Cloud Run
`¤sdd` `¤arquitectura` `¤frontend-ide`

## 1. Datos

Sin tablas. El sistema despliega ambos servicios en Google Cloud Run (`main:app` para el backend FastAPI y Next.js standalone para el frontend), con `frontend/next.config.ts` / `frontend/next.config.cloudrun.ts`, `tests/test_cabeceras_seguridad.py`, `tests/test_health_routers.py` y `tests/test_ret05_una_entrada.py`.

## 2. API

La única entrada de la API es `main:app` (Cloud Run arranca con `uvicorn main:app`):

- `tests/test_cabeceras_seguridad.py` verifica las cabeceras de seguridad en `next.config.ts` y la configuración de tiempo máximo (300 s) en el manifiesto de Cloud Run;
- `tests/test_health_routers.py` valida que `main.app` expone `/health`;
- `tests/test_sec16_secretos_obligatorios.py` y `tests/test_sec17_configuracion_nube.py` importan directamente `from main import app`.

## 3. Reglas

- **R1 · Una sola entrada.** Todos los módulos, pruebas, scripts y manifiestos apuntan exclusivamente a `main:app`.
- **R2 · Cabeceras y tiempo máximo en Cloud Run.** Las cabeceras de seguridad las declaran `next.config.ts` y el middleware, y el tiempo máximo de la generación en línea se configura y verifica en el manifiesto de Cloud Run.
- **R3 · Salud de la aplicación.** `main.app` expone `/health` para las sondas de Cloud Run y las pruebas de routers.
- **R4 · Alineación de configuración.** `pytest.ini`, `app_core/security.py`, `app_core/config.py`, `frontend/src/lib/auth/modo.ts`, `bucle_eventos.py`, `firma_anf.py`, `generacion_en_linea.py`, `test_gcp03_frontend_cloudrun.py` y `test_sec17_configuracion_nube.py` mantienen nomenclatura nativa de Cloud Run.
- **R-ADPA · Ortogonalidad ZERAG (`RET-05`).** Toda invocación a otra sala va por `app_core/pasillo/<otra_sala>.py` (`ImportsCruzados = ∅`, ADR 0001). `verificar_adpa` queda sin importaciones huérfanas.

## 4. Interfaz

Sin cambio visible. Recursos estáticos del frontend verificados en el humo de arranque.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** el árbol del proyecto, **entonces** `main:app` es la única entrada ASGI y el despliegue opera en Google Cloud Run. | `test_una_sola_entrada` |
| **Dado** `next.config.ts`, **entonces** las cabeceras de seguridad esperadas siguen declaradas. | `test_cabeceras_seguridad` |
| **Dado** `main.app`, **entonces** `/health` responde y SEC-16 y SEC-17 siguen verdes importando `main`. | `test_health_routers` |
| **Dado** el frontend, **cuando** se construye y se recorre el humo, **entonces** no hay recursos rotos. | `frontend/tests/humo/01_arranque.spec.ts` |

## 6. Trazabilidad

- Ficha: `governance/tareas/RET-05.md`.
- Especificación de referencia: `governance/especificaciones/README.md`.
- Depende de RET-01 y se coordina con SEC-21 en `tests/test_sec16_secretos_obligatorios.py` y `tests/test_sec17_configuracion_nube.py`.
- El tiempo máximo de 300 s de RM-13 se verifica en el manifiesto de Cloud Run.
