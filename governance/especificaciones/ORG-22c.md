# ORG-22c · Rutas de descubrimiento DLP y bóveda en la matriz de permisos
`¤sdd` `¤rbac-tenant`

## 1. Datos

Sin tablas ni migraciones. Cambian solo archivos de prueba:

| Archivo | Estado final |
| :--- | :--- |
| `tests/test_matriz_permisos.py` | `PREFIJOS_MATRIZ` incluye `/api/v1/dlp-discovery` y `/api/v1/boveda-cloud` |
| `tests/matriz/DLP-01.py` | sus tres filas, sin cambios de roles |
| `tests/matriz/BOV-01.py` (nuevo) | la fila de lectura de la suscripción y la ruta del operador en `FUERA_DE_MATRIZ` |

Hecho medido en `origin/main` 5e872a4a:
- `PREFIJOS_MATRIZ` vale `("/api/v1/roadmaps", "/api/v1/organizacion", "/api/v1/areas")`;
- `api/routers/dlp_discovery.py` registra tres rutas bajo `/dlp-discovery`, protegidas con `require_role(*svc.ROLES_ESCANEO)`, `ROLES_CONSULTA` y `ROLES_VINCULO`; `tests/matriz/DLP-01.py` ya las declara con esos roles;
- `features/boveda_cloud/routes/boveda_paquetes_routes.py` registra `GET /boveda-cloud/suscripcion`, con `contexto_consulta` y `ROLES_CONSULTA = ("admin_organizacion", "dpo", "coordinador")`, y `POST /boveda-cloud/suscripcion`, con `requiere_operador` (operador activo de la plataforma, sin rol de organización).

## 2. API

Sin rutas nuevas ni cambios de permisos. La matriz declara lo que ya hace el código:

| id_accion | Método | Ruta | Roles |
| :--- | :--- | :--- | :--- |
| `escanear_muestra_dlp` | POST | `/api/v1/dlp-discovery/escanear-muestra` | admin_organizacion, coordinador, implementador |
| `listar_escaneos_dlp` | GET | `/api/v1/dlp-discovery/escaneos` | los anteriores, dpo y auditor |
| `vincular_escaneo_dlp_rat` | POST | `/api/v1/dlp-discovery/escaneos/{escaneo_id}/vincular-rat` | coordinador |
| `consultar_suscripcion_boveda` | GET | `/api/v1/boveda-cloud/suscripcion` | admin_organizacion, dpo, coordinador |

`FUERA_DE_MATRIZ` de `BOV-01.py`: `("POST", "/api/v1/boveda-cloud/suscripcion")`, con el motivo «alta de suscripción reservada al operador de la plataforma (ORG-09); no la ejerce ningún rol de organización».

## 3. Reglas

- **R1 · Cobertura completa.** Toda ruta registrada bajo los cinco prefijos tiene fila o entrada en `FUERA_DE_MATRIZ` con su motivo. La detección de rutas sin cubrir ya existente lo comprueba.
- **R2 · Declarar, no cambiar.** Las filas reflejan los roles del código en `origin/main`. Si una ruta resulta mal protegida, la corrige otra ficha; esta no toca código de producción.
- **R3 · Auditor de solo lectura.** El auditor aparece solo en `listar_escaneos_dlp` (INV_LOPDP_AUDITOR_SOLE_ROLE).
- **R4 · Operador fuera de la matriz.** La ruta del operador se prueba con su propia guarda (ORG-09); aquí solo se declara fuera de la matriz.
- **R-ADPA · Ortogonalidad ZERAG (`ORG-22c`).** Solo los tres archivos de §1; sin imports nuevos.

## 4. Interfaz

No aplica.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** los cinco prefijos, **cuando** corre la prueba de rutas sin cubrir, **entonces** no queda ruta de DLP ni de bóveda sin fila o motivo. Mutación m1: quitar la fila `consultar_suscripcion_boveda` hace fallar la detección. | `tests/test_matriz_permisos.py` |
| **Dado** cada fila nueva y cada rol, **entonces** el rol autorizado no recibe 403 y el no autorizado recibe 403. Mutación m2: añadir `auditor` a `escanear_muestra_dlp` hace fallar la prueba. | `tests/test_matriz_permisos.py` |
| **Dado** el árbol con la ficha fusionada, **entonces** la suite completa pasa. | la suite existente |

## 6. Trazabilidad

- Ficha: `governance/tareas/ORG-22c.md`. Especificación de referencia: `governance/especificaciones/README.md`.
- Depende de ORG-22, DLP-01 y BOV-01, todas hechas.
