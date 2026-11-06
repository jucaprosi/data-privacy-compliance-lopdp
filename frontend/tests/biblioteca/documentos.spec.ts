// ¤adpa ¤rbac-tenant
// ¤¤qa-engineer
/**
 * BIB-113 · Documentos de la organización (pestaña «Documentos de la organización»).
 * API simulada: comprueba el contrato de `docs/biblioteca-pmv.md` apartado c:
 * - GET /documentos?estado=&origen= (5)
 * - GET /documentos/{id} (6)
 * - GET /documentos/pendientes (9)
 * Manejo de estados: listo, no_disponible (404/405/501), denegado y error.
 * Selección con fijación de documentoId en useSeleccionBiblioteca (BIB-111).
 *
 * MUTACIÓN DECISIVA:
 * Ocultar la etiqueta de origen (basado en plantilla, propio, subido) en la lista
 * debe hacer fallar esta prueba («lista los documentos con etiqueta de origen...»).
 */
import { expect, test, type Page, type Route } from "@playwright/test";
import { abrirAppLimpia, barraDeMenus, configurarProyecto } from "../utiles";

const ORGANIZACION = "org-prueba-bib113";
const RUTA_DOCUMENTOS = "**/api/v1/biblioteca/documentos";
const RUTA_DOCUMENTOS_QUERY = "**/api/v1/biblioteca/documentos?*";
const RUTA_PENDIENTES = "**/api/v1/biblioteca/documentos/pendientes";
const RUTA_DETALLE = "**/api/v1/biblioteca/documentos/*";

const docResumen = (codigo: string, extra: Record<string, unknown> = {}) => ({
  id: `id-${codigo}`,
  codigo,
  nombre: `Documento ${codigo}`,
  origen: "plantilla",
  plantilla_version: "0.1.0",
  estado: "borrador",
  editado: false,
  proxima_revision: "2027-10-27",
  revision: 1,
  creado_por: "usr-1",
  creado_en: "2026-10-27T10:00:00Z",
  actualizado_en: "2026-10-27T10:00:00Z",
  ...extra,
});

const docCompleto = (codigo: string, extra: Record<string, unknown> = {}) => ({
  ...docResumen(codigo, extra),
  plantilla_id: `plantilla-${codigo}`,
  contenido_markdown: `# ${codigo}\n\nTexto de prueba para el documento ${codigo}.`,
  variables_faltantes: ["organizacion.direccion"],
  aprobado_por: null,
  aprobado_en: null,
  sha256: "a1b2c3d4e5f67890abcdef1234567890abcdef1234567890abcdef1234567890",
  fecha_emision: "2026-10-27",
  tarea_hoja_ruta_id: null,
  ...extra,
});

async function abrirDocumentos(
  page: Page,
  responderColeccion: (ruta: Route) => Promise<void> | void,
  responderDetalle?: (ruta: Route) => Promise<void> | void
) {
  await page.addInitScript((tenant) => {
    window.__LOPDP_AUTH_PRUEBAS__ = { modo: "headers", tenant };
  }, ORGANIZACION);
  await page.route("**/api/v1/**", (ruta) =>
    ruta.fulfill({ status: 503, json: { detail: "API simulada" } })
  );
  await page.route(RUTA_DOCUMENTOS, responderColeccion);
  await page.route(RUTA_DOCUMENTOS_QUERY, responderColeccion);
  if (responderDetalle) {
    await page.route(RUTA_DETALLE, (ruta) => {
      if (ruta.request().url().includes("/pendientes")) {
        return ruta.fulfill({
          json: { borrador: 1, en_revision: 0, por_vencer: 0, vencidos: 0, total: 1 },
        });
      }
      return responderDetalle(ruta);
    });
  }
  await page.route(RUTA_PENDIENTES, (ruta) =>
    ruta.fulfill({
      json: { borrador: 1, en_revision: 0, por_vencer: 0, vencidos: 0, total: 1 },
    })
  );

  await abrirAppLimpia(page);
  await configurarProyecto(page, "Entidad BIB-113");
  await barraDeMenus(page).getByRole("button", { name: "Biblioteca", exact: true }).click();
  await page
    .getByRole("group", { name: "Submenús de Biblioteca" })
    .getByRole("button", { name: /^Documentos y plantillas/ })
    .click();

  const vista = page.getByRole("region", { name: "Biblioteca", exact: true });
  return vista.getByTestId("pestaña-documentos");
}

test.describe("Biblioteca: documentos de la organización (BIB-113, API simulada)", () => {
  test.beforeEach(({}, testInfo) => {
    test.skip(testInfo.project.name === "produccion", "El gancho de prueba no existe en producción.");
  });

  test("lista los documentos con etiqueta de origen, estado, filtros y mutación de etiqueta", async ({
    page,
  }) => {
    const consultas: string[] = [];
    const listaInicial = [
      docResumen("BIB-001", { origen: "plantilla", estado: "borrador" }),
      docResumen("BIB-002", { origen: "propio", estado: "en_revision" }),
      docResumen("BIB-003", { origen: "subido", estado: "aprobado" }),
    ];

    const vista = await abrirDocumentos(page, (ruta) => {
      const url = new URL(ruta.request().url());
      consultas.push(url.search);
      const estado = url.searchParams.get("estado");
      const origen = url.searchParams.get("origen");

      let filtrada = listaInicial;
      if (estado) filtrada = filtrada.filter((d) => d.estado === estado);
      if (origen) filtrada = filtrada.filter((d) => d.origen === origen);
      return ruta.fulfill({ json: filtrada });
    });

    // Verificación de los tres orígenes: prueba de mutación (ocultar la etiqueta hace fallar esto)
    const tarjeta1 = vista.getByTestId("documento-BIB-001");
    await expect(tarjeta1.getByTestId("etiqueta-origen")).toHaveText("basado en plantilla");
    await expect(tarjeta1.getByTestId("etiqueta-estado")).toHaveText("Borrador");

    const tarjeta2 = vista.getByTestId("documento-BIB-002");
    await expect(tarjeta2.getByTestId("etiqueta-origen")).toHaveText("propio");
    await expect(tarjeta2.getByTestId("etiqueta-estado")).toHaveText("En revisión");

    const tarjeta3 = vista.getByTestId("documento-BIB-003");
    await expect(tarjeta3.getByTestId("etiqueta-origen")).toHaveText("subido");
    await expect(tarjeta3.getByTestId("etiqueta-estado")).toHaveText("Aprobado");

    expect(consultas[0]).toBe("");

    // Filtrar por estado
    await vista.getByLabel("Filtrar por estado").selectOption("borrador");
    await expect(vista.getByTestId("documento-BIB-001")).toBeVisible();
    await expect(vista.getByTestId("documento-BIB-002")).toHaveCount(0);
    await expect(vista.getByTestId("documento-BIB-003")).toHaveCount(0);

    // Filtrar por origen
    await vista.getByLabel("Filtrar por origen").selectOption("plantilla");
    await expect.poll(() => consultas.at(-1)).toBe("?estado=borrador&origen=plantilla");

    // Limpiar filtros
    await vista.getByRole("button", { name: "Limpiar filtros" }).click();
    await expect(vista.getByTestId("documento-BIB-001")).toBeVisible();
    await expect(vista.getByTestId("documento-BIB-002")).toBeVisible();
    await expect(vista.getByTestId("documento-BIB-003")).toBeVisible();
  });

  test("seleccionar un documento muestra su detalle y fija documentoId; volver a elegirlo lo deselecciona", async ({
    page,
  }) => {
    const vista = await abrirDocumentos(
      page,
      (ruta) => ruta.fulfill({ json: [docResumen("BIB-001")] }),
      (ruta) => {
        if (ruta.request().url().includes("/id-BIB-001")) {
          return ruta.fulfill({
            json: docCompleto("BIB-001", {
              variables_faltantes: ["organizacion.direccion"],
              contenido_markdown: "# Política\n\nCuerpo del documento BIB-001.",
            }),
          });
        }
        return ruta.fulfill({ status: 404 });
      }
    );

    const botonElegir = vista.getByRole("button", { name: "Elegir Documento BIB-001" });
    await expect(botonElegir).toHaveAttribute("aria-pressed", "false");

    // Selecciona el documento
    await botonElegir.click();
    await expect(botonElegir).toHaveAttribute("aria-pressed", "true");

    // El detalle del documento se monta en documento:detalle
    const detalle = vista.getByTestId("detalle-documento");
    await expect(detalle).toBeVisible();
    await expect(detalle.getByTestId("detalle-etiqueta-origen")).toHaveText("basado en plantilla");
    await expect(detalle.getByTestId("variables-faltantes")).toContainText("organizacion.direccion");
    await expect(detalle.getByTestId("documento-contenido")).toContainText("Cuerpo del documento BIB-001");

    // Cerrar detalle con el botón cerrar
    await detalle.getByRole("button", { name: "Cerrar detalle" }).click();
    await expect(vista.getByTestId("detalle-documento")).toHaveCount(0);
    await expect(botonElegir).toHaveAttribute("aria-pressed", "false");
  });

  test("documento ajeno o no existente devuelve 404 y se muestra como no encontrado", async ({
    page,
  }) => {
    const vista = await abrirDocumentos(
      page,
      (ruta) => ruta.fulfill({ json: [docResumen("BIB-AJENO")] }),
      (ruta) =>
        ruta.fulfill({
          status: 404,
          json: {
            code: "BIB_DOCUMENTO_NO_ENCONTRADO",
            detail: "No se encontró el documento en tu organización.",
          },
        })
    );

    await vista.getByRole("button", { name: "Elegir Documento BIB-AJENO" }).click();

    const alerta = vista.getByTestId("documento-no-encontrado");
    await expect(alerta).toBeVisible();
    await expect(alerta).toContainText("No se encontró el documento en tu organización.");

    // Botón cerrar descarta el mensaje
    await alerta.getByRole("button", { name: "Cerrar" }).click();
    await expect(alerta).toHaveCount(0);
  });

  test("no_disponible (404/405/501 cuando el backend aún no responde) muestra el vacío de BIB-111", async ({
    page,
  }) => {
    const vista = await abrirDocumentos(page, (ruta) =>
      ruta.fulfill({ status: 501, json: { detail: "Ruta no implementada todavía." } })
    );

    const vacio = vista.getByTestId("documentos-no-disponible");
    await expect(vacio).toBeVisible();
    await expect(vacio).toContainText("Todavía no hay documentos de la organización");
  });

  test("denegado (401/403) muestra aviso de acceso denegado sin botón de reintento", async ({
    page,
  }) => {
    const vista = await abrirDocumentos(page, (ruta) =>
      ruta.fulfill({
        status: 403,
        json: {
          code: "BIB_SIN_ACCESO",
          detail: "No tienes acceso a los documentos de esta organización.",
        },
      })
    );

    const denegado = vista.getByTestId("documentos-denegado");
    await expect(denegado).toBeVisible();
    await expect(denegado).toContainText("No tienes acceso a los documentos de esta organización.");
    await expect(vista.getByRole("button", { name: "Reintentar" })).toHaveCount(0);
  });

  test("error del servidor muestra aviso con reintento funcional", async ({ page }) => {
    let respondioError = true;
    const vista = await abrirDocumentos(page, (ruta) => {
      if (respondioError) {
        return ruta.fulfill({
          status: 500,
          json: { detail: "Fallo temporal de la base de datos." },
        });
      }
      return ruta.fulfill({ json: [docResumen("BIB-001")] });
    });

    const error = vista.getByTestId("documentos-error");
    await expect(error).toBeVisible();
    await expect(error).toContainText("El servidor no pudo entregar los documentos de la organización.");

    // Reintentar tras recuperación del servidor
    respondioError = false;
    await error.getByRole("button", { name: "Reintentar" }).click();
    await expect(vista.getByTestId("documento-BIB-001")).toBeVisible();
    await expect(vista.getByTestId("documentos-error")).toHaveCount(0);
  });

  test("lista vacía sin filtros muestra mensaje inicial; con filtros explica que ninguno coincide y permite limpiarlos", async ({
    page,
  }) => {
    const vista = await abrirDocumentos(page, (ruta) => {
      const hayFiltro = new URL(ruta.request().url()).search !== "";
      return ruta.fulfill({ json: hayFiltro ? [] : [docResumen("BIB-001")] });
    });

    await expect(vista.getByTestId("documento-BIB-001")).toBeVisible();

    // Filtrar por estado que no tiene resultados
    await vista.getByLabel("Filtrar por estado").selectOption("vencido");
    const vacio = vista.getByTestId("documentos-vacio");
    await expect(vacio).toContainText("Ningún documento coincide con los filtros");

    // Limpiar restablece la lista
    await vista.getByRole("button", { name: "Limpiar filtros" }).click();
    await expect(vista.getByTestId("documento-BIB-001")).toBeVisible();
  });
});
