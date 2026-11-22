# BOV-02b · Montaje de los routers de objetos y del orquestador de la bóveda por su compuerta
`¤sdd` `¤adpa` `¤rbac-tenant` `¤arbitro`

## 1. Datos

Sin tablas ni migraciones. Estado final:

| Archivo | Estado final |
| :--- | :--- |
| `features/boveda_cloud/boveda_cloud_service.py` (sección `BOV-01`) | `__getattr__("router")` devuelve un `APIRouter` que incluye `boveda_paquetes_routes.router`, `router_objetos()` y `router_orquestador()` |
| `tests/matriz/BOV-02b.py` (nuevo) | filas de las tres rutas |
| `tests/matriz/roles/auditor.py` (sección `BOV-02b`, sembrada) | el auditor no usa las tres rutas |
| `tests/test_bov02b_montaje_routers.py` (nuevo) | casos de §5 |

Hecho medido en `origin/main` 60b8a5e0, con `APP_ENV=test` y el OpenAPI de `main.app`:
- `main.py` registra `("features.boveda_cloud.boveda_cloud_service", "boveda_cloud")` en su sección `BOV-01`. La compuerta solo entrega `boveda_paquetes_routes.router`.
- La compuerta ya expone `router_objetos()` (BOV-02) y `router_orquestador()` (BOV-04), pero nadie los registra. Faltan `POST /api/v1/boveda-cloud/objetos/url-subida-firmada`, `POST /api/v1/boveda-cloud/objetos/{objeto_id}/url-descarga-firmada` y `GET /api/v1/boveda-cloud/orquestador-10d`.
- `/api/v1/boveda-cloud` está en `PREFIJOS_MATRIZ`. Roles: `ROLES_OBJETOS` = admin_organizacion, dpo, coordinador, implementador y responsable_area; `ROLES_CONSULTA` = admin_organizacion, dpo y coordinador.

## 2. API

| Método y ruta | Roles |
| :--- | :--- |
| `POST /api/v1/boveda-cloud/objetos/url-subida-firmada` | `ROLES_OBJETOS` |
| `POST /api/v1/boveda-cloud/objetos/{objeto_id}/url-descarga-firmada` | `ROLES_OBJETOS` |
| `GET /api/v1/boveda-cloud/orquestador-10d` | `ROLES_CONSULTA` |

## 3. Reglas

- **R1 · Una puerta por sala.** `main.py` registra la sala una sola vez, por su compuerta, y la compuerta reúne sus routers. Ningún módulo fuera de la sala importa `features.boveda_cloud.routes`.
- **R2 · Matriz.** Las tres rutas tienen fila en `tests/matriz/BOV-02b.py` con los roles de §2, y la sección `BOV-02b` de `auditor.py` las marca `False`.
- **R-ADPA · Ortogonalidad ZERAG (`BOV-02b`).** Solo la sección `BOV-01` de la compuerta y las pruebas.

## 4. Interfaz

No aplica.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** `main.app`, **entonces** el OpenAPI tiene las tres rutas de §2 y la de suscripción. Mutación m1: devolver solo el router de paquetes hace fallar la prueba. | `test_rutas_de_la_sala_montadas` |
| **Dado** la matriz, **entonces** las tres rutas están cubiertas y el auditor recibe 403. | `tests/test_matriz_permisos.py` |
| **Dado** el árbol, **entonces** ningún módulo fuera de `features/boveda_cloud/` importa `features.boveda_cloud.routes`. | `test_rutas_solo_por_la_compuerta` |

Sin `import yaml`.

## 6. Trazabilidad

- Ficha: `governance/tareas/BOV-02b.md`. Especificación de referencia: `governance/especificaciones/README.md`.
- Pedido del CTO (2026-11-21). Depende de BOV-01, BOV-02, BOV-04 y ORG-22c, hechas.
