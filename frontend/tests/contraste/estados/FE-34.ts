// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
// ¤frontend-ide ¤arbitro
import type { Page } from "@playwright/test";
import { credencialSimulada, fijarAjustes, simularApi } from "../../auth/utilesAuth";

/**
 * Estados de FE-34 que `rutas.spec.ts` no alcanza solo (abrir un diálogo, abrir una vista NIIF con sus datos de prueba).
 * Clave: «<ruta o vista:id> · <nombre del estado>». El paso se ejecuta con la página cargada y el tema puesto; la prueba mide después.
 * La ficha FE-34 añade aquí sus pasos antes de quitar la ruta o vista de su archivo de pendientes.
 */
export const ESTADOS: Record<string, (page: Page) => Promise<void>> = {
  /**
   * `/organizaciones` solo pinta su pantalla con autenticación `oidc`; en modo `headers` (el de la medición por defecto)
   * redirige al tablero y lo que se mide es el marco de FE-35. Aquí se entra con sesión y dos organizaciones.
   */
  "/organizaciones · lista con credencial pendiente": async (page) => {
    const tema = await page.evaluate(() => (document.documentElement.classList.contains("theme-dark") ? "theme-dark" : "theme-light"));
    await fijarAjustes(page, { modo: "oidc", tenant: null });
    // Primer ingreso de quien tiene varias organizaciones: la credencial queda pendiente hasta que elige una.
    await page.addInitScript((token) => window.sessionStorage.setItem("lopdp-credencial-pendiente-v1", token), credencialSimulada().token);
    await simularApi(page, {
      organizaciones: [
        { tenant_id: "tenant-a", nombre_comercial: "Cooperativa Andina", roles: ["dpo"] },
        { tenant_id: "tenant-b", nombre_comercial: "Banco Bolívar", roles: ["implementador", "dpo"] },
      ],
    });
    await page.goto("/organizaciones");
    await page.getByRole("button", { name: /Cooperativa Andina/ }).waitFor();
    await page.evaluate((t) => { document.documentElement.classList.remove("theme-light", "theme-dark"); document.documentElement.classList.add(t); }, tema);
  },
};

/**
 * Preparaciones que corren antes de `page.goto` (FE-42 R3a). `vista:configuracion` solo está en el dock en modo `alta`
 * (`vistasPermitidas`, dashboardNavigation.ts): se siembra el store local sin configurar para que el tablero arranque ahí.
 */
export const PREPARACIONES: Record<string, (page: Page) => Promise<void>> = {
  "vista:configuracion": async (page) => {
    await page.addInitScript(() => {
      try {
        // La misma clave guarda el tema que fija la prueba: se fusiona, no se pisa.
        const previo = JSON.parse(window.localStorage.getItem("jubys-audit-storage") ?? "{}");
        window.localStorage.setItem(
          "jubys-audit-storage",
          JSON.stringify({ version: 6, ...previo, state: { ...previo.state, isConfigured: false, normativaSeleccionada: null, activeView: "configuracion" } }),
        );
      } catch {
        // Almacenamiento bloqueado: el tablero arranca sin configurar de todos modos.
      }
    });
  },
};

/** Vistas que se miden sin `configurarProyecto` (FE-44 R5): `medirVista` las abre con el proyecto sin configurar. */
export const SIN_CONFIGURAR = new Set(["vista:configuracion"]);
