/**
 * Audit trail y certificación notarial de screenshots (inspirado en ERP TRP).
 * Registra cada click con XPath, coordenadas y atributos para trazabilidad.
 *
 * Uso en tests:
 * ```typescript
 * test("mi test", async ({ page }) => {
 *   await AuditTrail.injectTracker(page);
 *   // ... test logic ...
 *   const log = await AuditTrail.getClickLog(page);
 *   console.log("Clics registrados:", log);
 *   await AuditTrail.captureSnapshot(page, "mi-screenshot");
 * });
 * ```
 */
import { type Page } from "@playwright/test";
import * as crypto from "crypto";
import * as fs from "fs";
import * as path from "path";

export interface ClickEntry {
  timestamp: string;
  tag: string;
  id: string;
  class: string;
  testId?: string;
  text?: string;
  x: number;
  y: number;
  width: number;
  height: number;
  xpath?: string;
}

export interface SnapshotMetadata {
  timestamp: string;
  path: string;
  sha256: string;
  bytes: number;
  url: string;
}

export class AuditTrail {
  /**
   * Inyecta un tracker de clics en la página para registrar audit trail.
   * Cada click se registra en window.auditLog (accesible desde tests).
   */
  static async injectTracker(page: Page): Promise<void> {
    await page.evaluate(() => {
      if (!(window as any).auditLog) {
        (window as any).auditLog = [];

        // Helper para calcular XPath
        function getXPath(el: Element): string {
          if (!el || el.nodeType !== 1) return "";
          if ((el as any).id) return `//*[@id="${(el as any).id}"]`;

          const parts: string[] = [];
          let current: Element | null = el;

          while (current && current.nodeType === 1) {
            let index = 1;
            let sibling = current.previousElementSibling;

            while (sibling) {
              if (sibling.nodeName === current.nodeName) index++;
              sibling = sibling.previousElementSibling;
            }

            parts.unshift(`${current.nodeName.toLowerCase()}[${index}]`);
            current = current.parentElement;
          }

          return "/" + parts.join("/");
        }

        document.addEventListener(
          "click",
          (e: Event) => {
            const clickEvent = e as MouseEvent;
            const target = clickEvent.target as HTMLElement;
            const rect = target.getBoundingClientRect();

            (window as any).auditLog.push({
              timestamp: new Date().toISOString(),
              tag: target.tagName.toLowerCase(),
              id: target.id || "",
              class: target.className || "",
              testId: target.getAttribute("data-testid") || "",
              text: (target.textContent || "").substring(0, 100).trim(),
              x: Math.round(rect.x),
              y: Math.round(rect.y),
              width: Math.round(rect.width),
              height: Math.round(rect.height),
              xpath: getXPath(target),
            });
          },
          true
        );
      }
    });
  }

  /**
   * Recupera el audit log de clics desde la página.
   */
  static async getClickLog(page: Page): Promise<ClickEntry[]> {
    try {
      return await page.evaluate(() => (window as any).auditLog || []);
    } catch {
      return [];
    }
  }

  /**
   * Limpia el audit log.
   */
  static async clearClickLog(page: Page): Promise<void> {
    await page.evaluate(() => {
      (window as any).auditLog = [];
    });
  }

  /**
   * Captura un screenshot y genera certificado notarial con hash SHA-256.
   */
  static async captureSnapshot(
    page: Page,
    name: string,
    dir = "./test-results/screenshots"
  ): Promise<SnapshotMetadata> {
    // Asegurar directorio
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }

    const filename = `${name}-${Date.now()}.png`;
    const filepath = path.join(dir, filename);

    // Tomar screenshot
    await page.screenshot({ path: filepath, fullPage: true });

    // Calcular SHA-256
    const data = fs.readFileSync(filepath);
    const hash = crypto.createHash("sha256").update(data).digest("hex");

    // Generar metadata
    const metadata: SnapshotMetadata = {
      timestamp: new Date().toISOString(),
      path: filepath,
      sha256: hash,
      bytes: data.length,
      url: page.url(),
    };

    // Guardar metadata
    const metaPath = `${filepath}.meta.json`;
    fs.writeFileSync(metaPath, JSON.stringify(metadata, null, 2), "utf-8");

    console.log(`📸 Screenshot: ${filepath}`);
    console.log(`   SHA-256: ${hash}`);
    console.log(`   Meta: ${metaPath}`);

    return metadata;
  }

  /**
   * Verifica la integridad de un screenshot usando su metadata.
   */
  static verifySnapshot(screenshotPath: string): boolean {
    const metaPath = `${screenshotPath}.meta.json`;

    if (!fs.existsSync(metaPath)) {
      console.warn(`No metadata found for ${screenshotPath}`);
      return false;
    }

    const metadata: SnapshotMetadata = JSON.parse(
      fs.readFileSync(metaPath, "utf-8")
    );
    const data = fs.readFileSync(screenshotPath);
    const currentHash = crypto.createHash("sha256").update(data).digest("hex");

    const isValid = currentHash === metadata.sha256;
    console.log(
      `🔐 Verification ${isValid ? "✅" : "❌"}: ${screenshotPath}`
    );
    if (!isValid) {
      console.log(
        `   Expected: ${metadata.sha256}\n   Got: ${currentHash}`
      );
    }

    return isValid;
  }

  /**
   * Exporta el audit log a un archivo JSON para análisis.
   */
  static async exportAuditLog(
    page: Page,
    outputPath: string
  ): Promise<void> {
    const log = await this.getClickLog(page);

    const dir = path.dirname(outputPath);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }

    fs.writeFileSync(
      outputPath,
      JSON.stringify(
        {
          timestamp: new Date().toISOString(),
          url: page.url(),
          clicksCount: log.length,
          clicks: log,
        },
        null,
        2
      ),
      "utf-8"
    );

    console.log(`📋 Audit log exported to ${outputPath}`);
  }
}
