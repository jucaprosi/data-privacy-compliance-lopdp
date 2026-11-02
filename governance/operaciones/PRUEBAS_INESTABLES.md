# Pruebas inestables de Playwright
`¤ci-cd` `¤frontend-ide`

> `retries: 1` en el CI esconde la inestabilidad: una prueba que pasa al segundo intento cuenta como verde. Este documento fija cómo se cuenta y qué pasa con ella.

---

## 1. Qué cuenta como reintento

Una prueba necesitó reintento si en una corrida del paso `Playwright Tests` falló y pasó después. Playwright la resume como `N flaky` al final del registro y la marca `[retry #1]` en cada línea del reporte `list`.

```powershell
gh run view <run_id> --log | Select-String -Pattern 'flaky|retry #|passed \('
```

Cuenta toda corrida de CI, sea de PR o de push, de cualquier rama. La línea `passed` también da la duración de la corrida.

## 2. Regla de cuarentena

1. Una prueba que necesita reintento **tres veces en una semana** (siete días corridos) entra en cuarentena.
2. La cuarentena tiene **fecha de salida, a lo sumo tres meses** desde la entrada.
3. Una prueba en cuarentena **sigue corriendo sin bloquear**: se ve su resultado, pero no detiene la fusión.
4. **Nunca se borra sin una ficha** en `governance/tareas/` que la arregle o la retire. Tampoco se quita la cuarentena sin esa ficha.
5. Vencida la fecha sin arreglo, la decisión se toma en una ficha: no se prorroga en silencio.
6. No se sube `timeout` ni `retries` para esconder una prueba inestable.

Quien detecta el tercer reintento añade la fila en la sección 3, en el mismo día.

El mecanismo que deja correr una prueba sin bloquear todavía no existe, porque toca el flujo del CI y ninguna prueba lo ha necesitado. La primera que entre en cuarentena abre la ficha que lo crea.

## 3. Registro de cuarentena

| Prueba | Entrada | Salida (máx. 3 meses) | Ficha | Corridas con reintento |
| :--- | :--- | :--- | :--- | :--- |
| Ninguna | | | | |

## 4. Dos servidores en el CI

Desde CI-04, `frontend/playwright.config.ts` corre dos proyectos:

| Proyecto | Servidor | Trabajadores | Pruebas |
| :--- | :--- | :---: | :--- |
| `produccion` | `next build` + `next start`, con `NEXT_PUBLIC_AUTH_MODE=headers` | 4 | todas las demás |
| `desarrollo` | `next dev` | 4 | las de `SOLO_DESARROLLO` |

Corren uno tras otro y comparten los 4 trabajadores.

`SOLO_DESARROLLO` existe porque un build de producción elimina a propósito `window.__LOPDP_AUTH_PRUEBAS__` y las rutas `/harness-roadmap/*`. Una prueba que use `fijarAjustes` o esas rutas se añade a la lista. La variable `NEXT_PUBLIC_AUTH_MODE=headers` vive solo en `webServer.env` del runner de pruebas; ningún despliegue la usa.

En local sigue `npm run dev`, con un solo proyecto.
