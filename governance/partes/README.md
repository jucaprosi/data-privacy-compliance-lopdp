# Partes de cierre

Un **parte** es el registro de la sesión para que otro agente tome la posta: la nota corta con la que un rol deja el estado de su trabajo para quien lo retome (otra sesión del mismo rol, otro rol o el propietario). Quien retoma lee primero el último parte de la carpeta de su rol. No sustituye al PRD, a los invariantes ni a las fichas: no es fuente normativa. Si un parte y una ficha se contradicen, manda la ficha.

## Dónde y cómo se llaman
- Carpeta: una por rol dentro de `governance/partes/` (decisión del propietario, 2026-11-12). Cada rol guarda sus partes **solo en la suya**; no se crean otras carpetas de partes ni se dejan partes sueltos en `governance/partes/`.

  | Rol | Carpeta |
  | :--- | :--- |
  | CTO | `governance/partes/cto/` |
  | Tech Lead | `governance/partes/tech-lead/` |
  | Arquitecto ADPA | `governance/partes/arquitecto/` |
  | UX/UI | `governance/partes/ux-ui/` |

  Un rol nuevo crea su carpeta con el mismo nombre que usa en el archivo, en minúsculas y con guion en lugar de espacios.
- Archivo: `AAAA-MM-DD_<TEMA>.md`, donde el tema es lo más relevante que se cerró o quedó por cerrar en la sesión, para poder identificar el parte y saber dónde buscar (decisión del propietario, 2026-11-12); por ejemplo `cto/2026-11-12_PRD_UNICO.md`. El parte resume toda la sesión, no solo ese tema, y su primer párrafo nombra los demás temas tratados. Los partes anteriores con nombre `AAAA-MM-DD_<rol>.md` se conservan tal cual.
- Quién los escribe: cada rol el suyo (`cto`, `tech-lead`, `arquitecto`, `ux-ui`), en su carpeta.
- Cómo se guardan: **primero en la máquina del propietario**, directamente en `C:\Users\Juan Carlos\Desktop\Plataforma LOPDP 360\governance\partes\<rol>\` (la carpeta de su rol en la copia principal), sin rama ni CI. Es una nota de relevo para quien retome en esa máquina, no código. Luego se empujan al repositorio **juntos, en un solo PR de gobernanza al día** que abre el CTO: copia los archivos nuevos de esa carpeta a su worktree, abre el PR y, al fusionarse, borra las copias locales y hace `git pull`, para que el `pull` no choque con archivos sin seguimiento. Los partes que ya están en `main` no se vuelven a copiar.
- Cómo se borran las copias locales: solo la que es **idéntica** a la de `main` (`git diff --quiet origin/main -- <archivo>` con salida 0, o `git diff --no-index` contra la versión de `main` si no tiene seguimiento). Una copia que difiere lleva contenido que aún no está en el repositorio: va al PR siguiente, nunca se descarta con `git checkout --` ni se borra. Ningún parte pide un comando que descarte cambios locales sin esa comprobación.

## Cabecera: el rol de quien escribe
Todo parte empieza, antes de las cuatro secciones, con el rol de quien lo escribe (decisión del propietario, 2026-11-12), para que quien lo retome sepa qué le toca hacer y qué no. Va en la cabecera, no como una sección más, y lleva estos cinco puntos:
- **Rol**: nombre del rol y quién lo asignó; cómo empieza una sesión nueva de ese rol (por ejemplo, esperando el mensaje del CTO).
- **Lugar en la cadena**: CTO → Arquitecto → UX/UI (si hay frontend) → Tech Lead → sesiones de ingeniería, señalando dónde está este rol.
- **Función**: lo que hace este rol, en una línea por tarea.
- **Límites**: lo que este rol no hace (editar, hacer commits, abrir o fusionar PR, actuar en la nube o en producción) y lo que solo ejecuta en copias o bases desechables.
- **Entregas y escalado**: a quién entrega cada resultado, qué vuelve al CTO, qué va al abogado (marcado ESTIMADO mientras no responda) y el idioma.

Si el rol cambia, el parte siguiente lo dice en la cabecera; no se reescribe el anterior.

## Qué lleva (cuatro secciones, siempre en este orden)
1. **Lo decidido**: decisiones tomadas, con su motivo en una línea y el PR o ficha que las recoge. Las que se apoyan en un supuesto sin cita legal verificada se marcan **ESTIMADO**.
2. **Lo que falta**: lo pendiente del equipo (roles y sesiones), con responsable y qué lo desbloquea. Lo que depende del propietario no va aquí: va en «Pendientes del usuario».
3. **Lo que no se toca**: límites vigentes (archivos, ramas, entornos, secretos) y por qué, para que quien retome no los cruce por error.
4. **Pendientes del usuario**: todo lo que solo puede hacer el propietario (pasos en Google Cloud con Antigravity, cambios en `.github/workflows/`, ajustes de GitHub, lecturas de producción, datos, documentos y decisiones suyas, consultas al abogado), en el orden en que conviene hacerlo y con el brief o el PR donde está cada uno. Es la lista que el propietario revisa primero.

## Reglas
- Sin secretos, claves ni URL de conexión.
- Un hecho que ya está en una ficha o en el PRD se cita por su identificador; no se copia.
- Un parte describe el estado a su fecha. Mientras no está en `main` se puede completar; una vez en `main` no se edita: el siguiente parte lo corrige. La historia de los partes solo crece (decisión del propietario, 2026-11-12).
- El estado al corte cita el commit de `main`, la cabeza de Alembic y el recuento de fichas, para poder volver a ese punto y comparar un parte con el anterior.
- Toda ruta que cita un parte existe en `main` o entra en el mismo PR que el parte; se comprueba antes de abrirlo.
