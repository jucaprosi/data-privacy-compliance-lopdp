# Programa RET: qué se elimina, en qué ficha y en qué orden
`¤sdd` `¤arbitro`

Arquitecto ADPA, 2026-11-14. Alcance fijado por el propietario mediante el CTO: se elimina todo lo que Google Cloud reemplazó. La historia la conserva git: no queda nada «como historia» en `main`.

Medido en `origin/main` b216ab4e con una búsqueda de los nombres de las plataformas retiradas:
- 137 archivos fuera de `governance/`;
- unos 220 dentro de `governance/`;
- ninguno en `.github/`, `scripts/` ni `.githooks/`.

Las fichas que ya existen solo se amplían; las que faltan se marcan como **nueva**.

## 1. Mapa

| Ficha | Qué elimina o reescribe | Brief al propietario |
| :--- | :--- | :--- |
| **RET-00** · árbitro de plataforma única (existe) | Pasa a ser el único árbitro, con dos ampliaciones. **(a)** Un detector por patrón de los restos de plataformas retiradas: hosts, prefijos de variables, nombres de paquetes y archivos de despliegue. Los patrones viven en `tests/plataforma_unica/patrones.txt` y el código del árbitro no los escribe como literales. **(b)** El alcance cubre todo el repositorio: `governance/` incluida, y `alembic/versions/` solo en comentarios. Las pendientes de cada ficha solo decrecen. | no |
| **RET-01** · configuración (existe; amplía) | La carga de archivos de entorno en `app_core/config.py`, `python-dotenv` de `requirements.txt`, `.env.example` y las variables de las plataformas retiradas en `app_core/huellas_produccion.py`, `app_core/cloud/gcp_runtime.py` y las guardias de arranque. Amplía su propiedad con `test_sec15/16/17/20`, `test_ep01_guardias_entorno.py`, `test_ep05_datos_pruebas.py`, `test_demo_purga.py`, `test_conftest_entorno.py` y `test_base_por_trabajador.py`. | sí: borrar de Secret Manager y de los secretos del repositorio en GitHub los secretos de las plataformas retiradas, después de fusionar |
| **RET-01a** · `tests/conftest.py` (#809) | La carga de archivos de entorno y la guardia antigua de la suite; la lista blanca de hosts locales. | no |
| **RET-02** · almacén de evidencias (existe; amplía) | `app_core/storage/r2.py` y `app_core/storage/__init__.py`, con el adaptador pasado a Cloud Storage, y los paquetes del almacén anterior en `requirements.txt`. En el frontend: `EvidenciaPanel.tsx`, `subirEvidencia.ts`, `HarnessEvidencia.tsx`, `useRoadmapStore.ts`, `types/roadmap.ts`, `generar_tipos.js`, `cliente.mock.test.ts`, los dos e2e de `criterio12`, `next.config.ts` y `features/roadmap/domain/models.py`. **Columna `r2_key`** (`roadmaps` y papelera de ORG-20): migración nueva `ret02_clave_objeto.py`, que la renombra a `clave_objeto`. No se edita ninguna migración aplicada. | no |
| **RET-03** · cola (existe) | `app_core/queue/` entero, el paquete de la cola en `requirements.txt` y `test_redis_client.py`. La generación pasa a Cloud Tasks o a la ejecución en línea, según su especificación. | sí, solo si se usa Cloud Tasks: crear la cola en GCP |
| **RET-04** · inferencia solo en Vertex AI (**nueva**) | `app_core/ai/` entero (cliente del proveedor anterior), `features/ai_copilot/services/assistant_provider.py`, `features/preanalisis/services/proveedor.py`, `features/roadmap/ai/client.py`, sus variables y sus pruebas (`test_ai_copilot_motivo_neutro.py`, `test_preanalisis.py`, `test_preanalisis_motivo_neutro.py`, `test_ia07_asistente_inferencia.py`). Absorbe las pendientes `IA-04.txt`, `IA-06.txt` e `IA-08.txt` del árbitro si esas fichas ya no las vacían. | no; Vertex ya está activo (`BRIEF_PROPIETARIO_VERTEX.md`) |
| **RET-05** · despliegue (existe; amplía) | `vercel.json`, `frontend/vercel.json`, `tests/test_vercel_despliegue.py` y las ramas de entrada de la plataforma anterior en `security.py`, `bucle_eventos.py`, `firma_anf.py` y `modo.ts`. Amplía su propiedad con `frontend/.dockerignore`, `frontend/README.md` y `frontend/tests/seguridad/cabeceras.spec.ts`. `package-lock.json` y `pnpm-lock.yaml` se regeneran sin los paquetes retirados. Si los dos archivos de bloqueo conviven, uno sobra y se elimina. | sí: borrar el proyecto de la plataforma de despliegue anterior y su integración con GitHub |
| **RET-06** · pruebas con la guardia antigua de base (existe; amplía) | Las 33 pruebas que ya posee, más las que llevan fixtures o comentarios de la base anterior: `test_bib117`, `test_bib_203/205/206/207`, `test_diagnostico_respuestas.py`, `test_diag12_estados.py`, `test_e2e_flujo_completo.py`, `test_e2e_hoja_de_ruta_real.py`, `test_evidencia_filtro_rol.py`, `test_evidencia_http.py`, `test_org_14…`, `test_organizacion_alta.py`, `test_organizacion_api.py`, `test_rat_plantilla_salud.py`, `test_roadmap_control_ref.py`, `features/organizacion/services/exportacion_engine.py` y `tests/duraciones.json`. Se mide archivo por archivo: si la mención es del almacén, de la cola o de la IA, va a RET-02, RET-03 o RET-04. | no |
| **RET-07** · retiro de los árbitros antiguos (falta la ficha; la especificación existe en 72f957db y se reescribe con este alcance) | Elimina la prueba de menciones de la base anterior, su carpeta de pendientes y permitidos, `test_ci17_…`, `verificadores/arnes_local.py` y `verificadores/README.md`, y cualquier prueba que solo vigilaba una plataforma retirada. RET-00 queda como árbitro único. | no |
| **RET-08** · notificador dentro de Google Cloud (**nueva**) | El boceto del proveedor de correo anterior en `features/notificaciones/` (`notificaciones_service.py`, `services/__init__.py`, `services/adaptadores.py`) y `tests/test_notificaciones.py`. Deja el puerto con el doble de pruebas y, si el propietario decide, el adaptador de Google Workspace. | sí: la decisión de proveedor (§3) y, con la Gmail API, la delegación de dominio en Workspace |
| **RET-09** · documentación sin plataformas retiradas (**nueva**) | Ver §2. | no |
| **RET-10** · comentarios de las migraciones aplicadas (**nueva**, pequeña) | Ver §4. | no |

## 2. Documentación (RET-09)

- **Se eliminan, porque solo describen plataformas retiradas:**
  - `governance/historico/pmv/`, la carpeta entera (9 archivos);
  - `governance/operaciones/VERIFICACION_GENERACION.md`;
  - `governance/apoyo/RETIRO_PLATAFORMAS_PMV.md`, cuando el programa termine;
  - `PROCESO_REESTRUCTURACION_COPILOTO.md`, en la raíz;
  - los documentos de `governance/` cuyo único tema sea una plataforma retirada, que la ficha lista al empezar.
- **Se reescriben las menciones sueltas,** sin tocar encabezados, tokens, roles ni candados:
  - en `governance/operaciones/`: `CONSOLIDACION_PRUEBAS.md`, `CREDENCIALES_Y_ROLES_BD.md`, `MIGRACION_CLOUDSQL_POSTGRES.md`, `PRUEBAS_DE_HUMO.md`, `PRUEBAS_EN_FISICO.md` (su §6 pasa al PostgreSQL local) y `entornos/pruebas/secretos.yaml`;
  - en la raíz de `governance/`: `ARQUITECTURA_SOFTWARE.md`, `AUDITORIA_SEGURIDAD_HOJA_DE_RUTA.md` y `PLAN_HOJA_DE_RUTA_INTELIGENTE.md`;
  - en `governance/arquitectura/`: los dos bocetos y `HOJA_DE_RUTA_ADPA.md`;
  - en `governance/apoyo/`: los informes.
- **Artefactos normativos** (`APORTES_INEDITOS.md`, 39 menciones; `FUENTES_Y_BIBLIOGRAFIA.md`, 7; `VPA_MAP.md`; `CANDIDATOS_VPA.json`):
  - un aporte o una fuente cuyo contenido es solo la plataforma retirada se retira entero;
  - uno que enseña algo general se reescribe en términos neutros;
  - los números de aporte no se reutilizan.
- **Fichas:**
  - Las fichas hechas que solo tratan de una plataforma retirada se eliminan: la serie de la base anterior (cinco fichas) y las de CI que solo la migraban.
  - En las demás se reescribe la mención.
  - Antes de eliminar una ficha se retiran sus apariciones en `depende_de` de otras fichas, para que el índice no rompa.
  - Los briefs y las especificaciones siguen la misma regla.
- **Partes:** los de `governance/partes/` se tratan igual que los demás documentos.

## 3. Decisión pendiente: proveedor del notificador

Google Cloud no tiene un servicio gestionado de correo transaccional. Recomiendo la **Gmail API de Google Workspace**: la cuenta de servicio de Cloud Run envía con delegación limitada al envío y la credencial vive en Secret Manager. La alternativa es el relé SMTP de Workspace. Si el propietario no admite Workspace como parte de Google, hace falta una excepción explícita en el PRD. Mientras tanto, RET-08 deja solo el puerto y el doble de pruebas.

## 4. Migraciones ya aplicadas (RET-10)

- **Menciones en comentarios y docstrings** (`20261008_app_role_rls.py` y `20261108_biblioteca_capacidades_propietario.py`): se reescriben solo los comentarios.
  - No hay riesgo de cabezas: `revision` y `down_revision` no cambian.
  - Tampoco de checksums: Alembic no guarda ninguna suma del archivo, solo la revisión en `alembic_version`.
  - Árbitro de la ficha: para cada migración editada, el AST sin docstrings ni comentarios es idéntico al de `origin/main`. Si cambia una sola sentencia, el PR se detiene.
- **Nombres de columna** (`r2_key` en `20261005_roadmaps.py` y en `org20_papelera.py`): son esquema vivo. No se editan; los renombra la migración nueva de RET-02.

## 5. Orden

1. **RET-00 ampliado y RET-01a (#809).** El árbitro único, con sus pendientes por ficha, va primero. Así cada ficha siguiente vacía su lista y ninguna puede volver a meter un nombre.
2. **En paralelo, sin orden entre ellas,** porque no comparten archivos: RET-01, RET-02, RET-03, RET-04, RET-05, RET-06, RET-08 (solo el puerto, hasta la decisión de §3) y RET-10.
3. **RET-07,** cuando las pendientes de RET-00 estén vacías. Retira los árbitros antiguos.
4. **RET-09,** al final o en paralelo con RET-07. Elimina las listas de permitidos de los árbitros antiguos a la vez que los documentos que esas listas nombran.
5. **Briefs al propietario,** cada uno después de fusionar su ficha:
   - **RET-01:** borrar los secretos de las plataformas retiradas en Secret Manager y en GitHub.
   - **RET-03:** crear la cola en GCP, solo si se usa Cloud Tasks.
   - **RET-05:** borrar el proyecto de la plataforma de despliegue anterior.
   - **RET-08:** dar la delegación de envío en Workspace.
   - **Al cerrar el programa:** borrar las cuentas y los proyectos de la base, la caché, el almacén y la IA anteriores.

Ningún workflow de `.github/` nombra una plataforma retirada, así que no hace falta brief de workflows.
