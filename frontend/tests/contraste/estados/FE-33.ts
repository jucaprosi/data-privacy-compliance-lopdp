// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
// ¤frontend-ide ¤arbitro
import type { Page } from "@playwright/test";

/**
 * Estados de FE-33 que `rutas.spec.ts` no alcanza solo (abrir un diálogo, abrir una vista NIIF con sus datos de prueba).
 * Clave: «<ruta o vista:id> · <nombre del estado>». El paso se ejecuta con la página cargada y el tema puesto; la prueba mide después.
 * La ficha FE-33 añade aquí sus pasos antes de quitar la ruta o vista de su archivo de pendientes.
 */
export const ESTADOS: Record<string, (page: Page) => Promise<void>> = {};

/**
 * Preparaciones de FE-33 (FE-41 R5): `rutas.spec.ts` las ejecuta antes de `page.goto`. Clave: la ruta.
 * Simulan la respuesta del token (la prueba abre `/aceptar/ejemplo` y `/proveedor/ejemplo`), sin red.
 */
export const PREPARACIONES: Record<string, (page: Page) => Promise<void>> = {
  "/aceptar/[token]": async (page) => {
    await page.route("**/api/v1/aceptar/ejemplo", (r) =>
      r.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ nombre_documento: "Política de privacidad v1", organizacion: "Acme Ecuador", sha256: "a".repeat(64) }),
      }),
    );
  },
  "/proveedor/[token]": async (page) => {
    await page.route("**/api/v1/publico/proveedor/ejemplo", (r) =>
      r.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          id: "cq-1",
          tenant_id: "t-1",
          organizacion: "Acme Ecuador",
          caduca_en: "2026-12-31T12:00:00Z",
          version_cuestionario: "1.0",
          preguntas: [
            { id: "p1", enunciado: "¿Cuenta con una política de seguridad de la información?", tipo: "si_no", obligatoria: true, cita: "LOPDP art. 37" },
            { id: "p2", enunciado: "Describa las medidas de cifrado que aplica.", tipo: "texto", obligatoria: false, cita: "LOPDP art. 37" },
          ],
        }),
      }),
    );
  },
};
