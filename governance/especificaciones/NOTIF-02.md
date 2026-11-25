# NOTIF-02 · Avisos y recordatorios de versiones por revisar
`¤sdd` `¤arbitro`

## 1. Datos

Hechos medidos en `origin/main` ed575cd2:
- No hay avisos en la plataforma: en el frontend solo existe `AvisoEntorno.tsx`.
- El puerto `Notificador` solo tiene `NotificadorFalso` y `NotificadorNoConfigurado` (`services/adaptadores.py`): no hay proveedor de correo activo.
- La sala no tiene rama de Alembic. Esta es su primera migración, que cuelga de `BASE_COMUN` con `branch_labels = ("notificaciones",)`.
- Los routers se registran por secciones marcadas en `main.py`, y los menús, pantallas y la cabecera por secciones en `menus/index.ts`, `pantallas/index.tsx` y `DashboardHeader.tsx`.

Tabla `avisos_plataforma`: `id`, `usuario_id` (→ `users`), `tipo` (`version_por_revisar`), `referencia` (id de la versión), `titulo`, `texto`, `enlace`, `leido_en` nulo, `pendiente` boolean, `recordatorios_enviados` entero, `proximo_recordatorio` nulo, `creado_en` y `actualizado_en`. UNIQUE (`usuario_id`, `tipo`, `referencia`). RLS: cada persona lee y marca solo los suyos. La tabla se añade a `TABLAS_POR_SALA` como de `notificaciones`.

## 2. API

En `api/routers/avisos.py`, para cualquier persona con sesión:
- `GET /avisos?filtro=sin_leer|todos&antes=<cursor>`: los 50 más recientes, con `{id, titulo, texto, enlace, leido, pendiente, creado_en}` y el número sin leer.
- `POST /avisos/{id}/leido`.
- `POST /avisos/sincronizar`: la ejecución programada, para un operador, como `disparar_por_el_job` de NORM-05.

## 3. Reglas

- **R1 · Origen del aviso.** `sincronizar` lee por `app_core/pasillo/biblioteca.py` las versiones `en_revision` (`versiones_en_revision()`, con plantilla, origen e `id_resolucion`) y, por el pasillo normativo, `fecha_vigencia_de` (NORM-07). Crea un aviso por versión y por persona con `revisor_tecnico` vigente, sin duplicar (UNIQUE).
- **R2 · Texto.** Título «Versión por revisar: {plantilla}». Texto «Motivo: {norma}, que entra en vigencia el {fecha}.», o «…que entró en vigencia el {fecha}.» si ya pasó, o «La norma no indica fecha de vigencia.». Si el origen es una petición: «Motivo: petición de {nombre}.». Enlace «Revisar la versión», al detalle de BIB-408.
- **R3 · Recordatorios (D3).** Con fecha, a 7 días y a 1 día de la vigencia; si al nacer faltan menos de 7 días, solo el de 1 día. Si la fecha ya pasó o no hay fecha, uno cada 7 días, con un máximo de 3. Un recordatorio no crea un aviso nuevo: actualiza el mismo, lo deja sin leer y añade «Faltan {n} días.».
- **R4 · Fin.** Cuando la versión deja de estar `en_revision` (aprobada, devuelta o descartada), el aviso pasa a `pendiente = false`, sin enlace, con «Ya no está pendiente», y se cancelan sus recordatorios.
- **R5 · Palabras.** Sin «conforme», «cumple», «garantiza», «certificado» ni «legal», y sin nombres de proveedores.
- **R6 · Correo.** No se promete correo: lo entrega una ficha posterior cuando haya proveedor (D7).
- **R-SP · Sin prohibiciones** (GEN-01 R3).
- **R-ADPA · Ortogonalidad ZERAG (`NOTIF-02`).** Solo los archivos de la propiedad. Otras salas se usan solo por sus pasillos (`app_core/pasillo/`). Las pruebas no usan `import yaml`.

## 4. Interfaz

Propuesta del UX/UI (2026-11-25):
- **Cabecera** (`DashboardHeader.tsx#NOTIF-02`): un botón con icono de campana y `aria-label` «Avisos, {n} sin leer», o «Avisos» si no hay ninguno sin leer. Con {n} > 0, una insignia con el número, visible sin color. Lleva a Inicio › Avisos. Sin panel flotante.
- **Inicio › Avisos** (submenú «Avisos» del menú Inicio): h2 «Avisos»; pestañas «Sin leer» y «Todos» (patrón tablist); lista `<ul>` con h3 de título, texto, `<time>` relativo, enlace de acción y botón «Marcar como leído». Al seguir el enlace, el aviso queda leído. Un aviso sin leer lleva el texto oculto «Sin leer». Vacío: «No tienes avisos sin leer.» o «No tienes avisos.», como `role=status`. Error: «No pudimos cargar tus avisos. Inténtalo de nuevo.», con «Reintentar». 50 avisos y «Ver más».

## 5. Aceptación

| Caso | Árbitro |
| :--- | :--- |
| **Dado** una versión `en_revision` de la IA y dos personas con `revisor_tecnico`, **entonces** `sincronizar` crea dos avisos, y al repetirlo no crea más. Mutación m1: quitar el UNIQUE da rojo. | `tests/test_notif02_avisos.py` |
| **Dado** una vigencia a 10 días, **entonces** hay recordatorios a 7 y a 1 día; a 5 días, solo a 1 día; sin fecha, cada 7 días hasta 3. Mutación m2: un cuarto recordatorio sin fecha da rojo. | ídem |
| **Dado** una versión publicada, **entonces** su aviso queda `pendiente = false` y sin enlace. Mutación m3: dejar el enlace da rojo. | ídem |
| **Dado** otra persona, **entonces** no lee ni marca avisos ajenos (RLS). Mutación m4: quitar la política da rojo. | ídem |
| **Dado** un aviso sin leer, **entonces** la cabecera dice «Avisos, 1 sin leer»; «Marcar como leído» lo saca de «Sin leer»; con un 500 se ven el error y «Reintentar»; a 375 px no hay desplazamiento horizontal. | `frontend/tests/avisos/bandeja.spec.ts` |
| **Dado** el grafo, **entonces** la sala tiene una sola cabeza y solo importa otras salas por sus pasillos. | `tests/test_alembic_cabeza_por_sala.py`, `tests/test_adpa_bulkhead.py` |

## 6. Trazabilidad

- **PRD:** Módulo 7 (Biblioteca) y notificaciones de la plataforma.
- Brief del CTO `ARQUITECTO_UXUI_PROPUESTAS_IA_PLANTILLAS` v1, v2 y v3 (2026-11-25), base `origin/main` ed575cd2, con las decisiones D1 a D7 del CTO y la propuesta de pantallas y textos del UX/UI (2026-11-25).
