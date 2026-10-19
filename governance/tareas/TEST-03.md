+++
id = "TEST-03"
titulo = "Arnés de integración: el frontend contra el backend real"
ola = "D"
estado = "pendiente"
sala = "frontend"
depende_de = ["TEST-02", "FE-07", "SEC-07"]
propiedad = ["frontend/playwright.integracion.config.ts", "frontend/tests/integracion/**", "frontend/playwright.config.ts"]
arbitro = "cd frontend; npx playwright test -c playwright.integracion.config.ts, sin pruebas omitidas, contra backend real y una rama Neon propia; prueba negativa documentada"
rastros = ["¤frontend-ide", "¤arbitro"]
+++

# TEST-03 · Arnés de integración: el frontend contra el backend real

**Objetivo.** Todas las pruebas de Playwright del repositorio simulan la API con `page.route`. Eso comprueba la interfaz, pero no que el frontend y el backend se entiendan: un cambio de contrato, de cabeceras o de forma de respuesta pasaría en verde. Este arnés levanta el backend y el frontend reales y recorre un conjunto pequeño de flujos sin interceptar ninguna llamada.

## Entrega
- `frontend/playwright.integracion.config.ts`: una configuración aparte de la de `frontend/playwright.config.ts`, con dos servidores:
  - Backend: `uvicorn main:app` en un puerto propio (5100), con `AUTH_MODE=headers` y la base de pruebas de `TEST_DATABASE_URL`.
  - Frontend: `next dev` en un puerto propio (3200), con `BACKEND_URL=http://127.0.0.1:5100` y `NEXT_PUBLIC_AUTH_MODE=headers`.
  - `reuseExistingServer = false`: nunca se reutiliza un servidor de otra sesión.
- **Precondiciones duras, sin omitir en silencio** («omitida no es pasada»): si falta `TEST_DATABASE_URL`, la configuración falla con un mensaje claro. Si el host de la base es el de producción (`ep-late-hall-b50bpbk5`), falla también.
- `frontend/tests/integracion/`: tres recorridos mínimos, cada uno con sus propios datos y limpiando al terminar, sin depender del orden:
  1. **Roles reales:** `GET /organizacion/me/roles` con la identidad de desarrollo devuelve la forma que espera el cliente, y el panel la muestra.
  2. **Tamaño de la organización:** `PATCH /organizacion/configuracion` como administrador y la ficha refleja la talla guardada.
  3. **Aislamiento:** una llamada sin `X-Tenant-ID` recibe 401 del backend real.
- Ninguna prueba usa `page.route`: `git grep page.route frontend/tests/integracion` no devuelve nada.
- Documentar en el encabezado de la configuración el comando exacto y la rama Neon necesaria (`test-int`).

## Límites
- No entra en el CI: eso exige tocar `.github/` (gobernanza reservada) y una base por ejecución, y queda para el propietario.
- No toca las pruebas existentes. En `frontend/playwright.config.ts` solo añade `testIgnore: "**/integracion/**"`: sin eso, el arnés normal (y el job de Playwright del CI) recogería los recorridos de integración, que necesitan backend y base de datos reales, y fallaría.
- Solo modo `headers`; el inicio de sesión real con Google no se prueba aquí.
- Nunca contra producción ni contra la rama `test` compartida.

## Hecho cuando
- Su árbitro pasa, la suite completa pasa y el check `Arnés Físico Determinista` del PR está en verde. No modificó ningún archivo fuera de su propiedad y dejó `estado = "hecha"` en esta especificación.
- La prueba negativa está en el informe: al romper a propósito cada recorrido (por ejemplo, devolver otra forma de `me/roles`) la prueba falla.
