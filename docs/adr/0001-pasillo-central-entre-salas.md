# ADR 0001: Pasillo central para las dependencias entre salas

**Estado:** aprobado por el propietario el 2026-10-30.
**Fecha:** 2026-10-30.
**Motivo del ADR (ADPA §7):** altera la estructura del pasillo central (`app_core`).

## Contexto

ADPA §3 solo admite la dependencia de una sala con el pasillo central. Si la sala A necesita una capacidad de la sala B, `app_core` invoca ambas compuertas. Hoy hay 11 dependencias directas entre salas, registradas como deuda en `DEUDA_LATERAL` (`tests/test_adpa_dependencias.py`).

| Tipo | Dependencia | Qué usa |
| :--- | :--- | :--- |
| Identidad y alcance | `roadmap` → `organizacion` | `allowed_area_ids`, `list_areas`, `list_tenant_users`, `check_four_eyes`, `RbacError`, `SoDViolation` |
| Identidad y alcance | `auditoria_capa` → `organizacion` | `list_my_roles` |
| Identidad y alcance | `plataforma` → `organizacion` | `create_or_get_user`, `grant_role`, `RoleGrant`, `UserCreate` |
| Identidad y alcance | `rat` → `organizacion` | `get_tenant_config` |
| Identidad y alcance | `riesgos_mtge` → `organizacion` | `obtener_informe_estado_designaciones` |
| Lectura | `riesgos_mtge` → `rat`, `roadmap` → `rat` | `listar_actividades_rat` |
| Lectura | `ai_copilot` → `niif18` | `NIIF18DoctrineService` |
| Lectura con cálculo | `roadmap` → `diagnostico` | Catálogo, respuestas, resultados, tipos y `evaluar_assessment_por_dimension` |
| Flujo | `auditoria_capa` → `roadmap` | `registrar_hallazgo`, `cerrar_hallazgo` y sus tipos |
| Flujo | `auditoria_capa` → `evidencias` | `normalizar_sha256`, `verificar_hash`, `HashInvalido` |

Las salas ya importan `app_core` (`audit`, `errors`, `db.session`, entre otros). Si `app_core` importara sus compuertas al cargar, se formaría un ciclo de importación.

## Decisión

### 1. Un paquete de pasillo: `app_core/pasillo/`

Cada capacidad entre salas es una función con nombre y firma propios, en un archivo por sala proveedora (`app_core/pasillo/rat.py`, `app_core/pasillo/organizacion.py`, etc.). La función importa la compuerta dentro de su cuerpo, y por eso no hay ciclo al cargar.

```python
async def listar_actividades_rat(session: AsyncSession, tenant_id: str) -> list[ActividadParaOtraSala]:
    from features.rat import rat_service
    return [...]
```

La sala llama a `pasillo.listar_actividades_rat(...)` y no conoce la sala de origen. Las funciones comparten la `session` de quien llama, de modo que transacción, contexto RLS y orden de operaciones no cambian.

### 2. Lo neutral baja a `app_core`; lo que lee tablas de una sala se queda en ella

- Pasan a `app_core`: `RbacError`, `SoDViolation` y `check_four_eyes`. Son reglas y errores puros, sin tablas ni conocimiento de `organizacion`.
- Se quedan en `organizacion` y se invocan por el pasillo: `allowed_area_ids`, `list_my_roles`, `list_areas`, `list_tenant_users`, `get_tenant_config`, `create_or_get_user`, `grant_role` y `obtener_informe_estado_designaciones`, porque leen o escriben tablas de esa sala.

### 3. El pasillo no transporta tipos internos

Devuelve tipos primitivos o tipos propios definidos en `app_core/pasillo/`, conforme a ADPA §3. La lógica que hoy está en la sala consumidora pero es de la sala proveedora se mueve a su compuerta. El caso principal: `roadmap` construye `RespuestaControl` y llama a `evaluar_assessment_por_dimension`; esa evaluación pasa a `diagnostico`, que entrega el resultado ya calculado.

## Alternativas descartadas

- **Registro de compuertas al arrancar.** Evita las importaciones tardías, pero añade un modo de fallo: cada punto de entrada (`main.py`, `scripts/`, pruebas) debe recordar registrar, y las llamadas pierden el tipado.
- **`app_core` lee y pasa los datos como parámetros, sin que la sala lo llame.** Es la forma más pura de ADPA §3, pero cambia las firmas de las compuertas y no resuelve los flujos a mitad de operación, como el hallazgo por control vencido dentro de un bucle. Puede adoptarse después en casos concretos.
- **Mover `organizacion` entera a `app_core`.** Saldaría 5 dependencias de golpe, pero metería dominio y tablas en el pasillo, y ADPA §2 lo reserva para arranque, orquestación y configuración global.
- **Eventos asíncronos.** Cambiaría el orden y la atomicidad de operaciones que hoy son transaccionales, lo que es un cambio de comportamiento.

## Consecuencias

- `DEUDA_LATERAL` llega a cero y el árbitro existente no necesita cambios: `app_core` ya puede importar compuertas y no sus archivos privados.
- El acoplamiento lógico no desaparece: pasa a ser explícito y a estar en un solo paquete. `app_core/pasillo/` tendrá unas 20 funciones y debe mantenerse sin lógica de negocio.
- Hay 21 sustituciones en pruebas (`test_evidencia_http.py`, `test_autenticacion.py`, `test_evidencia_validacion_servidor.py`) que nombran compuertas de estas salas; habrá que revisarlas por si dejan de interceptar la llamada.
- Quedan fuera de este ADR dos deudas relacionadas, que se tratarán aparte:
  - 15 archivos de sala importan `api.errores.ErrorNegocio`, una dependencia hacia la capa HTTP.
  - Varias compuertas exponen `AsyncSession` y modelos ORM, lo que ADPA §3 prohíbe.

## Plan de retiro

Requiere el PR #258 fusionado. Las tareas se reparten por sala consumidora, no por dependencia: 9 dependencias caben en 6 tareas cuyos archivos no se cruzan, y por eso pueden ejecutarse en paralelo. Las otras 2 esperan a DIAG-08. Agruparlas así evita que varias tareas editen el mismo archivo, como `controles_engine.py`, que concentra tres dependencias.

**Tanda 0, secuencial (cimiento).** Crea `app_core/pasillo/` con todas las funciones, aún sin consumidores; baja `RbacError`, `SoDViolation` y `check_four_eyes` a `app_core`, y `organizacion_service` los sigue exportando; y divide `DEUDA_LATERAL` en un archivo por sala consumidora (`tests/deuda_adpa/<sala>.txt`).

**Tanda 1, en paralelo.**

| Tarea | Dependencias | Archivos que toca |
| :--- | :--- | :--- |
| Roadmap | `organizacion` | `alcance_area_engine.py`, `evidencia_engine.py`, `informe_estado_engine.py`, `tarea_asignacion_engine.py`, sus pruebas y `deuda_adpa/roadmap.txt` |
| Auditoría | `evidencias`, `organizacion`, `roadmap` | `controles_engine.py`, `test_controles_periodicos.py`, `deuda_adpa/auditoria_capa.txt` |
| Riesgos | `organizacion`, `rat` | `obligaciones_engine.py`, `test_mtge_obligaciones.py`, `deuda_adpa/riesgos_mtge.txt` |
| Plataforma | `organizacion` | `operador_engine.py`, `test_plataforma_operador.py`, `deuda_adpa/plataforma.txt` |

**Tanda 2, en paralelo.**

| Tarea | Dependencias | Archivos que toca |
| :--- | :--- | :--- |
| RAT | `organizacion` | `plantilla_engine.py`, `test_rat_plantilla_salud.py`, `deuda_adpa/rat.txt` |
| Copiloto | `niif18` | `inference_engine.py`, `test_ai_sanitization.py`, `deuda_adpa/ai_copilot.txt` |

**Tanda 3, cuando DIAG-08 llegue a la base.** `roadmap` → `diagnostico` y `roadmap` → `rat`. Toca `contexto_generacion.py`, `hallazgo_engine.py` y `roadmap_prompts.py`, y mueve la evaluación a `diagnostico`. DIAG-08 reescribe los dos primeros y retira la escala antigua: mover ese código antes reintroduciría términos que `governance/contratos/escala_madurez.json` retira. `roadmap_prompts.py` llama al catálogo al cargarse y traga cualquier excepción, así que un fallo de importación degradaría el prompt sin avisar; esta tarea debe probarlo.

**Reglas de cada tanda.**

- Antes de lanzar una tanda se cruzan sus archivos con las ramas abiertas de todo el equipo, no solo entre sus tareas.

- Cada tarea declara sus archivos y una comprobación rechaza el PR si toca otro. La tabla es una estimación hecha por búsqueda; el primer paso de cada tarea es confirmarla.
- Si una tarea necesita una función nueva en `app_core/pasillo/`, se detiene: esa función va antes, en un PR del cimiento.
- Archivos distintos evitan conflictos de Git, no conflictos de comportamiento. Los PR se fusionan de uno en uno, y cada uno se actualiza con la base y repite la suite completa antes de fusionar.
- Un integrador revisa cada tanda al cerrar y baja `TOPE_DEUDA_LATERAL`. Las tareas no tocan ese archivo.
- Ninguna tarea añade migraciones, porque la cadena de Alembic es un recurso compartido.
