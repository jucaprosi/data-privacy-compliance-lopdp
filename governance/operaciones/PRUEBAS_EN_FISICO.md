# PRUEBAS EN FÍSICO — Guía del Propietario (DEV-01)

Esta guía detalla el procedimiento paso a paso para desplegar un entorno de demostración local en modo desarrollo (`AUTH_MODE=headers`), preparar los datos orgánicos mínimos con **un usuario independiente por cada rol** y probar interactivamente en el navegador las capacidades, alcances y restricciones visuales de cada uno.

---

## 1. Alcance y Límites

- **Qué sí cubre esta guía:**
  - Creación reproducible e idempotente de la organización de prueba en su rama Neon propia (`test-rm09` u otra asignada).
  - Levantamiento del backend FastAPI y del frontend Next.js en modo desarrollo con cabeceras explícitas (`headers`).
  - Navegación rol por rol (`admin_organizacion`, `coordinador`, `implementador`, `responsable_area`, `dpo`), verificando lo que cada uno puede y no puede ver/hacer.
- **Qué NO cubre esta guía:**
  - El inicio de sesión real vía Google OIDC (Federated Login). El flujo federado OIDC requiere credenciales OAuth configuradas en Google Cloud Console, DNS o callback local autorizado; para configurar y probar ese mecanismo, consulte [`governance/operaciones/CONFIGURACION_LOGIN_GOOGLE.md`](file:///C:/Users/Juan%20Carlos/Desktop/Plataforma%20LOPDP%20360/governance/operaciones/CONFIGURACION_LOGIN_GOOGLE.md) (y la ficha de OPS-05).
  - Alta pública de organizaciones (eso corresponde al onboarding de ORG-09).

---

## 2. Preparación de la Base de Datos y Creación de la Organización

Abra una consola de **PowerShell** y ejecute los siguientes comandos (cada bloque incluye su respectivo `cd`):

```powershell
cd "C:\Users\Juan Carlos\Desktop\Plataforma LOPDP 360"

# 1. Cargar la URL de su rama Neon de desarrollo desde el archivo local (fuera del repositorio).
# Nunca escriba la URL ni la contraseña en este documento ni en la consola.
$archivo = "C:\Users\Juan Carlos\Desktop\herramientas\rama-test-rm09.txt"
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
$archivo = "C:\Users\Juan Carlos\Desktop\herramientas\rama-test-rm09.txt"
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

Para cambiar de rol en el frontend, modifique las líneas `NEXT_PUBLIC_USER_ID` y `NEXT_PUBLIC_USER_ROLE` en `frontend/.env.local` y refresque el navegador (o reinicie `npm run dev` si Next.js no recarga variables en caliente):

### Rol 1: `admin_organizacion` (Administrador de la Organización)
- **Configuración en `.env.local`:**
  ```env
  NEXT_PUBLIC_USER_ID=usr-demo-admin
  NEXT_PUBLIC_USER_ROLE=admin_organizacion
  ```
- **Ruta principal:** `http://localhost:3000/dashboard` y `http://localhost:3000/organizacion`
- **Qué DEBE ver y poder hacer:**
  - Modificar el tamaño de la organización en la pestaña de configuración (`micro`, `pequena`, `mediana`, `corporativo`).
  - Ver y gestionar el árbol de estructura orgánica (unidades, cargos y jefaturas).
  - Ver las designaciones formales de DPD y Coordinador.
  - Asignar o revocar roles de usuarios.
- **Qué NO debe hacer:**
  - No puede asumir funciones de DPD sin violar SoD.

---

### Rol 2: `coordinador` (Coordinador del Tratamiento)
- **Configuración en `.env.local`:**
  ```env
  NEXT_PUBLIC_USER_ID=usr-demo-coordinador
  NEXT_PUBLIC_USER_ROLE=coordinador
  ```
- **Ruta principal:** `http://localhost:3000/dashboard` y `http://localhost:3000/roadmap`
- **Qué DEBE ver y poder hacer:**
  - Coordinar la implementación general de la LOPDP.
  - Asignar tareas de la Hoja de Ruta a los implementadores.
  - Solicitar acumulación de rol como responsable si la organización y la política SoD lo autorizan.
  - Visualizar el árbol de estructura orgánica y estado de cobertura.
- **Qué NO puede hacer:**
  - No puede editar la configuración del tenant (cambio de tamaño organizacional restringido al admin).

---

### Rol 3: `implementador` (Implementador de Medidas y Controles)
- **Configuración en `.env.local`:**
  ```env
  NEXT_PUBLIC_USER_ID=usr-demo-implementador
  NEXT_PUBLIC_USER_ROLE=implementador
  ```
- **Ruta principal:** `http://localhost:3000/roadmap`
- **Qué DEBE ver y poder hacer:**
  - Ver tareas asignadas en la Hoja de Ruta.
  - Cargar evidencias documentales y técnicas en la Bóveda de Evidencias.
  - Consultar requisitos normativos aplicables a sus tareas.
- **Qué NO puede hacer:**
  - No puede asignar roles ni crear unidades orgánicas.

---

### Rol 4: `responsable_area` (Responsable de Área / Unidad Operativa)
- **Configuración en `.env.local`:**
  ```env
  NEXT_PUBLIC_USER_ID=usr-demo-responsable
  NEXT_PUBLIC_USER_ROLE=responsable_area
  ```
- **Ruta principal:** `http://localhost:3000/roadmap` y `http://localhost:3000/rat`
- **Qué DEBE ver y poder hacer:**
  - Actúa como titular de la jefatura de la «Unidad de Operaciones y Procesos».
  - Ver y validar los inventarios de datos y tratamientos que conciernen exclusivamente a su área funcional acotada.
- **Qué NO puede hacer:**
  - No tiene visibilidad sobre áreas operativas no asignadas ni puede designar delegados.

---

### Rol 5: `dpo` (Delegado de Protección de Datos / DPD)
- **Configuración en `.env.local`:**
  ```env
  NEXT_PUBLIC_USER_ID=usr-demo-dpo
  NEXT_PUBLIC_USER_ROLE=dpo
  ```
- **Ruta principal:** `http://localhost:3000/dashboard`, `http://localhost:3000/organizacion/designaciones`, `http://localhost:3000/arco`
- **Qué DEBE ver y poder hacer:**
  - Ver su designación formal activa bajo el Art. 49 del Reglamento General.
  - Registrar declaraciones previas de conflictos de interés y aceptación.
  - Supervisar en modo **solo lectura / auditoría** el árbol orgánico y las solicitudes ARCO.
  - Emitir observaciones motivadas sobre solicitudes de excepción SoD.
- **Qué NO puede hacer (Incompatibilidad Estricta):**
  - No puede tener ningún otro rol simultáneo en el mismo tenant.
  - No puede ejercer jefaturas de unidades operativas ni cargos de administración/control.
  - Cualquier intento de asignarle funciones de ejecución operativa es rechazado automáticamente por la compuerta con código 400/409.

---

## 6. Verificación de Idempotencia Automatizada

Si desea volver a inicializar o verificar el estado de los datos en cualquier momento sin perder la consistencia:

```powershell
cd "C:\Users\Juan Carlos\Desktop\Plataforma LOPDP 360"
.\.venv\Scripts\python.exe -m pytest tests\test_crear_organizacion_dev.py -v
```

Todas las pruebas deben concluir en verde (**PASSED**).
