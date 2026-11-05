// ¤adpa ¤rbac-tenant ¤arbitro
import { expect, test, type Page } from "@playwright/test";
import { abrirAppLimpia, barraDeMenus, configurarProyecto } from "../utiles";

const documento = {
  id: "doc-303", codigo: "BIB-303", nombre: "Política verificada", origen: "plantilla",
  plantilla_version: "1.0", estado: "aprobado", editado: false, proxima_revision: "2027-11-03",
  revision: 2, creado_por: "u", creado_en: "2026-11-03T10:00:00Z", actualizado_en: "2026-11-03T10:00:00Z",
};
const completo = { ...documento, plantilla_id: "p", contenido_markdown: "# Política", variables_faltantes: [],
  aprobado_por: "r", aprobado_en: "2026-11-03T10:00:00Z", sha256: "a".repeat(64), fecha_emision: "2026-11-03" };
const enlace = { id: "e-1", documento_id: documento.id, documento_revision: 2, accion_id: "a-1",
  accion_titulo: "Capacitar al personal", accion_estado: "en_progreso", requisito: "P7", hallazgo_id: null,
  hallazgo_titulo: null, hallazgo_origen: null, hallazgo_origen_ref: null, pregunta: null,
  assessment_version: null, creado_por: "u", creado_en: "2026-11-03T10:00:00Z" };
const evidencia = { id: "ev-1", accion_id: "a-1", titulo: "Acta de capacitación", version: "1.0",
  sha256: "b".repeat(64), clasificacion: "interna", permisos: ["coordinador", "dpo"], fecha: "2026-11-01",
  control_ref: "P7", documento_id: null, documento_revision: null, creado_por: "autor", creado_en: "2026-11-01T10:00:00Z" };
const rechazo = { id: "v-1", accion_id: "a-1", evidencia_id: "ev-1", criterio: "Cubre al 100 % del personal",
  evidencia_legible: false, resultado: "no_conforme", eficacia_requerida: false, eficacia_conforme: null,
  revisor: "revisora", fecha: "2026-11-02", observaciones: "Acta ilegible", creado_en: "2026-11-02T10:00:00Z" };

async function abrir(page: Page, verificaciones: unknown[] = [rechazo]) {
  const enviados: unknown[] = [];
  await page.addInitScript(() => { window.__LOPDP_AUTH_PRUEBAS__ = { modo: "headers", tenant: "tenant-a" }; });
  await page.route("**/api/v1/**", (r) => r.fulfill({ status: 503, json: { detail: "API simulada" } }));
  await page.route("**/api/v1/biblioteca/documentos", (r) => r.fulfill({ json: [documento] }));
  await page.route("**/api/v1/biblioteca/documentos/pendientes", (r) => r.fulfill({ json: { borrador: 0, en_revision: 0, por_vencer: 0, vencidos: 0, total: 0 } }));
  await page.route("**/api/v1/biblioteca/documentos/doc-303", (r) => r.fulfill({ json: completo }));
  await page.route("**/api/v1/biblioteca/documentos/doc-303/enlaces", (r) => r.fulfill({ json: [enlace] }));
  let lista = verificaciones;
  await page.route("**/api/v1/biblioteca/verificaciones/acciones/a-1", (r) => r.fulfill({ json: {
    accion_id: "a-1", veredicto: lista.length ? (lista.at(-1) as { resultado: string }).resultado : "pendiente",
    evidencias: [evidencia], verificaciones: lista } }));
  await page.route("**/api/v1/biblioteca/verificaciones/acciones/a-1/verificaciones", async (r) => {
    const cuerpo = r.request().postDataJSON();
    enviados.push(cuerpo);
    if (cuerpo.resultado === "conforme" && !cuerpo.evidencia_legible) {
      return r.fulfill({ status: 422, json: { detail: "Una evidencia ilegible no puede declararse conforme." } });
    }
    lista = [...lista, { ...rechazo, id: "v-2", ...cuerpo, revisor: "revisora" }];
    return r.fulfill({ status: 201, json: { accion_id: "a-1", veredicto: cuerpo.resultado, evidencias: [evidencia], verificaciones: lista } });
  });
  await abrirAppLimpia(page); await configurarProyecto(page, "Entidad BIB-303");
  await barraDeMenus(page).getByRole("button", { name: "Biblioteca", exact: true }).click();
  await page.getByRole("group", { name: "Submenús de Biblioteca" }).getByRole("button", { name: /^Documentos y plantillas/ }).click();
  const vista = page.getByRole("region", { name: "Biblioteca", exact: true });
  await vista.getByRole("button", { name: "Elegir Política verificada" }).click();
  return { panel: vista.getByRole("region", { name: "Evidencias y verificación" }), enviados };
}

test("muestra evidencia con versión, hash, clasificación, permisos y fecha, y el historial", async ({ page }, info) => {
  test.skip(info.project.name === "produccion", "La API simulada solo corre en desarrollo.");
  const { panel } = await abrir(page);
  await expect(panel).toContainText("Un documento aprobado no equivale a implementación");
  await expect(panel.getByTestId("veredicto")).toHaveText("No conforme: la acción sigue abierta");
  const ev = panel.getByRole("list", { name: "Evidencias registradas" });
  await expect(ev).toContainText("Acta de capacitación · versión 1.0 · interna · 2026-11-01");
  await expect(ev).toContainText("Hash bbbbbbbbbbbb… · permisos coordinador, dpo · control P7");
  await expect(panel.getByRole("list", { name: "Historial de verificaciones" })).toContainText("Acta ilegible");
  await expect(panel.getByRole("alert")).toHaveCount(0);
});

test("un conforme ilegible se rechaza y uno legible se suma sin borrar el rechazo previo", async ({ page }, info) => {
  test.skip(info.project.name === "produccion", "La API simulada solo corre en desarrollo.");
  const { panel, enviados } = await abrir(page);
  await panel.getByLabel("Criterio de aceptación").fill("Cubre al 100 % del personal");
  await panel.getByLabel("Resultado").selectOption("conforme");
  await panel.getByRole("button", { name: "Guardar verificación" }).click();
  await expect(panel).toContainText("Una evidencia ilegible no puede declararse conforme.");
  await panel.getByLabel("Evidencia legible").check();
  await panel.getByRole("button", { name: "Guardar verificación" }).click();
  await expect(panel.getByTestId("veredicto")).toHaveText("Conforme: la acción puede cerrarse");
  const historial = panel.getByRole("list", { name: "Historial de verificaciones" }).getByRole("listitem");
  await expect(historial).toHaveCount(2);
  await expect(historial.first()).toContainText("No conforme");
  expect(enviados.at(-1)).toMatchObject({ evidencia_id: "ev-1", evidencia_legible: true, resultado: "conforme" });
  expect(JSON.stringify(enviados)).not.toContain("revisor");
});
