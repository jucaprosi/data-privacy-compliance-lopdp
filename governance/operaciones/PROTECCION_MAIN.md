# Protección de la Rama `main`: Procedimiento Operativo y Estado de Reglas
`¤ci-cd` `¤seguridad`

> **DOCUMENTO OPERATIVO DE GOBERNANZA — SALA OPERACIONES:**
> Este documento rige los mecanismos de protección, estado de reglas de GitHub, políticas de integración continua (CI) y los criterios para la activación de "ramas al día" (`required_status_checks.strict = true`) y el cumplimiento de administradores (`enforce_admins = true`).

---

## 1. Estado Actual de la Protección de `main` en GitHub

Consultado vía GitHub CLI (`gh api`) el 2026-10-18:

### 1.1. Protección Clásica de Rama
Comando ejecutado:
```bash
gh api repos/jucaprosi/data-privacy-compliance-lopdp/branches/main/protection
```

Respuesta JSON en crudo obtenida:
```json
{
  "url": "https://api.github.com/repos/jucaprosi/data-privacy-compliance-lopdp/branches/main/protection",
  "required_status_checks": {
    "url": "https://api.github.com/repos/jucaprosi/data-privacy-compliance-lopdp/branches/main/protection/required_status_checks",
    "strict": false,
    "contexts": [
      "Arnés Físico Determinista",
      "Playwright Frontend"
    ],
    "contexts_url": "https://api.github.com/repos/jucaprosi/data-privacy-compliance-lopdp/branches/main/protection/required_status_checks/contexts",
    "checks": [
      {"context": "Arnés Físico Determinista", "app_id": 15368},
      {"context": "Playwright Frontend", "app_id": 15368}
    ]
  },
  "required_signatures": {
    "url": "https://api.github.com/repos/jucaprosi/data-privacy-compliance-lopdp/branches/main/protection/required_signatures",
    "enabled": false
  },
  "enforce_admins": {
    "url": "https://api.github.com/repos/jucaprosi/data-privacy-compliance-lopdp/branches/main/protection/enforce_admins",
    "enabled": false
  },
  "required_linear_history": {
    "enabled": false
  },
  "allow_force_pushes": {
    "enabled": false
  },
  "allow_deletions": {
    "enabled": false
  },
  "block_creations": {
    "enabled": false
  },
  "required_conversation_resolution": {
    "enabled": false
  },
  "lock_branch": {
    "enabled": false
  },
  "allow_fork_syncing": {
    "enabled": false
  }
}
```

### 1.2. Conjuntos de Reglas Modernos (Rulesets)
Comando ejecutado:
```bash
gh api repos/jucaprosi/data-privacy-compliance-lopdp/rulesets
```
Salida obtenida: `[]` (no se utilizan GitHub Repository Rulesets; la protección reside exclusivamente en las Branch Protection Rules clásicas).

### 1.3. Lo No Verificado
- **NO VERIFICADO**: La configuración de permisos a nivel de organización o permisos de usuario individuales con rol Maintain/Admin en la interfaz web de GitHub que no se expone mediante este endpoint específico de protección de rama.
- **NO VERIFICADO**: Si existen secretos de repositorio o entornos configurados en GitHub Actions que puedan alterar la ejecución de los checks requeridos bajo condiciones específicas.

---

## 2. Pasos para Activar «Ramas al Día» (`strict = true`)

Actualmente, `required_status_checks.strict` está configurado en `false`. Si se requiere exigir que las ramas estén actualizadas con `main` antes de fusionar:

### 2.1. Vía GitHub Web UI
1. Navegar a **Settings** en el repositorio `jucaprosi/data-privacy-compliance-lopdp`.
2. En la barra lateral izquierda, ir a **Code and automation** → **Branches**.
3. En la sección **Branch protection rules**, editar la regla existente para el patrón `main`.
4. Marcar la casilla: **«Require branches to be up to date before merging»** (Requiere que las ramas estén al día antes de fusionar).
5. Asegurar que en la lista de comprobaciones obligatorias se mantengan seleccionadas:
   - `Arnés Físico Determinista`
   - `Playwright Frontend`
6. Hacer clic en **Save changes**.

### 2.2. Vía GitHub CLI (`gh api`)
Ejecutar una petición `PATCH` a la configuración de status checks requeridos:
```bash
gh api --method PATCH repos/jucaprosi/data-privacy-compliance-lopdp/branches/main/protection/required_status_checks \
  --field strict=true \
  --raw-field contexts='["Arnés Físico Determinista", "Playwright Frontend"]'
```

### 2.3. Análisis de Coste y Trade-offs
- **Coste de concurrencia**: Si varias ramas/PRs se desarrollan en paralelo, cada vez que un PR se fusiona en `main`, todos los demás PRs abiertos quedan inmediatamente desactualizados y GitHub bloquea el botón de merge hasta que se actualicen contra `main` (haciendo merge o rebase) y vuelvan a correr la suite completa de CI (aproximadamente 3 a 5 minutos por corrida).
- **Trade-off**: 
  - `strict = false` (Actual): Máxima velocidad de integración en tandas paralelas bajo el aislamiento por propiedad exclusiva ADPA. Las colisiones en archivos independientes no ocurren en código, solo podrían ocurrir en migraciones relacionales si coinciden en tiempo.
  - `strict = true` (Estricto): Garantía matemática de que el código integrado fue probado exactamente contra la última cabeza de `main`, a costa de forzar re-ejecuciones de CI y serializar el flujo de fusiones.

---

## 3. Pasos para `enforce_admins` (Aplicar Reglas a Administradores)

Actualmente, `enforce_admins.enabled` es `false`.

### 3.1. Procedimiento de Activación
- **Vía UI**: En **Settings** → **Branches** → regla `main` → activar **«Do not allow bypassing the above settings»** (o «Include administrators»).
- **Vía `gh api`**:
  ```bash
  gh api --method POST repos/jucaprosi/data-privacy-compliance-lopdp/branches/main/protection/enforce_admins
  ```
  *(Para desactivar de nuevo si fuera necesario: `gh api --method DELETE repos/jucaprosi/data-privacy-compliance-lopdp/branches/main/protection/enforce_admins`)*.

### 3.2. Deuda Actual y Evidencia de Empujes Directos
Cuando `enforce_admins` está en `false`, los administradores del repositorio pueden realizar empujes directos (`git push origin main`) saltándose los checks de protección con el mensaje `Bypassed rule violations`.

Se evidencia en el historial reciente de commits en `main` que se han realizado empujes directos sin Pull Request para tareas operativas y documentales:
1. `302051d` - `SEC-07: retirar compatibilidad del token simulado en modo headers` (direct push por `@juancarlosproanios`).
2. `5c4ba29` - `coord: cierre lote (RM-10, SEC-07, FIRMA-01) - BL-14, BL-18, BL-45 retirados; arnes verde 734/0` (direct push).
3. `a479127` - `docs(firma_electronica): boceto BBAP paso 1 y compuerta ADPA conforme a D-4 y Aporte 111` (direct push).
4. `8738882` - `coord: fix cierre lote - restaurar Sin agente/No verificado en BRIEFS` (direct push).
5. `3ba2191` - `coord: veredicto del arnes tras cierre lote 2026-10-18 (734/0)` (direct push).

**Impacto**: Activar `enforce_admins = true` impediría de inmediato que el rol coordinador o el propietario realicen empujes directos de documentación, cierres de lote o ajustes de gobernanza sin abrir un PR y esperar la corrida completa de CI.

---

## 4. Disparador de la Ficha CI-01 y Gestión de Cabezas Alembic

### 4.1. El Disparador
La especificación `governance/tareas/CI-01.md` establece con precisión cuándo debe considerarse activar la protección estricta:
> **Disparador:** dos cabezas de Alembic en `main` o conflictos de fusión repetidos entre PRs de la Fase 7.

Bajo la arquitectura ADPA:
- El aislamiento de desarrollo descansa en la **propiedad exclusiva de archivos**. Los agentes trabajan en archivos disjuntos, eliminando prácticamente a cero el riesgo de conflictos de merge en código fuente.
- El único punto de convergencia relacional son las revisiones de Alembic (`alembic/versions/*.py`).

### 4.2. Resolución de Conflictos con `alembic merge heads`
Si dos ramas crean una migración al mismo tiempo con la misma `down_revision` y ambas se fusionan en `main`, se generan dos cabezas (`two heads`), lo que provoca que `pytest tests/test_alembic_una_cabeza.py` falle.

Mientras `strict = false` permanezca como política:
1. El incidente **no** requiere bloquear a todos los agentes ni cambiar la protección de GitHub de emergencia.
2. El desarrollador o coordinador resuelve la bifurcación directamente ejecutando:
   ```bash
   alembic merge heads -m "merge multiple heads from parallel waves"
   ```
3. Se verifica que exista una sola cabeza:
   ```bash
   pytest tests/test_alembic_una_cabeza.py
   ```
4. Se integra el commit de unión de cabezas a `main`.

Solo si este escenario o conflictos de fusión se vuelven **repetidos y costosos**, se detona el disparador para activar `strict = true`.

---

## 5. Tabla de Decisiones

| Decisión | Ahora (Estado Actual) | De Reserva (Plan de Contingencia) | Recomendación |
| :--- | :--- | :--- | :--- |
| **`strict = true`** | **No** (`strict = false`) | Activar si hay $\ge 2$ choques de Alembic o conflictos recurrentes | **Mantener `strict = false`**. El confinamiento ADPA funciona y evita retrasos artificiales en tandas paralelas. |
| **`enforce_admins = true`** | **No** (`enforce_admins = false`) | Activar cuando se consolide la automatización total de bots/releases | **Mantener `false` temporalmente**. Permite al coordinador registrar cierres de lote y artefactos sin la sobrecarga de PRs vacíos. |
| **`required status checks`** | `Arnés Físico Determinista`, `Playwright Frontend` | Incorporar nuevos verificadores si se crean (ej. auditoría de RLS o contrato OpenAPI) | **Conservar ambos checks actuales**. Ambos están activos en el workflow `zero-regression-pipeline.yml` y validados. |

---

## 6. Recomendación Argumentada

1. **Qué activar ahora**:
   - Mantener la configuración actual: `strict = false` y `enforce_admins = false`, con los dos checks obligatorios (`Arnés Físico Determinista` y `Playwright Frontend`).
   - Mantener `allow_force_pushes = false` y `allow_deletions = false` (ya protegidos).

2. **Qué dejar de reserva**:
   - `strict = true`: Dejar como plan de reserva listo para ser ejecutado vía GitHub UI o `gh api` conforme al procedimiento de la Sección 2, exclusivamente si se produce el disparador de la Sección 4.
   - `enforce_admins = true`: Dejar como mejora futura una vez culminadas las tandas de desarrollo multi-agente.

3. **Por qué (Justificación de Ingeniería)**:
   - **Paralelismo de desarrollo**: Exigir ramas al día en un equipo o enjambre de agentes que trabajan por propiedad exclusiva de archivos serializa las fusiones. Cada PR obligaría a sincronizar y volver a ejecutar CI en los demás, desperdiciando minutos de cómputo y tiempo humano.
   - **Flexibilidad operativa del coordinador**: El coordinador del repositorio necesita asentar cierres de lotes, actualización de veredictos (`.test_verdict.json`) y ajustes de briefs documentales de forma ágil sin demoras de pipelines.
   - **Resiliencia controlada**: El arnés existente (`test_alembic_una_cabeza.py`) detecta inmediatamente cualquier choque relacional en el commit de `main`, permitiendo resolverlo limpiamente con `alembic merge heads` sin penalizar la velocidad de entrega de las tareas independientes.
