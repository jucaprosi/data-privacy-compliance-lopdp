/**
 * Resolutor de localizadores con Jerarquía PCP (Priority/Confidence/Precision).
 * Inspirado en la implementación ERP: reduce duplicación de selectores.
 *
 * Jerarquía de resolución (en orden de preferencia):
 * N1: ID (#element)
 * N2: data-testid ([data-testid="..."])
 * N3: role (role=name)
 * N4: name/placeholder
 * N5: CSS
 * N6: text ("text=...")
 *
 * Uso:
 * ```typescript
 * const button = LocatorResolver.resolve(page, "data-testid=btn-guardar");
 * await button.click();
 *
 * // O con chaining inteligente:
 * await LocatorResolver.resolve(page, "#myForm input[type=email]").fill("test@example.com");
 * ```
 */
import { type Locator, type Page } from "@playwright/test";

export class LocatorResolver {
  /**
   * Resuelve un selector a un Locator usando la jerarquía PCP.
   * Soporta múltiples formatos de selector para máxima flexibilidad.
   */
  static resolve(page: Page, selector: string): Locator {
    const s = selector.trim();

    // N1: ID - formato: #myId
    if (s.startsWith("#")) {
      return page.locator(s);
    }

    // N2: data-testid - múltiples formatos soportados
    if (s.includes("data-testid=")) {
      const match = s.match(/data-testid=["']?([^"'\]]+)["']?/);
      if (match?.[1]) {
        return page.getByTestId(match[1]);
      }
    }

    if (s.startsWith("[data-testid=")) {
      const match = s.match(/data-testid=["']?([^"'\]]+)["']?/);
      if (match?.[1]) {
        return page.getByTestId(match[1]);
      }
    }

    // N3: role - formato: role=button, role=link[name="texto"]
    if (s.startsWith("role=")) {
      const roleMatch = s.match(
        /role=(\w+)(?:\[name=["']?([^"'\]]+)["']?\])?/
      );
      if (roleMatch) {
        const roleName = roleMatch[1] as any;
        const roleName2 = roleMatch[2];

        if (roleName2) {
          return page.getByRole(roleName, { name: roleName2 });
        }
        return page.getByRole(roleName);
      }
    }

    // N4: Placeholder
    if (s.startsWith("placeholder=")) {
      const match = s.match(/placeholder=["']?([^"']+)["']?/);
      if (match?.[1]) {
        return page.getByPlaceholder(match[1]);
      }
    }

    // N6: text - formato: text="algo" o text=/regex/
    if (s.startsWith("text=")) {
      let textValue = s.replace(/^text=["']?/, "").replace(/["']?$/, "");

      // Regex support
      if (textValue.startsWith("/") && textValue.endsWith("/")) {
        const pattern = textValue.slice(1, -1);
        return page.getByText(new RegExp(pattern));
      }

      return page.getByText(textValue);
    }

    // N5: CSS fallback
    return page.locator(s);
  }

  /**
   * Resuelve múltiples selectores y retorna el primero visible.
   * Útil como fallback cuando hay variación en selectores.
   */
  static async resolveAny(
    page: Page,
    selectors: string[]
  ): Promise<Locator | null> {
    for (const selector of selectors) {
      const locator = this.resolve(page, selector);
      if (await locator.isVisible().catch(() => false)) {
        return locator;
      }
    }
    return null;
  }

  /**
   * Resuelve un selector y espera a que sea visible con timeout.
   */
  static async resolveAndWait(
    page: Page,
    selector: string,
    timeoutMs = 10000
  ): Promise<Locator> {
    const locator = this.resolve(page, selector);
    await locator.waitFor({ state: "visible", timeout: timeoutMs });
    return locator;
  }

  /**
   * Construye un selector data-testid de forma segura.
   */
  static testId(id: string): string {
    return `[data-testid="${id}"]`;
  }

  /**
   * Construye un selector role de forma segura.
   */
  static role(
    role: string,
    options?: { name?: string | RegExp; exact?: boolean }
  ): string {
    if (!options?.name) {
      return `role=${role}`;
    }

    const nameValue =
      options.name instanceof RegExp
        ? `/${options.name.source}/`
        : `"${options.name}"`;
    return `role=${role}[name=${nameValue}]`;
  }

  /**
   * Construye un selector text de forma segura.
   */
  static text(text: string | RegExp): string {
    if (text instanceof RegExp) {
      return `text=/${text.source}/`;
    }
    return `text="${text}"`;
  }

  /**
   * Construye un selector placeholder de forma segura.
   */
  static placeholder(text: string): string {
    return `placeholder="${text}"`;
  }
}

/**
 * Exports helper para una sintaxis más limpia en tests.
 */
export const L = LocatorResolver;
