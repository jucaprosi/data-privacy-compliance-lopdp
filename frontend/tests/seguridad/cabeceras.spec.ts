/**
 * Arnés de interfaz de SEC-06: cabeceras HTTP de seguridad del frontend.
 *
 * Comprueba las cabeceras REALES que emite el servidor de Next (no solo lo declarado en
 * next.config.ts) y que la interfaz sigue funcionando con ellas. La CSP completa está en modo
 * informe: sus avisos aparecen en la consola del navegador y aquí solo se registran, no se
 * convierten en fallos (decidir si pasar a modo obligatorio es del propietario).
 */
import { expect, test } from "@playwright/test";

const RUTAS = ["/", "/dashboard"];

for (const ruta of RUTAS) {
  test.describe(`Cabeceras de seguridad en ${ruta}`, () => {
    test("emite las cabeceras de endurecimiento con su valor", async ({ page }) => {
      const respuesta = await page.goto(ruta);
      expect(respuesta?.status()).toBe(200);
      const h = respuesta!.headers();

      expect(h["x-content-type-options"]).toBe("nosniff");
      expect(h["x-frame-options"]).toBe("DENY");
      expect(h["referrer-policy"]).toBe("strict-origin-when-cross-origin");
      expect(h["permissions-policy"]).toContain("camera=()");
      expect(h["permissions-policy"]).toContain("geolocation=()");

      const hsts = h["strict-transport-security"];
      expect(hsts).toBeTruthy();
      expect(Number(/max-age=(\d+)/.exec(hsts)?.[1])).toBeGreaterThanOrEqual(31_536_000);
    });

    test("la única CSP obligatoria es frame-ancestors; la política completa va en modo informe", async ({ page }) => {
      const respuesta = await page.goto(ruta);
      const h = respuesta!.headers();

      expect(h["content-security-policy"]).toBe("frame-ancestors 'none'");
      const informe = h["content-security-policy-report-only"];
      expect(informe).toContain("default-src 'self'");
      expect(informe).toContain("object-src 'none'");
      expect(informe).toContain("https://*.r2.cloudflarestorage.com");
    });

    test("la interfaz sigue funcionando: la CSP en modo informe no bloquea nada", async ({ page }) => {
      const bloqueos: string[] = [];
      page.on("console", (mensaje) => {
        const texto = mensaje.text();
        // Chrome registra como `error` («Refused to …») lo que una política OBLIGATORIA bloquea;
        // lo que solo avisa una política en modo informe llega como `info` y dice «report-only».
        if (mensaje.type() === "error" && /Content Security Policy|Refused to/i.test(texto)) bloqueos.push(texto);
      });

      await page.goto(ruta);
      await expect(page.getByRole("textbox", { name: /Razón Social/ })).toBeVisible();

      expect(bloqueos, "ninguna política obligatoria debe estar bloqueando recursos").toEqual([]);
    });
  });
}

test("no se puede incrustar el panel en un iframe ajeno (clickjacking)", async ({ page }) => {
  await page.goto("/");
  const resultado = await page.evaluate(async () => {
    const marco = document.createElement("iframe");
    marco.src = "/dashboard";
    document.body.appendChild(marco);
    // Un documento bloqueado por frame-ancestors / X-Frame-Options carga una página de error vacía.
    await new Promise((r) => setTimeout(r, 1500));
    try {
      return { accesible: Boolean(marco.contentDocument?.body?.innerText?.trim()) };
    } catch {
      return { accesible: false };
    }
  });
  // Mismo origen: X-Frame-Options DENY lo bloquea igualmente, así que no debe quedar contenido legible.
  expect(resultado.accesible).toBe(false);
});

test("resumen informativo: avisos de la CSP en modo informe (no falla)", async ({ page }, testInfo) => {
  const porDirectiva = new Map<string, number>();
  page.on("console", (mensaje) => {
    const texto = mensaje.text();
    if (!/report-only/i.test(texto)) return;
    const directiva = /(script-src|style-src|img-src|font-src|connect-src|default-src|frame-src|object-src)/.exec(texto)?.[1] ?? "otra";
    porDirectiva.set(directiva, (porDirectiva.get(directiva) ?? 0) + 1);
  });
  for (const ruta of RUTAS) {
    await page.goto(ruta);
    await page.waitForTimeout(800);
  }
  const lineas = [...porDirectiva].sort().map(([d, n]) => `${d}: ${n} avisos`);
  const resumen = lineas.join("\n") || "(sin avisos)";
  await testInfo.attach("avisos-csp-informe.txt", { body: resumen, contentType: "text/plain" });
  console.log(`CSP informe — avisos por directiva (servidor de pruebas: en desarrollo suma el eval de HMR): ${lineas.join("; ") || "ninguno"}`);
});
