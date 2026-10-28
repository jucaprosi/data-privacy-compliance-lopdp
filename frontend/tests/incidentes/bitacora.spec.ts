/**
 * INC-01: la bitácora de incidentes se lee y se registra en el servidor.
 *
 * La API se simula a nivel de contexto con un «servidor» en memoria: así se comprueba qué envía la
 * pantalla (nunca autoría, plazos ni huellas) y qué muestra a cada rol.
 */
import { expect, test, type BrowserContext } from "@playwright/test";

import { abrirAppLimpia, configurarProyecto, irASala } from "../utiles";

interface IncidenteSimulado {
  id: string;
  secuencia: number;
  fecha_deteccion: string;
  titulo: string;
  descripcion: string;
  severidad: string;
  afecta_datos_personales: boolean;
  categorias_datos: string[];
  medidas_inmediatas: string;
  registrado_por: string;
  registrado_en: string;
  huella_anterior: string;
  huella: string;
}

function incidenteDePrueba(secuencia: number, titulo: string): IncidenteSimulado {
  return {
    id: `incidente-${secuencia}`,
    secuencia,
    fecha_deteccion: new Date(Date.now() - 3 * 3600_000).toISOString(),
    titulo,
    descripcion: "",
    severidad: "Alta",
    afecta_datos_personales: true,
    categorias_datos: [],
    medidas_inmediatas: "",
    registrado_por: "usuario-servidor",
    registrado_en: new Date().toISOString(),
    huella_anterior: "0".repeat(64),
    huella: String(secuencia).repeat(64).slice(0, 64),
  };
}

async function simularApi(
  context: BrowserContext,
  { roles, incidentes = [], rechazo }: { roles: string[]; incidentes?: IncidenteSimulado[]; rechazo?: string }
) {
  const servidor = { incidentes: [...incidentes], cuerpos: [] as Record<string, unknown>[] };
  await context.route("**/api/v1/organizacion/me/roles", (route) =>
    route.fulfill({ json: { roles: roles.map((role) => ({ role })) } })
  );
  await context.route("**/api/v1/incidentes", async (route) => {
    if (route.request().method() === "POST") {
      const cuerpo = route.request().postDataJSON() as Record<string, unknown>;
      servidor.cuerpos.push(cuerpo);
      if (rechazo) {
        await route.fulfill({ status: 422, json: { detail: rechazo } });
        return;
      }
      const nuevo = {
        ...incidenteDePrueba(servidor.incidentes.length + 1, String(cuerpo.titulo)),
        ...cuerpo,
        registrado_por: "usuario-servidor",
      } as IncidenteSimulado;
      servidor.incidentes.push(nuevo);
      await route.fulfill({ status: 201, json: nuevo });
      return;
    }
    await route.fulfill({
      json: { incidentes: [...servidor.incidentes].reverse(), cadena_integra: true, primer_alterado: null },
    });
  });
  return servidor;
}

test.describe("Bitácora de incidentes en el servidor (INC-01)", () => {
  test("el coordinador reporta un incidente y lo ve en la bitácora; solo envía lo que declara", async ({ page, context }) => {
    const servidor = await simularApi(context, { roles: ["coordinador"] });
    await abrirAppLimpia(page);
    await configurarProyecto(page);
    await irASala(page, /Playbook Incidentes/);

    await page.getByRole("button", { name: "Reportar vulneración" }).click();
    const formulario = page.getByRole("form", { name: "Reportar vulneración" });
    await formulario.getByLabel("Título del incidente").fill("Correo con datos de clientes enviado por error");
    await formulario.getByLabel("Severidad").selectOption("Crítica");
    await formulario.getByLabel("Contacto (Email / Teléfono)").check();
    await formulario.getByLabel("Medidas inmediatas de contención").fill("Se pidió al destinatario borrar el correo.");
    await formulario.getByRole("button", { name: "Registrar incidente" }).click();

    await expect(page.getByText("Incidente n.º 1 registrado. Ya no se puede editar ni borrar.")).toBeVisible();
    const lista = page.getByRole("list", { name: "Bitácora de incidentes" });
    await expect(lista).toContainText("N.º 1 · Correo con datos de clientes enviado por error");
    await expect(lista).toContainText("Crítica");

    expect(servidor.cuerpos).toHaveLength(1);
    expect(Object.keys(servidor.cuerpos[0]).sort()).toEqual([
      "afecta_datos_personales",
      "categorias_datos",
      "descripcion",
      "fecha_deteccion",
      "medidas_inmediatas",
      "severidad",
      "titulo",
    ]);
    expect(servidor.cuerpos[0].categorias_datos).toEqual(["Contacto (Email / Teléfono)"]);
  });

  test("el DPO consulta la bitácora en modo lectura", async ({ page, context }) => {
    await simularApi(context, { roles: ["dpo"], incidentes: [incidenteDePrueba(1, "Pérdida de una laptop")] });
    await abrirAppLimpia(page);
    await configurarProyecto(page);
    await irASala(page, /Playbook Incidentes/);

    await expect(page.getByText(/Modo lectura: su rol consulta la bitácora/)).toBeVisible();
    await expect(page.getByRole("list", { name: "Bitácora de incidentes" })).toContainText("N.º 1 · Pérdida de una laptop");
    await expect(page.getByRole("button", { name: "Reportar vulneración" })).toHaveCount(0);
  });

  test("no muestra un plazo legal que no está en la ley ni pide un archivo que no guarda", async ({ page, context }) => {
    await simularApi(context, { roles: ["implementador"], incidentes: [incidenteDePrueba(1, "Acceso indebido")] });
    await abrirAppLimpia(page);
    await configurarProyecto(page);
    await irASala(page, /Playbook Incidentes/);
    await page.getByRole("button", { name: "Reportar vulneración" }).click();

    const seccion = page.getByRole("region", { name: "Playbook de incidentes y bitácora" });
    await expect(seccion.getByText(/Los plazos de notificación a la Superintendencia y a los titulares/)).toBeVisible();
    await expect(seccion).toContainText(/hace 3 h/);
    const texto = await seccion.innerText();
    expect(texto).not.toMatch(/SLA|72\s*h|Ley de Ciberseguridad|Art\.?\s*40/i);
    await expect(seccion.locator('input[type="file"]')).toHaveCount(0);
  });

  test("un rechazo del servidor se muestra y no aparece en la bitácora", async ({ page, context }) => {
    const rechazo = "La fecha de detección no puede ser posterior al momento del registro.";
    await simularApi(context, { roles: ["responsable_area"], rechazo });
    await abrirAppLimpia(page);
    await configurarProyecto(page);
    await irASala(page, /Playbook Incidentes/);

    await page.getByRole("button", { name: "Reportar vulneración" }).click();
    const formulario = page.getByRole("form", { name: "Reportar vulneración" });
    await formulario.getByLabel("Título del incidente").fill("Prueba de rechazo");
    await formulario.getByRole("button", { name: "Registrar incidente" }).click();

    await expect(page.getByRole("alert").filter({ hasText: rechazo })).toBeVisible();
    await expect(page.getByText("Todavía no hay incidentes registrados en esta organización.")).toBeVisible();
  });
});
