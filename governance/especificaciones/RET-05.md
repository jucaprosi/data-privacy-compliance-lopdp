# RET-05 · Sin configuración ni entrada de Vercel en `main`
`¤sdd` `¤arquitectura` `¤frontend-ide`

## 1. Datos

Sin tablas. Se retiran archivos de despliegue del PMV: `vercel.json` (raíz y `frontend/`), `api/index.py`, `frontend/public/vercel.svg` y las entradas `.vercel` de los `.gitignore`.

## 2. API

No hay rutas nuevas. La única entrada de la API es `main:app` (Cloud Run arranca con `uvicorn main:app`).

Medido en `main`: cuatro pruebas dependen hoy de lo que se retira, así que cambian en la misma ficha:
- `tests/test_cabeceras_seguridad.py:47` lee `vercel.json` y afirma `functions["api/index.py"].maxDuration == 300`;
- `tests/test_health_routers.py:69-90` carga `api/index.py` para el `/health` de emergencia;
- `tests/test_sec16_secretos_obligatorios.py:132` y `tests/test_sec17_configuracion_nube.py:165` importan `from api.index import app`.

## 3. Reglas

- **R1 · Una sola entrada.** Ningún módulo, prueba, script ni manifiesto importa `api.index`. Las pruebas que lo importaban pasan a `main.app`.
- **R2 · Las cabeceras de seguridad no dependen de Vercel.** Las pone `next.config.ts` o el middleware, y `test_cabeceras_seguridad.py` las sigue comprobando ahí. La afirmación sobre `maxDuration` de `vercel.json` se retira: el tiempo máximo de la generación en línea se fija en Cloud Run y se comprueba en su manifiesto.
- **R3 · El `/health` de emergencia.** Si la aplicación no importa, Cloud Run falla el arranque y no enruta tráfico; ese es el comportamiento buscado. La prueba del `/health` en 503 desde `api/index.py` se retira con el archivo. La sustituye una que comprueba que `main.app` expone `/health`.
- **R4 · `tests/test_vercel_despliegue.py` se retira.** Su invariante pertenece a la rama `produccion`.
- **R5 · Comentarios y nombres.** `pytest.ini`, `app_core/security.py`, `app_core/config.py`, `frontend/src/lib/modo.ts`, `bucle_eventos.py`, `firma_anf.py` y `generacion_en_linea.py` dejan de nombrar Vercel. `test_gcp03_frontend_cloudrun.py` y `test_sec17_configuracion_nube.py` también.
- **R6 · Nada hacia `produccion`.** La rama `produccion` conserva sus `vercel.json` y su `api/index.py`.
- **R-ADPA · Ortogonalidad ZERAG (`RET-05`).** Toda invocación a otra sala va por `app_core/pasillo/<otra_sala>.py` (`ImportsCruzados = ∅`, ADR 0001). `verificar_adpa` queda sin importaciones huérfanas.

## 4. Interfaz

Sin cambio visible. Se retira el icono `vercel.svg` si ninguna pantalla lo usa; la ficha lo comprueba. Pasa por UX/UI solo si alguna pantalla lo mostraba.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** el árbol, **entonces** no existen `vercel.json`, `frontend/vercel.json` ni `api/index.py`, y nadie importa `api.index`. Mutación: restaurar el import en una prueba hace fallar el árbitro. | `test_una_sola_entrada` |
| **Dado** `next.config.ts`, **entonces** las cabeceras de seguridad esperadas siguen declaradas. | `test_cabeceras_seguridad` |
| **Dado** `main.app`, **entonces** `/health` responde y SEC-16 y SEC-17 siguen verdes importando `main`. | `test_health_routers` |
| **Dado** el frontend, **cuando** se construye y se recorre el humo, **entonces** no hay recursos rotos. | `frontend/tests/humo/01_arranque.spec.ts` |

## 6. Trazabilidad

- Ficha: `governance/tareas/RET-05.md`.
- Programa: `governance/apoyo/RETIRO_PLATAFORMAS_PMV.md` (PR #763), decisión del propietario del 2026-11-13.
- Especificación de referencia: `governance/especificaciones/README.md`.
- No se toca la rama `produccion` ni la historia (`alembic/versions/`, `governance/historico/pmv/`, fichas `hecha`, aportes, bibliografía). `.github/workflows/` y `verificadores/` son del propietario: si hacen falta, va un brief.
- Depende de RET-01. Orden con SEC-21, que posee `tests/test_sec16_secretos_obligatorios.py` y `tests/test_sec17_configuracion_nube.py`.
- El tiempo máximo de 300 s de RM-13 pasa a comprobarse en el manifiesto de Cloud Run.
