// ¤adpa ¤frontend-ide
// ¤¤qa-engineer
/**
 * BIB-103 · Ficha de plantilla. API simulada: `GET /plantillas/{id}`, `POST /plantillas/{id}/copias` y el
 * `POST /documentos` de BIB-107 por su contrato. Esto NO acredita RLS ni persistencia (los prueba
 * `tests/test_bib_103_ficha.py`). La ranura `plantilla:ficha` la pintará el catálogo (BIB-102); mientras, el
 * anfitrión de pruebas de `fichas/anfitrionPruebas.tsx` la monta con `window.__LOPDP_FICHA_PRUEBAS__`.
 *
 * Pendiente del coordinador: añadir esta prueba a `SOLO_DESARROLLO` de `playwright.config.ts` (fuera de la
 * `propiedad` de BIB-103). Hasta entonces, en CI cae en el proyecto «produccion» y se omite.
 */
import { expect, test, type Page } from "@playwright/test";
import { abrirAppLimpia, barraDeMenus, configurarProyecto } from "../utiles";

const ORGANIZACION = "org-prueba-bib103";
const PLANTILLA = "plantilla-smartcidi-1";
const COPIA = "mi-plantilla-1";

const FICHA_SMARTCIDI = {
  id: PLANTILLA, codigo: "BIB-001", nombre: "Política de protección de datos personales", tipo: "politica",
  fuente: "smartcidi", version: "0.2.0", formato: "MD", ola: 1, validacion_legal: "pendiente",
  estado_editorial: "publicada", fecha_corte_normativo: "2026-10-27", base_lopdp: "POR VERIFICAR", revision_meses: 12,
  ficha: {
    nombre: "Política", objetivo: "Fijar cómo la empresa protege los datos personales.", fuentes: "LOPDP (por verificar)",
    fecha_revision: "2026-10-28", instrucciones: "Complete los datos de la organización.", dependencias: "Ninguna",
    restricciones: "Solo para empresas privadas pequeñas.",
  },
  avisos: [], origen_plantilla_id: null, origen_version: null,
  cuerpo_markdown: "# Política de {{organizacion.razon_social}}",
  variables: [
    { clave: "organizacion.razon_social", etiqueta: "Razón social", ambito: "organizacion", origen: "organizacion", obligatoria: true, disponible: true },
    { clave: "organizacion.direccion", etiqueta: "Domicilio principal", ambito: "organizacion", origen: "organizacion", obligatoria: true, disponible: false },
    { clave: "contexto.canal", etiqueta: "Canal de solicitudes", ambito: "contexto", origen: "persona", obligatoria: true, disponible: false },
  ],
  vista_previa: {
    demostrativa: true, aviso: "Vista previa demostrativa: los datos son de ejemplo y no pertenecen a ninguna organización.",
    markdown: "# Política de Empresa Ejemplo S.A.",
  },
  acciones: { usar: true, copiar: true },
};
const FICHA_COPIA = {
  ...FICHA_SMARTCIDI, id: COPIA, fuente: "organizacion", version: 1, estado_editorial: "mi_plantilla", ficha: null,
  origen_plantilla_id: PLANTILLA, origen_version: "0.2.0", acciones: { usar: true, copiar: false },
};

async function prepararSesion(page: Page) {
  await page.addInitScript(
    ({ tenant, plantillaId }) => {
      window.__LOPDP_AUTH_PRUEBAS__ = { modo: "headers", tenant };
      window.__LOPDP_FICHA_PRUEBAS__ = { plantillaId };
    },
    { tenant: ORGANIZACION, plantillaId: PLANTILLA },
  );
  await page.route("**/api/v1/**", (route) => route.fulfill({ status: 503, json: { detail: "API simulada" } }));
}

async function abrirFicha(page: Page) {
  await abrirAppLimpia(page);
  await configurarProyecto(page, "Entidad BIB-103");
  await barraDeMenus(page).getByRole("button", { name: "Biblioteca", exact: true }).click();
  await page
    .getByRole("group", { name: "Submenús de Biblioteca" })
    .getByRole("button", { name: /^Documentos y plantillas/ })
    .click();
  const vista = page.getByRole("region", { name: "Biblioteca", exact: true });
  await vista.getByRole("tab", { name: "Plantillas" }).click();
  return vista.getByRole("article", { name: "Ficha de plantilla" });
}

test.describe("Biblioteca: ficha de plantilla (BIB-103, API simulada)", () => {
  test.beforeEach(({}, testInfo) => {
    test.skip(testInfo.project.name === "produccion", "Los ganchos de prueba no existen en producción.");
  });

  test("muestra la ficha, las variables con su disponibilidad y una vista previa identificada como demostrativa", async ({ page }) => {
    await prepararSesion(page);
    await page.route(`**/api/v1/biblioteca/plantillas/${PLANTILLA}`, (route) => route.fulfill({ json: FICHA_SMARTCIDI }));
    const ficha = await abrirFicha(page);

    await expect(ficha.getByRole("heading", { name: "Política de protección de datos personales" })).toBeVisible();
    await expect(ficha).toContainText("BIB-001 · versión 0.2.0 · formato MD · Modelo de plantilla");
    await expect(ficha).toContainText("Estado editorial de la plantilla: Publicada · Pendiente de validación legal");
    await expect(ficha).toContainText("Fijar cómo la empresa protege los datos personales.");
    await expect(ficha.getByTestId("variable-organizacion.razon_social")).toContainText("La organización ya tiene este dato");
    await expect(ficha.getByTestId("variable-organizacion.direccion")).toContainText("Falta este dato en la organización");
    await expect(ficha.getByTestId("variable-contexto.canal")).toContainText("Lo completa la persona al crear el documento");
    const previa = ficha.getByRole("region", { name: "Vista previa demostrativa" });
    await expect(previa).toContainText("los datos son de ejemplo y no pertenecen a ninguna organización");
    await expect(previa).toContainText("Empresa Ejemplo S.A.");
    await expect(ficha.getByRole("button", { name: "Editar como «Mi plantilla»" })).toBeVisible();
  });

  test("«Usar en esta organización» crea el documento por POST /documentos con la plantilla elegida", async ({ page }) => {
    await prepararSesion(page);
    await page.route(`**/api/v1/biblioteca/plantillas/${PLANTILLA}`, (route) => route.fulfill({ json: FICHA_SMARTCIDI }));
    let cuerpo: unknown = null;
    await page.route("**/api/v1/biblioteca/documentos", async (route) => {
      cuerpo = route.request().postDataJSON();
      await route.fulfill({ status: 201, json: { id: "doc-1", estado: "borrador", variables_faltantes: ["organizacion.direccion"] } });
    });
    const ficha = await abrirFicha(page);

    await ficha.getByRole("button", { name: "Usar en esta organización" }).click();
    await expect(ficha.getByRole("status")).toContainText("Documento creado en borrador");
    await expect(ficha.getByRole("status")).toContainText("faltan 1 datos");
    expect(cuerpo).toEqual({ plantilla_id: PLANTILLA });
  });

  test("editar un modelo de plantilla crea la copia «Mi plantilla» y la ficha pasa a la copia", async ({ page }) => {
    await prepararSesion(page);
    await page.route(`**/api/v1/biblioteca/plantillas/${PLANTILLA}`, (route) => route.fulfill({ json: FICHA_SMARTCIDI }));
    await page.route(`**/api/v1/biblioteca/plantillas/${COPIA}`, (route) => route.fulfill({ json: FICHA_COPIA }));
    let metodo = "";
    await page.route(`**/api/v1/biblioteca/plantillas/${PLANTILLA}/copias`, async (route) => {
      metodo = route.request().method();
      await route.fulfill({ status: 201, json: { id: COPIA, fuente: "organizacion", nombre: "Mi plantilla: Política", version: 1, origen_plantilla_id: PLANTILLA, origen_version: "0.2.0" } });
    });
    const ficha = await abrirFicha(page);

    await ficha.getByRole("button", { name: "Editar como «Mi plantilla»" }).click();
    await expect(ficha).toContainText("Mi plantilla", { timeout: 10_000 });
    await expect(ficha).toContainText("Estado editorial de la plantilla: Copia de la organización");
    await expect(ficha).toContainText("copia de la versión 0.2.0");
    await expect(ficha.getByRole("button", { name: "Editar como «Mi plantilla»" })).toHaveCount(0);
    expect(metodo).toBe("POST");
  });

  test("una plantilla inexistente o de otra organización muestra el error sin datos", async ({ page }) => {
    await prepararSesion(page);
    await page.route(`**/api/v1/biblioteca/plantillas/${PLANTILLA}`, (route) =>
      route.fulfill({ status: 404, json: { code: "BIB_PLANTILLA_NO_ENCONTRADA", detail: "No se encontró la plantilla." } }));
    const ficha = await abrirFicha(page);

    await expect(ficha.getByRole("alert")).toContainText("No se encontró la plantilla.");
    await expect(ficha.getByRole("button", { name: "Usar en esta organización" })).toHaveCount(0);
  });
});
