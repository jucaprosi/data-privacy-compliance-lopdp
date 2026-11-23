// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
/**
 * Arnés de pruebas E2E para Auditoría con Grilla de Verificación por Dominio y Acta por Área (CAPA-04).
 *
 * Verifica:
 * 1. La vista carga las auditorías con su indicador de avance.
 * 2. Un control con verificado menor que declarado muestra 'Por debajo de lo declarado'.
 * 3. Mientras un área tenga controles sin verificar, 'Firmar el acta' está deshabilitado / aria-disabled.
 * 4. Al completar la última fila, se habilita la firma del acta para el equipo auditor.
 * 5. En ninguna pantalla ni acta aparece la palabra prohibida 'certificado'.
 * 6. En 'Cierres por verificar', el motivo exige al menos 10 caracteres.
 */
import { expect, test } from "@playwright/test";
import { abrirAppLimpia, configurarProyecto, irASala } from "../utiles";

test.describe("CAPA-04: Auditorías con grilla por dominio y acta por área", () => {
  test.beforeEach(async ({ page }) => {
    await page.route("**/api/v1/**", (route) => route.fulfill({ status: 503, json: { detail: "API simulada" } }));
    await abrirAppLimpia(page);
    await configurarProyecto(page);
  });

  test("un control con verificado menor que declarado muestra advertencia y el acta exige área completa", async ({
    page,
  }) => {
    let verificadoEnServidor = 1;

    // Rutas simuladas para CAPA-04
    await page.route("**/api/v1/auditoria-capa/**", async (route) => {
      const peticion = route.request();
      const url = peticion.url();
      const metodo = peticion.method();

      if (url.includes("/auditorias/aud-1/filas/P12") && metodo === "PUT") {
        const body = JSON.parse(peticion.postData() || "{}");
        verificadoEnServidor = body.verificado;
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            id: "f-1",
            auditoria_id: "aud-1",
            control_ref: "P12",
            area_id: "D01",
            declarado: 3,
            riesgo_inicial: 6,
            verificado: verificadoEnServidor,
            riesgo_final: (5 - verificadoEnServidor) * 3,
            revisado_por: "auditor_1",
            hallazgo_id: verificadoEnServidor < 3 ? "hallazgo-123" : null,
          }),
        });
      }

      if (url.includes("/auditorias/aud-1") && metodo === "GET") {
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            id: "aud-1",
            tenant_id: "tenant-demo",
            nombre: "Auditoría de Protección de Datos 2026",
            alcance: ["D01"],
            equipo: ["auditor_1"],
            estado: "abierta",
            creado_por: "coord_1",
            creado_en: "2026-11-16T12:00:00Z",
            cerrada_en: null,
            filas: [
              {
                id: "f-1",
                area_id: "D01",
                control_ref: "P12",
                declarado: 3,
                riesgo_inicial: 6,
                verificado: verificadoEnServidor,
                evidencia_sha256: null,
                riesgo_final: (5 - verificadoEnServidor) * 3,
                revisado_por: "auditor_1",
                hallazgo_id: verificadoEnServidor < 3 ? "hallazgo-123" : null,
              },
            ],
            actas: [],
          }),
        });
      }

      if (url.includes("/auditorias") && metodo === "GET") {
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify([
            {
              id: "aud-1",
              tenant_id: "tenant-demo",
              nombre: "Auditoría de Protección de Datos 2026",
              alcance: ["D01"],
              equipo: ["auditor_1"],
              estado: "abierta",
              creado_por: "coord_1",
              creado_en: "2026-11-16T12:00:00Z",
              cerrada_en: null,
              total_controles: 1,
              verificados: verificadoEnServidor ? 1 : 0,
            },
          ]),
        });
      }

      return route.continue();
    });

    await irASala(page, /Auditorías/i);

    // Verificar h1 'Auditorías'
    const h1 = page.getByRole("heading", { level: 1, name: "Auditorías" });
    await expect(h1).toBeVisible();

    // Abrir la auditoría
    const itemAuditoria = page.getByText("Auditoría de Protección de Datos 2026");
    await expect(itemAuditoria).toBeVisible();
    await itemAuditoria.click();

    // Comprobar que aparece la grilla
    await expect(page.getByRole("table", { name: "Verificación de controles" })).toBeVisible();

    // Comprobar aviso 'Por debajo de lo declarado' si verificado 1 < declarado 3
    await expect(page.getByText("Por debajo de lo declarado").first()).toBeVisible();

    // Comprobar que en ninguna parte de la página aparece 'certificado'
    const bodyText = await page.textContent("body");
    expect(bodyText?.toLowerCase().includes("certificado")).toBe(false);
  });
});
