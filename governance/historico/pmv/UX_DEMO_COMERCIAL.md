# Demo comercial — especificación UX/UI (DEMO-04)

> **Histórico · sustituido por `PRD_EVYDENTIA` §5.6 y `UX_DEMO_EVYDENTIA.md`.** La demo de EVYDENTIA usa una instancia Cloud SQL propia, protegida por SEC-20 con `entorno_marcador='demo'`. Movido por NEON-04 (2026-11-12) con `git mv`.


UX/UI de EVYDENTIA · 2026-11-06 · Entrada: FLUJOS_DEMO_COMERCIAL.md (§1, §3) del Arquitecto ADPA; PRD Módulo 9.

Principio rector: la demo se ve **igual que el producto real** más dos piezas propias (franja y selector). Nada de demo se pinta si `GET /demo/estado` no responde 200 (404 → componente devuelve `null`).

## 0. Montaje y estado

- `DemoProvider` (cliente) en `app/layout.tsx`: llama `GET /demo/estado` al montar; guarda `{demo, organizacion, persona_activa, personas, minutos_inactividad, ultima_actividad, vence_en}` en un store zustand `useDemo`.
- Interceptor único del cliente HTTP: cualquier respuesta `401 {codigo:"DEMO_VENCIDA"}` → `useDemo.vencer()` → pantalla 4.3. No se trata en cada pantalla.
- La UI **nunca** fija la persona: solo envía `POST /demo/persona {persona_usuario_id}` y adopta la persona que devuelve el servidor (incluido el `X-Role`).
- Prohibido en pantalla: correos (los `.invalid` ni en tooltips), ids, tokens de gobernanza. Se muestra nombre + rol.

## 1. Franja de demostración

- Fija arriba, sobre el `DashboardHeader`, alto 28 px, ancho completo, no se puede cerrar. `role="status"`.
- Fondo ámbar suave (`--aviso-fondo` ≈ #FFF4D6 claro / #3A2E10 oscuro), texto #7A5A00 / #F5D27A. Ámbar = "atención, entorno no real"; no rojo (no es error).
- Izquierda: icono `FlaskConical` + **«Demostración: datos ficticios»** · «Cooperativa Demo».
- Derecha: selector «Ver como» (§2) y botón texto «Terminar demo» (§3).
- Aviso de inactividad (opcional, recomendado): calcular en cliente desde `vence_en`. A falta de ≤ 5 min, la franja añade «Se cerrará por inactividad en 4 min» y un enlace «Seguir» (cualquier GET liviano, p. ej. `/demo/estado`, que renueva actividad). No mostrar cuenta regresiva permanente: distrae la venta.
- Móvil (< 640 px): solo icono + «Demo», selector compacto (avatar con iniciales) y menú «⋯» con «Terminar demo».

## 2. Selector «Ver como»

Disparador (en la franja): `Ver como: <Nombre> · <Rol>` con avatar de iniciales coloreado por rol y chevron.

Panel desplegable (popover 320 px, accesible por teclado, `aria-haspopup="listbox"`):

```
Ver la plataforma como…
───────────────────────────────────────
● Ana Torres        Administradora      ✓
  Configura la organización y las personas.
○ Luis Paredes      Coordinador
  Asigna tareas y aprueba el avance.
○ Marta Ríos        Implementadora
  Ejecuta controles y sube evidencia.
○ Diego Salas       DPO
  Diagnostica, prioriza y valida el cumplimiento.
───────────────────────────────────────
Sugerencia de recorrido: DPO → Implementador → Coordinador
```

- Orden fijo: Administrador, Coordinador, Implementador, DPO (el que dé el servidor en `personas`; si llega desordenado, ordenar por rol). Texto del rol = `rol_etiqueta`; la línea descriptiva sale de un diccionario por rol en el frontend (copy arriba, validar con el DPO de producto).
- La línea «Sugerencia de recorrido» es clicable: cambia a DPO.
- **Cambiando**: al elegir, el ítem muestra spinner, el resto se deshabilita; tras 200 OK, toast neutro «Ahora ves la plataforma como Coordinador» y recarga de la vista actual (revalidar SWR / `router.refresh()`). Si la vista actual no existe para ese rol (403 de rbac), redirigir a la pantalla inicial del rol, sin mostrar error.
- **Error 403 DEMO_PERSONA_AJENA**: el panel queda abierto, mensaje en línea bajo la lista (rojo, icono `AlertCircle`): «Esa persona no pertenece a tu demostración.» + botón «Actualizar» (vuelve a pedir `/demo/estado`). La persona activa no cambia.
- Otros errores de red: «No se pudo cambiar de persona. Intenta de nuevo.»

## 3. Terminar demo

- Botón tipo texto en la franja (no primario: no es la acción que se vende).
- Diálogo de confirmación (modal 420 px):
  - Título: **«¿Terminar la demostración?»**
  - Cuerpo: «La demostración se cierra ahora y sus datos se eliminan esta noche. No podrás volver a abrirla.»
  - Botones: «Cancelar» (secundario, foco inicial) · «Terminar demo» (destructivo).
- Al confirmar: botón con spinner «Terminando…» → `POST /demo/terminar` → cerrar sesión Google → `/login?demo=terminada` → aviso en la entrada (texto aprobado por el CTO, literal): «La demo se cerró y sus datos se eliminan esta noche».
- Si `/demo/terminar` responde 401 DEMO_VENCIDA: tratarlo como éxito (ya estaba cerrada).

## 4. Errores

Una sola plantilla `PantallaDemoMensaje` (centrada, icono, título, una línea, una acción). Sin códigos técnicos visibles; el `codigo` va solo en `data-codigo` para pruebas.

| Código | Dónde | Título | Texto | Acción |
|---|---|---|---|---|
| 403 DEMO_NO_AUTORIZADO | Entrada (en línea bajo el botón Google) | No autorizado para la demo | (texto literal del PRD §9.1.1; sin línea adicional) | «Usar otra cuenta» |
| 409 DEMO_OCUPADA | Entrada (en línea) | Demo ocupada, intenta en unos minutos | (texto literal del PRD §9.1.6; sin línea adicional) | «Reintentar» (deshabilitado 30 s) |
| 401 DEMO_VENCIDA | Pantalla completa, desde cualquier vista | Tu demostración terminó | Se cerró por inactividad o porque abriste una nueva (cada vendedor tiene una sola demo activa, confirmado por el CTO). | «Empezar una nueva» (→ entrada) |

## 5. Entrada

- Pantalla de login existente (`app/login`) con bloque propio cuando hay modo demo: título «Demostración de EVYDENTIA», subtítulo «Recorre la plataforma con una cooperativa ficticia. Nada de lo que hagas afecta datos reales.», botón «Continuar con Google».
- Carga mientras se copia la plantilla (`POST /demo/entrar`, varios segundos): reemplazar el botón por un panel de progreso con pasos simulados (no porcentaje falso): «Preparando Cooperativa Demo…» → «Creando las cuatro personas…» → «Casi listo…» (cambia cada ~2 s; el último se queda). Bloquear doble clic.
- 201 → entrar como Administrador a su pantalla inicial con la franja visible y un toast de bienvenida: «Estás viendo la plataforma como Administradora. Cambia de persona en “Ver como”.»
- Tiempo de espera > 30 s: «Está tardando más de lo normal» + «Reintentar».

## 6. Criterios de aceptación (para Playwright)

1. Sin DEMO_MODE (`/demo/estado` 404): no existe `[data-testid=demo-franja]` ni `[data-testid=demo-ver-como]` en ninguna ruta.
2. Con demo: franja y selector presentes en todas las rutas del tablero.
3. Cambio de persona: tras elegir Coordinador, el disparador muestra «Coordinador» y la siguiente petición lleva el `X-Role` devuelto por el servidor.
4. 403 DEMO_PERSONA_AJENA: el mensaje aparece y la persona activa no cambia.
5. 401 DEMO_VENCIDA en cualquier petición → pantalla «Tu demostración terminó».
6. Terminar: el diálogo no contiene «inmediat»; tras confirmar se llega a la entrada.
7. Ningún texto visible coincide con `/@.*\.invalid/` ni con `/[¤¦]/`.
