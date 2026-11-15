# Cobertura del programa RET: qué ficha retira cada resto de plataformas retiradas
`¤sdd` `¤arbitro`

Arquitecto ADPA, 2026-11-14. Medido en `origin/main` b216ab4e con una búsqueda de los nombres de las plataformas retiradas fuera de `governance/`: 137 archivos. La columna «ficha» sale de la propiedad declarada en `governance/tareas/RET-*.md`. Si dice «sin ficha», ninguna RET posee el archivo.

## 1. Lo que ya cubren RET-00..06

| Grupo | Ficha |
| :--- | :--- |
| configuración, guardias de arranque, `requirements.txt`, plantilla de variables | RET-01 |
| `tests/conftest.py` | RET-01a |
| almacén de evidencias del roadmap (`app_core/storage/r2.py`, `evidencia_engine.py`, `api/routers/roadmaps.py`, `frontend/src/lib/roadmap/cliente.ts`, `mockServer.ts`, `next.config.ts`) | RET-02 |
| cola de la hoja de ruta (`app_core/queue/redis_client.py`, `generacion_en_linea.py`, `test_redis_client.py`, `test_roadmap_service.py`) | RET-03 |
| despliegue y entrada (`vercel.json`, `frontend/vercel.json`, `next.config.cloudrun.ts`, `pytest.ini`, `.gitignore`, `security.py`, `bucle_eventos.py`, `firma_anf.py`, `modo.ts`, humo y cabeceras) | RET-05 |
| 33 pruebas con la guardia antigua de base | RET-06 |
| catálogos y pendientes del árbitro | RET-00 |

## 2. Huecos y quién los absorbe

| Grupo (archivos sin ficha) | Propuesta |
| :--- | :--- |
| **Proveedor de IA anterior:** `app_core/ai/__init__.py`, `app_core/ai/deepseek_client.py`, `features/ai_copilot/services/assistant_provider.py`, `features/preanalisis/services/proveedor.py`, `features/roadmap/ai/client.py`, `test_ai_copilot_motivo_neutro.py`, `test_preanalisis.py`, `test_preanalisis_motivo_neutro.py` y `test_ia07_asistente_inferencia.py` | Los absorben IA-04, IA-06 e IA-08, que ya tienen pendientes en el árbitro. Hay que medir que su propiedad incluya estos archivos; lo que no entre va a **RET-04 · Inferencia solo en Vertex AI** (ficha nueva). |
| **Notificador:** `features/notificaciones/notificaciones_service.py`, `services/__init__.py`, `services/adaptadores.py` y `tests/test_notificaciones.py` | **RET-08 · Notificador dentro de Google Cloud** (ficha nueva). Retira el boceto del proveedor anterior y deja el puerto con el doble de pruebas. Depende de la decisión de proveedor (§3). |
| **Restos del almacén de evidencias en el frontend:** `EvidenciaPanel.tsx`, `subirEvidencia.ts`, `HarnessEvidencia.tsx`, `useRoadmapStore.ts`, `types/roadmap.ts`, `generar_tipos.js`, `cliente.mock.test.ts`, los dos e2e de `criterio12` y `features/roadmap/domain/models.py` | Los absorbe RET-02: amplía su propiedad. |
| **Configuración de la nube y entornos:** `app_core/cloud/gcp_runtime.py`, `test_sec16_secretos_obligatorios.py`, `test_sec17_configuracion_nube.py`, `test_sec20_huella_cloudsql.py`, `test_ep01_guardias_entorno.py`, `test_ep05_datos_pruebas.py`, `test_demo_purga.py`, `test_conftest_entorno.py`, `test_base_por_trabajador.py` y `test_conftest_guardias.py` | `test_conftest_guardias.py` va a RET-01a (#809); el resto, a RET-01, ampliando su propiedad. |
| **Despliegue del frontend:** `frontend/.dockerignore`, `frontend/README.md`, `frontend/package-lock.json`, `frontend/pnpm-lock.yaml` y `frontend/tests/seguridad/cabeceras.spec.ts` | Los absorbe RET-05, ampliando su propiedad. Los archivos de bloqueo se regeneran; no se editan a mano. |
| **Pruebas con fixtures o comentarios antiguos:** `test_bib117_capacidades.py`, `test_bib_203/205/206/207`, `test_diagnostico_respuestas.py`, `test_e2e_flujo_completo.py`, `test_e2e_hoja_de_ruta_real.py`, `test_evidencia_filtro_rol.py`, `test_evidencia_http.py`, `test_org_14_datos_documentales.py`, `test_organizacion_alta.py`, `test_organizacion_api.py`, `test_rat_plantilla_salud.py`, `test_roadmap_control_ref.py`, `test_diag12_estados.py`, `features/organizacion/services/exportacion_engine.py` y `tests/duraciones.json` | Los absorbe RET-06, ampliando su propiedad, siempre que la mención sea la guardia de base. Si es otra cosa (almacén, cola o IA), va a la ficha de ese grupo. Hay que medirlo archivo por archivo. |
| **Guardia de menciones y su serie:** la prueba de menciones, sus listas de permitidos y pendientes, `test_ci17_…`, `verificadores/README.md` y `verificadores/arnes_local.py` | **RET-07 · Retiro del árbitro de menciones.** Su especificación está escrita (rama `tarea/juan-carlos/espec-ret`, 72f957db), pero no tiene ficha ni está en `main`. Va al final, cuando los pendientes de RET-00 estén vacíos. |
| **Historia:** `alembic/versions/20261005_roadmaps.py`, `20261008_app_role_rls.py`, `20261108_biblioteca_capacidades_propietario.py` y `org20_papelera.py` | Las migraciones aplicadas no se editan. RET-00 las deja fuera del árbitro, como historia. |
| **Documentos sueltos:** `PROCESO_REESTRUCTURACION_COPILOTO.md` (raíz) y `data/Guia_Integracion_OneShot_SMARTCIDI.pdf` | El `.md` pasa a `governance/historico/`, en la tanda de RET-07. El PDF es material de entrada del propietario y no se modifica: RET-00 excluye `data/`. |

En `governance/` hay 129 fichas y otros documentos que nombran las plataformas. Las fichas hechas y `governance/historico/` quedan como historia. Las fichas abiertas que dependan de una plataforma retirada se revisan una por una en RET-07.

## 3. Decisión pendiente del propietario: proveedor del notificador

Google Cloud no tiene un servicio gestionado de correo transaccional. Las opciones dentro de Google:

1. **Gmail API de Google Workspace (recomendada).** La cuenta de servicio de Cloud Run envía desde un buzón del dominio de la operadora, con delegación de dominio limitada al permiso de envío. La credencial vive en Secret Manager, y las cuotas son las de Workspace, alrededor de 2 000 mensajes al día por buzón.
2. **Relé SMTP de Google Workspace.** Envío por SMTP autenticado desde Cloud Run. Es más simple, pero el secreto es una contraseña de aplicación y no hay registro por mensaje en la API.

Las dos cumplen la plataforma única si se entiende «Google Cloud» como el conjunto de Google: Cloud y Workspace. Si el propietario no admite Workspace, la única salida es un proveedor externo, y eso exige una excepción explícita en el PRD. Mientras no decida, el puerto queda con el doble de pruebas y RET-08 no implementa ningún proveedor real.

## 4. Fichas que hay que escribir

- **RET-04 · Inferencia solo en Vertex AI:** solo si IA-04, IA-06 e IA-08 no cubren los archivos de §2.
- **RET-07 · Retiro del árbitro de menciones:** falta la ficha; la especificación ya existe.
- **RET-08 · Notificador dentro de Google Cloud:** ficha y especificación nuevas, después de la decisión de §3.
- **Ampliaciones de propiedad:** RET-01, RET-02, RET-05 y RET-06, según §2.
