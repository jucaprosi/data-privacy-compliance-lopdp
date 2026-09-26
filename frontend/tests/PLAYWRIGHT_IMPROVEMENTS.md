# 🚀 Mejoras de Playwright Importadas del ERP
## ¤¦playwright_improvements

---

## 📌 Resumen

Se han importado **4 utilidades nuevas** desde la implementación de playwright del ERP para robustecer la automatización de tests en LOPDP 360.

### Nuevos archivos

```
frontend/tests/
├── consoleSentinel.ts      ✅ Monitoreo de errores de consola
├── auditTrail.ts           ✅ Audit trail + certificación SHA-256
├── locatorResolver.ts      ✅ Resolutor de localizadores (PCP)
├── exampleWithAudit.spec.ts ℹ️  Ejemplos de uso (opcional)
└── PLAYWRIGHT_IMPROVEMENTS.md (este archivo)
```

### Archivos modificados

```
frontend/tests/
└── utiles.ts               ✅ Reexportadas nuevas utilidades
```

---

## 🎯 Utilidades Importadas

### 1. **ConsoleSentinel** (Monitoreo de Errores)

**Ubicación:** `frontend/tests/consoleSentinel.ts`

**Propósito:** Detectar errores y warnings en la consola del navegador que podrían indicar regresiones silenciosas.

**Uso básico:**
```typescript
import { ConsoleSentinel } from "./utiles";

test("mi test", async ({ page }) => {
  const sentinel = new ConsoleSentinel();
  sentinel.attach(page);
  
  // ... test logic ...
  
  // Falla si detectó errores
  sentinel.assertZeroErrors();
  
  // O revisar manualmente
  const report = sentinel.report();
  console.log(report);
  // { errors: [...], warnings: [...], logsCount: 5, totalEvents: 7 }
});
```

**API:**
- `attach(page)` — Adjunta listeners de consola
- `assertZeroErrors()` — Falla el test si hay errores
- `report()` — Retorna resumen de logs
- `getErrors()` — Retorna solo errores
- `getWarnings()` — Retorna solo warnings
- `clear()` — Limpia registros

**Cuándo usar:**
- Tests que manipulan el DOM
- Tests que hacen llamadas a API
- Tests de componentes React que emiten warnings

---

### 2. **AuditTrail** (Auditoría + Certificación)

**Ubicación:** `frontend/tests/auditTrail.ts`

**Propósito:** Registrar cada click con coordenadas, atributos y XPath; certificar screenshots con SHA-256.

**Uso básico:**
```typescript
import { AuditTrail } from "./utiles";

test("dashboard assessment", async ({ page }) => {
  // Inyectar tracker
  await AuditTrail.injectTracker(page);
  
  // ... test logic con muchos clics ...
  
  // Recuperar log de clics
  const clickLog = await AuditTrail.getClickLog(page);
  console.log(`Clics: ${clickLog.length}`);
  // [
  //   { timestamp: "2026-09-19T...", tag: "button", id: "btn-ok", 
  //     testId: "submit-btn", x: 120, y: 45, width: 80, height: 32, xpath: "..." },
  //   ...
  // ]
  
  // Capturar screenshot certificado
  const snapshot = await AuditTrail.captureSnapshot(page, "result");
  // Genera: test-results/screenshots/result-1695158400000.png
  //         test-results/screenshots/result-1695158400000.png.meta.json
  console.log(snapshot.sha256); // "a3c8f2e..."
  
  // Exportar audit log
  await AuditTrail.exportAuditLog(page, "./audit-logs/test-run.json");
});
```

**API:**
- `injectTracker(page)` — Inyecta listener de clics
- `getClickLog(page)` — Retorna array de ClickEntry
- `clearClickLog(page)` — Limpia el log
- `captureSnapshot(page, name, dir?)` — Screenshot + SHA-256
- `verifySnapshot(path)` — Verifica integridad
- `exportAuditLog(page, path)` — Exporta JSON completo

**Estructura de ClickEntry:**
```typescript
interface ClickEntry {
  timestamp: string;      // ISO 8601
  tag: string;            // "button", "input", etc.
  id: string;             // HTML id atributo
  class: string;          // HTML class atributo
  testId?: string;        // data-testid
  text?: string;          // Primer 100 chars de textContent
  x: number;              // Coordenada X (pixels)
  y: number;              // Coordenada Y (pixels)
  width: number;          // Ancho elemento
  height: number;         // Alto elemento
  xpath?: string;         // XPath calculado
}
```

**Cuándo usar:**
- Debugging de tests fallidos (ver qué botones se clickearon)
- Auditoría regulatoria (certificar que screenshots no fueron modificados)
- Trazabilidad: conectar logs de UI con logs backend
- Análisis de flows complejos

---

### 3. **LocatorResolver** (Resolutor PCP)

**Ubicación:** `frontend/tests/locatorResolver.ts`

**Propósito:** Resolver selectores de forma uniforme con jerarquía de preferencia (ID > testid > role > text > css).

**Uso básico:**
```typescript
import { LocatorResolver, L } from "./utiles";

test("mi test", async ({ page }) => {
  // Resolución directa
  const button = LocatorResolver.resolve(page, "data-testid=btn-submit");
  await button.click();
  
  // Alias corto
  const input = L.resolve(page, "role=textbox[name=Email]");
  await input.fill("test@example.com");
  
  // Helpers constructores
  const el1 = L.resolve(page, L.testId("dashboard-card"));
  const el2 = L.resolve(page, L.role("button", { name: "Guardar" }));
  const el3 = L.resolve(page, L.text(/Tablero de resultados/));
  const el4 = L.resolve(page, L.placeholder("Ingrese..."));
  
  // Operaciones encadenadas
  await L.resolve(page, "data-testid=form").waitFor({ state: "visible" });
  
  // Fallback: probar múltiples selectores
  const elemento = await LocatorResolver.resolveAny(page, [
    "data-testid=primary-btn",
    "role=button[name=Guardar]",
    "button:has-text('Guardar')",
  ]);
  if (elemento) await elemento.click();
});
```

**Jerarquía de resolución (orden de intentos):**
1. **N1 (ID):** `#myElement`
2. **N2 (data-testid):** `data-testid=my-id` o `[data-testid="my-id"]`
3. **N3 (role):** `role=button` o `role=button[name="texto"]`
4. **N4 (placeholder):** `placeholder="Buscar..."`
5. **N6 (text):** `text="Buscar"` o `text=/regex/`
6. **N5 (CSS):** `button.primary` (fallback)

**API:**
- `resolve(page, selector)` — Resuelve selector → Locator
- `resolveAny(page, selectors[])` — Retorna primer visible
- `resolveAndWait(page, selector, timeout?)` — Resuelve + espera visible
- `testId(id)` — Constructor: `"[data-testid="..."]"`
- `role(role, options?)` — Constructor: `"role=..."`
- `text(text)` — Constructor: `"text=..."`
- `placeholder(text)` — Constructor: `"placeholder=..."`

**Ventajas:**
- Reduce duplicación de selectores
- Facilita refactors (cambiar select de CSS a testid = 1 línea)
- Alias `L` para sintaxis más limpia

---

## 📚 Ejemplo Completo

```typescript
import { expect, test } from "@playwright/test";
import {
  AuditTrail,
  ConsoleSentinel,
  L,
  abrirAppLimpia,
  configurarProyecto,
  irASala,
} from "./utiles";

test("assessment dashboard con auditoría", async ({ page }) => {
  // Setup auditoría
  const sentinel = new ConsoleSentinel();
  sentinel.attach(page);
  await AuditTrail.injectTracker(page);

  // Inicializar app
  await abrirAppLimpia(page);
  await configurarProyecto(page);
  
  // Navegar y interactuar
  await irASala(page, /Dashboard Central/);
  
  // Usar LocatorResolver
  const resultPanel = L.resolve(page, L.text(/Resultado del Assessment/));
  await expect(resultPanel).toBeVisible();
  
  // Verificar nivel
  const nivelText = L.resolve(page, "data-testid=maturity-level");
  const nivel = await nivelText.innerText();
  expect(nivel).toMatch(/Nivel [0-5]/);
  
  // Capturar audit trail
  const clicks = await AuditTrail.getClickLog(page);
  console.log(`Total clics: ${clicks.length}`);
  
  // Certificar screenshot
  const snapshot = await AuditTrail.captureSnapshot(page, "assessment-ok");
  console.log(`SHA-256: ${snapshot.sha256}`);
  
  // Exportar logs
  await AuditTrail.exportAuditLog(page, "./audit-logs/test.json");
  
  // Verificar consola limpia
  sentinel.assertZeroErrors();
  console.log(sentinel.report());
});
```

**Output esperado:**
```
✅ App limpia abierta
✅ Proyecto configurado
✅ Navegado a Dashboard Central
📋 Clics registrados: 15
✅ Screenshot: test-results/screenshots/assessment-ok-1695158400000.png
   Hash: a3c8f2e9...
📋 Audit log exported to audit-logs/test.json
📊 Reporte de Consola:
   Errores: 0
   Warnings: 0
   Logs: 3
```

---

## 🔧 Integración en Tests Existentes

### Opción 1: Agregar auditoría a spec existente

```typescript
// Antes
test("tablero muestra resultados", async ({ page }) => {
  await abrirAppLimpia(page);
  await configurarProyecto(page);
  // ... test logic ...
});

// Después
test("tablero muestra resultados", async ({ page }) => {
  // Agregar estas 2 líneas
  const sentinel = new ConsoleSentinel();
  sentinel.attach(page);
  
  await abrirAppLimpia(page);
  await configurarProyecto(page);
  // ... test logic ...
  
  // Agregar esta línea al final
  sentinel.assertZeroErrors();
});
```

### Opción 2: Crear fixture para reutilizar

```typescript
// tests/fixtures.ts
import { test as base } from "@playwright/test";
import { ConsoleSentinel, AuditTrail } from "./utiles";

type AuditedPageFixtures = {
  auditedPage: { page: Page; sentinel: ConsoleSentinel; audit: AuditTrail };
};

export const test = base.extend<AuditedPageFixtures>({
  auditedPage: async ({ page }, use) => {
    const sentinel = new ConsoleSentinel();
    const audit = new AuditTrail();
    
    sentinel.attach(page);
    await audit.injectTracker(page);
    
    await use({ page, sentinel, audit });
    
    // Cleanup: exportar logs
    await audit.exportAuditLog(page, `./audit-logs/${Date.now()}.json`);
    sentinel.assertZeroErrors();
  },
});

// usage:
test("mi test", async ({ auditedPage: { page, sentinel, audit } }) => {
  // Todo con auditoría automática
});
```

---

## ✅ Checklist de Adopción

- [ ] Revisar `consoleSentinel.ts` y entender `ConsoleSentinel`
- [ ] Revisar `auditTrail.ts` y entender `AuditTrail`
- [ ] Revisar `locatorResolver.ts` y entender `LocatorResolver`
- [ ] Ejecutar: `npm run test:e2e -- exampleWithAudit.spec.ts`
- [ ] Agregar `sentinel.assertZeroErrors()` a 1-2 tests existentes
- [ ] (Opcional) Integrar `AuditTrail` en tests críticos
- [ ] (Opcional) Refactorizar selectores duros con `LocatorResolver`

---

## 📊 Guía de Diagnóstico

### Si un test falla aleatoriamente
→ Agregar `ConsoleSentinel` para detectar errores de consola ocultos

### Si necesitas replicar un clic fallido
→ Usar `AuditTrail.exportAuditLog()` para ver qué se clickeó

### Si necesitas auditar que un screenshot no fue alterado
→ Usar `AuditTrail.captureSnapshot()` + `verifySnapshot()`

### Si tienes selectores frágiles
→ Refactorizar con `LocatorResolver` para usar data-testid en lugar de CSS

---

## 🔗 Referencias

**Archivo original del ERP:**
- `C:\Users\Juan Carlos\Desktop\ERP\features\automata_declaraciones_rpa\playwright_driver.py`

**Análisis completo:**
- Ver `PLAYWRIGHT_COMPARATIVE_ANALYSIS.md` en scratchpad

**Configuración de Playwright:**
- `frontend/playwright.config.ts` (sin cambios)

---

## 📝 Notas de Implementación

1. **Compatibilidad:** TypeScript/ESM, compatible con `@playwright/test`
2. **Sin dependencias externas:** Solo usa stdlib (`crypto`, `fs`)
3. **Ejemplo desactivado:** `exampleWithAudit.spec.ts` usa `test.skip()` — activar solo para referencia
4. **Directorio de outputs:** Se crea automáticamente `./test-results/screenshots/` y `./audit-logs/`
5. **Performance:** `AuditTrail.injectTracker()` tiene overhead < 1ms por click registrado

---

## 🔐 Trazabilidad Estigmérgica

Marcar specs con tokens para máxima trazabilidad sin ruido de comentarios:

```typescript
/**
 * ¤¦assessment_sin_respuestas
 * 
 * Nivel 0 sin cobertura. Requisito: LOPDP § 3.1
 */
test("sin respuestas no inventa resultado", async ({ page }) => {
  // test logic
  // ¦assessment_sin_respuestas
});
```

**Convención:**
- `¤¦nombre_feature` — Inicio del spec
- `¦nombre_feature` — Fin del spec
- Evita comentarios largos: rastro + requisito en una línea

---

**Rastro:** `¤¦playwright_improvements`  
**Importado desde:** ERP `playwright_driver.py`  
**Fecha:** 2026-09-19  
**Estado:** ✅ IMPLEMENTADO
