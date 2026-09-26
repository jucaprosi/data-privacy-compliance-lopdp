/**
 * Ejemplo de test con auditoría completa.
 * Demuestra el uso de ConsoleSentinel, AuditTrail y LocatorResolver.
 *
 * Ejecutar: npm run test:e2e -- exampleWithAudit.spec.ts
 *
 * Este spec es OPCIONAL y solo sirve como referencia.
 * Desactivar después de verificación con: test.skip()
 */
import { expect, test } from "@playwright/test";

import {
  AuditTrail,
  ConsoleSentinel,
  L,
  abrirAppLimpia,
  configurarProyecto,
  irASala,
  LocatorResolver,
} from "./utiles";

test.describe("Ejemplo: Dashboard con Auditoría Completa", () => {
  test.skip("demo de auditoría y monitoreo", async ({ page }) => {
    // 1. Inicializar Centinela y Audit Trail
    const sentinel = new ConsoleSentinel();
    sentinel.attach(page);
    await AuditTrail.injectTracker(page);

    // 2. Setup de la app
    await abrirAppLimpia(page);
    console.log("App limpia abierta");

    // 3. Configurar proyecto
    await configurarProyecto(page);
    console.log("Proyecto configurado");

    // 4. Navegar a Dashboard Central
    await irASala(page, /Dashboard Central/);
    console.log("Navegado a Dashboard Central");

    // 5. Usar LocatorResolver para interactuar
    // (Este es un ejemplo de sintaxis - adaptarlo a tu interfaz real)
    const dashboardTitle = LocatorResolver.resolve(
      page,
      L.text(/Tablero de resultados/)
    );
    await expect(dashboardTitle).toBeVisible();

    // 6. Capturar audit trail
    const clickLog = await AuditTrail.getClickLog(page);
    console.log(`📋 Clics registrados: ${clickLog.length}`);
    if (clickLog.length > 0) {
      console.log("Primeros 3 clics:");
      clickLog.slice(0, 3).forEach((click, i) => {
        console.log(
          `  ${i + 1}. ${click.tag}#${click.id} @ (${click.x}, ${click.y})`
        );
      });
    }

    // 7. Capturar screenshot notarial
    const snapshot = await AuditTrail.captureSnapshot(
      page,
      "dashboard-result"
    );
    console.log(`✅ Screenshot: ${snapshot.path}`);
    console.log(`   Hash: ${snapshot.sha256.substring(0, 16)}...`);

    // 8. Exportar audit log
    await AuditTrail.exportAuditLog(
      page,
      "./test-results/audit-logs/dashboard-example.json"
    );

    // 9. Verificar zero errors en consola
    const report = sentinel.report();
    console.log("📊 Reporte de Consola:");
    console.log(`   Errores: ${report.errors.length}`);
    console.log(`   Warnings: ${report.warnings.length}`);
    console.log(`   Logs: ${report.logsCount}`);

    sentinel.assertZeroErrors();

    expect(report.totalEvents).toBeGreaterThanOrEqual(0);
  });

  test.skip("demo: verificación de integrity de screenshot", async ({
    page,
  }) => {
    await abrirAppLimpia(page);
    await configurarProyecto(page);

    // Capturar snapshot
    const metadata = await AuditTrail.captureSnapshot(
      page,
      "integrity-test"
    );
    console.log(`Screenshot guardado en: ${metadata.path}`);

    // Verificar integridad
    const isValid = AuditTrail.verifySnapshot(metadata.path);
    expect(isValid).toBe(true);

    // Modificar archivo para demostrar falso positivo
    // (NO descomentar en CI - solo para local debugging)
    // fs.writeFileSync(metadata.path, Buffer.from([0, 0, 0]));
    // const isValidAfterChange = AuditTrail.verifySnapshot(metadata.path);
    // expect(isValidAfterChange).toBe(false);
  });

  test.skip("demo: LocatorResolver con múltiples estrategias", async ({
    page,
  }) => {
    await abrirAppLimpia(page);

    // Probar diferentes estrategias de resolución
    const testLocators = [
      L.testId("dashboard-card"),
      L.role("button", { name: "Dashboard Central" }),
      L.text(/Tablero/),
    ];

    console.log("Intentando resolver localizadores...");
    for (const locator of testLocators) {
      try {
        const resolved = LocatorResolver.resolve(page, locator);
        const isVisible = await resolved
          .isVisible()
          .catch(() => false);
        console.log(
          `  ${locator}: ${isVisible ? "✅ visible" : "❌ no visible"}`
        );
      } catch (e) {
        console.log(`  ${locator}: ⚠️ error`);
      }
    }
  });
});
