/**
 * Arnés de pruebas E2E para la Bitácora Inviolable del DPO (DPO-01).
 *
 * Verifica:
 * 1. El rol `dpo` ve el formulario de emisión, emite un dictamen y lo ve reflejado en la bitácora (sin ver el botón de acuse).
 * 2. El rol `admin_organizacion` no ve el formulario de emisión, ve el dictamen pendiente, firma el acuse de recibo y ve el estado actualizado con quién y cuándo firmó.
 * 3. Otros roles (`coordinador`, `implementador`) no ven ni el formulario de emisión ni el botón de acuse.
 */
import { expect, test, type Page, type Request } from "@playwright/test";

import { abrirAppLimpia, configurarProyecto, irASala } from "../utiles";

interface DictamenSimulado {
  id: string;
  tenant_id: string;
  dpo_id: string;
  tipo: string;
  asunto: string;
  referencia_normativa: string;
  cuerpo: string;
  fecha_emision: string;
  es_vinculante: boolean;
  prev_hash: string;
  sha256_hash: string;
  acuse_recibo_alta_direccion: boolean;
  acuse_por: string | null;
  fecha_acuse: string | null;
}

async function instalarApiSimuladaBitacora(
  page: Page,
  userId: string,
  roles: string[],
  dictamenesIniciales: DictamenSimulado[] = [],
): Promise<{ dictamenes: DictamenSimulado[] }> {
  const estado = {
    dictamenes: [...dictamenesIniciales],
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
        tenant_id: "tenant-dpo-e2e",
        roles: roles.map((role) => ({
          role,
          area_id: null,
          area_nombre: null,
          valid_to: null,
        })),
      });
    }

    if (destino.startsWith("/organizacion/designaciones") && metodo === "GET") {
      return responder(200, []);
    }

    if (destino === "/dpo/bitacora" && metodo === "GET") {
      return responder(200, {
        tenant_id: "tenant-dpo-e2e",
        total: estado.dictamenes.length,
        dictamenes: estado.dictamenes,
      });
    }

    if (destino === "/dpo/dictamenes" && metodo === "POST") {
      if (!roles.includes("dpo")) {
        return responder(403, { detail: "Solo el DPO puede emitir dictámenes." });
      }
      const payload = JSON.parse(peticion.postData() ?? "{}") as {
        tipo?: string;
        asunto?: string;
        referencia_normativa?: string;
        cuerpo?: string;
      };
      const prevHash =
        estado.dictamenes.length > 0
          ? estado.dictamenes[estado.dictamenes.length - 1].sha256_hash
          : "0".repeat(64);
      const nuevo: DictamenSimulado = {
        id: `dict-e2e-${estado.dictamenes.length + 1}`,
        tenant_id: "tenant-dpo-e2e",
        dpo_id: userId,
        tipo: payload.tipo ?? "OPINION_CONSULTIVA",
        asunto: payload.asunto ?? "",
        referencia_normativa: payload.referencia_normativa ?? "Art. 50 LOPDP",
        cuerpo: payload.cuerpo ?? "",
        fecha_emision: "2026-10-26T15:00:00Z",
        es_vinculante: false,
        prev_hash: prevHash,
        sha256_hash: "a".repeat(64),
        acuse_recibo_alta_direccion: false,
        acuse_por: null,
        fecha_acuse: null,
      };
      estado.dictamenes.push(nuevo);
      return responder(200, { status: "SUCCESS", dictamen: nuevo });
    }

    const matchAcuse = destino.match(/^\/dpo\/dictamenes\/([^/]+)\/acuse$/);
    if (matchAcuse && metodo === "POST") {
      if (!roles.includes("admin_organizacion")) {
        return responder(403, { detail: "Solo admin_organizacion puede firmar el acuse." });
      }
      const dictamenId = decodeURIComponent(matchAcuse[1]);
      const encontrado = estado.dictamenes.find((d) => d.id === dictamenId);
      if (!encontrado) {
        return responder(404, { detail: "Dictamen no encontrado." });
      }
      if (encontrado.acuse_recibo_alta_direccion) {
        return responder(409, { detail: "El dictamen ya cuenta con acuse de recibo." });
      }
      encontrado.acuse_recibo_alta_direccion = true;
      encontrado.acuse_por = userId;
      encontrado.fecha_acuse = "2026-10-26T16:30:00Z";
      return responder(200, { status: "SUCCESS", dictamen: encontrado });
    }

    return responder(200, {});
  });

  return estado;
}

test.describe("Bitácora del DPO (DPO-01)", () => {
  test("el rol dpo ve el formulario, emite un dictamen y lo ve en la bitácora sin botón de acuse", async ({
    page,
  }) => {
    await instalarApiSimuladaBitacora(page, "usuario-dpo-titular", ["dpo"], []);
    await abrirAppLimpia(page);
    await configurarProyecto(page, "Clínica DPO-01");
    await irASala(page, /Cockpit DPD \/ DPO/);

    const form = page.getByTestId("form-emitir-dictamen");
    await expect(form).toBeVisible();

    await page.getByTestId("select-tipo-dictamen").selectOption("ADVERTENCIA_RIESGO");
    await page.getByTestId("input-referencia-dictamen").fill("Art. 50 LOPDP y Art. 42 LOPDP");
    await page
      .getByTestId("input-asunto-dictamen")
      .fill("Suspensión de biometría sin evaluación de impacto previa");
    await page
      .getByTestId("textarea-cuerpo-dictamen")
      .fill("Se recomienda suspender la captura biométrica hasta contar con EIPD aprobada.");

    await page.getByTestId("btn-emitir-dictamen").click();

    const card = page.getByTestId("dictamen-card-dict-e2e-1");
    await expect(card).toBeVisible();
    await expect(card).toContainText("Suspensión de biometría sin evaluación de impacto previa");
    await expect(card).toContainText("usuario-dpo-titular");
    await expect(page.getByTestId("estado-acuse-dict-e2e-1")).toContainText(
      "Pendiente Acuse de Alta Dirección",
    );
    await expect(page.getByTestId("btn-firmar-acuse-dict-e2e-1")).toHaveCount(0);
  });

  test("admin_organizacion ve el dictamen pendiente, firma el acuse y ve quién y cuándo firmó", async ({
    page,
  }) => {
    const dictamenPendiente: DictamenSimulado = {
      id: "dict-pendiente-01",
      tenant_id: "tenant-dpo-e2e",
      dpo_id: "usuario-dpo-titular",
      tipo: "OPINION_CONSULTIVA",
      asunto: "Revisión de cláusulas de encargados de tratamiento",
      referencia_normativa: "Art. 50 LOPDP",
      cuerpo: "Incluir obligaciones de notificación de incidentes en contratos con proveedores.",
      fecha_emision: "2026-10-26T14:00:00Z",
      es_vinculante: false,
      prev_hash: "0".repeat(64),
      sha256_hash: "b".repeat(64),
      acuse_recibo_alta_direccion: false,
      acuse_por: null,
      fecha_acuse: null,
    };

    await instalarApiSimuladaBitacora(
      page,
      "gerente-general-01",
      ["admin_organizacion"],
      [dictamenPendiente],
    );
    await abrirAppLimpia(page);
    await configurarProyecto(page, "Clínica DPO-01");
    await irASala(page, /Cockpit DPD \/ DPO/);

    await expect(page.getByTestId("form-emitir-dictamen")).toHaveCount(0);

    const botonAcuse = page.getByTestId("btn-firmar-acuse-dict-pendiente-01");
    await expect(botonAcuse).toBeVisible();
    await botonAcuse.click();

    await expect(botonAcuse).toHaveCount(0);
    await expect(page.getByTestId("estado-acuse-dict-pendiente-01")).toContainText(
      "Acuse de Recibo Directivo Asentado",
    );
    await expect(page.getByTestId("detalle-acuse-dict-pendiente-01")).toContainText(
      "gerente-general-01",
    );
  });

  test("otros roles (coordinador, implementador) no ven ni el formulario de emisión ni el botón de acuse", async ({
    page,
  }) => {
    const dictamenPendiente: DictamenSimulado = {
      id: "dict-pendiente-02",
      tenant_id: "tenant-dpo-e2e",
      dpo_id: "usuario-dpo-titular",
      tipo: "OPINION_CONSULTIVA",
      asunto: "Cifrado de respaldos en almacenamiento externo",
      referencia_normativa: "Art. 50 LOPDP",
      cuerpo: "Activar cifrado en reposo con rotación periódica de llaves.",
      fecha_emision: "2026-10-26T14:00:00Z",
      es_vinculante: false,
      prev_hash: "0".repeat(64),
      sha256_hash: "c".repeat(64),
      acuse_recibo_alta_direccion: false,
      acuse_por: null,
      fecha_acuse: null,
    };

    await instalarApiSimuladaBitacora(
      page,
      "usuario-coordinador-01",
      ["coordinador"],
      [dictamenPendiente],
    );
    await abrirAppLimpia(page);
    await configurarProyecto(page, "Clínica DPO-01");
    await irASala(page, /Cockpit DPD \/ DPO/);

    await expect(page.getByTestId("dictamen-card-dict-pendiente-02")).toBeVisible();
    await expect(page.getByTestId("form-emitir-dictamen")).toHaveCount(0);
    await expect(page.getByTestId("btn-firmar-acuse-dict-pendiente-02")).toHaveCount(0);
  });
});
