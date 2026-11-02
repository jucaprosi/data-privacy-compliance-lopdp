/**
 * Arnés de pruebas E2E del informe anual del DPO y la inscripción ante la SPDP (DPO-02).
 *
 * Verifica:
 * 1. El rol `dpo` genera el informe del año (POST), ve el resumen y la huella de la cadena y puede descargarlo.
 * 2. Otro rol (`coordinador`) solo consulta (GET): no se llama al POST y el botón dice «Consultar».
 * 3. `admin_organizacion` registra la inscripción y ve el historial; el `dpo` la ve sin formulario.
 */
import { expect, test, type Page, type Request } from "@playwright/test";

import { abrirAppLimpia, configurarProyecto, irASala } from "../utiles";

const HUELLA = "f".repeat(64);

interface EntradaInscripcion {
  id: string;
  inscrito: boolean;
  fecha_inscripcion: string | null;
  numero_tramite: string | null;
  registrado_por: string;
  registrado_at: string;
}

function informe(anio: number) {
  return {
    tenant_id: "tenant-dpo-e2e",
    anio,
    generado_at: "2026-10-29T10:00:00+00:00",
    resumen: {
      total_actuaciones: 4,
      consultas_atendidas: 2,
      dictamenes: 1,
      escalamientos: 1,
      con_acuse_de_direccion: 3,
      sin_acuse_de_direccion: 1,
    },
    actuaciones_por_tipo: { OPINION_CONSULTIVA: 2, VALIDACION_EIPD: 1, ALERTA_RIESGO_GRAVE: 1 },
    actuaciones: [],
    inscripcion_spdp: null,
    cadena: { huella: HUELLA, integra: true, dictamen_alterado: null, total_en_cadena: 6 },
  };
}

async function instalarApi(page: Page, userId: string, roles: string[]) {
  const estado = {
    llamadas: [] as string[],
    historial: [] as EntradaInscripcion[],
    cuerpoInscripcion: null as unknown,
  };

  await page.route("**/api/v1/**", async (route) => {
    const peticion: Request = route.request();
    const url = new URL(peticion.url());
    const destino = `${url.pathname.replace(/^\/api\/v1/, "")}${url.search}`;
    const metodo = peticion.method();
    const responder = (status: number, cuerpo: unknown) =>
      route.fulfill({ status, contentType: "application/json", body: JSON.stringify(cuerpo) });

    if (destino === "/organizacion/me/roles" && metodo === "GET") {
      return responder(200, {
        user_id: userId,
        tenant_id: "tenant-dpo-e2e",
        roles: roles.map((role) => ({ role, area_id: null, area_nombre: null, valid_to: null })),
      });
    }
    if (destino.startsWith("/organizacion/designaciones") && metodo === "GET") return responder(200, []);
    if (destino === "/dpo/bitacora" && metodo === "GET") {
      return responder(200, { tenant_id: "tenant-dpo-e2e", total: 0, dictamenes: [] });
    }

    if (destino === "/dpo/informe-anual" && metodo === "POST") {
      estado.llamadas.push("POST informe");
      if (!roles.includes("dpo")) return responder(403, { detail: "Solo el DPO genera el informe." });
      const { anio } = JSON.parse(peticion.postData() ?? "{}") as { anio: number };
      return responder(200, informe(anio));
    }
    const consulta = destino.match(/^\/dpo\/informe-anual\?anio=(\d+)$/);
    if (consulta && metodo === "GET") {
      estado.llamadas.push("GET informe");
      return responder(200, informe(Number(consulta[1])));
    }
    if (destino.startsWith("/dpo/informe-anual/documento") && metodo === "GET") {
      estado.llamadas.push("GET documento");
      return route.fulfill({
        status: 200,
        contentType: "text/markdown; charset=utf-8",
        body: `# Informe\n\nHuella de la cadena de la bitácora: ${HUELLA}\n`,
      });
    }

    if (destino === "/dpo/inscripcion" && metodo === "GET") {
      return responder(200, {
        tenant_id: "tenant-dpo-e2e",
        vigente: estado.historial[0] ?? null,
        historial: estado.historial,
      });
    }
    if (destino === "/dpo/inscripcion" && metodo === "POST") {
      if (!roles.includes("admin_organizacion")) return responder(403, { detail: "Solo admin_organizacion." });
      estado.cuerpoInscripcion = JSON.parse(peticion.postData() ?? "{}");
      const c = estado.cuerpoInscripcion as {
        inscrito: boolean;
        fecha_inscripcion: string | null;
        numero_tramite: string | null;
      };
      const nueva: EntradaInscripcion = {
        id: `ins-${estado.historial.length + 1}`,
        inscrito: c.inscrito,
        fecha_inscripcion: c.fecha_inscripcion,
        numero_tramite: c.numero_tramite,
        registrado_por: userId,
        registrado_at: "2026-10-29T11:00:00Z",
      };
      estado.historial.unshift(nueva);
      return responder(200, nueva);
    }
    return responder(200, {});
  });
  return estado;
}

async function abrirCockpit(page: Page) {
  await abrirAppLimpia(page);
  await configurarProyecto(page, "Clínica DPO-02");
  await irASala(page, /Cockpit DPD \/ DPO/);
}

test.describe("Informe anual e inscripción SPDP del DPO (DPO-02)", () => {
  test("el dpo genera el informe, ve el resumen y la huella y lo descarga", async ({ page }) => {
    const estado = await instalarApi(page, "usuario-dpo-titular", ["dpo"]);
    await abrirCockpit(page);

    await page.getByTestId("pestana-dpo-informe").click();
    await expect(page.getByTestId("btn-obtener-informe")).toContainText("Generar informe");
    await page.getByTestId("input-anio-informe").fill("2026");
    await page.getByTestId("btn-obtener-informe").click();

    await expect(page.getByTestId("informe-total")).toHaveText("4");
    await expect(page.getByTestId("informe-consultas")).toHaveText("2");
    await expect(page.getByTestId("informe-escalamientos")).toHaveText("1");
    await expect(page.getByTestId("informe-huella")).toContainText(HUELLA);
    await expect(page.getByTestId("informe-inscripcion")).toContainText("sin registro");
    expect(estado.llamadas).toContain("POST informe");

    const descarga = page.waitForEvent("download");
    await page.getByTestId("btn-descargar-informe").click();
    expect((await descarga).suggestedFilename()).toBe("informe-dpo-2026.md");
    expect(estado.llamadas).toContain("GET documento");
  });

  test("un rol que no es dpo solo consulta el informe: no se llama al POST", async ({ page }) => {
    const estado = await instalarApi(page, "usuario-coordinador-01", ["coordinador"]);
    await abrirCockpit(page);

    await page.getByTestId("pestana-dpo-informe").click();
    await expect(page.getByTestId("btn-obtener-informe")).toContainText("Consultar informe");
    await page.getByTestId("btn-obtener-informe").click();

    await expect(page.getByTestId("informe-total")).toHaveText("4");
    expect(estado.llamadas).toContain("GET informe");
    expect(estado.llamadas).not.toContain("POST informe");
  });

  test("admin_organizacion registra la inscripción y ve el historial; el dpo la ve sin formulario", async ({
    page,
  }) => {
    await instalarApi(page, "gerente-general-01", ["admin_organizacion"]);
    await abrirCockpit(page);

    await page.getByTestId("pestana-dpo-inscripcion").click();
    await expect(page.getByTestId("historial-vacio")).toBeVisible();
    await page.getByTestId("input-fecha-inscripcion").fill("2026-02-01");
    await page.getByTestId("input-numero-tramite").fill("TR-0001");
    await page.getByTestId("btn-registrar-inscripcion").click();

    await expect(page.getByTestId("inscripcion-vigente")).toContainText("TR-0001");
    await expect(page.getByTestId("historial-inscripcion")).toContainText("gerente-general-01");
  });

  test("el dpo consulta la inscripción y no ve el formulario de registro", async ({ page }) => {
    await instalarApi(page, "usuario-dpo-titular", ["dpo"]);
    await abrirCockpit(page);

    await page.getByTestId("pestana-dpo-inscripcion").click();
    await expect(page.getByTestId("inscripcion-vigente")).toContainText("Sin registro de inscripción");
    await expect(page.getByTestId("form-inscripcion")).toHaveCount(0);
  });
});
