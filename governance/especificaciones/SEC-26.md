# SEC-26 · Matriz del operador de la plataforma
`¤sdd` `¤rbac-tenant` `¤arbitro`

## 1. Datos

Sin tablas. El invariante 9 dice que el `operador_plataforma` nunca lee datos de cliente. Hoy lo prueban casos sueltos: `tests/test_plataforma_operador.py:106` (403 a quien no es operador), `:163` (solo metadatos permitidos) y `:438` (como `lopdp_app` sin tenant ve 0 filas). No hay una prueba que recorra todas las rutas de organización con ese rol. La matriz ya carga roles aparte desde `tests/matriz/roles/<rol>.py` (`tests/test_matriz_permisos.py:458-470`, ORG-22), y una clave que falta rompe la carga.

## 2. API

No aplica.

## 3. Reglas

- **R1 · Todo decidido.** `tests/matriz/roles/operador_plataforma.py` declara `ROL = "operador_plataforma"` y `PERMITIDO` con cada `id_accion` de la matriz. Las rutas de organización van a `False`; solo las de `/plataforma` van a `True`.
- **R2 · Respuesta sin datos.** Para cada `False`, la petición con la identidad del operador da 403, o 404 sin cuerpo de cliente. Nunca 200 con filas de un tenant. La identidad es un usuario con la marca de operador y sin rol en el tenant de prueba.
- **R3 · Roles de plataforma en la carga.** `tests/test_matriz_permisos.py:473` solo acepta valores de `Role` (`features/organizacion/domain/roles.py`), y el recorrido de la l. 573 solo itera esos valores. `operador_plataforma` no es un rol de organización y no se añade a `Role`. La carga acepta además `ROLES_PLATAFORMA = {"operador_plataforma"}`, definido junto a ella, y el recorrido incluye esos roles con la identidad de R2. Un rol que no esté en ninguno de los dos conjuntos sigue rompiendo la carga.
- **R-SP · Sin prohibiciones** (GEN-01 R3).
- **R-ADPA · Ortogonalidad ZERAG (`SEC-26`).** Solo los archivos de la propiedad.

## 4. Interfaz

Sin pantalla.

## 5. Aceptación

| Caso | Árbitro |
| :--- | :--- |
| **Dado** la matriz completa, **entonces** cada ruta de organización responde al operador sin datos de cliente. Mutación m1: abrir `ver_hoja_de_ruta` al operador en un doble del control de acceso da rojo. | `tests/test_matriz_permisos.py` |
| **Dado** un `id_accion` nuevo sin decidir para el operador, **entonces** la carga falla («operador_plataforma sin decidir en <id>»). Mutación m2: quitar una clave da rojo. | ídem |
| **Dado** `tests/matriz/roles/rol_inventado.py`, **entonces** la carga falla como hoy. Mutación m3: aceptar cualquier `ROL` da rojo. | `tests/test_matriz_permisos.py` |

## 6. Trazabilidad

- PRD §7 criterio 3; `INV_LOPDP_OPERATOR_NO_TENANT_DATA` (n.º 9). Análisis de brechas de la tanda 129: `governance/partes/arquitecto/2026-11-28_BRECHAS_PRD.md`.
