# Partes de cierre

Un **parte** es la nota corta con la que un rol deja el estado de su trabajo para quien lo retome (otra sesión, otro rol o el propietario). No sustituye al PRD, a los invariantes ni a las fichas: no es fuente normativa. Si un parte y una ficha se contradicen, manda la ficha.

## Dónde y cómo se llaman
- Carpeta predeterminada: `governance/Partes/` (con mayúscula inicial, tal como la creó el propietario). Todo parte nuevo va ahí; no se crean otras carpetas de partes.
- Archivo: `AAAA-MM-DD_<rol>.md`, por ejemplo `2026-11-12_cto.md`. Un archivo por rol y día; si hay más de un cierre el mismo día, se añade una sección fechada con la hora, no un archivo nuevo.
- Quién los escribe: cada rol el suyo (`cto`, `tech-lead`, `arquitecto`, `ux-ui`). Se abren con un PR de gobernanza propio.

## Qué lleva (tres secciones, siempre en este orden)
1. **Lo decidido**: decisiones tomadas, con su motivo en una línea y el PR o ficha que las recoge. Las que se apoyan en un supuesto sin cita legal verificada se marcan **ESTIMADO**.
2. **Lo que falta**: lo pendiente, con responsable (rol, sesión o propietario) y qué lo desbloquea. Los pasos del propietario en Google Cloud, GitHub o producción van aparte, en su propia lista.
3. **Lo que no se toca**: límites vigentes (archivos, ramas, entornos, secretos) y por qué, para que quien retome no los cruce por error.

## Reglas
- Sin secretos, claves ni URL de conexión.
- Un hecho que ya está en una ficha o en el PRD se cita por su identificador; no se copia.
- Un parte describe el estado a su fecha. No se edita después; el siguiente parte lo corrige.
