# CAPA-03 · Reapertura por evidencia vencida
`¤sdd` `¤controles-periodicos` `¤evidencias-vigencia`

## 1. Datos

Sin tablas nuevas. Lee `controles_periodicos` y `verificaciones_control` (CAPA-02) y la vigencia de evidencias **solo** por `evidencias_service.vigencia_de(session, tenant_id, sha256) -> {vence_el: date | None, vigente: bool}` (EVI-02).

## 2. API

Sin ruta nueva. `POST /auditoria-capa/controles/vencer` (CAPA-02) pasa a ejecutar también R1.

## 3. Reglas

- **R1 · Evidencia vencida reabre.** Para cada control `vigente` cuya última verificación tenga `evidencia_sha256` con `vigente = false`: `estado := 'vencido'` y `registrar_hallazgo(origen='control_periodico', origen_ref=f"{control.id}:evidencia:{sha256}", severidad='alta', titulo=f"Evidencia vencida del control: {nombre}")`; `hallazgo_vigente_id := id`.
- **R2 · Idempotencia.** La clave `origen_ref` incluye el `sha256`: la misma evidencia vencida no genera dos hallazgos; una evidencia nueva vigente registrada en una verificación posterior devuelve el control a `vigente` por R1 de CAPA-02.
- **R3 · Fuente única.** `auditoria_capa` no guarda `vence_el` ni ninguna copia; toda lectura de vigencia es una llamada a la compuerta (`INV_LOPDP_COMPLIANCE_GRAPH_SSOT`).
- **R4 · Sin evidencia.** Una verificación sin `evidencia_sha256` no se reabre por esta regla.

## 4. Interfaz

Sin interfaz propia: la pantalla de CAPA-02 muestra el motivo del hallazgo («Evidencia vencida»).

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** un control vigente cuya última verificación cita una evidencia con `vence_el` ayer, **cuando** corre `vencer`, **entonces** el control queda `vencido` y hay exactamente un hallazgo con `origen_ref` que termina en el `sha256`. Mutación: leer una fecha guardada en `auditoria_capa` hace fallar la prueba (no existe tal columna). | `test_reapertura_por_evidencia_vencida` |
| **Dado** el mismo estado, **cuando** corre `vencer` otra vez, **entonces** no hay un segundo hallazgo. | `test_reapertura_idempotente` |
| **Dado** el control reabierto, **cuando** se registra una verificación con una evidencia vigente, **entonces** vuelve a `vigente` y el hallazgo se cierra. | `test_evidencia_nueva_restituye` |
| **Dado** una verificación sin evidencia, **entonces** no se reabre. | `test_sin_evidencia_no_reabre` |

## 6. Trazabilidad

- Ficha: `governance/tareas/CAPA-03.md`. PRD: Módulo 3, criterio 17; Biblioteca G («Vigencia»). Invariantes: `INV_LOPDP_COMPLIANCE_GRAPH_SSOT`, `INV_LOPDP_SINGLE_ACTION_PLAN`. Depende del contrato `vigencia_de` de EVI-02.
