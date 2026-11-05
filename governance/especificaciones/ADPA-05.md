# ADPA-05 · Andamiaje de `domain/errores.py` por sala y secciones `#ID` en compuertas
`¤sdd` `¤adpa` `¤errores`

## 1. Datos

Sin tablas nuevas. Módulos `features/<sala>/domain/errores.py` en las 15 salas con tareas pendientes.

## 2. API

Sin rutas nuevas.

## 3. Reglas

- **R1 · Catálogo de errores local por sala.** Cada `features/<sala>/domain/errores.py` contiene secciones `# --- INICIO <ID> ---` / `# --- FIN <ID> ---` y registra sus códigos en `CATALOGO_ERRORES` y `CodigoErrorNegocio`.
- **R2 · Secciones `#<ID>` en compuertas y routers compartidos.** Todas las secciones `#<ID>` reclamadas en `propiedad` de tareas pendientes existen físicamente en `<sala>_service.py`, `diagnostico_respuestas.py` y `diagnostico_resultados.py`.

## 4. Interfaz

Sin interfaz propia.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** el conjunto de tareas pendientes con entradas `archivo#ID` de backend, **cuando** se ejecuta `test_adpa05_secciones_y_errores.py`, **entonces** cada archivo existe y contiene los marcadores `# --- INICIO <ID> ---` y `# --- FIN <ID> ---`. | `test_secciones_backend_y_catalogos_errores_existen` |

## 6. Trazabilidad

- Aporte 118 (`BIB-112`) y PRD §7.1 Regla 2.
