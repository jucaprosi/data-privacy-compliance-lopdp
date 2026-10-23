# PRUEBAS EN FÍSICO — Guía del Propietario (DEV-01)

Esta guía detalla el procedimiento paso a paso para desplegar un entorno de demostración local en modo desarrollo (`AUTH_MODE=headers`), preparar los datos orgánicos mínimos con **un usuario independiente por cada rol** y probar interactivamente en el navegador las capacidades, alcances y restricciones visuales de cada uno.

---

## 1. Alcance y Límites

- **Qué sí cubre esta guía:**
  - Creación reproducible e idempotente de la organización de prueba en una rama Neon propia para pruebas en físico (`pruebas-fisicas`, hija de `test`; nunca `production` ni `test`).
  - Levantamiento del backend FastAPI y del frontend Next.js en modo desarrollo con cabeceras explícitas (`headers`).
  - Navegación rol por rol (`admin_organizacion`, `coordinador`, `implementador`, `responsable_area`, `dpo`), verificando lo que cada uno puede y no puede ver/hacer.
- **Qué NO cubre esta guía:**
  - El inicio de sesión real vía Google OIDC (Federated Login). El flujo federado OIDC requiere credenciales OAuth configuradas en Google Cloud Console, DNS o callback local autorizado; para configurar y probar ese mecanismo, consulte [`governance/operaciones/CONFIGURACION_LOGIN_GOOGLE.md`](file:///C:/Users/Juan%20Carlos/Desktop/Plataforma%20LOPDP%20360/governance/operaciones/CONFIGURACION_LOGIN_GOOGLE.md) (y la ficha de OPS-05).
  - El operador de la plataforma se prueba aparte, en la sección 5 bis.

---

## 2. Preparación de la Base de Datos y Creación de la Organización

Abra una consola de **PowerShell** y ejecute los siguientes comandos (cada bloque incluye su respectivo `cd`):

```powershell
cd "C:\Users\Juan Carlos\Desktop\Plataforma LOPDP 360"

# 1. Cargar la URL de su rama Neon de desarrollo desde el archivo local (fuera del repositorio).
# Nunca escriba la URL ni la contraseña en este documento ni en la consola.
$archivo = "C:\Users\Juan Carlos\Desktop\herramientas\rama-pruebas-fisicas.txt"
$linea = Get-Content $archivo -Encoding UTF8 | Where-Object { $_ -match 'TEST_DATABASE_URL=' } | Select-Object -First 1
$env:TEST_DATABASE_URL = ($linea -replace '^.*?TEST_DATABASE_URL=', '').Trim().Trim('"')
if ($env:TEST_DATABASE_URL -match 'ep-late-hall-b50bpbk5') { throw "Esa URL es de producción: abortado." }
$env:DATABASE_URL = $env:TEST_DATABASE_URL
$env:AUTH_MODE = "headers"

# 2. Asegurar que las migraciones estén al día (cabeza única)
.\.venv\Scripts\alembic.exe upgrade head

# 3. Ejecutar el script generador de la organización demo
.\.venv\Scripts\python.exe scripts\crear_organizacion_dev.py
```

> **Nota:** El script es **estrictamente idempotente**. Puede ejecutarlo tantas veces como desee y nunca duplicará registros ni arrojará errores de restricción única.
> Cuenta con **fallo cerrado**: si detecta el host de producción (`ep-late-hall-b50bpbk5`) o si `AUTH_MODE != 'headers'`, abortará de forma inmediata sin tocar la base.

---

## 3. Configuración del Frontend (`frontend/.env.local`)

El script `scripts/crear_organizacion_dev.py` imprime al finalizar los identificadores exactos. Para configurar su entorno frontend:

Abra o cree el archivo `frontend/.env.local`:

```env
NEXT_PUBLIC_AUTH_MODE=headers
NEXT_PUBLIC_TENANT_ID=tenant-corp-demo
NEXT_PUBLIC_API_URL=http://localhost:5000/api/v1
```

Añada las variables del usuario con el que desea interactuar en el navegador (consulte la sección 5 para alternar entre roles).

---

## 4. Arranque de los Servidores de Desarrollo

Requiere dos terminales de PowerShell abiertas en paralelo:

### Terminal 1 — Backend (FastAPI):
```powershell
cd "C:\Users\Juan Carlos\Desktop\Plataforma LOPDP 360"
# Cargar la URL de su rama Neon de desarrollo desde el archivo local (fuera del repositorio).
# Nunca escriba la URL ni la contraseña en este documento ni en la consola.
$archivo = "C:\Users\Juan Carlos\Desktop\herramientas\rama-pruebas-fisicas.txt"
$linea = Get-Content $archivo -Encoding UTF8 | Where-Object { $_ -match 'TEST_DATABASE_URL=' } | Select-Object -First 1
$env:TEST_DATABASE_URL = ($linea -replace '^.*?TEST_DATABASE_URL=', '').Trim().Trim('"')
if ($env:TEST_DATABASE_URL -match 'ep-late-hall-b50bpbk5') { throw "Esa URL es de producción: abortado." }
$env:DATABASE_URL = $env:TEST_DATABASE_URL
$env:AUTH_MODE = "headers"

.\.venv\Scripts\python.exe main.py
# El backend quedará escuchando en http://127.0.0.1:5000
```

### Terminal 2 — Frontend (Next.js):
```powershell
cd "C:\Users\Juan Carlos\Desktop\Plataforma LOPDP 360\frontend"
npm run dev
# El frontend quedará escuchando en http://localhost:3000
```

---

## 5. Matriz de Roles y Pruebas en el Navegador

> **Revisado por el coordinador el 2026-10-22.** La versión anterior citaba rutas que no existen (`/organizacion`, `/roadmap`, `/rat`, `/arco`, `/organizacion/designaciones`) y atribuía permisos que contradicen el PRD §5.2 (por ejemplo, que el implementador sube evidencias). Lo que sigue se ha contrastado con el código del frontend y con la matriz de permisos; lo que no se ha comprobado en pantalla está marcado como «no verificado».

**Dónde está cada cosa.** Todo se hace en `http://localhost:3000/dashboard`. El menú lateral tiene los módulos («Hoja de Ruta», «RAT Maestro», «Derechos ARCO+», «Bóveda Evidencias», «Cockpit DPD / DPO», entre otros). Dentro de **«Hoja de Ruta»** hay pestañas que dependen del rol:

| Pestaña | Quién la ve | Qué hay |
| :-- | :-- | :-- |
| Olas & Tareas | todos | La hoja de ruta generada: olas y tareas (el responsable de área, solo las de su área). |
| Generar Hoja de Ruta | `implementador` | El formulario para **generar** la hoja de ruta con IA. |
| Administración | `admin_organizacion` | Usuarios, Áreas, Roles, Estructura y Configuración. |
| Custodia de Evidencias | según la tarea elegida | Subir, ver y validar evidencias de una tarea. |

Para cambiar de rol, modifique `NEXT_PUBLIC_USER_ID` y `NEXT_PUBLIC_USER_ROLE` en `frontend/.env.local` y reinicie `npm run dev`.

| Rol | `NEXT_PUBLIC_USER_ID` | `NEXT_PUBLIC_USER_ROLE` |
| :-- | :-- | :-- |
| Administrador de la organización | `usr-demo-admin` | `admin_organizacion` |
| Coordinador | `usr-demo-coordinador` | `coordinador` |
| Implementador | `usr-demo-implementador` | `implementador` |
| Responsable de área (Operaciones) | `usr-demo-responsable` | `responsable_area` |
| Delegado de protección de datos | `usr-demo-dpo` | `dpo` |

### Qué puede hacer cada rol (PRD §5.2)

| Acción | Responsable de área | Coordinador | DPO | Implementador | Administrador |
| :-- | :-: | :-: | :-: | :-: | :-: |
| Ver diagnóstico y hoja de ruta | su área | ✅ | ✅ | ✅ | ✅ |
| Generar la hoja de ruta con IA | ❌ | ❌ | ❌ | ✅ | ❌ |
| Editar tareas y marcarlas completadas | ❌ | ❌ | ❌ | ✅ | ❌ |
| Distribuir tareas a responsables de área | ❌ | ✅ | ❌ | ❌ | ❌ |
| Subir evidencia | ✅ | solo si no hay responsables | ❌ | ❌ | ❌ |
| Validar o rechazar evidencia | ❌ | ✅ | ✅ | ✅ | ❌ |
| Ver toda la evidencia | solo la suya | ✅ | ✅ | ✅ | ✅ |
| Ver el registro de auditoría | ❌ | ✅ | ✅ | ✅ | ✅ |
| Gestionar usuarios | ❌ | solo solicita altas | ❌ | ❌ | ✅ |
| Asignar y revocar roles | ❌ | ❌ | ❌ | ❌ | ✅ |
| Configurar la organización (tamaño y sector) | ❌ | ❌ | ❌ | ❌ | ✅ |
| Solicitar el alta de un responsable de área | ❌ | ✅ | ❌ | ❌ | ❌ |
| Aprobar, rechazar y ejecutar esa alta | ❌ | ❌ | ❌ | ✅ | ❌ |

### Recorrido de prueba recomendado (de punta a punta)
1. **Implementador** → «Hoja de Ruta» → Generar Hoja de Ruta: generar la hoja de ruta (requiere `DEEPSEEK_API_KEY`).
2. **Coordinador** → «Hoja de Ruta» → Olas & Tareas: asignar una tarea al responsable de Operaciones.
3. **Responsable de área** → la tarea → Custodia de Evidencias: subir un PDF (requiere las variables `R2_*` y que el bucket permita subidas desde `http://localhost:3000`).
4. **Responsable de área** intenta validar su propia evidencia: debe rechazarse (quien sube no valida).
5. **DPO** → la tarea → Custodia de Evidencias: aprobar la evidencia.
6. **Implementador** → marcar la tarea como completada.

### Bloqueos que conviene comprobar
- Al **administrador**, en Administración → Roles: dar al DPO cualquier otro rol → **409** (independencia del delegado).
- Al **administrador**, en Administración → Roles: dar `responsable_area` directamente cuando ya hay implementador → **409** que indica el flujo de solicitud (ORG-05).
- Revocar al último administrador de la organización → **409**.

### No verificado en pantalla
- Las designaciones formales del DPD y del coordinador (ORG-06) tienen API, pero no se ha localizado su pantalla.
- El contenido de los módulos «RAT Maestro», «Derechos ARCO+» y «Cockpit DPD / DPO» para cada rol no se ha recorrido.

## 5 bis. Operador de la plataforma (ORG-09, FE-10)

Las pantallas del operador están fuera del dashboard: `http://localhost:3000/plataforma` (organizaciones e invitaciones) y `http://localhost:3000/invitacion` (aceptación).

1. Dese de alta como operador **en su rama de pruebas** (nunca en producción con esta guía):

```powershell
cd "C:\Users\Juan Carlos\Desktop\Plataforma LOPDP 360"
$archivo = "C:\Users\Juan Carlos\Desktop\herramientas\rama-pruebas-fisicas.txt"
$linea = Get-Content $archivo -Encoding UTF8 | Where-Object { $_ -match 'TEST_DATABASE_URL=' } | Select-Object -First 1
$env:MIGRATION_DATABASE_URL = ($linea -replace '^.*?TEST_DATABASE_URL=', '').Trim().Trim('"')
if ($env:MIGRATION_DATABASE_URL -match 'ep-late-hall-b50bpbk5') { throw "Esa URL es de producción: abortado." }
.\.venv\Scripts\python.exe -m features.plataforma.administrar_operadores alta "operador@example.test" "Operador de pruebas"
Remove-Item Env:MIGRATION_DATABASE_URL
```

2. En `frontend/.env.local`, para actuar como operador en modo `headers`:

```env
NEXT_PUBLIC_USER_ID=operador-pruebas
NEXT_PUBLIC_USER_EMAIL=operador@example.test
```

3. En `/plataforma`, cree una organización con el correo de administrador `admin-nuevo@example.test`; copie el código (se muestra una sola vez).
4. Cambie `NEXT_PUBLIC_USER_EMAIL` a `admin-nuevo@example.test`, reinicie `npm run dev` y acepte el código en `/invitacion`. Con otro correo la aceptación debe rechazarse (403).

---

## 6. Verificación de Idempotencia Automatizada

Si desea volver a inicializar o verificar el estado de los datos en cualquier momento sin perder la consistencia:

```powershell
cd "C:\Users\Juan Carlos\Desktop\Plataforma LOPDP 360"
# En la misma ventana en la que cargó TEST_DATABASE_URL desde rama-pruebas-fisicas.txt (sección 2)
.\.venv\Scripts\python.exe -m pytest tests\test_crear_organizacion_dev.py -v
```

Todas las pruebas deben concluir en verde (**PASSED**).
