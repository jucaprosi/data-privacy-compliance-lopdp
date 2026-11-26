# NOTIF-02 · Avisos y recordatorios de versiones por revisar
`¤sdd` `¤arbitro`

## 1. Datos

Hechos medidos en `origin/main` ed575cd2:
- No hay avisos en la plataforma: en el frontend solo existe `AvisoEntorno.tsx`.
- El puerto `Notificador` solo tiene `NotificadorFalso` y `NotificadorNoConfigurado` (`services/adaptadores.py`): no hay proveedor de correo activo.
- La sala no tiene rama de Alembic. Esta es su primera migración, que cuelga de `BASE_COMUN` con `branch_labels = ("notificaciones",)`.
- Los routers se registran por secciones marcadas en `main.py`, y los menús, pantallas y la cabecera por secciones en `menus/index.ts`, `pantallas/index.tsx` y `DashboardHeader.tsx`.

Tabla `avisos_plataforma`: `id`, `usuario_id` (→ `users`), `tipo` (`version_por_revisar`), `referencia` (id de la versión), `titulo`, `texto`, `enlace`, `leido_en` nulo, `pendiente` boolean, `recordatorios_hechos` entero, `proximo_recordatorio` nulo, `creado_en` y `actualizado_en`. UNIQUE (`usuario_id`, `tipo`, `referencia`). RLS: cada persona lee y marca solo los suyos. La tabla se añade a `TABLAS_POR_SALA` como de `notificaciones`.

## 2. API

En `api/routers/avisos.py`, para cualquier persona con sesión:
- `GET /avisos?filtro=sin_leer|todos&antes=<cursor>`: los 50 más recientes, con `{id, titulo, texto, enlace, leido, pendiente, creado_en}` y el número sin leer.
- `POST /avisos/{id}/leido`.
- `POST /avisos/sincronizar`: la ejecución programada, para un operador, como `disparar_por_el_job` de NORM-05.

## 3. Reglas

- **R1 · Origen del aviso.** `sincronizar` lee por `app_core/pasillo/biblioteca.py` las versiones `en_revision` (`versiones_en_revision()`, con plantilla, origen e `id_resolucion`) y a quienes tienen `revisor_tecnico` vigente (`revisores_tecnicos()`), con las funciones de lectura de BIB-415, porque el operador que ejecuta `sincronizar` no tiene capacidades de biblioteca y, por el pasillo normativo, `fecha_vigencia_de` (NORM-07). Crea un aviso por versión y por cada una de esas personas, sin duplicar (UNIQUE).
- **R2 · Texto** (UX/UI, 2026-11-25). Es la única fuente de los textos del aviso; el correo de NOTIF-03 los reutiliza. Título «Versión por revisar: {plantilla}». Enlace «Revisar la versión», al detalle de BIB-408. Línea de motivo, una sola según el caso:
  - resolución con fecha futura: «Motivo del cambio: {norma}, {artículo}, que entra en vigencia el {fecha}.»;
  - resolución que entra en vigencia hoy: «Motivo del cambio: {norma}, {artículo}, que entra en vigencia hoy.»;
  - resolución con fecha pasada: «Motivo del cambio: {norma}, {artículo}, que entró en vigencia el {fecha}.»;
  - resolución sin fecha: «Motivo del cambio: {norma}, {artículo}. La norma no indica fecha de vigencia.»;
  - petición: con texto, «Motivo del cambio: petición de {nombre}: «{texto}».»; sin texto, «Motivo del cambio: petición de {nombre}.». Sin norma, artículo ni fecha. El texto se corta a 200 caracteres, con «…» si se corta, y va como texto plano, nunca como formato ni enlace.
  - Sin {artículo}, se quita «, {artículo}» entero. Ningún campo se imprime vacío ni como «None»: si un dato falta, se usa la variante que no lo nombra.
  - {fecha} va en largo y en español, sin cero a la izquierda en el día («5 de diciembre de 2026»), en hora de Ecuador y sin hora; «hoy» también se calcula en hora de Ecuador.
- **R3 · Recordatorios (D3).**
  - Con fecha futura: a 7 días y a 1 día de la vigencia; si al nacer el aviso faltan menos de 7 días, solo el de 1 día. Texto: «La norma que motiva el cambio entra en vigencia el {fecha} (faltan {n} días).», con «(falta 1 día)» si {n} = 1, o «La norma que motiva el cambio entra en vigencia hoy.».
  - Sin fecha, con fecha pasada o por petición: a los 5 y a los 10 días de la creación del aviso. Texto: «Sigue sin revisión técnica desde hace {n} días.», con «desde hace 1 día» si {n} = 1.
  - Un recordatorio no crea un aviso nuevo: actualiza el mismo, lo deja sin leer y añade su texto. Los recordatorios se detienen al revisar la versión o al descartarla (R4).
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
| **Dado** una vigencia a 10 días, **entonces** hay recordatorios a 7 y a 1 día; a 5 días, solo a 1 día; sin fecha, con fecha pasada o por petición, a los 5 y a los 10 días de la creación, y ninguno más. Mutación m2: un tercer recordatorio sin fecha da rojo. | ídem |
| **Dado** cada variante de R2 y R3 (fecha futura, hoy, pasada, sin fecha, sin artículo, petición con y sin texto, y recordatorios con {n} = 1 y {n} > 1), **entonces** el texto es el de R2 o R3 y no contiene «undefined», «null», «None», «{», «}», «, ,» ni dos espacios seguidos. Mutación m5: dejar «, ,» al faltar el artículo da rojo. Mutación m6: «faltan 1 días» da rojo. Mutación m7: una petición de 300 caracteres sin cortar da rojo. | ídem |
| **Dado** una versión publicada, **entonces** su aviso queda `pendiente = false` y sin enlace. Mutación m3: dejar el enlace da rojo. | ídem |
| **Dado** otra persona, **entonces** no lee ni marca avisos ajenos (RLS). Mutación m4: quitar la política da rojo. | ídem |
| **Dado** un aviso sin leer, **entonces** la cabecera dice «Avisos, 1 sin leer»; «Marcar como leído» lo saca de «Sin leer»; con un 500 se ven el error y «Reintentar»; a 375 px no hay desplazamiento horizontal. | `frontend/tests/avisos/bandeja.spec.ts` |
| **Dado** el grafo, **entonces** la sala tiene una sola cabeza y solo importa otras salas por sus pasillos. | `tests/test_alembic_cabeza_por_sala.py`, `tests/test_adpa_bulkhead.py` |

## 6. Trazabilidad

- **PRD:** Módulo 7 (Biblioteca) y notificaciones de la plataforma.
- Brief del CTO `ARQUITECTO_UXUI_PROPUESTAS_IA_PLANTILLAS` v1, v2 y v3 (2026-11-25), base `origin/main` ed575cd2, con las decisiones D1 a D7 del CTO y la propuesta de pantallas y textos del UX/UI (2026-11-25).
