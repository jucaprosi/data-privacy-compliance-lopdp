// ¤adpa ¤rbac-tenant ¤rat ¤arbitro
import { expect, test, type Page } from "@playwright/test";
import { abrirAppLimpia, barraDeMenus, configurarProyecto } from "../utiles";

const documento = {
  id: "doc-402", codigo: "BIB-402", nombre: "Política vinculada", origen: "plantilla",
  plantilla_version: "1.0", estado: "borrador", editado: false, proxima_revision: "2027-11-04",
  revision: 1, creado_por: "u", creado_en: "2026-11-04T10:00:00Z", actualizado_en: "2026-11-04T10:00:00Z",
};
const completo = { ...documento, plantilla_id: "p", contenido_markdown: "# Política", variables_faltantes: [],
  aprobado_por: null, aprobado_en: null, sha256: "a".repeat(64), fecha_emision: "2026-11-04" };

type Vinculo = { id: string; documento_id: string; tipo: string; ref: string; estado: string; creado_por: string; creado_en: string };

async function abrir(page: Page, rol: string, inicial: Vinculo[] = []) {
  let vinculos = [...inicial];
  const puts: unknown[] = [];
  await page.addInitScript(() => { window.__LOPDP_AUTH_PRUEBAS__ = { modo: "headers", tenant: "tenant-a" }; });
  await page.route("**/api/v1/**", (r) => r.fulfill({ status: 503, json: { detail: "API simulada" } }));
  await page.route("**/api/v1/organizacion/me/roles", (r) => r.fulfill({ json: [{ role: rol, tenant_id: "tenant-a" }] }));
  await page.route("**/api/v1/biblioteca/documentos", (r) => r.fulfill({ json: [documento] }));
  await page.route("**/api/v1/biblioteca/documentos/pendientes", (r) => r.fulfill({ json: { borrador: 1, en_revision: 0, por_vencer: 0, vencidos: 0, total: 1 } }));
  await page.route("**/api/v1/biblioteca/documentos/doc-402", (r) => r.fulfill({ json: completo }));
  await page.route("**/api/v1/biblioteca/documentos/doc-402/vinculos", async (r) => {
    if (r.request().method() === "PUT") {
      const entrada = r.request().postDataJSON() as { tratamientos: string[]; controles: string[]; tareas: string[] };
      puts.push(entrada);
      if (entrada.controles.includes("P99")) {
        return r.fulfill({ status: 422, json: { detail: { code: "VINCULO_REF_INEXISTENTE", message: "El tratamiento, control o tarea indicado no existe en tu organización." } } });
      }
      const previo = (tipo: string, ref: string) => vinculos.find((v) => v.tipo === tipo && v.ref === ref);
      const armar = (tipo: string, refs: string[]) => refs.map((ref) => previo(tipo, ref) ?? {
        id: `doc-402:${tipo}:${ref}`, documento_id: "doc-402", tipo, ref, estado: "vigente", creado_por: "u", creado_en: "2026-11-04T10:00:00Z" });
      vinculos = [...armar("control", entrada.controles), ...armar("tarea", entrada.tareas), ...armar("tratamiento", entrada.tratamientos)];
    }
    return r.fulfill({ json: { vinculos } });
  });
  await page.route("**/api/v1/biblioteca/tratamientos/*/documentos", (r) => {
    const id = decodeURIComponent(new URL(r.request().url()).pathname.split("/").at(-2) ?? "");
    const usan = vinculos.filter((v) => v.tipo === "tratamiento" && v.ref === id);
    return r.fulfill({ json: usan.map((v) => ({ documento_id: v.documento_id, codigo: documento.codigo, nombre: documento.nombre, estado_documento: "borrador", estado: v.estado })) });
  });
  await abrirAppLimpia(page); await configurarProyecto(page, "Entidad BIB-402");
  await barraDeMenus(page).getByRole("button", { name: "Biblioteca", exact: true }).click();
  await page.getByRole("group", { name: "Submenús de Biblioteca" }).getByRole("button", { name: /^Documentos y plantillas/ }).click();
  const vista = page.getByRole("region", { name: "Biblioteca", exact: true });
  await vista.getByRole("button", { name: "Elegir Política vinculada" }).click();
  return { panel: vista.getByRole("region", { name: "Vínculos", exact: true }), puts };
}

test("vincular un tratamiento lo muestra en «Documentos que lo usan»", async ({ page }, info) => {
  test.skip(info.project.name === "produccion", "La API simulada solo corre en desarrollo.");
  const { panel, puts } = await abrir(page, "implementador");
  await panel.getByLabel("ID del tratamiento del RAT").fill("rat-7");
  await panel.getByRole("group", { name: "Tratamientos" }).getByRole("button", { name: "Vincular" }).click();
  await expect(panel.getByTestId("vinculos-tratamiento")).toContainText("rat-7");
  expect(puts.at(-1)).toEqual({ tratamientos: ["rat-7"], controles: [], tareas: [] });
  await panel.getByRole("button", { name: "Documentos que lo usan" }).click();
  await expect(panel.getByRole("region", { name: "Documentos que lo usan rat-7" })).toContainText("Política vinculada");
});

test("un control fuera de P1–P80 muestra el aviso del servidor sin alerta", async ({ page }, info) => {
  test.skip(info.project.name === "produccion", "La API simulada solo corre en desarrollo.");
  const { panel } = await abrir(page, "coordinador");
  await panel.getByLabel("Control P1 a P80").fill("P99");
  await panel.getByRole("group", { name: "Controles" }).getByRole("button", { name: "Vincular" }).click();
  await expect(panel.getByRole("status")).toContainText("no existe en tu organización");
  await expect(panel.getByRole("alert")).toHaveCount(0);
  await expect(panel.getByTestId("vinculos-control")).not.toContainText("P99");
});

test("un tratamiento cambiado muestra «Revisar» y quien solo lee no edita", async ({ page }, info) => {
  test.skip(info.project.name === "produccion", "La API simulada solo corre en desarrollo.");
  const { panel } = await abrir(page, "dpo", [{ id: "doc-402:tratamiento:rat-1", documento_id: "doc-402", tipo: "tratamiento",
    ref: "rat-1", estado: "revisar", creado_por: "u", creado_en: "2026-11-04T10:00:00Z" }]);
  await expect(panel.getByTestId("vinculos-tratamiento")).toContainText("Revisar");
  await expect(panel.getByRole("button", { name: "Vincular" })).toHaveCount(0);
  await expect(panel.getByRole("button", { name: /^Quitar/ })).toHaveCount(0);
});
