+++
id = "DEMO-04"
titulo = "Interfaz demo: selector «Ver como», franja, «Terminar demo» y pantallas de error"
ola = "D"
estado = "pendiente"
sala = "frontend"
depende_de = ["FE-10", "FE-17", "FE-19", "FE-20", "FE-21", "BIB-115", "ORG-21"]
propiedad = ["frontend/src/lib/demo/", "frontend/src/components/demo/", "frontend/src/lib/auth/cabeceras.ts#DEMO-04", "frontend/src/lib/auth/fetchAutenticado.ts#DEMO-04", "frontend/src/components/layout/DashboardHeader.tsx#DEMO-04", "frontend/src/app/login/page.tsx#DEMO-04", "frontend/tests/demo/"]
arbitro = "Playwright frontend/tests/demo/ en el proyecto «desarrollo» del CI (CI-16) + tsc --noEmit + eslint; los 8 criterios de la ficha"
rastros = ["¤demo", "¤interfaz"]
+++

# DEMO-04 · Interfaz demo: selector «Ver como», franja, «Terminar demo» y pantallas de error

**Por qué.** El vendedor necesita cambiar de persona en cualquier pantalla, saber siempre que está en una demo y poder cerrarla. Todo lo decide el servidor; el frontend solo pinta lo que `GET /demo/estado` declara. Trabaja contra el contrato de §3 con la API simulada, por eso corre en paralelo con el backend.

## Entrega (en este orden; detalle en `governance/apoyo/UX_DEMO_COMERCIAL.md`)
1. **`lib/demo/`:** cliente de `/demo/*` y store `useDemo`. Al montar, `GET /demo/estado`; con 404 no se pinta nada de la demo.
2. **`cabeceras.ts#DEMO-04`:** `X-Role` = el rol que devolvió el servidor para la persona activa.
3. **`fetchAutenticado.ts#DEMO-04`:** un único punto que, ante 401 con `codigo = DEMO_VENCIDA`, muestra a pantalla completa «Tu demostración terminó» con el botón «Empezar una nueva».
4. **Franja (`components/demo/`, montada en `DashboardHeader.tsx#DEMO-04`):** ámbar, fija, «Demostración: datos ficticios», encima de la cabecera; avisa cuando falten 5 minutos o menos según `vence_en`.
5. **Selector «Ver como»:** las 4 personas con una línea por rol y la sugerencia de recorrido DPO → Implementador → Coordinador; estado «cambiando…»; 403 `DEMO_PERSONA_AJENA` en línea.
6. **«Terminar demo»:** diálogo «La demostración se cierra ahora y sus datos se eliminan esta noche. No podrás volver a abrirla.» (nunca «inmediato»). Un 401 cuenta como éxito. Después se cierra la sesión de Google y la entrada muestra, literal: «La demo se cerró y sus datos se eliminan esta noche».
7. **Entrada (`login/page.tsx#DEMO-04`):** «Continuar con Google» y progreso por pasos durante la copia; 403 y 409 en línea; ante 409 se reintenta a los 30 segundos.

## Criterios de aceptación (Playwright, `frontend/tests/demo/`, API simulada)
1. Sin demo (`/demo/estado` 404): no existen `[data-testid=demo-franja]` ni `[data-testid=demo-ver-como]` en ninguna ruta.
2. Con demo: franja y selector en todas las rutas del tablero.
3. Al elegir Coordinador, el disparador muestra «Coordinador» y la siguiente petición lleva el `X-Role` devuelto por el servidor.
4. 403 `DEMO_PERSONA_AJENA`: aparece el mensaje y la persona activa no cambia.
5. 401 `DEMO_VENCIDA` en cualquier petición: pantalla «Tu demostración terminó».
6. «Terminar»: el diálogo no contiene «inmediat»; tras confirmar se llega a la entrada con el aviso literal del punto 6.
7. Ningún texto visible coincide con `/@.*\.invalid/` ni con `/[¤¦]/`.
8. Dos pestañas: se entra en la segunda y la primera muestra «Tu demostración terminó».

## Límites
- **Contrato congelado (CTO, 2026-11-06):** rutas, cuerpos, códigos 401/403/409 y `X-Role` de `FLUJOS_DEMO_COMERCIAL.md` §3, y las firmas de `demo_service.py` que fija DEMO-00. Si hay que cambiarlos, se para y se consulta a la Coordinadora; las fichas afectadas se ajustan en la misma tanda.
- Solo archivos de `frontend/`. No toca `app/layout.tsx` (su dueña es EP-02): la franja y el selector se montan en `DashboardHeader.tsx#DEMO-04`.
- El frontend nunca envía `X-User-ID` ni elige la persona por su cuenta.

## Fuentes
- PRD, Módulo 9 «Demo comercial» (`governance/artefactos/PRD.md`, PR #432, aprobado por el CTO el 2026-11-06).
- Flujos y contrato de la API: `governance/apoyo/FLUJOS_DEMO_COMERCIAL.md` (§3 congelado por el CTO).
- Corte ortogonal y matriz flujo × archivo del Arquitecto de soluciones ADPA (2026-11-06): ninguna ruta con dos dueños; lo compartido es una compuerta o el contrato de DEMO-00, que las demás solo leen.
- Especificación UX/UI: `governance/apoyo/UX_DEMO_COMERCIAL.md`.
- Decisiones del CTO: rol inicial Administrador; 60 minutos sin actividad; tope de 20 demos activas; `DEMO_VENDEDORES` en Vercel; una sola demo activa por vendedor (motivo `reemplazo`).
