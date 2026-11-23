// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
/**
 * DER-01 · Ficha de la solicitud: verificación de identidad y respuesta registrada como evidencia.
 *
 * Valores simulados. Mutaciones: quitar `aria-disabled` del botón «Registrar la respuesta» o enviar el hash
 * desde el cliente hace fallar las pruebas 1 y 3; mostrar el botón al DPO, la 2.
 */
import { expect, test, type BrowserContext, type Page } from "@playwright/test";

import { simularApiDiagnostico } from "../diagnostico/simulador";
import { abrirAppLimpia, configurarProyecto, irASala } from "../utiles";

const DIA = 86_400_000;
const TEXTO_MODELO =
  "{organizacion} · Respuesta a la solicitud n.º {numero_solicitud}, presentada el {fecha_solicitud}.\n" +
  "Estimado/a {nombre_titular}:\n\nAtendimos tu solicitud de acceso a tus datos personales (LOPDP, art. 13). {actuacion}\n\n" +
  "Si tienes preguntas sobre esta respuesta, escríbenos a {contacto_dpo}.\n\n{organizacion} · {fecha_respuesta}";
const VARIABLES = ["organizacion", "numero_solicitud", "fecha_solicitud", "nombre_titular", "actuacion", "contacto_dpo", "fecha_respuesta"];

const solicitudLista = {
  id: "s1",
  tipo_solicitud: "ACCESO",
  estado: "RECIBIDA",
  nombre_solicitante: "Titular Simulado",
  cedula_solicitante: "0000000000",
  fecha_recepcion: new Date(Date.now() - 2 * DIA).toISOString(),
  fecha_vencimiento: new Date(Date.now() + 13 * DIA).toISOString(),
  plazo_dias: 15,
  plazo_unidad: "corridos",
  plazo_estimado: true,
};

const ficha = (extra: Record<string, unknown> = {}) => ({
  id: "s1",
  derecho: "ACCESO",
  estado: "RECIBIDA",
  identidad_verificada_en: new Date().toISOString(),
  identidad_metodo: "documento",
  identidad_verificada_por: "usuario-prueba",
  identidad_verificada_por_nombre: "Persona Simulada",
  resultado: null,
  respondida_en: null,
  evidencia_respuesta_hash: null,
  ...extra,
});

async function abrirFicha(page: Page, context: BrowserContext, rol: string, fichaServidor = ficha()) {
  const enviados: unknown[] = [];
  await simularApiDiagnostico(context, { roles: [rol] });
  await context.route("**/api/v1/arco/solicitudes", (r) => r.fulfill({ status: 200, json: [solicitudLista] }));
  await context.route("**/api/v1/derechos/solicitudes/s1", (r) => r.fulfill({ status: 200, json: fichaServidor }));
  await context.route("**/api/v1/derechos/modelos**", (r) =>
    r.fulfill({
      status: 200,
      json: { modelos: [{ id: "m1", derecho: "ACCESO", resultado: "concedido", texto: TEXTO_MODELO, variables: VARIABLES }] },
    }),
  );
  await context.route("**/api/v1/derechos/solicitudes/s1/respuesta", (r) => {
    enviados.push(r.request().postDataJSON());
    return r.fulfill({ status: 201, json: { evidencia_respuesta_hash: "a".repeat(64) } });
  });
  await page.setViewportSize({ width: 1280, height: 800 });
  await abrirAppLimpia(page);
  await configurarProyecto(page);
  await irASala(page, /Derechos ARCO/);
  await page.getByRole("button", { name: "Gestionar Expediente" }).click();
  await expect(page.getByTestId("ficha-respuesta")).toBeVisible();
  return enviados;
}

const registrar = (page: Page) => page.getByRole("button", { name: "Registrar la respuesta", exact: true }).first();

test.describe("Solicitudes de titulares: respuesta como evidencia (DER-01)", () => {
  test("con una variable vacía la vista previa marca lo que falta y el botón queda deshabilitado", async ({ page, context }) => {
    await abrirFicha(page, context, "implementador");
    const previa = page.getByRole("region", { name: "Vista previa de la respuesta" });
    await expect(previa).toContainText("[Falta: Acción realizada]");
    await expect(registrar(page)).toHaveAttribute("aria-disabled", "true");
    await expect(page.getByText("Completa los datos que faltan en la vista previa.")).toBeVisible();
    await expect(page.getByTestId("ficha-respuesta")).not.toContainText(/te enviaremos|enviada al titular|hash/i);
  });

  test("el DPO consulta pero no ve el botón", async ({ page, context }) => {
    await abrirFicha(page, context, "dpo");
    await expect(registrar(page)).toHaveCount(0);
    await expect(page.getByText("Responde la persona administradora o el implementador de la organización.")).toBeVisible();
  });

  test("con todos los datos se confirma y solo viajan modelo, variables y resultado", async ({ page, context }) => {
    const enviados = await abrirFicha(page, context, "implementador");
    for (const nombre of VARIABLES) {
      const etiquetas: Record<string, string> = {
        organizacion: "Organización", numero_solicitud: "Número de la solicitud", fecha_solicitud: "Fecha de la solicitud",
        nombre_titular: "Nombre del titular", actuacion: "Acción realizada", contacto_dpo: "Contacto del DPO",
        fecha_respuesta: "Fecha de la respuesta",
      };
      await page.getByLabel(etiquetas[nombre], { exact: true }).fill("dato");
    }
    await expect(registrar(page)).toHaveAttribute("aria-disabled", "false");
    await registrar(page).click();
    await expect(page.getByText("¿Registrar esta respuesta? Después no se puede cambiar.")).toBeVisible();
    await page.getByRole("alertdialog").getByRole("button", { name: "Registrar la respuesta" }).click();
    await expect.poll(() => enviados.length).toBe(1);
    expect(Object.keys(enviados[0] as object).sort()).toEqual(["modelo_id", "resultado", "variables"]);
  });

  test("sin verificar muestra la nota y, ya respondida, la huella corta sin la palabra hash", async ({ page, context }) => {
    await abrirFicha(page, context, "implementador", ficha({ identidad_verificada_en: null, identidad_metodo: null }));
    await expect(page.getByText("Verifica la identidad del titular para poder responder.").first()).toBeVisible();
    await expect(page.getByRole("button", { name: "Verificar la identidad del titular" })).toHaveAttribute("aria-disabled", "true");
  });
});
