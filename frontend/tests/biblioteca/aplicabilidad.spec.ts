// ¤adpa ¤rbac-tenant
// ¤¤qa-engineer
/**
 * BIB-204 · Aplicabilidad explicable y plantillas recomendadas.
 *
 * Prueba la sección de plantillas recomendadas en la pestaña «Plantillas», el triestado
 * (Aplica, No aplica, Información insuficiente), los filtros y la corrección humana explicable.
 */
import { expect, test, type Page, type Route } from "@playwright/test";
import { abrirAppLimpia, barraDeMenus, configurarProyecto } from "../utiles";

const ORGANIZACION = "org-prueba-bib204";
const RUTA_APLICABILIDAD = "**/api/v1/biblioteca/aplicabilidad**";
const RUTA_PLANTILLAS = "**/api/v1/biblioteca/plantillas**";

const PLANTILLAS_MOCK = [
  {
    codigo: "RAT-01",
    nombre: "Registro de actividades de tratamiento",
    resultado: "Aplica",
    resultado_calculado: "Aplica",
    tipo: "Registro",
    familia: "Tratamientos",
    formato: "XLSX",
    naturaleza: "Obligación condicional",
    es_obligacion: true,
    fuentes_normativas: ["N02", "N12"],
    version_regla: "1.0",
    motivo_recomendacion: "Obligación legal expresa: responsable con 100 o más trabajadores.",
    hechos_relevantes: { num_trabajadores: 120 },
    hechos_faltantes: [],
    reglas_evaluadas: [
      {
        regla_id: "AP-02",
        nombre: "Responsable y trabajadores >=100",
        resultado: "Aplica",
        explicacion: "Organización con 120 trabajadores (>= 100).",
        fuente_normativa: "N02;N12",
        version_regla: "1.0",
        hechos_analizados: { num_trabajadores: 120 },
        hechos_faltantes: [],
      },
    ],
  },
  {
    codigo: "VAR-BIO",
    nombre: "Protocolo de datos biométricos",
    resultado: "Información insuficiente",
    resultado_calculado: "Información insuficiente",
    tipo: "Procedimiento",
    familia: "Tecnología",
    formato: "DOCX",
    naturaleza: "Obligación condicional",
    es_obligacion: false,
    fuentes_normativas: ["N11"],
    version_regla: "1.0",
    motivo_recomendacion: "Se desconoce si los tratamientos procesan datos biométricos.",
    hechos_relevantes: {},
    hechos_faltantes: ["actividades_rat"],
    reglas_evaluadas: [
      {
        regla_id: "AP-07",
        nombre: "Uso de biometría",
        resultado: "Información insuficiente",
        explicacion: "Se desconoce si los tratamientos procesan datos biométricos.",
        fuente_normativa: "N11",
        version_regla: "1.0",
        hechos_analizados: {},
        hechos_faltantes: ["actividades_rat"],
      },
    ],
  },
  {
    codigo: "LIA-01",
    nombre: "Evaluación de interés legítimo",
    resultado: "No aplica",
    resultado_calculado: "No aplica",
    tipo: "Evaluación",
    familia: "Legitimación",
    formato: "DOCX",
    naturaleza: "Medida demostrativa",
    es_obligacion: false,
    fuentes_normativas: ["N01", "N07"],
    version_regla: "1.0",
    motivo_recomendacion: "Ningún tratamiento registrado se fundamenta en interés legítimo.",
    hechos_relevantes: {},
    hechos_faltantes: [],
    reglas_evaluadas: [
      {
        regla_id: "AP-04",
        nombre: "Finalidad propone interés legítimo",
        resultado: "No aplica",
        explicacion: "Ningún tratamiento registrado se fundamenta en interés legítimo.",
        fuente_normativa: "N01;N07",
        version_regla: "1.0",
        hechos_analizados: { tratamientos_interes_legitimo: 0 },
        hechos_faltantes: [],
      },
    ],
  },
];

async function abrirSeccionRecomendados(page: Page) {
  await page.addInitScript((tenant) => {
    window.__LOPDP_AUTH_PRUEBAS__ = { modo: "headers", tenant };
  }, ORGANIZACION);

  await page.route(RUTA_PLANTILLAS, (route) => route.fulfill({ status: 200, json: [] }));
  await page.route(RUTA_APLICABILIDAD, (route) => {
    if (route.request().method() === "POST") {
      const data = route.request().postDataJSON();
      return route.fulfill({
        status: 200,
        json: {
          resultado_original: "No aplica",
          resultado_modificado: data.resultado_modificado,
          motivo: data.motivo,
          evidencia: data.evidencia,
          autor_id: "u-prueba",
          fecha: new Date().toISOString(),
          es_obligacion_confirmada: false,
        },
      });
    }
    return route.fulfill({ status: 200, json: PLANTILLAS_MOCK });
  });

  await abrirAppLimpia(page);
  await configurarProyecto(page, "Entidad BIB-204");
  await barraDeMenus(page).getByRole("button", { name: "Biblioteca", exact: true }).click();
  await page
    .getByRole("group", { name: "Submenús de Biblioteca" })
    .getByRole("button", { name: /^Documentos y plantillas/ })
    .click();

  const vista = page.getByRole("region", { name: "Biblioteca", exact: true });
  await vista.getByRole("tab", { name: "Plantillas" }).click();
  return vista;
}

test.describe("Biblioteca: aplicabilidad determinista y recomendados (BIB-204)", () => {
  test.beforeEach(({}, testInfo) => {
    test.skip(testInfo.project.name === "produccion", "El gancho de prueba no existe en producción.");
  });

  test("muestra la sección de recomendados con las plantillas evaluadas", async ({ page }) => {
    const vista = await abrirSeccionRecomendados(page);
    const seccion = vista.getByTestId("seccion-recomendados");
    await expect(seccion).toBeVisible();

    // Por defecto filtro 'Recomendadas' muestra solo las que aplican (RAT-01)
    await expect(seccion.getByTestId("tarjeta-aplicabilidad-RAT-01")).toBeVisible();
    await expect(seccion.getByTestId("resultado-RAT-01")).toContainText("Aplica");
    await expect(seccion.getByTestId("tarjeta-aplicabilidad-VAR-BIO")).toHaveCount(0);
  });

  test("filtra por triestado: Información insuficiente y No aplica", async ({ page }) => {
    const vista = await abrirSeccionRecomendados(page);
    const seccion = vista.getByTestId("seccion-recomendados");

    // Filtro Información insuficiente
    await seccion.getByTestId("filtro-información-insuficiente").click();
    await expect(seccion.getByTestId("tarjeta-aplicabilidad-VAR-BIO")).toBeVisible();
    await expect(seccion.getByTestId("resultado-VAR-BIO")).toContainText("Información insuficiente");
    await expect(seccion.getByTestId("tarjeta-aplicabilidad-RAT-01")).toHaveCount(0);

    // Filtro No aplica
    await seccion.getByTestId("filtro-no-aplica").click();
    await expect(seccion.getByTestId("tarjeta-aplicabilidad-LIA-01")).toBeVisible();
    await expect(seccion.getByTestId("resultado-LIA-01")).toContainText("No aplica");

    // Filtro Todas
    await seccion.getByTestId("filtro-todas").click();
    await expect(seccion.getByTestId("tarjeta-aplicabilidad-RAT-01")).toBeVisible();
    await expect(seccion.getByTestId("tarjeta-aplicabilidad-VAR-BIO")).toBeVisible();
    await expect(seccion.getByTestId("tarjeta-aplicabilidad-LIA-01")).toBeVisible();
  });

  test("permite corregir manualmente la aplicabilidad con motivo y evidencia", async ({ page }) => {
    const vista = await abrirSeccionRecomendados(page);
    const seccion = vista.getByTestId("seccion-recomendados");

    await seccion.getByTestId("filtro-todas").click();
    await seccion.getByTestId("boton-modificar-LIA-01").click();

    const modal = page.getByTestId("modal-modificar");
    await expect(modal).toBeVisible();

    await modal.getByTestId("select-resultado-modificado").selectOption("Aplica");
    await modal.getByTestId("input-motivo").fill("Se proyecta nueva campaña publicitaria bajo interés legítimo");
    await modal.getByTestId("input-evidencia").fill("Acta del comité comercial #14");

    await modal.getByTestId("boton-guardar-modificacion").click();
    await expect(modal).toHaveCount(0);

    // Tras guardar, la tarjeta muestra el resultado modificado y badge de corrección manual
    await expect(seccion.getByTestId("resultado-LIA-01")).toContainText("Aplica");
    await expect(seccion.getByTestId("tarjeta-aplicabilidad-LIA-01")).toContainText("Corregido manualmente");
  });
});
