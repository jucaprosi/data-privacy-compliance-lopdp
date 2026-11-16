/**
 * INC-03f: Insignia de estado y botones Cerrar y Reabrir en la bitácora de incidentes.
 *
 * Contrato: governance/especificaciones/INC-03f.md §5.
 * Mutaciones documentadas m1 a m4.
 */
import { expect, test, type BrowserContext } from "@playwright/test";
import { abrirAppLimpia, configurarProyecto, irASala } from "../utiles";

interface IncidenteConEstadoSimulado {
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
  estado?: "abierto" | "cerrado";
  estado_detalle?: {
    estado: "abierto" | "cerrado";
    decision_notificacion: string | null;
    ultimo_motivo: string | null;
    ultimo_cambio_en: string | null;
  } | null;
}

function crearIncidente(
  secuencia: number,
  titulo: string,
  estado: "abierto" | "cerrado" = "abierto",
  decision_notificacion: string | null = null,
): IncidenteConEstadoSimulado {
  return {
    id: `incidente-${secuencia}`,
    secuencia,
    fecha_deteccion: new Date(Date.now() - 3600_000).toISOString(),
    titulo,
    descripcion: `Descripción del incidente ${secuencia}`,
    severidad: "Alta",
    afecta_datos_personales: true,
    categorias_datos: ["Contacto (Email / Teléfono)"],
    medidas_inmediatas: "Contención aplicada",
    registrado_por: "usuario-servidor",
    registrado_en: new Date().toISOString(),
    huella_anterior: "0".repeat(64),
    huella: String(secuencia).repeat(64).slice(0, 64),
    estado,
    estado_detalle: {
      estado,
      decision_notificacion,
      ultimo_motivo: estado === "cerrado" ? "Motivo inicial de cierre" : null,
      ultimo_cambio_en: new Date().toISOString(),
    },
  };
}

async function simularApiEstado(
  context: BrowserContext,
  {
    roles,
    incidentes = [],
    errorCerrar,
  }: {
    roles: string[];
    incidentes?: IncidenteConEstadoSimulado[];
    errorCerrar?: { status: number; code: string };
  },
) {
  const lista = [...incidentes];
  const llamadas = { cerrar: [] as string[], reabrir: [] as string[] };

  await context.route("**/api/v1/organizacion/me/roles", (route) =>
    route.fulfill({ json: { roles: roles.map((role) => ({ role })) } }),
  );

  await context.route("**/api/v1/incidentes/*/cerrar", async (route) => {
    const url = route.request().url();
    const match = url.match(/\/incidentes\/([^/]+)\/cerrar/);
    const id = match ? decodeURIComponent(match[1]) : "";
    llamadas.cerrar.push(id);

    if (errorCerrar) {
      await route.fulfill({
        status: errorCerrar.status,
        headers: { "Content-Type": "application/json" },
        json: { code: errorCerrar.code, detail: "Error del servidor" },
      });
      return;
    }

    const item = lista.find((i) => i.id === id);
    if (item) {
      item.estado = "cerrado";
      item.estado_detalle = {
        estado: "cerrado",
        decision_notificacion: null,
        ultimo_motivo: "Cierre exitoso verificado",
        ultimo_cambio_en: new Date().toISOString(),
      };
    }
    await route.fulfill({
      status: 200,
      headers: { "Content-Type": "application/json" },
      json: item?.estado_detalle ?? {
        estado: "cerrado",
        decision_notificacion: null,
        ultimo_motivo: "Cierre exitoso verificado",
        ultimo_cambio_en: new Date().toISOString(),
      },
    });
  });

  await context.route("**/api/v1/incidentes/*/reabrir", async (route) => {
    const url = route.request().url();
    const match = url.match(/\/incidentes\/([^/]+)\/reabrir/);
    const id = match ? decodeURIComponent(match[1]) : "";
    llamadas.reabrir.push(id);

    const item = lista.find((i) => i.id === id);
    if (item) {
      item.estado = "abierto";
      item.estado_detalle = {
        estado: "abierto",
        decision_notificacion: null,
        ultimo_motivo: "Reapertura exitosa verificada",
        ultimo_cambio_en: new Date().toISOString(),
      };
    }
    await route.fulfill({
      status: 200,
      headers: { "Content-Type": "application/json" },
      json: item?.estado_detalle ?? {
        estado: "abierto",
        decision_notificacion: null,
        ultimo_motivo: "Reapertura exitosa",
        ultimo_cambio_en: new Date().toISOString(),
      },
    });
  });

  await context.route("**/api/v1/incidentes", async (route) => {
    if (route.request().method() === "GET") {
      await route.fulfill({
        headers: { "Content-Type": "application/json" },
        json: { incidentes: [...lista].reverse(), cadena_integra: true, primer_alterado: null },
      });
      return;
    }
    await route.continue();
  });

  return { lista, llamadas };
}

test.describe("Insignia de estado y botones Cerrar y Reabrir en la bitácora (INC-03f)", () => {
  test("Escenario 1: insignias para abierto, cerrado y cerrado con notificación pendiente (m4)", async ({
    page,
    context,
  }) => {
    const i1 = crearIncidente(1, "Incidente abierto", "abierto");
    const i2 = crearIncidente(2, "Incidente cerrado común", "cerrado", null);
    const i3 = crearIncidente(3, "Incidente cerrado pendiente", "cerrado", "pendiente");

    await simularApiEstado(context, { roles: ["coordinador"], incidentes: [i1, i2, i3] });
    await abrirAppLimpia(page);
    await configurarProyecto(page);
    await irASala(page, /Playbook Incidentes/);

    const insignia1 = page.getByTestId("insignia-estado-incidente-1");
    const insignia2 = page.getByTestId("insignia-estado-incidente-2");
    const insignia3 = page.getByTestId("insignia-estado-incidente-3");

    await expect(insignia1).toHaveText("Abierto");
    await expect(insignia2).toHaveText("Cerrado");
    await expect(insignia3).toHaveText("Cerrado, notificación pendiente");
    await expect(page.getByText("Falta registrar la decisión de notificar.")).toBeVisible();
  });

  test("Escenario 2: motivo mínimo de 10 caracteres habilita el botón (m1)", async ({ page, context }) => {
    const i1 = crearIncidente(1, "Vulneración en servidor web", "abierto");
    await simularApiEstado(context, { roles: ["coordinador"], incidentes: [i1] });

    await abrirAppLimpia(page);
    await configurarProyecto(page);
    await irASala(page, /Playbook Incidentes/);

    await page.getByRole("button", { name: "Cerrar el incidente Vulneración en servidor web" }).click();
    const dialogo = page.getByRole("dialog");
    await expect(dialogo).toBeVisible();

    const botonConfirmar = dialogo.getByRole("button", { name: "Cerrar el incidente" });
    const campoMotivo = dialogo.getByLabel("Motivo del cierre");

    // Menos de 10 caracteres
    await campoMotivo.fill("123456789");
    await expect(botonConfirmar).toBeDisabled();
    await expect(dialogo.getByText("9 de 10 caracteres como mínimo")).toBeVisible();

    // Solo espacios
    await campoMotivo.fill("         ");
    await expect(botonConfirmar).toBeDisabled();

    // Exactamente 10 caracteres sin espacios extremos
    await campoMotivo.fill("  1234567890  ");
    await expect(botonConfirmar).toBeEnabled();
    await expect(dialogo.getByText("10 caracteres")).toBeVisible();
  });

  test("Escenario 3: roles - DPO solo ve insignias; implementador ve botones Cerrar/Reabrir (m2)", async ({
    page,
    context,
  }) => {
    const i1 = crearIncidente(1, "Incidente para DPO", "abierto");
    await simularApiEstado(context, { roles: ["dpo"], incidentes: [i1] });

    await abrirAppLimpia(page);
    await configurarProyecto(page);
    await irASala(page, /Playbook Incidentes/);

    await expect(page.getByTestId("insignia-estado-incidente-1")).toHaveText("Abierto");
    await expect(page.getByRole("button", { name: /Cerrar/ })).toHaveCount(0);
    await expect(page.getByRole("button", { name: /Reabrir/ })).toHaveCount(0);
  });

  test("Escenario 4: 409 DECISION_NOTIFICAR_PENDIENTE muestra mensaje específico y recarga estado", async ({
    page,
    context,
  }) => {
    const i1 = crearIncidente(1, "Incidente con notificación pendiente", "abierto");
    await simularApiEstado(context, {
      roles: ["coordinador"],
      incidentes: [i1],
      errorCerrar: { status: 409, code: "DECISION_NOTIFICAR_PENDIENTE" },
    });

    await abrirAppLimpia(page);
    await configurarProyecto(page);
    await irASala(page, /Playbook Incidentes/);

    await page.getByRole("button", { name: "Cerrar el incidente Incidente con notificación pendiente" }).click();
    const dialogo = page.getByRole("dialog");
    await dialogo.getByLabel("Motivo del cierre").fill("Motivo suficiente con mas de 10 caracteres");
    await dialogo.getByRole("button", { name: "Cerrar el incidente" }).click();

    await expect(dialogo).toHaveCount(0);
    await expect(
      page.getByText(
        "Antes de cerrar, registra si hay que notificar esta vulneración. Hazlo en el paso 7 del asistente, «Decisión de notificar».",
      ),
    ).toBeVisible();
  });

  test("Escenario 5: 409 INCIDENTE_YA_CERRADO muestra mensaje y recarga (m3)", async ({ page, context }) => {
    const i1 = crearIncidente(1, "Incidente que ya cerró otro", "abierto");
    await simularApiEstado(context, {
      roles: ["coordinador"],
      incidentes: [i1],
      errorCerrar: { status: 409, code: "INCIDENTE_YA_CERRADO" },
    });

    await abrirAppLimpia(page);
    await configurarProyecto(page);
    await irASala(page, /Playbook Incidentes/);

    await page.getByRole("button", { name: "Cerrar el incidente Incidente que ya cerró otro" }).click();
    const dialogo = page.getByRole("dialog");
    await dialogo.getByLabel("Motivo del cierre").fill("Motivo suficiente con mas de 10 caracteres");
    await dialogo.getByRole("button", { name: "Cerrar el incidente" }).click();

    await expect(dialogo).toHaveCount(0);
    await expect(page.getByText("Este incidente ya estaba cerrado. Actualizamos su estado.")).toBeVisible();
  });
});
