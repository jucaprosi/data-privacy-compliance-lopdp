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
`solicitarDescarga` → `fetchAutenticado(url_descarga)` → `blob()` → `URL.createObjectURL` → `<a download>` → `revokeObjectURL`. `BotonDescargaPlantilla` muestra los mensajes de 401 y 403 sin cerrar la sesión.

## Pruebas y mutaciones
Las 7 pruebas del §5 y las mutaciones M1 a M4 del §6 del diseño. `tests/test_bib_104_descarga.py` no comprueba el código HTTP y debe seguir en verde.
