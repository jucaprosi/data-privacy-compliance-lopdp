/**
 * Arnés de pruebas E2E para Auditoría y Acciones Correctivas (CAPA-01).
 *
 * Verifica en la sala «Historial de Auditoría»:
 * 1. El rol `coordinador` (y `dpo`) ve el formulario de alta, registra un hallazgo CAPA y lo ve en la lista.
 * 2. El rol `admin_organizacion` no ve el formulario de alta, ve el hallazgo abierto (si no es el responsable),
 *    adjunta el identificador de evidencia y cierra el caso, quedando `CERRADO_VERIFICADO`.
 * 3. El rol `implementador` consulta los casos pero no ve el formulario de alta ni la acción de cierre.
 */
import { expect, test, type Page, type Request } from "@playwright/test";

import { abrirAppLimpia, configurarProyecto, irASala } from "../utiles";

interface TicketSimulado {
  id: string;
  tenant_id: string;
  control_id: string;
  severidad: string;
  descripcion_hallazgo: string;
  causa_raiz: string;
  accion_correctiva: string;
  responsable_implementacion_id: string;
  creado_por: string;
  auditor_verificador_id: string | null;
  estado: string;
  evidencia_cierre_id: string | null;
  fecha_creacion: string;
  fecha_cierre: string | null;
}

async function instalarApiSimuladaCapa(
  page: Page,
  userId: string,
  roles: string[],
  ticketsIniciales: TicketSimulado[] = [],
): Promise<{ tickets: TicketSimulado[] }> {
  const estado = {
    tickets: [...ticketsIniciales],
  };

  await page.route("**/api/v1/**", async (route) => {
    const peticion: Request = route.request();
    const urlCompleta = new URL(peticion.url());
    const destino = `${urlCompleta.pathname.replace(/^\/api\/v1/, "")}${urlCompleta.search}`;
    const metodo = peticion.method();

    const responder = (status: number, cuerpo: unknown) =>
      route.fulfill({
        status,
        contentType: "application/json",
        body: JSON.stringify(cuerpo),
      });

    if (destino === "/organizacion/me/roles" && metodo === "GET") {
      return responder(200, {
        user_id: userId,
        tenant_id: "tenant-capa-e2e",
        roles: roles.map((role) => ({
          role,
          area_id: null,
          area_nombre: null,
          valid_to: null,
        })),
      });
    }

    if (destino === "/capa/tickets" && metodo === "GET") {
      return responder(200, estado.tickets);
    }

    if (destino === "/capa/tickets" && metodo === "POST") {
      if (!roles.includes("coordinador") && !roles.includes("dpo")) {
        return responder(403, { detail: "Rol no autorizado para registrar hallazgos CAPA." });
      }
      const payload = JSON.parse(peticion.postData() ?? "{}") as {
        control_id?: string;
        severidad?: string;
        descripcion_hallazgo?: string;
        causa_raiz?: string;
        accion_correctiva?: string;
        responsable_implementacion_id?: string;
      };
      const nuevo: TicketSimulado = {
        id: `capa-e2e-${estado.tickets.length + 1}`,
        tenant_id: "tenant-capa-e2e",
        control_id: payload.control_id ?? "P1",
        severidad: payload.severidad ?? "NO_CONFORMIDAD_MENOR",
        descripcion_hallazgo: payload.descripcion_hallazgo ?? "",
        causa_raiz: payload.causa_raiz ?? "",
        accion_correctiva: payload.accion_correctiva ?? "",
        responsable_implementacion_id: payload.responsable_implementacion_id ?? "",
        creado_por: userId,
        auditor_verificador_id: null,
        estado: "ABIERTO",
        evidencia_cierre_id: null,
        fecha_creacion: "2026-10-27T12:00:00Z",
        fecha_cierre: null,
      };
      estado.tickets.unshift(nuevo);
      return responder(201, nuevo);
    }

    const matchCerrar = destino.match(/^\/capa\/tickets\/([^/]+)\/cerrar$/);
    if (matchCerrar && metodo === "POST") {
      if (!roles.includes("coordinador") && !roles.includes("admin_organizacion")) {
        return responder(403, { detail: "Rol no autorizado para cerrar acciones correctivas CAPA." });
      }
      const ticketId = decodeURIComponent(matchCerrar[1]);
      const encontrado = estado.tickets.find((t) => t.id === ticketId);
      if (!encontrado) {
        return responder(404, { detail: "Ticket no encontrado." });
      }
      if (encontrado.responsable_implementacion_id === userId) {
        return responder(403, { detail: "Violación SoD: auto-verificación prohibida." });
      }
      const payload = JSON.parse(peticion.postData() ?? "{}") as { evidencia_id?: string };
      encontrado.estado = "CERRADO_VERIFICADO";
      encontrado.auditor_verificador_id = userId;
      encontrado.evidencia_cierre_id = payload.evidencia_id ?? "";
      encontrado.fecha_cierre = "2026-10-27T14:00:00Z";
      return responder(200, encontrado);
    }

    return responder(200, {});
  });

  return estado;
}

test.describe("Sala Historial de Auditoría · Acciones Correctivas CAPA (CAPA-01)", () => {
  test("el rol coordinador ve el formulario en Historial de Auditoría, registra un hallazgo y lo ve listado", async ({
    page,
  }) => {
    await instalarApiSimuladaCapa(page, "coord-usuario-01", ["coordinador"], []);
    await abrirAppLimpia(page);
    await configurarProyecto(page, "Corporación CAPA-01");
    await irASala(page, /Historial de Auditoría/);

    const form = page.getByTestId("capa-form-registro");
    await expect(form).toBeVisible();

    await form.getByPlaceholder("Ej. P14").fill("P14");
    await form.getByPlaceholder("ID del miembro activo").fill("impl-miembro-01");
    await form
      .getByPlaceholder("Describe la no conformidad detectada")
      .fill("Respaldos de base de datos sin cifrado AES-256");
    await form
      .getByPlaceholder("Origen técnico u organizativo")
      .fill("Parámetro por defecto en el volumen de respaldo");
    await form
      .getByPlaceholder("Plan de remediación verificable")
      .fill("Habilitar cifrado en reposo y rotar llaves KMS");

    await form.getByRole("button", { name: /Registrar hallazgo CAPA/i }).click();

    const card = page.getByTestId("capa-ticket-capa-e2e-1");
    await expect(card).toBeVisible();
    await expect(card).toContainText("Respaldos de base de datos sin cifrado AES-256");
    await expect(card).toContainText("P14");
    await expect(card).toContainText("impl-miembro-01");
    await expect(card).toContainText("ABIERTO");
  });

  test("admin_organizacion no ve el formulario de alta, verifica y cierra un caso abierto de otro responsable", async ({
    page,
  }) => {
    const ticketAbierto: TicketSimulado = {
      id: "capa-abierto-01",
      tenant_id: "tenant-capa-e2e",
      control_id: "P22",
      severidad: "NO_CONFORMIDAD_MAYOR",
      descripcion_hallazgo: "Cláusula de confidencialidad ausente en contratos de soporte",
      causa_raiz: "Plantilla contractual desactualizada",
      accion_correctiva: "Actualizar plantilla y firmar adendas con el personal técnico",
      responsable_implementacion_id: "impl-miembro-01",
      creado_por: "dpo-usuario-01",
      auditor_verificador_id: null,
      estado: "ABIERTO",
      evidencia_cierre_id: null,
      fecha_creacion: "2026-10-27T10:00:00Z",
      fecha_cierre: null,
    };

    await instalarApiSimuladaCapa(
      page,
      "admin-verificador-01",
      ["admin_organizacion"],
      [ticketAbierto],
    );
    await abrirAppLimpia(page);
    await configurarProyecto(page, "Corporación CAPA-01");
    await irASala(page, /Historial de Auditoría/);

    await expect(page.getByTestId("capa-form-registro")).toHaveCount(0);

    const panelCierre = page.getByTestId("capa-cierre-panel-capa-abierto-01");
    await expect(panelCierre).toBeVisible();

    await panelCierre
      .getByLabel("Evidencia de cierre para capa-abierto-01")
      .fill("EVD-ADENDA-2026-09");
    await panelCierre.getByRole("button", { name: /Verificar y Cerrar CAPA/i }).click();

    await expect(panelCierre).toHaveCount(0);
    const card = page.getByTestId("capa-ticket-capa-abierto-01");
    await expect(card).toContainText("CERRADO_VERIFICADO");
    await expect(card).toContainText("admin-verificador-01");
    await expect(card).toContainText("EVD-ADENDA-2026-09");
  });

  test("implementador consulta los casos pero no ve el formulario de alta ni la acción de cierre", async ({
    page,
  }) => {
    const ticketAbierto: TicketSimulado = {
      id: "capa-abierto-02",
      tenant_id: "tenant-capa-e2e",
      control_id: "P35",
      severidad: "OBSERVACION",
      descripcion_hallazgo: "Procedimiento de atención de derechos ARCO sin difusión interna",
      causa_raiz: "Falta de capacitación trimestral",
      accion_correctiva: "Ejecutar taller obligatorio y publicar guía en intranet",
      responsable_implementacion_id: "impl-miembro-01",
      creado_por: "coord-usuario-01",
      auditor_verificador_id: null,
      estado: "ABIERTO",
      evidencia_cierre_id: null,
      fecha_creacion: "2026-10-27T11:00:00Z",
      fecha_cierre: null,
    };

    await instalarApiSimuladaCapa(
      page,
      "impl-miembro-01",
      ["implementador"],
      [ticketAbierto],
    );
    await abrirAppLimpia(page);
    await configurarProyecto(page, "Corporación CAPA-01");
    await irASala(page, /Historial de Auditoría/);

    await expect(page.getByTestId("capa-ticket-capa-abierto-02")).toBeVisible();
    await expect(page.getByTestId("capa-form-registro")).toHaveCount(0);
    await expect(page.getByTestId("capa-cierre-panel-capa-abierto-02")).toHaveCount(0);
  });
});
