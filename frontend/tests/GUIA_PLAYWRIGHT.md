# Guía de Playwright para quien trabaje en el frontend

Playwright es el árbitro de la interfaz: lo que no pasa aquí no está comprobado. Esta guía es para
cualquier IA o persona que ejecute o escriba pruebas. Todo lo de abajo está comprobado en este
repositorio (Playwright 1.63, Chromium, Windows).

## 1. Preparación (una vez por máquina)

```bash
cd frontend
npm install
npx playwright install chromium
```

Los navegadores se guardan en `%LOCALAPPDATA%\ms-playwright`, fuera del repositorio. Si una prueba
dice que falta el ejecutable, es este paso.

## 2. Ejecutar

Siempre desde `frontend/`. El arnés levanta solo el servidor de desarrollo y lo apaga al terminar;
no hace falta arrancar nada antes.

| Qué | Comando |
|---|---|
| Todo | `npx playwright test` |
| Un archivo | `npx playwright test tests/roadmap/integracion.spec.ts` |
| Una prueba por nombre | `npx playwright test -g "ve solo las subvistas"` |
| Ver qué hay sin ejecutar | `npx playwright test --list` |
| Informe de la última ejecución | `npm run test:e2e:report` |

### Varias sesiones a la vez: un puerto distinto cada una

Si dos chats comparten la carpeta y ambos usan el puerto 3000, uno de los dos reutiliza el servidor
del otro (compilando otra rama) y los resultados no valen. Cada sesión fija el suyo:

```bash
PLAYWRIGHT_PORT=3101 npx playwright test tests/roadmap
```

Usa 3101, 3102, 3103… y no el 3000, que es el del propietario. En PowerShell:
`$env:PLAYWRIGHT_PORT=3101; npx playwright test tests/roadmap`.

**Antes de ejecutar, comprueba en qué rama estás** (`git branch --show-current`): el servidor
compila lo que haya en disco, no lo que crees tener.

## 3. Cómo se escribe una prueba aquí

- **La API no existe.** Las pruebas no necesitan backend: se simula con
  `page.route("**/api/v1/**", ...)` y cada prueba registra las llamadas que hace la interfaz. Ver
  `tests/roadmap/integracion.spec.ts` (función `prepararApi`) como modelo. Toda llamada no simulada
  se responde 404 y queda registrada, para detectar llamadas inesperadas.
- **Helpers compartidos** en `tests/utiles.ts`: `abrirAppLimpia`, `configurarProyecto`, `irASala`.
  Si un cambio de la interfaz los rompe, el arreglo es del propietario de ese helper, no se
  esquiva con una copia local sin dejarlo dicho.
- **Selectores por rol y nombre accesible** (`getByRole`, `getByLabel`), no por clase CSS ni por
  texto suelto. Si no hay un rol que lo identifique, es una falta de accesibilidad de la interfaz:
  corrígela allí.
- **Rutas de arnés** `/harness-roadmap/*`: existen para montar un componente aislado; devuelven 404
  en producción.
- **Esperas:** nunca `waitForTimeout`. Usa aserciones que reintentan (`await expect(...)`).
- **Cada prueba parte limpia.** No dependas del orden ni de datos que dejó otra.
- **Prueba negativa obligatoria:** una prueba que nunca ha fallado no demuestra nada. Rompe a
  propósito lo que verifica y comprueba que falla, antes de darla por buena.

## 4. Trampas conocidas

- **Primera visita lenta.** El servidor de desarrollo compila cada ruta bajo demanda. Por eso el
  arnés usa 3 trabajadores (2 en CI) y 15 s de espera por aserción. No subas los trabajadores: los
  fallos serían de lentitud, no de regresión.
- **`[WebServer] ECONNREFUSED 127.0.0.1:5000`** en la salida: es el reenvío de `/api/v1` hacia un
  backend que no está corriendo. Es ruido si la prueba simula la API; si no la simula, esa prueba
  depende de un backend y está mal escrita.
- **Perfil de operación obligatorio.** Desde el commit `c92490e` la ficha exige responder todas las
  preguntas Sí/No antes de «Guardar Ficha». Usa `configurarProyecto`, que ya lo hace.
- **El CI no ejecuta Playwright**, solo `tsc --noEmit` y `next build`. Un Playwright en verde es
  evidencia local: pégala en el PR (comando y resultado), no la des por supuesta.
- **Cabeceras de seguridad (SEC-06).** La CSP está en modo informe. Si una prueba nueva carga un
  recurso de otro origen, aparecerá como aviso en `tests/seguridad/cabeceras.spec.ts`, que lo
  resume sin fallar. Un bloqueo real sí hace fallar la prueba.
- **Artefactos de fallo** (`test-results/`, `playwright-report/`) están ignorados por git. No los
  confirmes. La traza de un fallo se abre con `npx playwright show-trace <ruta/trace.zip>`.

## 5. Qué entregar en un PR que toca la interfaz

1. `npx tsc --noEmit` y `npm run build` sin errores.
2. El Playwright de tu área en verde, con el comando exacto y el puerto usado.
3. Las pruebas nuevas, con la comprobación de que fallan cuando rompes lo que verifican.
4. Si algo no se pudo comprobar, dilo como «no verificado»; no lo omitas.

## 6. Con un asistente que controla un navegador (MCP)

Un navegador manejado por MCP sirve para mirar y depurar; **no sustituye al arnés**: el criterio de
éxito es `npx playwright test`, que es repetible y no depende de lo que alguien vio en pantalla. Si
usas un navegador MCP, levanta el servidor con `npm run dev -- --port <tu puerto>` y navega a
`http://localhost:<tu puerto>`.
