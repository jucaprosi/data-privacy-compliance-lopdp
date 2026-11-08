+++
id = "SEC-19"
titulo = "La descarga con token exige sesión, y el token es de quien la usa"
ola = "D"
estado = "pendiente"
sala = "biblioteca, frontend"
depende_de = ["BIB-112", "CI-16"]
propiedad = ["api/routers/biblioteca_descargas.py", "features/biblioteca/services/descarga.py", "features/biblioteca/domain/errores.py#BIB-104", "frontend/src/lib/biblioteca/descargas.ts", "frontend/src/components/biblioteca/descargas/BotonDescargaPlantilla.tsx", "frontend/tests/biblioteca/descarga.spec.ts", "tests/test_sec19_descarga_con_sesion.py"]
crea = ["tests/test_sec19_descarga_con_sesion.py"]
arbitro = "pytest tests/test_sec19_descarga_con_sesion.py tests/test_bib_104_descarga.py + npx playwright test frontend/tests/biblioteca/descarga.spec.ts + python scripts/generar_indice_tareas.py --verificar"
rastros = ["¤seguridad", "¤arbitro"]
+++

# SEC-19 · La descarga con token exige sesión

Diseño completo: `governance/apoyo/DISENO_SEC-19_DESCARGA_CON_SESION.md` (Arquitecto ADPA, 2026-11-08). **Seguridad revisa antes del reparto.**

**Hallazgo.** `api/routers/biblioteca_descargas.py` toma el tenant y el usuario del token `?token=` sin llamar a `get_context`. Con la clave de firma conocida, cualquiera descarga como otra persona. SEC-16 (#479) ya cerró la clave en la nube; SEC-19 cierra el acceso.

## Contrato (primero la sesión, luego el token)
| Caso | HTTP | Código |
|---|---|---|
| Sin sesión o con sesión inválida | 401 | el de `get_context` |
| Token mal firmado, caducado o con `pid` distinto | 403 | `BIB_TOKEN_DESCARGA_INVALIDO` (pasa de 401 a 403) |
| `sub` o `tid` del token distintos de los de la sesión | 403 | `BIB_TOKEN_DE_OTRA_PERSONA` (nuevo, mensaje genérico) |
| Todo coincide | 200 | — |

El tenant, el usuario y la RLS salen siempre de la sesión. En los errores no se leen bytes ni se escribe auditoría.

## Frontend
`solicitarDescarga` → `fetchAutenticado(url_descarga)` → `blob()` → `URL.createObjectURL` → `<a download>` → `revokeObjectURL`. `BotonDescargaPlantilla` muestra los mensajes de los 403 sin cerrar la sesión; el 401 lo resuelve el manejo global.

## Pruebas y mutaciones
Las 7 pruebas del §5 y las mutaciones M1 a M4 del §6 del diseño. `tests/test_bib_104_descarga.py` no comprueba el código HTTP y debe seguir en verde.

## Interfaz (revisión UX/UI, 2026-11-08)
- Los mensajes dependen del código, no del texto del servidor; para estos casos no se usa `mensajeDelServidor` de `lib/biblioteca/http.ts`.
  - 401: actúa solo el manejo global de `lib/auth/fetchAutenticado.ts` (`alExpirarLaSesion`, que lleva a `/login?motivo=expirada`). El botón no muestra mensaje propio: quita «Preparando descarga…» y no muestra el aviso de éxito, para que no salgan dos avisos a la vez.
  - 403 `BIB_TOKEN_DESCARGA_INVALIDO`: un reintento silencioso (como máximo uno por clic); si vuelve a fallar, «No pudimos preparar la descarga. Inténtalo de nuevo.» con el botón «Reintentar descarga».
  - 403 `BIB_TOKEN_DE_OTRA_PERSONA`: «La descarga se pidió con otra sesión. Vuelve a pedirla desde aquí.» con el botón «Reintentar descarga», sin cerrar la sesión.
- El aviso de éxito se muestra solo después de guardar el archivo.
- El botón conserva su nombre accesible y su testid, y lleva `aria-busy` mientras descarga. El error va en `role=alert` con `data-codigo`.
- Cuatro criterios nuevos de Playwright (a-d) en `descarga.spec.ts`. El (a) dice: «un 401 activa el manejo global de sesión caducada y no muestra el aviso de éxito ni error-descarga».
- Los dos 403 llevan códigos distintos en el backend (`BIB_TOKEN_DESCARGA_INVALIDO` y `BIB_TOKEN_DE_OTRA_PERSONA`, nuevo en `errores.py#BIB-104`), como pide el contrato.
- Otros errores (404 `BIB_ARCHIVO_NO_DISPONIBLE`, red, 5xx): se conserva el mensaje genérico «No se pudo iniciar la descarga de la plantilla.», en `role=alert` con su `data-codigo`; nunca el texto del servidor.
- Foco: el error en `role=alert` se anuncia solo y el foco no se mueve. Después de «Reintentar descarga», el foco vuelve al botón principal. Mientras dura el reintento, «Reintentar descarga» queda deshabilitado y el principal lleva `aria-busy`, para evitar dobles clics.
- Fuera de alcance: hoy `/login` no tiene parámetro de retorno a la Biblioteca. Agregarlo toca `lib/auth/fetchAutenticado.ts` y la página de login, que no son de SEC-19; si se quiere, se hace en otra ficha.

## Revisión de Seguridad (2026-11-08): aprobada para el reparto
1. **Versión:** el token también ata `ver`. Si `ver` no coincide con la versión publicada, responde 403 `BIB_TOKEN_DESCARGA_INVALIDO`. Se suma la **prueba 8**.
2. **Orden estricto:** sesión → firma verificada (`jwt.decode` con `aud`) → `sub`/`tid`/`pid`/`ver`. Ningún claim se lee sin verificar (nada de `verify_signature=False`) para elegir el código de error. `BIB_TOKEN_DE_OTRA_PERSONA` solo se emite con firma válida.
3. **Solo con OIDC:** la garantía vale solo con `AUTH_MODE=oidc`; con `headers` la sesión es autodeclarada (`api/rbac.py:4`). Las pruebas 2 a 4, o al menos una de ellas, corren en modo oidc.
4. El §1 del diseño quedó desactualizado: SEC-16 está hecha (#479) y `archivos.py#SEC-16` ya tiene su marca. Retirar la clave fija fuera de la nube requiere una ficha nueva; está fuera de alcance aquí.
5. El fetch cruzado necesita que el origen del frontend esté en `CORS_ORIGINS` de Cloud Run (SEC-17 lo deja en el brief para el propietario). En los 403 no se registra el token en los logs.

**Validada por el Arquitecto ADPA y por UX/UI (2026-11-08).** Si alguna prueba de `tests/test_bib_104_descarga.py` descargaba sin sesión, pasa a la propiedad de SEC-19 con aviso al Tech Lead.
