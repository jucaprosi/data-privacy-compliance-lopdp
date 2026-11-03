// ¤adpa ¤rbac-tenant ¤frontend-ide
// ¤¤qa-engineer
/**
 * BIB-114 · Editor de borrador y captura de variables de contexto en el frontend.
 * Contrato de `docs/biblioteca-pmv.md` apartado c):
 *  - Botón «Usar en esta organización» en `plantilla:acciones` captura variables_contexto (texto, si_no, lista)
 *    y llama a `POST /biblioteca/documentos`.
 *  - Si el servidor responde 404, 405 o 501, el botón se muestra como no disponible.
 *  - Editor en `documento:editor` muestra `contenido_markdown`, variables faltantes (`⟦falta: …⟧`) listadas aparte
 *    y avisos de la plantilla cuando aplican.
 *  - Guarda con `PATCH /biblioteca/documentos/{id}` con control de `revision`.
 *  - Un 409 se muestra como conflicto con opción de recargar.
 *  - ÁRBITRO DE MUTACIÓN: anunciar «guardado» tras un error 409 o 500 debe hacer fallar esta suite.
 */
import { expect, test, type Page } from "@playwright/test";
import { abrirAppLimpia, barraDeMenus, configurarProyecto } from "../utiles";

const ORGANIZACION = "org-prueba-bib114";
const PLANTILLA_ID = "plantilla-bib-011";
const DOCUMENTO_ID = "doc-borrador-114";

const FICHA_PLANTILLA = {
  id: PLANTILLA_ID,
  codigo: "BIB-011",
  nombre: "Aviso de videovigilancia",
  tipo: "aviso",
  fuente: "smartcidi",
  version: "0.1.0",
  formato: "MD",
  ola: 3,
  validacion_legal: "pendiente",
  estado_editorial: "publicada",
  fecha_corte_normativo: "2026-10-27",
  base_lopdp: "POR VERIFICAR",
  revision_meses: 12,
  ficha: null,
  avisos: [
    {
      cuando: "contexto.camaras_acceso_publico",
      nivel: "alto",
      texto: "Tratamiento a gran escala: requiere evaluación de impacto previa y designación obligatoria de delegado.",
    },
  ],
  origen_plantilla_id: null,
  origen_version: null,
  cuerpo_markdown: "# Aviso de videovigilancia de {{organizacion.razon_social}}\n\nFinalidad: {{contexto.finalidad_concreta}}",
  variables_contexto: [
    {
      clave: "contexto.camaras_acceso_publico",
      etiqueta: "¿Las cámaras graban zonas abiertas al público?",
      tipo: "si_no",
      obligatoria: true,
    },
    {
      clave: "contexto.finalidad_concreta",
      etiqueta: "Finalidad concreta de las cámaras",
      tipo: "texto",
      obligatoria: true,
    },
    {
      clave: "contexto.destinatarios",
      etiqueta: "Destinatarios de las grabaciones",
      tipo: "lista",
      obligatoria: false,
    },
  ],
  variables: [
    {
      clave: "organizacion.razon_social",
      etiqueta: "Razón social",
      ambito: "organizacion",
      origen: "organizacion",
      obligatoria: true,
      disponible: true,
    },
    {
      clave: "contexto.camaras_acceso_publico",
      etiqueta: "¿Las cámaras graban zonas abiertas al público?",
      ambito: "contexto",
      origen: "persona",
      obligatoria: true,
      disponible: false,
    },
    {
      clave: "contexto.finalidad_concreta",
      etiqueta: "Finalidad concreta de las cámaras",
      ambito: "contexto",
      origen: "persona",
      obligatoria: true,
      disponible: false,
    },
    {
      clave: "contexto.destinatarios",
      etiqueta: "Destinatarios de las grabaciones",
      ambito: "contexto",
      origen: "persona",
      obligatoria: false,
      disponible: false,
    },
  ],
  vista_previa: { demostrativa: true, aviso: "Vista previa demostrativa", markdown: "Previa" },
  acciones: { usar: true, copiar: false },
};

const DOCUMENTO_BORRADOR = {
  id: DOCUMENTO_ID,
  codigo: "BIB-011",
  nombre: "Aviso de videovigilancia",
  origen: "plantilla",
  plantilla_id: PLANTILLA_ID,
  plantilla_version: "0.1.0",
  contenido_markdown:
    "# Aviso de videovigilancia de Empresa Ejemplo S.A.\n\n" +
    "⟦falta: organizacion.direccion⟧\n\n" +
    "Finalidad: Seguridad y prevención de hurtos.",
  variables_faltantes: ["organizacion.direccion"],
  editado: false,
  estado: "borrador",
  revision: 1,
  sha256: "hash-sha256-rev1",
  fecha_emision: "2026-11-03",
  proxima_revision: "2027-11-03",
  creado_por: "usr-tester",
  creado_en: "2026-11-03T10:00:00Z",
  actualizado_en: "2026-11-03T10:00:00Z",
};

async function prepararSesion(page: Page, configPruebas: Record<string, unknown> = {}) {
  await page.addInitScript(
    ({ tenant, config }) => {
      window.__LOPDP_AUTH_PRUEBAS__ = { modo: "headers", tenant };
      (window as unknown as Record<string, unknown>).__LOPDP_FORMULARIOS_PRUEBAS__ = config;
    },
    { tenant: ORGANIZACION, config: configPruebas },
  );
  await page.route("**/api/v1/**", (route) => route.fulfill({ status: 503, json: { detail: "API simulada" } }));
}

async function abrirBiblioteca(page: Page) {
  await abrirAppLimpia(page);
  await configurarProyecto(page, "Entidad BIB-114");
  await barraDeMenus(page).getByRole("button", { name: "Biblioteca", exact: true }).click();
  await page
    .getByRole("group", { name: "Submenús de Biblioteca" })
    .getByRole("button", { name: /^Documentos y plantillas/ })
    .click();
  return page.getByRole("region", { name: "Biblioteca", exact: true });
}

test.describe("BIB-114 · Editor de borrador y captura de variables de contexto (API simulada)", () => {
  test.describe.configure({ mode: "serial" });

  test.beforeEach(({}, testInfo) => {
    test.skip(testInfo.project.name === "produccion", "Los ganchos de prueba no existen en producción.");
  });

  test("captura variables_contexto (texto, si_no, lista) validando obligatoriedad y llama a POST /documentos", async ({ page }) => {
    await prepararSesion(page, { plantillaId: PLANTILLA_ID, ranura: "plantilla:acciones" });
    await page.route(`**/api/v1/biblioteca/plantillas/${PLANTILLA_ID}`, (route) =>
      route.fulfill({ json: FICHA_PLANTILLA }),
    );

    let payloadCapturado: Record<string, unknown> | null = null;
    await page.route("**/api/v1/biblioteca/documentos", async (route) => {
      payloadCapturado = route.request().postDataJSON() as Record<string, unknown>;
      await route.fulfill({ status: 201, json: DOCUMENTO_BORRADOR });
    });

    const vista = await abrirBiblioteca(page);
    await vista.getByRole("tab", { name: "Plantillas" }).click();

    // El botón «Usar en esta organización» debe estar visible
    const botonUsar = vista.getByTestId("boton-usar-plantilla");
    await expect(botonUsar).toBeVisible();
    await botonUsar.click();

    // Formulario de captura de variables de contexto
    const formulario = vista.getByTestId("formulario-variables-contexto");
    await expect(formulario).toBeVisible();
    await expect(formulario.getByText("Variables de contexto para el borrador")).toBeVisible();

    // Intentar enviar sin completar el campo obligatorio de texto
    await formulario.getByTestId("boton-confirmar-creacion").click();
    await expect(formulario.getByText("Este campo es obligatorio.")).toBeVisible();
    expect(payloadCapturado).toBeNull();

    // Completar los campos de prueba: texto, si_no y lista
    await formulario
      .getByTestId("input-contexto.finalidad_concreta")
      .fill("Prevención de pérdidas y control de acceso");
    await formulario
      .getByTestId("select-contexto.camaras_acceso_publico")
      .selectOption("si");
    await formulario
      .getByTestId("textarea-contexto.destinatarios")
      .fill("Policía Nacional, Jefe de Seguridad, Fiscalía");

    // Enviar formulario
    await formulario.getByTestId("boton-confirmar-creacion").click();

    // Verificación del payload enviado a POST /documentos
    await expect.poll(() => payloadCapturado).not.toBeNull();
    expect(payloadCapturado).toMatchObject({
      plantilla_id: PLANTILLA_ID,
      contexto: {
        "contexto.camaras_acceso_publico": "si",
        "contexto.finalidad_concreta": "Prevención de pérdidas y control de acceso",
        "contexto.destinatarios": ["Policía Nacional", "Jefe de Seguridad", "Fiscalía"],
      },
    });

    // Confirmación visual del documento creado en borrador
    await expect(vista.getByTestId("mensaje-documento-creado")).toContainText("Documento creado en borrador");
    await expect(vista.getByTestId("mensaje-documento-creado")).toContainText("faltan 1 datos para pasar a revisión");
  });

  test("si el servidor responde 404, 405 o 501, el botón se muestra como no disponible", async ({ page }) => {
    await prepararSesion(page, { plantillaId: PLANTILLA_ID, ranura: "plantilla:acciones" });
    await page.route(`**/api/v1/biblioteca/plantillas/${PLANTILLA_ID}`, (route) =>
      route.fulfill({ json: FICHA_PLANTILLA }),
    );
    // Simular que el endpoint POST /documentos no está implementado (501)
    await page.route("**/api/v1/biblioteca/documentos", (route) =>
      route.fulfill({ status: 501, json: { detail: "Ruta aún no implementada en el servidor" } }),
    );

    const vista = await abrirBiblioteca(page);
    await vista.getByRole("tab", { name: "Plantillas" }).click();

    await vista.getByTestId("boton-usar-plantilla").click();
    const formulario = vista.getByTestId("formulario-variables-contexto");
    await formulario
      .getByTestId("input-contexto.finalidad_concreta")
      .fill("Vigilancia general");
    await formulario.getByTestId("boton-confirmar-creacion").click();

    // El botón pasa a indicar «No disponible» y queda deshabilitado
    const botonDeshabilitado = vista.getByTestId("boton-usar-plantilla");
    await expect(botonDeshabilitado).toBeDisabled();
    await expect(botonDeshabilitado).toContainText("No disponible");
    await expect(vista.getByText(/no está disponible en este momento/i)).toBeVisible();
  });

  test("editor en documento:editor muestra contenido Markdown, variables faltantes listadas aparte y avisos", async ({ page }) => {
    await prepararSesion(page, { documentoId: DOCUMENTO_ID, ranura: "documento:editor" });
    await page.route(`**/api/v1/biblioteca/documentos/${DOCUMENTO_ID}`, (route) =>
      route.fulfill({ json: DOCUMENTO_BORRADOR }),
    );
    await page.route(`**/api/v1/biblioteca/plantillas/${PLANTILLA_ID}`, (route) =>
      route.fulfill({ json: FICHA_PLANTILLA }),
    );

    const vista = await abrirBiblioteca(page);
    await vista.getByRole("tab", { name: "Documentos de la organización" }).click();

    const editor = vista.getByTestId("editor-borrador");
    await expect(editor).toBeVisible();

    // Contenido Markdown en textarea
    const textarea = editor.getByTestId("editor-markdown");
    await expect(textarea).toBeVisible();
    await expect(textarea).toHaveValue(DOCUMENTO_BORRADOR.contenido_markdown);

    // Variables faltantes listadas en su sección separada
    const seccionFaltantes = editor.getByTestId("seccion-variables-faltantes");
    await expect(seccionFaltantes).toBeVisible();
    await expect(seccionFaltantes).toContainText("Variables faltantes (1)");
    await expect(seccionFaltantes.getByTestId("falta-organizacion.direccion")).toContainText("⟦falta: organizacion.direccion⟧");

    // Avisos de la plantilla reflejados
    const seccionAvisos = editor.getByTestId("seccion-avisos");
    await expect(seccionAvisos).toBeVisible();
    await expect(seccionAvisos).toContainText("Tratamiento a gran escala");
  });

  test("guarda con PATCH y revision anunciando «guardado» y actualizando revision", async ({ page }) => {
    await prepararSesion(page, { documentoId: DOCUMENTO_ID, ranura: "documento:editor" });
    await page.route(`**/api/v1/biblioteca/documentos/${DOCUMENTO_ID}`, (route) =>
      route.fulfill({ json: DOCUMENTO_BORRADOR }),
    );
    await page.route(`**/api/v1/biblioteca/plantillas/${PLANTILLA_ID}`, (route) =>
      route.fulfill({ json: FICHA_PLANTILLA }),
    );

    let patchPayload: Record<string, unknown> | null = null;
    await page.route(`**/api/v1/biblioteca/documentos/${DOCUMENTO_ID}`, async (route) => {
      if (route.request().method() === "PATCH") {
        patchPayload = route.request().postDataJSON() as Record<string, unknown>;
        const actualizado = {
          ...DOCUMENTO_BORRADOR,
          revision: 2,
          editado: true,
          contenido_markdown: "# Aviso de videovigilancia modificado\n\nDirección resuelta.",
          variables_faltantes: [],
        };
        await route.fulfill({ status: 200, json: actualizado });
      } else {
        await route.fulfill({ json: DOCUMENTO_BORRADOR });
      }
    });

    const vista = await abrirBiblioteca(page);
    await vista.getByRole("tab", { name: "Documentos de la organización" }).click();

    const editor = vista.getByTestId("editor-borrador");
    const textarea = editor.getByTestId("editor-markdown");
    await textarea.fill("# Aviso de videovigilancia modificado\n\nDirección resuelta.");

    await editor.getByTestId("boton-guardar").click();

    // Verificación del payload PATCH
    await expect.poll(() => patchPayload).not.toBeNull();
    expect(patchPayload).toEqual({
      contenido_markdown: "# Aviso de videovigilancia modificado\n\nDirección resuelta.",
      revision: 1,
    });

    // Anuncio de guardado y revisión actualizada
    await expect(editor.getByTestId("mensaje-guardado")).toContainText("Guardado correctamente (revisión 2)");
    await expect(editor).toContainText("Revisión: 2");
    await expect(editor.getByTestId("seccion-variables-faltantes")).toContainText("No quedan variables faltantes");
  });

  test("MUTACIÓN DECISIVA: un 409 muestra conflicto con recarga y NUNCA anuncia «guardado»", async ({ page }) => {
    await prepararSesion(page, { documentoId: DOCUMENTO_ID, ranura: "documento:editor" });
    let contadorGet = 0;
    await page.route(`**/api/v1/biblioteca/documentos/${DOCUMENTO_ID}`, async (route) => {
      if (route.request().method() === "PATCH") {
        await route.fulfill({
          status: 409,
          json: {
            code: "BIB_DOCUMENTO_REVISION_DESFASADA",
            detail: "La revisión del documento está desfasada. Otro usuario guardó cambios.",
          },
        });
      } else {
        contadorGet++;
        if (contadorGet === 1) {
          await route.fulfill({ json: DOCUMENTO_BORRADOR });
        } else {
          // Documento recargado con la revisión más reciente
          await route.fulfill({
            json: {
              ...DOCUMENTO_BORRADOR,
              revision: 3,
              contenido_markdown: "# Contenido más reciente del servidor",
            },
          });
        }
      }
    });
    await page.route(`**/api/v1/biblioteca/plantillas/${PLANTILLA_ID}`, (route) =>
      route.fulfill({ json: FICHA_PLANTILLA }),
    );

    const vista = await abrirBiblioteca(page);
    await vista.getByRole("tab", { name: "Documentos de la organización" }).click();

    const editor = vista.getByTestId("editor-borrador");
    const textarea = editor.getByTestId("editor-markdown");
    await textarea.fill("# Intento de modificación desfasada");

    await editor.getByTestId("boton-guardar").click();

    // Debe mostrar la alerta de conflicto 409
    const alertaConflicto = editor.getByTestId("alerta-conflicto");
    await expect(alertaConflicto).toBeVisible();
    await expect(alertaConflicto).toContainText("Conflicto de edición (409)");
    await expect(alertaConflicto).toContainText("La revisión del documento está desfasada");

    // ÁRBITRO DE MUTACIÓN: NUNCA debe anunciarse «guardado» ni existir estado de éxito
    await expect(editor.getByTestId("mensaje-guardado")).toHaveCount(0);
    await expect(editor.getByText(/guardado correctamente/i)).toHaveCount(0);

    // El botón de recargar debe estar presente y funcional
    const botonRecargar = editor.getByTestId("boton-recargar");
    await expect(botonRecargar).toBeVisible();
    await botonRecargar.click();

    // Tras recargar, la alerta de conflicto desaparece y el contenido se actualiza
    await expect(alertaConflicto).toHaveCount(0);
    await expect(textarea).toHaveValue("# Contenido más reciente del servidor");
    await expect(editor).toContainText("Revisión: 3");
  });

  test("fallo de red o error 500 al guardar muestra alerta de error y NUNCA anuncia «guardado»", async ({ page }) => {
    await prepararSesion(page, { documentoId: DOCUMENTO_ID, ranura: "documento:editor" });
    await page.route(`**/api/v1/biblioteca/documentos/${DOCUMENTO_ID}`, async (route) => {
      if (route.request().method() === "PATCH") {
        await route.fulfill({
          status: 500,
          json: { detail: "Error interno del servidor al persistir" },
        });
      } else {
        await route.fulfill({ json: DOCUMENTO_BORRADOR });
      }
    });
    await page.route(`**/api/v1/biblioteca/plantillas/${PLANTILLA_ID}`, (route) =>
      route.fulfill({ json: FICHA_PLANTILLA }),
    );

    const vista = await abrirBiblioteca(page);
    await vista.getByRole("tab", { name: "Documentos de la organización" }).click();

    const editor = vista.getByTestId("editor-borrador");
    await editor.getByTestId("boton-guardar").click();

    // Muestra alerta de error
    const alertaError = editor.getByTestId("alerta-error");
    await expect(alertaError).toBeVisible();
    await expect(alertaError).toContainText("Error interno del servidor");

    // NUNCA debe anunciarse «guardado»
    await expect(editor.getByTestId("mensaje-guardado")).toHaveCount(0);
    await expect(editor.getByText(/guardado correctamente/i)).toHaveCount(0);
  });
});
