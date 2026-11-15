# RET-03 · Generación de la hoja de ruta sin cola externa
`¤sdd` `¤roadmap`

## 1. Datos

Sin tablas nuevas ni colas externas. La generación de la hoja de ruta se ejecuta en línea (RM-18). El paquete `redis` permanece en `requirements.txt` exclusivamente para la caché de GCP-06 (`REDIS_URL`).

## 2. API

| Método y ruta | Cambio |
| :--- | :--- |
| `GET /roadmaps/jobs/{job_id}` | se retira |
| `POST /roadmaps/generate` | sin cambio de contrato: responde con el resultado de la generación en línea |

Medido en `main`: el cliente del frontend define `getJob` (`frontend/src/lib/roadmap/cliente.ts:195`) y el servidor simulado la atiende (`mockServer.ts:400`). La ficha comprueba primero si alguna pantalla llama a `getJob`.
- Si ninguna la usa, se retiran la función, el tipo `RoadmapJobStatus` y la rama del servidor simulado.
- Si alguna la usa, la ficha se detiene y lo informa.

## 3. Reglas

- **R1 · Sin cola.** Se retiran `enqueue_generation`, `get_job`, `pop_job` y `get_job_status`, sus exportaciones en `roadmap_service.py` y la ruta de trabajos.
- **R2 · Sin estado nuevo.** No se crea una tabla de trabajos. Si hiciera falta un estado, vive en la tabla del roadmap y lo decide otra ficha.
- **R3 · La generación en línea no cambia de comportamiento.** Las pruebas de RM-18 siguen verdes sin cambiar lo que afirman.
- **R4 · Solo ejecución en línea.** Todo el flujo de generación invoca el motor en línea y conserva los contratos síncronos de RM-18.
- **R-ADPA · Ortogonalidad ZERAG (`RET-03`).** Toda invocación a otra sala va por `app_core/pasillo/<otra_sala>.py` (`ImportsCruzados = ∅`, ADR 0001). `verificar_adpa` queda sin importaciones huérfanas.

## 4. Interfaz

Sin cambio visible: la pantalla de la hoja de ruta ya usa la generación en línea. Se retira del cliente lo que consultaba trabajos, si nadie lo usa.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** el árbol, **entonces** la generación de hojas de ruta opera únicamente en línea sobre Google Cloud Run. | `test_sin_cola_externa` |
| **Dado** `GET /roadmaps/jobs/{id}`, **entonces** 404: la ruta no existe. Mutación: dejar la ruta registrada hace fallar la prueba. | `test_ruta_de_trabajos_retirada` |
| **Dado** una generación en línea, **entonces** responde igual que antes del retiro. | `test_generacion_en_linea_sin_cola` |
| **Dado** el cliente del frontend, **entonces** compila sin `getJob` ni `RoadmapJobStatus`. | `frontend/tests/roadmap/generacion.spec.ts` |

## 6. Trazabilidad

- Ficha: `governance/tareas/RET-03.md`.
- Especificación de referencia: `governance/especificaciones/README.md`.
- No se tocan `alembic/versions/` ni las ramas `produccion` y `dev/Aleczandra`. `.github/workflows/` y `verificadores/` son del propietario: si hacen falta, va un brief.
- Depende de RET-01. Decisión del CTO: la generación vigente es la en línea (RM-18).
- Orden con IA-06, que posee `features/roadmap/services/generacion_engine.py` (ahí viven `enqueue_generation` y `get_job`).
- Orden con RM-25b y RET-02, que comparten `api/routers/roadmaps.py` y `cliente.ts`.
