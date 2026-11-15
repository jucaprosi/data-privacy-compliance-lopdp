# RET-04 · Inferencia solo en Vertex AI
`¤sdd` `¤arbitro` `¤esquema-asistente` `¤validar-salida-asistente`

## 1. Datos

Sin tablas ni migraciones.

| Archivo | Estado final |
| :--- | :--- |
| `app_core/ai/` (`__init__.py` y el cliente) | se borra entero; ningún módulo lo importa (medido) |
| `features/ai_copilot/services/assistant_provider.py` | genera con `app_core/pasillo/inferencia.py`; `esquema_asistente()` y `validar_salida_asistente()` |
| `features/preanalisis/services/proveedor.py` | `ProveedorIA` con una sola implementación sobre `app_core/pasillo/inferencia.py`; conserva `inyectar_proveedor_de_prueba` y `restablecer_proveedor_entorno` |
| `features/roadmap/ai/client.py` | `call_roadmap_llm` genera con `app_core/pasillo/inferencia.py`; conserva `TruncatedOutputError` y `LLMTimeoutError` |
| sus cuatro pruebas de dominio | se reescriben contra el doble de `features/inferencia` (`inyectar_cliente_de_prueba`) |

La configuración de la inferencia es la de `features/inferencia`: proyecto, región y modelos permitidos de Vertex AI, leídos del entorno que llega desde Secret Manager.

## 2. API

Sin rutas nuevas. `GET /api/v1/ai_copilot/estado` y los estados de preanálisis y roadmap reflejan `inferencia.estado()`: disponible o no, con `MOTIVO_NEUTRO`.

## 3. Reglas

- **R1 · Un solo camino.** Cada uno de los tres proveedores genera con `generar_estructurado` (o `generar_trazado` donde ya hay prompt versionado) de `app_core/pasillo/inferencia.py`. Ninguno crea su propio cliente HTTP ni lee claves de IA.
- **R2 · Contrato intacto.** Las firmas públicas de los tres proveedores, sus esquemas de salida y lo que afirma cada prueba de dominio no cambian. Si la plataforma no está disponible, cada proveedor responde con `InferenciaNoDisponible` y `MOTIVO_NEUTRO`, como el resto de las salas.
- **R3 · Tokens.** Las funciones del esquema y de la validación de salida del asistente se llaman `esquema_asistente` y `validar_salida_asistente`, con sus tokens `¤esquema-asistente` y `¤validar-salida-asistente`, que ya están en `VPA_MAP.md`. Sus llamadores se actualizan en el mismo PR.
- **R4 · Borrado completo.** `app_core/ai/` y las variables de entorno del cliente anterior desaparecen del código. Los manifiestos de `governance/operaciones/entornos/` los limpia RET-09. No queda un alias, un sustituto ni una prueba que compruebe el borrado.
- **R5 · Paquete.** `openai` sale de `requirements.txt` cuando ningún módulo lo importa. `requirements.txt` es de IA-08: si esta ficha deja el paquete sin uso, lo anota en el PR y IA-08 lo retira.
- **R-ADPA · Ortogonalidad ZERAG (`RET-04`).** Las salas `ai_copilot`, `preanalisis` y `roadmap` llegan a `inferencia` solo por `app_core/pasillo/inferencia.py`, con `ImportsCruzados = ∅`.

## 4. Interfaz

Sin cambios. Los avisos al cliente siguen sin nombrar proveedor, modelo ni variables.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** el cliente doble de `features/inferencia`, **cuando** el asistente enriquece una implementación, **entonces** la salida pasa por `validar_salida_asistente` y conserva las citas permitidas. | `tests/test_ia07_asistente_inferencia.py` |
| **Dado** el preanálisis con el doble, **cuando** se analiza un texto, **entonces** el resultado y el enmascarado no cambian. | `tests/test_preanalisis.py` |
| **Dado** la inferencia no disponible, **entonces** los tres proveedores responden con el motivo neutro. | `tests/test_ai_copilot_motivo_neutro.py` y `tests/test_preanalisis_motivo_neutro.py` |
| **Dado** el árbol con la ficha fusionada, **entonces** la suite completa pasa y `test_adpa_bulkhead.py` sigue en verde. | la suite existente |

## 6. Trazabilidad

- Ficha: `governance/tareas/RET-04.md`. Especificación de referencia: `governance/especificaciones/README.md`.
- Sala destino: `features/inferencia` (IA-03, IA-10) y su pasillo `app_core/pasillo/inferencia.py`.
- Mapa del programa: `governance/partes/arquitecto/2026-11-14_COBERTURA_PLATAFORMA_UNICA.md`, fila RET-04.
