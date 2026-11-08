# Biblioteca: Administración editorial en el producto (interfaz, ficha de frontend)

UX/UI de EVYDENTIA · 2026-11-07 · v2: el CTO redujo el alcance. **No hay pantalla para conceder ni revocar**: las capacidades se conceden con el script de desarrollo del Arquitecto, porque `lopdp_app` solo tiene SELECT sobre `biblioteca_capacidades` (`alembic/versions/20261025_biblioteca_base.py:116`).

Base: `origin/main` 5499287. PRD «Biblioteca C».

Fichas:
- frontend: **BIB-120** (provisional);
- backend: **BIB-117** (provisional, del Arquitecto).

## 1. Ruta y entrada de menú

- **Entrada:** menú «Biblioteca», segundo submenú, con el nombre «Administración editorial» y el subtítulo «Versiones maestras, revisiones y publicación».
- **Vista:** `biblioteca_editorial`, montada en `app/dashboard/page.tsx` como las demás vistas. No hay ruta nueva bajo `app/`.
- `harness-biblioteca/editorial` se queda solo para pruebas.

**Visibilidad.** El submenú se pinta solo si la persona tiene al menos una capacidad editorial.
- **Fuente preferida:** un GET ligero de solo lectura en BIB-117, `GET /api/v1/biblioteca/editorial/capacidades` → `{capacidades: string[]}` (ruta fijada con el Arquitecto; el CTO decide si se usa o se reutiliza la respuesta editorial). Usa el SELECT y la política `bib_cap_propia`, que ya existen.
- **Fuente de respaldo**, si BIB-117 no lo da: `GET /api/v1/biblioteca/editorial` (`listarEditorial`), que ya devuelve `capacidades`. Un 403 o una lista vacía ocultan el submenú. No conviene para el menú porque trae hasta 200 versiones en cada carga del tablero.
- Mientras carga, si hay error o si la lista está vacía, no se pinta. Es solo comodidad: la autorización sigue en el servidor.
- **Estado vacío**, si alguien abre la vista sin capacidades (por ejemplo, porque se las revocaron con la sesión abierta): «No tienes permisos editoriales en la Biblioteca. Los asigna el equipo de la plataforma.»

## 2. «Mis permisos editoriales» (solo lectura): sí encaja

No es una vista aparte: es una **franja de cabecera dentro de la Administración editorial**. Así no se suma otra entrada al menú para mostrar cuatro valores.

```
Tus permisos editoriales   [Editor] [Revisor técnico]
Recuerda: no puedes revisar ni publicar las versiones que tú creaste.
```

- Etiquetas de los cuatro permisos: Editor, Revisor técnico, Revisor jurídico y Publicador. Solo se muestran los que la persona tiene.
- Al pasar el cursor o enfocar cada etiqueta, una línea dice qué permite:
  - Editor: crea versiones y carga el archivo maestro.
  - Revisor técnico: aprueba o rechaza el contenido técnico.
  - Revisor jurídico: aprueba o rechaza el contenido jurídico.
  - Publicador: publica o retira versiones con ambas revisiones aprobadas.
- La línea «Recuerda…» solo aparece si la persona tiene el permiso de Editor y además alguno de los otros tres.
- Reemplaza el párrafo actual «Permisos editoriales: …».

## 3. Ajustes de presentación de `AdministracionEditorial.tsx` (sin cambiar su lógica)

- Usar los tokens del tema en lugar de `bg-purple-700`, `text-zinc-100` y `border-red-500`.
- `h-dvh` y `overflow-y-auto` pasan al contenedor de la vista: dentro del tablero, la pantalla no ocupa todo el alto de la ventana.
- Hoy se muestran `responsable_id` y `revisor_id`. Si BIB-117 agrega nombres, se muestran los nombres. Si no, se mantienen los ids y se anota como deuda (cambio de datos, fuera de esta ficha).
- Mensajes nuevos del estado vacío y de la cabecera: §1 y §2. Los textos que ya existen se conservan.

## 4. Accesibilidad para Playwright (rol y nombre)

| Elemento | Rol | Nombre accesible |
|---|---|---|
| Submenú | el que use `MenuLateral` para los submenús (hoy `button`) | Administración editorial |
| Vista | `main` (ya existe) | Administración editorial |
| Cabecera de permisos | `region` | Tus permisos editoriales |
| Lista de etiquetas | `list` | Tus permisos editoriales |
| Cada etiqueta | `listitem` | Editor / Revisor técnico / Revisor jurídico / Publicador |
| Estado vacío | `status` | No tienes permisos editoriales en la Biblioteca. Los asigna el equipo de la plataforma. |

No cambian los nombres que ya existen: «Actualizar listado», «Crear versión en revisión», «Versiones maestras», «Detalle editorial», «Registrar revisión técnica», «Registrar revisión jurídica», «Motivo de la decisión», «Publicar versión», «Retirar versión», «Preparar versión sustituta» e «Historial editorial». Así `frontend/tests/biblioteca/editorial.spec.ts` sigue valiendo.

**Criterios de prueba:**
1. Sin capacidades, el submenú no existe.
2. Con «editor», el submenú existe y la cabecera muestra solo «Editor».
3. Con editor y revisor técnico, aparece la línea «Recuerda…».
4. Si la vista se abre con 403, se muestra el estado vacío.
5. Las pruebas de `editorial.spec.ts` siguen en verde.

## 5. Propiedad de archivos (BIB-120), versión enviada al CTO

Crea:
- `frontend/src/components/layout/menus/BIB-120.ts`: submenú y `declare module` de `biblioteca_editorial`.
- `frontend/src/components/layout/pantallas/BIB-120.tsx`: registra la vista en `PANTALLAS` y monta `AdministracionEditorial` en su contenedor.
- `frontend/src/lib/biblioteca/capacidadesEditoriales.ts`: `leerMisCapacidades()`. Si existe, usa `GET /api/v1/biblioteca/editorial/capacidades`; si no, usa `listarEditorial`. En los dos casos, un 403 `BIB_SIN_CAPACIDAD` o un error devuelven `[]`.
- `frontend/tests/biblioteca/editorial-menu.spec.ts`.

Visibilidad con un predicado en el submenú (acordado con el Arquitecto): el submenú no aparece mientras carga ni con la lista vacía, y tampoco en Ctrl+K.

Secciones `// === BIB-120 === … // === fin BIB-120 ===`:
- `frontend/src/components/layout/menus/index.ts`: registro.
- `frontend/src/components/layout/pantallas/index.tsx`: registro.
- `frontend/src/components/layout/menus/base.ts`: campo opcional `visible?: (ctx: ContextoVisibilidad) => boolean` en `Submenu` y tipo `ContextoVisibilidad { capacidadesEditoriales: readonly string[] | null }`, donde `null` significa que sigue cargando. Es un punto de extensión genérico, no exclusivo de BIB-120.
- `frontend/src/components/layout/dashboardNavigation.ts`: `vistasPermitidas` recibe `ctx` y descarta los submenús cuyo `visible(ctx)` sea falso.
- `frontend/src/app/dashboard/page.tsx`: carga las capacidades con `leerMisCapacidades()` y pasa `ctx` a las dos llamadas de `vistasPermitidas` (~l.163 y ~l.195).
- `frontend/src/components/CommandPalette.tsx`: filtra `SUBMENUS` con el mismo predicado (recibe `ctx` por prop o reutiliza `vistasPermitidas`).

`menus/BIB-120.ts` declara `visible: (c) => (c.capacidadesEditoriales?.length ?? 0) > 0`.

Ajusta: `frontend/src/components/biblioteca/editorial/AdministracionEditorial.tsx` (§2 y §3).

Fuera de esta ficha: `MenuLateral.tsx` (solo presenta lo que recibe) y el backend.

## 6. Lo que pide a BIB-117 (backend)

1. `GET /api/v1/biblioteca/editorial/capacidades` → `{capacidades: [...]}`. Responde 200 aunque la lista esté vacía, nunca 403, para que el menú no tenga que interpretar errores.
2. Nombres junto a `responsable_id` y `revisor_id` en `VistaEditorial` (el Arquitecto lo confirmó sin choque).
