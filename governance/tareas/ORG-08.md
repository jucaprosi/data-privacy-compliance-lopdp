+++
id = "ORG-08"
titulo = "Retirar el alias y los restos del rol «encargado»: el código como si «coordinador» siempre hubiera sido el nombre"
ola = "D"
estado = "hecha"
sala = "organizacion"
depende_de = ["ORG-00", "ORG-02", "ORG-05", "ORG-06", "FE-05", "SEC-03"]
propiedad = ["api/rbac.py", "frontend/src/lib/roadmap/generar_tipos.js", "frontend/tests/roadmap/admin.spec.ts", "tests/test_roadmap_auditoria_consulta.py", "tests/test_roadmap_tarea_asignacion.py", "tests/test_sin_rol_antiguo.py", "tests/test_responsable_requests.py", "tests/test_rol_coordinador.py", "governance/artefactos/PRD.md", "governance/arquitectura/HOJA_DE_RUTA_ADPA.md", "features/organizacion/services/solicitud_responsable_engine.py", "frontend/src/app/harness-roadmap/evidencia/HarnessEvidencia.tsx", "frontend/src/lib/roadmap/mockServer.ts", "tests/test_evidencia_http.py"]
arbitro = "pytest tests/test_sin_rol_antiguo.py tests/test_rol_coordinador.py tests/test_matriz_permisos.py + suite completa; Playwright de frontend/tests/roadmap; tsc --noEmit y next build; prueba de mutación documentada"
rastros = ["¤rbac-tenant", "¤seguridad"]
+++

# ORG-08 · Retirar el alias y los restos del rol «encargado»

**Objetivo.** ORG-00 renombró el rol `encargado` a `coordinador` y dejó, a propósito, una compatibilidad (`ROLE_ALIASES` en `api/rbac.py`) para clientes ya desplegados. Producción no tiene ninguna fila con el rol antiguo (medido el 2026-10-18 y el 2026-10-19) y el frontend desplegado ya usa `coordinador`, de modo que esa compatibilidad solo mantiene vivo el nombre antiguo. La decisión del propietario es dejar el código **como si `coordinador` hubiera sido el nombre desde el principio**, sin parches ni alias. Las migraciones históricas no se reescriben: ya están aplicadas en bases existentes y su historia es inmutable.

## Entrega
- Eliminar `ROLE_ALIASES` y su uso en `api/rbac.py`: un `X-Role: encargado` deja de reconocerse (responde como cualquier rol desconocido).
- `frontend/src/lib/roadmap/generar_tipos.js` deja de generar `'encargado'` en `OrganizacionRole`: **el generador produce hoy el tipo antiguo**, de modo que regenerar `frontend/src/types/roadmap.ts` revertiría el renombrado. Tras el cambio, regenerar los tipos no altera `roadmap.ts`.
- Pruebas que hoy dependen del alias: `tests/test_roadmap_tarea_asignacion.py` y `tests/test_roadmap_auditoria_consulta.py` envían `X-Role: encargado` y usan `u_encargado`, «Encargado Test» y docstrings con el nombre antiguo. Pasan a `coordinador` (rol enviado, variables y textos), **sin debilitar ninguna aserción**. `frontend/tests/roadmap/admin.spec.ts` conserva su comprobación de que la interfaz no ofrece el rol antiguo.
- PRD y `HOJA_DE_RUTA_ADPA.md`: donde «encargado» designa el rol de la plataforma, pasa a «coordinador». **No se cambia el sentido legal**: «encargado del tratamiento» (tercero que trata datos por cuenta del responsable, Art. 4 de la LOPDP) se queda como está.
- **Árbitro permanente contra regresiones:** `tests/test_sin_rol_antiguo.py` falla si la **palabra** «encargado» (insensible a mayúsculas y como palabra completa: `\bencargado\b`) o `ROLE_ALIASES` aparece en `*.py`, `*.ts`, `*.tsx` o `*.js`, sea cadena, identificador, variable, **nombre de prueba, docstring o comentario**. Una auditoría encontró que ORG-02 dejó en `tests/test_responsable_requests.py` variables `encargado` y una prueba, `test_destino_encargado_permitido_en_micro_y_pequena`, cuyo nombre contradice lo que ahora comprueba (exige una excepción): se renombran aquí (`coordinador_solicitante`, `test_destino_coordinador_requiere_excepcion_en_micro_y_pequena`). Excluye `alembic/versions/` (historia) y los directorios donde la palabra tiene su sentido legal (`features/regulacion_rag`, `features/ai_copilot`, `features/transferencias`, `features/terceros`, `features/diagnostico`, `frontend/src/lib/bancoPreguntas`, `frontend/src/lib/assessmentReferencia.ts`, `frontend/src/lib/dimensionesSGPDP.ts`, `frontend/src/lib/normativas.ts`, `tmp/`). La lista de exclusiones vive en un solo sitio de la propia prueba, con el motivo de cada una.
- **Prueba de mutación obligatoria:** reintroducir a propósito una cadena `"encargado"` como rol en un archivo no excluido y comprobar que `test_sin_rol_antiguo.py` falla; quitarla y comprobar que pasa.

- **Ampliación del coordinador (2026-10-22):** quedaban restos del rol en comentarios, un texto de interfaz del simulador y docstrings de pruebas, en archivos de tareas ya cerradas; se añaden a la propiedad para retirarlos en vez de eximirlos.

## Límites
- No edita migraciones históricas ni `alembic/versions/*_rol_coordinador.py`.
- No toca los archivos de ORG-02 (`regla_tamano_engine.py`, `roles_engine.py`, `solicitud_responsable_engine.py`, `tests/test_responsable_requests.py`, `tests/test_rol_coordinador.py`, la sección RM-16 de la compuerta): ORG-02 deja sin nombres antiguos lo suyo y esta tarea empieza cuando ya está integrada.
- No cambia reglas ni permisos.

## Hecho cuando
- Su árbitro pasa, la suite completa pasa y el check `Arnés Físico Determinista` del PR está en verde. No modificó ningún archivo fuera de su propiedad y dejó `estado = "hecha"` en esta especificación.
