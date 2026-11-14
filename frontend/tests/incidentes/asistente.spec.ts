/**
 * Asistente de vulneración en ocho pasos (INC-02, governance/especificaciones/INC-02.md §5 y los criterios
 * cerrados por UX/UI en governance/tareas/INC-02.md). API simulada con las reglas del servidor.
 *
 * Verifica:
 * 1. Con el paso 3 vacío no se avanza al 7 y el texto dice qué falta.
 * 2. Justificación de 10 caracteres: 422 y no avanza; con 20, sí; «No notificar» también la exige.
 * 3. En el paso 8 solo los botones que pide la decisión.
 * 4. Al generar, «Abrir el informe» y el status; el coordinador ve los botones con aria-disabled.
 * 5. Dos lecciones guardan dos hallazgos.
 * 6. Ningún texto interno, id, carácter de gobernanza ni afirmación de cumplimiento o de plazo cumplido.
 * 7. A 375 px, sin desplazamiento horizontal.
 * Mutación: quitar la comprobación del orden en la sección 7 (cliente y API simulada) → el criterio 1 falla.
 */
import { expect, test, type Page } from "@playwright/test";

import { abrirAppLimpia, configurarProyecto, irASala } from "../utiles";

const ID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee";
const TITULO = "Acceso indebido a correos";
const HUELLA = "0123456789abcdef".repeat(4);
const NOMBRES = [
  "Identificación",
  "Tratamientos afectados",
  "Titulares y datos",
  "Descripción y tipo",
  "Efectos y medidas",
  "Resolución",
  "Decisión de notificar",
  "Informes y notificación",
];
const COMPLETAS: Record<number, Record<string, unknown>> = {
  1: { fecha_conocimiento: "2026-11-10T14:00:00.000Z", detectado_por: "Mesa de ayuda", contacto_dpo: "Delegada, dpo@correo.invalid" },
  2: { tratamiento_ids: ["Nómina"] },
  3: { titulares_aproximados: 120, registros_aproximados: 300, categorias_datos: ["Contacto"] },
  4: { descripcion: "Consulta masiva desde una credencial filtrada.", tipo: "confidencialidad" },
  5: { efectos: "Exposición de correos.", medidas: "Credencial revocada.", recomendaciones_titulares: "Cambia tu clave." },
  6: { resolucion: "Acceso cerrado.", lecciones: [] },
};

interface Estado {
  secciones: Record<number, Record<string, unknown>>;
  informes: string[];
  notificados: string[];
  hallazgos: string[];
  puts: number[];
}

function destinos(decision: unknown): string[] {
  return decision === "spdp" ? ["spdp"] : decision === "titulares" ? ["titulares"] : decision === "ambos" ? ["spdp", "titulares"] : [];
}

function salida(e: Estado) {
  const completa = (n: number) =>
    n <= 7 ? n in e.secciones : 7 in e.secciones && destinos(e.secciones[7].decision).every((d) => e.informes.includes(d) && e.notificados.includes(d));
  const actual = [1, 2, 3, 4, 5, 6, 7, 8].find((n) => !completa(n)) ?? 8;
  return {
    seccion_actual: actual,
    decision: (e.secciones[7]?.decision as string) ?? null,
    secciones: NOMBRES.map((nombre, i) => ({ id: i + 1, nombre, completa: completa(i + 1), datos: e.secciones[i + 1] ?? null })),
    informes: e.informes,
    notificados: e.notificados,
  };
}

async function simularApi(page: Page, roles: string[], secciones: Record<number, Record<string, unknown>>) {
  const e: Estado = { secciones: { ...secciones }, informes: [], notificados: [], hallazgos: [], puts: [] };
  await page.route("**/api/v1/**", async (route) => {
    const peticion = route.request();
    const ruta = new URL(peticion.url()).pathname.replace(/^\/api\/v1/, "");
    const metodo = peticion.method();
    const rol = peticion.headers()["x-role"] ?? "";
    const responder = (status: number, cuerpo: unknown) =>
      route.fulfill({ status, contentType: "application/json", body: JSON.stringify(cuerpo) });

    if (ruta === "/organizacion/me/roles") {
      return responder(200, {
        user_id: "u-1",
        tenant_id: "tenant-inc02-e2e",
        roles: roles.map((role) => ({ role, area_id: null, area_nombre: null, valid_to: null })),
      });
    }
    if (ruta === "/incidentes" && metodo === "GET") {
      return responder(200, {
        incidentes: [{ id: ID, titulo: TITULO, fecha_deteccion: "2026-11-10T14:00:00+00:00", estado: "abierto" }],
        cadena_integra: true,
        primer_alterado: null,
      });
    }
    if (ruta === "/incidentes/asistentes") return responder(200, { [ID]: { seccion_actual: salida(e).seccion_actual, decision: null } });
    if (ruta === `/incidentes/${ID}/asistente`) return responder(200, salida(e));
    const put = ruta.match(/^\/incidentes\/[^/]+\/asistente\/(\d)$/);
    if (put && metodo === "PUT") {
      const n = Number(put[1]);
      const cuerpo = JSON.parse(peticion.postData() ?? "{}") as Record<string, unknown>;
      e.puts.push(n);
      if ((n <= 6 && !["implementador", "coordinador"].includes(rol)) || (n >= 7 && !["implementador", "dpo"].includes(rol))) {
        return responder(403, { detail: "Rol no autorizado" });
      }
      if (n === 7) {
        if (String(cuerpo.justificacion ?? "").trim().length < 20) return responder(422, { code: "DECISION_SIN_JUSTIFICACION" });
        const falta = [1, 2, 3, 4, 5, 6].find((x) => !(x in e.secciones));
        if (falta) return responder(409, { code: "SECCION_ANTERIOR_INCOMPLETA", detail: `Antes de seguir, completa el paso ${falta}.` });
      }
      if (n === 8) {
        e.notificados.push(String(cuerpo.destino));
        return responder(200, salida(e));
      }
      if (n === 6) for (const l of (cuerpo.lecciones as string[]) ?? []) if (!e.hallazgos.includes(l)) e.hallazgos.push(l);
      e.secciones[n] = cuerpo;
      return responder(200, salida(e));
    }
    const informe = ruta.match(/^\/incidentes\/[^/]+\/informes$/);
    if (informe && metodo === "POST") {
      const { destino } = JSON.parse(peticion.postData() ?? "{}") as { destino: string };
      e.informes.push(destino);
      return responder(201, { sha256: HUELLA, evidencia_id: `evd-${destino}` });
    }
    if (ruta === "/evidencias/documentos") {
      return responder(200, {
        documentos: [{ id: "evd-spdp", codigo: "EVD-0001", nombre_archivo: "constancia-sispdp.pdf", sha256_hash: HUELLA }],
      });
    }
    return responder(200, {});
  });
  return e;
}

async function abrirAsistente(page: Page) {
  await abrirAppLimpia(page);
  await configurarProyecto(page, "Clínica INC-02");
  await irASala(page, /Asistente de vulneración/);
  const main = page.getByRole("main", { name: "Asistente de vulneración" });
  await expect(main.getByRole("progressbar", { name: "Avance del asistente" })).toBeVisible();
  await main.getByRole("button", { name: `Continuar el asistente de ${TITULO}` }).click();
  return main;
}

async function irAlPaso(main: ReturnType<Page["getByRole"]>, n: number) {
  await main.getByRole("list", { name: "Pasos del asistente" }).getByRole("button", { name: new RegExp(`^Paso ${n} de 8`) }).click();
}

function sin(secciones: number[]) {
  return Object.fromEntries(Object.entries(COMPLETAS).filter(([k]) => !secciones.includes(Number(k))));
}

test.describe("Asistente de vulneración (INC-02)", () => {
  test("con el paso 3 vacío no se avanza al 7 y dice qué falta", async ({ page }) => {
    const e = await simularApi(page, ["implementador"], sin([3]));
    const main = await abrirAsistente(page);
    await expect(main.getByRole("heading", { name: "Paso 3 de 8: Titulares y datos" })).toBeVisible();
    await main.getByRole("button", { name: "Guardar y continuar" }).click();
    await expect(main.getByRole("alert")).toContainText("Completa este paso antes de continuar: Número aproximado de titulares");
    expect(e.puts).toHaveLength(0);

    await irAlPaso(main, 7);
    await main.getByRole("radio", { name: /Notificar a la Autoridad/ }).check();
    await main.getByRole("textbox", { name: "Justificación" }).fill("Afecta correos de más de cien personas.");
    await main.getByRole("button", { name: "Guardar y continuar" }).click();
    await expect(main.getByRole("alert")).toContainText("Antes de seguir, completa el paso 3: Titulares y datos.");
    await expect(main.getByRole("heading", { name: "Paso 7 de 8: Decisión de notificar" })).toBeVisible();
    await main.getByRole("button", { name: "Ir al paso 3" }).click();
    await expect(main.getByRole("heading", { name: "Paso 3 de 8: Titulares y datos" })).toBeVisible();
    await expect(main.getByRole("listitem").filter({ hasText: "Paso 3 de 8" })).toHaveAttribute("aria-current", "step");
  });

  test("la justificación exige 20 caracteres, también para «No notificar»", async ({ page }) => {
    const e = await simularApi(page, ["dpo"], COMPLETAS);
    const main = await abrirAsistente(page);
    await expect(main.getByRole("heading", { name: "Paso 7 de 8: Decisión de notificar" })).toBeVisible();
    await expect(main.getByText("Los plazos legales no se calculan aquí.", { exact: false })).toBeVisible();

    await main.getByRole("radio", { name: /No notificar/ }).check();
    await main.getByRole("textbox", { name: "Justificación" }).fill("Muy breve.");
    await expect(main.getByText("10 de 20 caracteres como mínimo")).toBeVisible();
    await main.getByRole("button", { name: "Guardar y continuar" }).click();
    await expect(main.getByRole("alert")).toContainText("Justificación");
    expect(e.puts).toHaveLength(0);

    await main.getByRole("textbox", { name: "Justificación" }).fill("x".repeat(20));
    await main.getByRole("button", { name: "Guardar y continuar" }).click();
    await expect(main.getByRole("heading", { name: "Paso 8 de 8: Informes y notificación" })).toBeVisible();
    await expect(main.getByText("Decidiste no notificar; no hay informes que generar.")).toBeVisible();
    await expect(main.getByRole("button", { name: /Generar/ })).toHaveCount(0);
  });

  test("el 422 del servidor muestra su texto fijo y no avanza", async ({ page }) => {
    await simularApi(page, ["dpo"], COMPLETAS);
    await page.route(`**/api/v1/incidentes/${ID}/asistente/7`, (route) =>
      route.fulfill({ status: 422, contentType: "application/json", body: JSON.stringify({ code: "DECISION_SIN_JUSTIFICACION" }) }),
    );
    const main = await abrirAsistente(page);
    await main.getByRole("radio", { name: /Notificar a los titulares/ }).check();
    await main.getByRole("textbox", { name: "Justificación" }).fill("Veinte caracteres justos.");
    await main.getByRole("button", { name: "Guardar y continuar" }).click();
    await expect(main.getByRole("alert")).toHaveText("Explica tu decisión con al menos 20 caracteres.");
    await expect(main.getByRole("heading", { name: "Paso 7 de 8: Decisión de notificar" })).toBeVisible();
  });

  test("en el paso 8 solo los informes que pide la decisión; generar muestra «Abrir» y el aviso", async ({ page }) => {
    const e = await simularApi(page, ["dpo"], { ...COMPLETAS, 7: { decision: "spdp", justificacion: "Afecta correos de más de cien personas." } });
    const main = await abrirAsistente(page);
    await expect(main.getByRole("heading", { name: "Paso 8 de 8: Informes y notificación" })).toBeVisible();
    await expect(main.getByRole("button", { name: "Generar comunicación a los titulares" })).toHaveCount(0);
    await main.getByRole("button", { name: "Generar informe para la Autoridad" }).click();
    await expect(main.getByRole("status")).toHaveText("Informe generado y guardado como evidencia.");
    await expect(main.getByRole("link", { name: "Abrir el informe para la Autoridad" })).toBeVisible();
    await expect(main.getByText("Presenta el informe en el SISPDP (servicios.spdp.gob.ec).")).toBeVisible();
    expect(e.informes).toEqual(["spdp"]);

    await main.getByLabel("Fecha de notificación").fill("2026-11-12T10:00");
    await main.getByLabel("Evidencia de la notificación").selectOption({ label: "EVD-0001 · constancia-sispdp.pdf" });
    await main.getByRole("button", { name: "Registrar notificación" }).click();
    await expect(main.getByRole("status")).toHaveText("Notificación registrada.");
    expect(e.notificados).toEqual(["spdp"]);
  });

  test("el coordinador ve los informes con aria-disabled y sin escribir", async ({ page }) => {
    const e = await simularApi(page, ["coordinador"], { ...COMPLETAS, 7: { decision: "ambos", justificacion: "Afecta correos de más de cien personas." } });
    const main = await abrirAsistente(page);
    await irAlPaso(main, 8);
    for (const nombre of ["Generar informe para la Autoridad", "Generar comunicación a los titulares"]) {
      await expect(main.getByRole("button", { name: nombre })).toHaveAttribute("aria-disabled", "true");
      await main.getByRole("button", { name: nombre }).click({ force: true });
    }
    await expect(main.getByText("Solo el DPO o el implementador generan los informes.")).toBeVisible();
    expect(e.informes).toHaveLength(0);
    await irAlPaso(main, 7);
    await expect(main.getByRole("textbox", { name: "Justificación" })).toBeDisabled();
  });

  test("dos lecciones guardan dos hallazgos", async ({ page }) => {
    const e = await simularApi(page, ["implementador"], sin([6]));
    const main = await abrirAsistente(page);
    await expect(main.getByRole("heading", { name: "Paso 6 de 8: Resolución" })).toBeVisible();
    await main.getByLabel("Resolución", { exact: true }).fill("Acceso cerrado y registros revisados.");
    await main.getByRole("button", { name: "Añadir lección" }).click();
    await main.getByLabel("Lección 1").fill("Rotar credenciales cada trimestre");
    await main.getByRole("button", { name: "Añadir lección" }).click();
    await main.getByLabel("Lección 2").fill("Alertar consultas masivas");
    await main.getByRole("button", { name: "Guardar y continuar" }).click();
    await expect(main.getByRole("status")).toHaveText("Lección guardada como hallazgo.");
    expect(e.hallazgos).toEqual(["Rotar credenciales cada trimestre", "Alertar consultas masivas"]);
  });

  test("sin textos internos ni afirmaciones de cumplimiento y sin desbordar a 375 px", async ({ page }) => {
    await simularApi(page, ["implementador"], { ...COMPLETAS, 7: { decision: "ambos", justificacion: "Afecta correos de más de cien personas." } });
    const main = await abrirAsistente(page);
    await page.setViewportSize({ width: 375, height: 800 });
    // Al estrechar, el panel vuelve a montar la vista: se reabre el asistente si volvió a la lista.
    const continuar = main.getByRole("button", { name: `Continuar el asistente de ${TITULO}` });
    await expect(main.getByRole("list", { name: "Pasos del asistente" }).or(continuar)).toBeVisible();
    if (await continuar.isVisible()) await continuar.click();
    for (const n of [7, 8]) {
      await irAlPaso(main, n);
      const texto = await main.innerText();
      for (const prohibido of [/LEG-03/, /REG-01/, /hash/i, /sha256/i, /[¤¦]/, /cumpli[óo]/i, /\bcumple\b/i, /dentro del plazo/i, new RegExp(ID)]) {
        expect(texto).not.toMatch(prohibido);
      }
      const desborde = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
      expect(desborde).toBeLessThanOrEqual(0);
    }
  });
});
