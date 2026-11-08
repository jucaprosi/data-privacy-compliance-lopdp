# SEC-19 · La descarga con token exige sesión, y el token es de quien la usa

Arquitecto de soluciones ADPA · 2026-11-08 · Base: `origin/main` 0bd990f. Solo diseño.

## 0. Hechos comprobados

- `api/routers/biblioteca_descargas.py:44-51`: si llega `?token=`, el tenant y el usuario salen del token y **no se llama a `get_context`**: no hay sesión.
- `features/biblioteca/services/descarga.py:158-162`: `ejecutar_descarga` solo compara `pid` y `tid` del token con lo que recibe, y luego fija la RLS con ese tenant y ese usuario.
- `features/biblioteca/services/archivos.py:24`: `SESSION_SECRET` → `SECRET_KEY` → clave fija pública. **El despliegue de Cloud Run (`deploy-gcp.yml:62`) no define `SESSION_SECRET` ni `SECRET_KEY`**, así que en la nube hoy se firma con la clave fija. Es explotable ya, no en teoría.
- El frontend abre el enlace con un `<a href>` oculto (`frontend/src/lib/biblioteca/descargas.ts:29-38`): una navegación del navegador **no envía `Authorization` ni `X-Role`**.
- `BIB_TOKEN_DESCARGA_INVALIDO` es un **401** (`features/biblioteca/domain/errores.py:46`, sección BIB-104).

## 1. Corte: la clave es de SEC-16; SEC-19 se queda con el acceso

**SEC-16 (pendiente) ya es dueña de `archivos.py#SEC-16`**: «la clave de firma sale de `SESSION_SECRET` en una sola función; el alias `SECRET_KEY` y la clave fija quedan solo fuera de la nube». La exención 142 de `_exenciones_propiedad.txt` dice que esa sección aún no tiene marca.

- **No le doy a SEC-19 la línea de la clave.** Habría dos dueñas del mismo archivo.
- Si el objetivo es retirar la clave fija **también fuera de la nube**, hay que **ampliar la entrega de SEC-16**:
  - `SESSION_SECRET` obligatoria siempre;
  - sin `SECRET_KEY` ni clave fija;
  - en `APP_ENV=test`, el secreto lo pone la prueba.
- Así `archivos.py` sigue con una sola dueña. **Decisión para Tech Lead:** ampliar SEC-16 en el PR de gobernanza, que es mi recomendación, o mantenerla como está.
- Además, antes de fusionar SEC-16, la persona que despliega carga `SESSION_SECRET` en Secret Manager y en el `--set-secrets` de Cloud Run. Eso es del propietario.

SEC-19 no depende de SEC-16: no comparte archivos con ella y corrige el fallo aunque la clave siga siendo débil, porque con sesión obligatoria un token falsificado no sirve para otra persona.

## 2. Propiedad de SEC-19

BIB-104, dueña original de estos archivos, está `hecha`. Ninguna otra ficha viva los posee: lo comprobé con grep en `governance/tareas`, y solo aparecen BIB-104 y SEC-16 (que tiene `archivos.py`, que SEC-19 no toca).

```
propiedad = [
  "api/routers/biblioteca_descargas.py",
  "features/biblioteca/services/descarga.py",
  "features/biblioteca/domain/errores.py#BIB-104",
  "frontend/src/lib/biblioteca/descargas.ts",
  "frontend/src/components/biblioteca/descargas/BotonDescargaPlantilla.tsx",
  "frontend/tests/biblioteca/descarga.spec.ts",
  "tests/test_sec19_descarga_con_sesion.py",
]
crea = ["tests/test_sec19_descarga_con_sesion.py"]
depende_de = []
arbitro = "pytest tests/test_sec19_descarga_con_sesion.py tests/test_bib_104_descarga.py + npx playwright test frontend/tests/biblioteca/descarga.spec.ts + python scripts/generar_indice_tareas.py --verificar"
```

- `errores.py#BIB-104`: la marca existe y su dueña está hecha. SEC-19 la asume para cambiar el estado de un código y añadir uno. Así no hace falta sembrar una marca nueva.
- `tests/test_bib_104_descarga.py` no está en su propiedad: solo lo ejecuta. Si alguna de sus pruebas dependía de descargar sin sesión, **debe fallar**, y esa prueba pasa a la propiedad de SEC-19 para corregirla. Tech Lead lo verifica al crear la ficha.

## 3. Contrato de error

El orden importa: primero la sesión, luego el token.

| Caso | HTTP | Código |
|---|---|---|
| Sin sesión o con sesión inválida (con o sin token) | **401** | el de `get_context`, igual que hoy |
| Sesión válida y token mal firmado, caducado o con `pid` distinto | **403** | `BIB_TOKEN_DESCARGA_INVALIDO`, que pasa de 401 a 403 |
| Sesión válida y `sub` ≠ usuario de la sesión, o `tid` ≠ tenant de la sesión | **403** | `BIB_TOKEN_DE_OTRA_PERSONA` (nuevo; mensaje genérico, sin revelar de quién es) |
| Todo coincide | 200 | — |

- El código del token pasa a 403 porque, con sesión válida, un 401 haría creer al frontend que caducó la sesión.
- El tenant, el usuario y la RLS salen **siempre** de la sesión, nunca del token. El token solo **ata** la descarga a una plantilla, una versión y un plazo.
- La auditoría registra al usuario de la sesión.
- En ningún caso de error se leen los bytes ni se escribe auditoría.

## 4. Frontend: sí cambia

Con sesión obligatoria, el `<a href>` daría 401. El nuevo flujo:
1. `solicitarDescarga(plantillaId)`, como hoy;
2. `fetchAutenticado(res.url_descarga)`, que envía `Authorization`, `X-Tenant-ID` y `X-Role`;
3. `blob()` → `URL.createObjectURL` → `<a download=nombre_archivo>` → `click` → `revokeObjectURL`.

`dispararDescargaEnNavegador` pasa a ser asíncrona y recibe el `Response`. `BotonDescargaPlantilla` espera esa función y muestra los errores 401 y 403 con sus mensajes. El límite de 10 MB permite tener el archivo en memoria. Para la Biblioteca no queda ninguna descarga por navegación directa.

Fuera de alcance: mover el token de la query a una cabecera. Con sesión obligatoria, que el token aparezca en los registros ya no basta para robar una descarga.

## 5. Pruebas

Backend (PostgreSQL real; secreto generado en la prueba):
1. Token válido y sesión del mismo usuario y tenant: 200, y la auditoría con el usuario de la sesión.
2. Token válido sin sesión: 401, sin bytes ni auditoría.
3. Token de A con la sesión de B, del mismo tenant: 403 `BIB_TOKEN_DE_OTRA_PERSONA`, sin auditoría.
4. Token del tenant T1 con una sesión en T2: 403 `BIB_TOKEN_DE_OTRA_PERSONA`.
5. Token **firmado con la clave fija pública** y `SESSION_SECRET` definida en la prueba: 403 `BIB_TOKEN_DESCARGA_INVALIDO`.
6. Token caducado, o con `pid` de otra plantilla: 403 `BIB_TOKEN_DESCARGA_INVALIDO`.
7. Sin token y con sesión (la ruta sigue existiendo): sin cambios.

Frontend (Playwright): la petición al archivo lleva `Authorization`, se descarga un archivo con `nombre_archivo`, y un 403 muestra el mensaje sin cerrar la sesión.

## 6. Mutaciones que deben fallar

- M1: el router vuelve a tomar `tid` y `sub` del token: fallan las pruebas 3 y 4.
- M2: se quita la comparación `sub == usuario de la sesión`: falla la prueba 3.
- M3: se omite `get_context` cuando hay token: falla la prueba 2.
- M4: el frontend vuelve al `<a href>` directo: falla la prueba de Playwright, porque no hay `Authorization`.

## 7. Revisión de Seguridad

Sí, antes del reparto: cambia cómo se autoriza una descarga.
