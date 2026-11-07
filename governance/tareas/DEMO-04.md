+++
id = "DEMO-04"
titulo = "Selector «Ver como», franja de demostración y «Terminar demo» en el frontend"
ola = "D"
estado = "pendiente"
sala = "frontend"
depende_de = ["DEMO-01", "FE-17", "FE-19", "FE-20", "FE-21", "ORG-21"]
propiedad = ["frontend/src/lib/demo/", "frontend/src/components/demo/", "frontend/src/lib/auth/fetchAutenticado.ts#DEMO-04", "frontend/src/components/layout/DashboardHeader.tsx#DEMO-04", "frontend/src/app/login/page.tsx#DEMO-04", "frontend/tests/demo/demo-activa.spec.ts"]
arbitro = "Playwright frontend/tests/demo/demo-activa.spec.ts en el proyecto «desarrollo» del CI (CI-16) + tsc --noEmit + eslint; los 8 criterios de la ficha"
rastros = ["¤demo", "¤interfaz"]
+++

# DEMO-04 · Selector «Ver como», franja de demostración y «Terminar demo» en el frontend

**Por qué.** El vendedor necesita cambiar de persona en cualquier pantalla, saber siempre que está en una demo y poder cerrarla. Todo lo decide el servidor; el frontend solo pinta lo que `GET /demo/estado` declara.

## Entrega (en este orden; detalle en `governance/apoyo/UX_DEMO_COMERCIAL.md`)
1. **`frontend/src/lib/demo/`:** proveedor y store `useDemo`. Al montar, `GET /demo/estado`; con 404 no se pinta nada de la demo.
2. **`fetchAutenticado.ts#DEMO-04`:** un único punto que, ante 401 con `codigo = DEMO_VENCIDA`, muestra a pantalla completa «Tu demostración terminó» con el botón «Empezar una nueva».
3. **Franja (`components/demo/`, montada en `DashboardHeader.tsx#DEMO-04`):** ámbar, fija, «Demostración: datos ficticios», encima de la cabecera. Cuando falten 5 minutos o menos según `vence_en`, avisa de la inactividad.
4. **Selector «Ver como»:** las 4 personas con una línea por rol y la sugerencia de recorrido DPO → Implementador → Coordinador. Estado «cambiando…». El error 403 `DEMO_PERSONA_AJENA` se muestra en línea. Adopta el `X-Role` que devuelve el servidor.
5. **«Terminar demo»:** diálogo con el texto «La demostración se cierra ahora y sus datos se eliminan esta noche. No podrás volver a abrirla.» (nunca «inmediato»). Si el servidor responde 401, cuenta como éxito. Después se cierra la sesión de Google y la entrada muestra, literal: «La demo se cerró y sus datos se eliminan esta noche».
6. **Entrada (`login/page.tsx#DEMO-04`):** «Continuar con Google» y progreso por pasos durante la copia de la plantilla. 403 y 409 se muestran en línea; ante 409 se reintenta a los 30 segundos.

## Criterios de aceptación (Playwright, `demo-activa.spec.ts`, API simulada)
1. Sin demo (`/demo/estado` 404): no existen `[data-testid=demo-franja]` ni `[data-testid=demo-ver-como]` en ninguna ruta.
2. Con demo: franja y selector en todas las rutas del tablero.
3. Al elegir Coordinador, el disparador muestra «Coordinador» y la siguiente petición lleva el `X-Role` devuelto por el servidor.
4. 403 `DEMO_PERSONA_AJENA`: aparece el mensaje y la persona activa no cambia.
5. 401 `DEMO_VENCIDA` en cualquier petición: pantalla «Tu demostración terminó».
6. «Terminar»: el diálogo no contiene «inmediat»; tras confirmar se llega a la entrada con el aviso literal del punto 5.
7. Ningún texto visible coincide con `/@.*\.invalid/` ni con `/[¤¦]/`.
8. Dos pestañas: se entra en la segunda y la primera muestra «Tu demostración terminó» (una sola demo activa por vendedor).

## Límites
- El frontend nunca envía `X-User-ID` ni elige la persona por su cuenta; el modo `headers` sigue prohibido en la nube.
- Sin `DEMO_MODE` en el servidor, nada de esto aparece. No toca `app/layout.tsx` (lo tiene EP-02).

## Fuentes
- PRD, Módulo 9 «Demo comercial» (`governance/artefactos/PRD.md`, PR #432, aprobado por el CTO el 2026-11-06).
- Flujos y proyección ADPA del Arquitecto de soluciones: `governance/apoyo/FLUJOS_DEMO_COMERCIAL.md`.
- Especificación UX/UI: `governance/apoyo/UX_DEMO_COMERCIAL.md`.
- Decisiones del CTO: rol inicial Administrador; vencimiento a los 60 minutos sin actividad; tope de 20 demos activas; lista `DEMO_VENDEDORES` en Vercel; dirección `*.vercel.app`; una sola demo activa por vendedor (la nueva entrada vence la anterior, motivo `reemplazo`).
