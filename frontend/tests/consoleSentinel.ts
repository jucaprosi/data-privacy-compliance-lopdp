/**
 * Monitoreo de consola y errores de página (inspirado en ERP).
 * Útil para detectar regresiones silenciosas que solo aparecen en consola.
 *
 * Uso en tests:
 * ```typescript
 * const sentinel = new ConsoleSentinel();
 * sentinel.attach(page);
 * // ... test logic ...
 * sentinel.assertZeroErrors(); // falla si hay errores
 * console.log(sentinel.report());
 * ```
 */
import { expect, type Page } from "@playwright/test";

export class ConsoleSentinel {
  private errors: string[] = [];
  private warnings: string[] = [];
  private logs: string[] = [];

  /**
   * Adjunta listeners a los eventos de consola de la página.
   */
  attach(page: Page): void {
    page.on("console", (msg) => {
      const text = msg.text();
      if (msg.type() === "error") {
        this.errors.push(text);
      } else if (msg.type() === "warning") {
        this.warnings.push(text);
      } else {
        this.logs.push(text);
      }
    });

    page.on("pageerror", (error) => {
      this.errors.push(`PageError: ${error.message}`);
    });
  }

  /**
   * Falla el test si se detectaron errores en la consola.
   */
  assertZeroErrors(): void {
    if (this.errors.length > 0) {
      throw new Error(
        `Centinela detectó ${this.errors.length} error(es) en consola:\n${this.errors.join("\n")}`
      );
    }
  }

  /**
   * Genera un reporte del monitoreo para debugging.
   */
  report() {
    return {
      errors: this.errors,
      warnings: this.warnings,
      logsCount: this.logs.length,
      totalEvents: this.errors.length + this.warnings.length + this.logs.length,
    };
  }

  /**
   * Retorna solo los errores capturados.
   */
  getErrors(): string[] {
    return [...this.errors];
  }

  /**
   * Retorna solo los warnings capturados.
   */
  getWarnings(): string[] {
    return [...this.warnings];
  }

  /**
   * Limpia todos los registros.
   */
  clear(): void {
    this.errors = [];
    this.warnings = [];
    this.logs = [];
  }
}
