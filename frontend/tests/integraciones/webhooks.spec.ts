// ¤arbitro ¤api-integraciones ¤frontend-ide
/**
 * Arnés de interfaz de API-02b: Webhooks firmados con techo del paquete.
 *
 * Cubre todos los escenarios de aceptación de governance/especificaciones/API-02b.md (§5):
 * - Techo alcanzado con `aria-disabled` y aviso del máximo.
 * - Paso de secreto que no cierra con Escape ni clic fuera, y tras «Ya lo guardé» no queda en DOM ni almacenamiento.
 * - «Probar» verdadero y falso, 422 en el campo de URL, 503 y error genérico con textos fijos (sin detail del servidor).
 * - «Rotar secreto» y «Desactivar» definitivo (sin acciones en filas desactivadas).
 * - Ausencia total de términos técnicos prohibidos (algoritmo de firma/cifrado, `webhook.prueba`, ids internos).
 * - Visibilidad exclusiva para `admin_organizacion` (403 no pinta el panel) y diseño sin desbordes a 375 px.
 */
import { expect, test, type Page } from "@playwright/test";

import { abrirAppLimpia, abrirSubmenu, barraDeMenus, configurarProyecto, submenuPorNombre } from "../utiles";
import { credencialSimulada, fijarAjustes, ruta, sembrarSesion } from "../auth/utilesAuth";
import { medirContraste } from "../contraste";

interface WebhookItem {
  id: string;
  url: string;
  eventos: string[];
  activo: boolean;
  creada_en: string;
  rotada_en: string | null;
}

interface ServidorSimulado {
  webhooks: WebhookItem[];
  maximo: number;
  roles: string[];
  estadoLista?: number;
  errorCrear?: { status: number; code: string; detail: string };
  resultadoPrueba?: { entregado: boolean; intentos: number; estado_http: number | null };
  esperarPrueba?: Promise<void>;
  llamadasPost: Array<{ destino: string; cuerpo: Record<string, unknown> | null }>;
}

const SECRETO_INICIAL = "whsec_prueba_inicial_no_real_1234567890";
const SECRETO_ROTADO = "whsec_prueba_rotado_no_real_0987654321";

async function instalarMocks(page: Page, servidor: ServidorSimulado): Promise<void> {
  await page.route("**/api/v1/**", async (route) => {
    const req = route.request();
    const destino = ruta(req.url());
    const metodo = req.method();
    const json = (status: number, cuerpo: unknown) =>
      route.fulfill({ status, contentType: "application/json", body: JSON.stringify(cuerpo) });

    if (destino === "/organizacion/me/roles") {
      return json(200, {
        user_id: "u-admin",
        tenant_id: "t-1",
        roles: servidor.roles.map((role) => ({ role, area_id: null, area_nombre: null, valid_to: null })),
      });
    }

    if (destino === "/integraciones/techos" && metodo === "GET") {
      const activos = servidor.webhooks.filter((w) => w.activo).length;
      return json(200, {
        claves: { maximo: 10, activas: 0 },
        webhooks: { maximo: servidor.maximo, activos },
      });
    }

    if (destino === "/integraciones/claves" && metodo === "GET") {
      return json(200, { claves: [] });
    }

    if (destino.startsWith("/integraciones/webhooks")) {
      if (!servidor.roles.includes("admin_organizacion")) {
        return json(403, { detail: "Rol no autorizado para esta operación" });
      }

      if (destino === "/integraciones/webhooks" && metodo === "GET") {
        if (servidor.estadoLista && servidor.estadoLista !== 200) {
          return json(servidor.estadoLista, { detail: "Error interno del servidor simulado", code: "ERROR" });
        }
        return json(200, { webhooks: servidor.webhooks });
      }

      const cuerpo = req.postData() ? (JSON.parse(req.postData()!) as Record<string, unknown>) : null;
      if (metodo === "POST") {
        servidor.llamadasPost.push({ destino, cuerpo });
      }

      if (destino === "/integraciones/webhooks" && metodo === "POST") {
        if (servidor.errorCrear) {
          return json(servidor.errorCrear.status, {
            detail: servidor.errorCrear.detail,
            code: servidor.errorCrear.code,
            action_required: null,
          });
        }
        const activos = servidor.webhooks.filter((w) => w.activo).length;
        if (activos >= servidor.maximo) {
          return json(409, {
            detail: "Límite alcanzado en servidor",
            code: "TECHO_WEBHOOKS_ALCANZADO",
            action_required: null,
          });
        }
        const nuevo: WebhookItem = {
          id: `wh-id-interno-${servidor.webhooks.length + 1}`,
          url: String(cuerpo?.url ?? ""),
          eventos: (cuerpo?.eventos as string[]) ?? [],
          activo: true,
          creada_en: "2026-11-19T12:00:00Z",
          rotada_en: null,
        };
        servidor.webhooks.unshift(nuevo);
        return json(201, { status: "SUCCESS", webhook: nuevo, secreto_en_claro: SECRETO_INICIAL });
      }

      const mRotar = destino.match(/^\/integraciones\/webhooks\/([^/]+)\/rotar-secreto$/);
      if (mRotar && metodo === "POST") {
        const fila = servidor.webhooks.find((w) => w.id === mRotar[1]);
        if (!fila) return json(404, { detail: "No encontrado", code: "WEBHOOK_NO_ENCONTRADO" });
        fila.rotada_en = "2026-11-19T15:30:00Z";
        return json(200, { status: "SUCCESS", webhook: { ...fila }, secreto_en_claro: SECRETO_ROTADO });
      }

      const mDes = destino.match(/^\/integraciones\/webhooks\/([^/]+)\/desactivar$/);
      if (mDes && metodo === "POST") {
        const fila = servidor.webhooks.find((w) => w.id === mDes[1]);
        if (!fila) return json(404, { detail: "No encontrado", code: "WEBHOOK_NO_ENCONTRADO" });
        fila.activo = false;
        return json(200, { status: "SUCCESS", webhook: { ...fila } });
      }

      const mProbar = destino.match(/^\/integraciones\/webhooks\/([^/]+)\/probar$/);
      if (mProbar && metodo === "POST") {
        if (servidor.esperarPrueba) {
          await servidor.esperarPrueba;
        }
        return json(200, servidor.resultadoPrueba ?? { entregado: true, intentos: 1, estado_http: 204 });
      }
    }

    return json(404, { detail: "No simulado", code: "NOT_MOCKED" });
  });
}

async function abrirIntegraciones(page: Page, servidor: ServidorSimulado): Promise<void> {
  await fijarAjustes(page);
  await sembrarSesion(page, credencialSimulada());
  await instalarMocks(page, servidor);
  await abrirAppLimpia(page);
  if (!(await barraDeMenus(page).getByRole("button", { name: "Inventario", exact: true }).isVisible())) {
    await configurarProyecto(page, "Entidad API-02b");
  }
  await abrirSubmenu(page, submenuPorNombre(/Claves de integración/)!);
}

const panel = (page: Page) => page.getByRole("region", { name: "Avisos automáticos (webhooks)" });

test.describe("API-02b · Avisos automáticos (webhooks)", () => {
  test("techo alcanzado muestra aria-disabled y línea del máximo", async ({ page }) => {
    const servidor: ServidorSimulado = {
      maximo: 2,
      roles: ["admin_organizacion"],
      llamadasPost: [],
      webhooks: [
        {
          id: "wh-interno-1",
          url: "https://uno.ejemplo.invalid/hook",
          eventos: ["webhook.prueba"],
          activo: true,
          creada_en: "2026-11-18T10:00:00Z",
          rotada_en: null,
        },
        {
          id: "wh-interno-2",
          url: "https://dos.ejemplo.invalid/hook",
          eventos: ["webhook.prueba"],
          activo: true,
          creada_en: "2026-11-18T11:00:00Z",
          rotada_en: "2026-11-19T08:00:00Z",
        },
      ],
    };

    await abrirIntegraciones(page, servidor);
    const p = panel(page);
    await expect(p.getByRole("heading", { name: "Avisos automáticos (webhooks)" })).toBeVisible();
    await expect(p.getByRole("status").filter({ hasText: "2 de 2 webhooks activos" })).toBeVisible();
    await expect(p.getByRole("table", { name: "Webhooks" })).toBeVisible();

    const btnAnadir = p.getByRole("button", { name: "Añadir webhook", exact: true });
    await expect(btnAnadir).toHaveAttribute("aria-disabled", "true");
    await expect(btnAnadir).toBeDisabled();
    await expect(
      p.getByText("Alcanzaste el máximo de webhooks de tu plan (2). Desactiva uno para añadir otro."),
    ).toBeVisible();

    await btnAnadir.click({ force: true });
    await expect(page.getByRole("dialog")).toHaveCount(0);
  });

  test("paso del secreto no cierra con Escape y tras Ya lo guardé no queda en DOM ni localStorage", async ({ page }) => {
    const servidor: ServidorSimulado = {
      maximo: 2,
      roles: ["admin_organizacion"],
      llamadasPost: [],
      webhooks: [],
    };

    await abrirIntegraciones(page, servidor);
    const p = panel(page);
    await expect(p.getByText("Aún no hay webhooks. Añade uno para avisar a otro sistema.")).toBeVisible();
    await expect(p.getByRole("status").filter({ hasText: "0 de 2 webhooks activos" })).toBeVisible();

    await p.getByRole("button", { name: "Añadir webhook", exact: true }).click();
    const dialogo = page.getByRole("dialog", { name: "Añadir webhook" });
    await expect(dialogo).toBeVisible();
    await expect(dialogo.getByRole("button", { name: "Cancelar" })).toBeFocused();

    // Solo se ofrece "Aviso de prueba"; sin marcar no se envía POST
    const grupoEventos = dialogo.getByRole("group", { name: "Eventos" });
    await expect(grupoEventos.getByRole("checkbox")).toHaveCount(1);
    await expect(grupoEventos.getByRole("checkbox", { name: "Aviso de prueba" })).toBeVisible();
    await dialogo.getByRole("textbox", { name: "Dirección del webhook" }).fill("https://hooks.ejemplo.invalid/avisos");
    await dialogo.getByRole("button", { name: "Añadir webhook", exact: true }).click();
    await expect(dialogo.getByText("Elige al menos un evento.")).toBeVisible();
    expect(servidor.llamadasPost).toHaveLength(0);

    // Marcar evento y enviar
    await grupoEventos.getByRole("checkbox", { name: "Aviso de prueba" }).check();
    await dialogo.getByRole("button", { name: "Añadir webhook", exact: true }).click();

    // Paso del secreto en el mismo diálogo
    const dialogoSecreto = page.getByRole("dialog", { name: "Copia el secreto ahora" });
    await expect(dialogoSecreto).toBeVisible();
    await expect(dialogoSecreto.getByRole("textbox", { name: "Secreto del webhook" })).toHaveValue(SECRETO_INICIAL);

    // Escape ni clic fuera cierran el paso del secreto
    await page.keyboard.press("Escape");
    await expect(dialogoSecreto).toBeVisible();
    await page.mouse.click(5, 5);
    await expect(dialogoSecreto).toBeVisible();

    await dialogoSecreto.getByRole("button", { name: "Copiar el secreto" }).click();
    await expect(dialogoSecreto.getByRole("status")).toHaveText("Secreto copiado.");

    const btnYaLoGuarde = dialogoSecreto.getByRole("button", { name: "Ya lo guardé" });
    await expect(btnYaLoGuarde).toBeDisabled();
    await dialogoSecreto.getByRole("checkbox", { name: "Guardé el secreto en un lugar seguro" }).check();
    await expect(btnYaLoGuarde).toBeEnabled();
    await btnYaLoGuarde.click();

    await expect(page.getByRole("dialog")).toHaveCount(0);
    await expect(p.getByRole("button", { name: "Añadir webhook", exact: true })).toBeFocused();
    await expect(p.getByRole("status").filter({ hasText: "1 de 2 webhooks activos" })).toBeVisible();

    // El secreto no queda ni en el DOM, ni en almacenamiento, ni en la URL
    const fugas = await page.evaluate((secreto) => {
      const enDom = document.body.innerHTML.includes(secreto) || document.body.innerText.includes(secreto);
      const enLocal = JSON.stringify(window.localStorage).includes(secreto);
      const enSession = JSON.stringify(window.sessionStorage).includes(secreto);
      const enUrl = window.location.href.includes(secreto);
      return { enDom, enLocal, enSession, enUrl };
    }, SECRETO_INICIAL);
    expect(fugas).toEqual({ enDom: false, enLocal: false, enSession: false, enUrl: false });
  });

  test("probar verdadero/falso, 422 en campo y 503 con textos fijos", async ({ page }) => {
    const url = "https://receptor.ejemplo.invalid/hook";
    let liberarPrueba!: () => void;
    const esperarPrueba = new Promise<void>((resolve) => {
      liberarPrueba = resolve;
    });
    const servidor: ServidorSimulado = {
      maximo: 5,
      roles: ["admin_organizacion"],
      llamadasPost: [],
      esperarPrueba,
      resultadoPrueba: { entregado: true, intentos: 1, estado_http: 204 },
      webhooks: [
        {
          id: "wh-id-prueba-1",
          url,
          eventos: ["webhook.prueba"],
          activo: true,
          creada_en: "2026-11-19T10:00:00Z",
          rotada_en: null,
        },
      ],
    };

    await abrirIntegraciones(page, servidor);
    const p = panel(page);

    // Probar verdadero
    const btnProbar = p.getByRole("button", { name: `Probar el webhook ${url}` });
    await btnProbar.click();
    await expect(btnProbar).toHaveAttribute("aria-busy", "true");
    await expect(p.getByText("Enviando un aviso de prueba… puede tardar unos segundos.")).toBeVisible();
    liberarPrueba();
    await expect(
      p.getByRole("status").filter({
        hasText: "El aviso de prueba llegó. Tu sistema respondió con el código 204 tras 1 intento.",
      }),
    ).toBeVisible();

    // Probar falso con código HTTP
    servidor.esperarPrueba = undefined;
    servidor.resultadoPrueba = { entregado: false, intentos: 3, estado_http: 502 };
    await btnProbar.click();
    await expect(
      p.getByRole("alert").filter({
        hasText:
          "El aviso de prueba no llegó tras 3 intentos. Comprueba la dirección y que tu sistema responda. Tu sistema respondió con el código 502.",
      }),
    ).toBeVisible();

    // 422 WEBHOOK_URL_NO_PERMITIDA en el campo
    servidor.errorCrear = {
      status: 422,
      code: "WEBHOOK_URL_NO_PERMITIDA",
      detail: "detalle tecnico interno 169.254.169.254",
    };
    await p.getByRole("button", { name: "Añadir webhook", exact: true }).click();
    const dialogo = page.getByRole("dialog", { name: "Añadir webhook" });
    const campoUrl = dialogo.getByRole("textbox", { name: "Dirección del webhook" });
    await campoUrl.fill("http://127.0.0.1/interno");
    await dialogo.getByRole("group", { name: "Eventos" }).getByRole("checkbox", { name: "Aviso de prueba" }).check();
    await dialogo.getByRole("button", { name: "Añadir webhook", exact: true }).click();

    await expect(campoUrl).toHaveAttribute("aria-invalid", "true");
    await expect(
      dialogo.getByText("Esta dirección no está permitida. Usa una dirección pública que empiece por https://."),
    ).toBeVisible();
    await expect(page.getByText("detalle tecnico interno")).toHaveCount(0);

    // 503 WEBHOOKS_CIFRADO_NO_CONFIGURADO con texto fijo (nunca detail del servidor)
    servidor.errorCrear = {
      status: 503,
      code: "WEBHOOKS_CIFRADO_NO_CONFIGURADO",
      detail: "Fernet WEBHOOKS_CLAVE_CIFRADO ausente en servidor",
    };
    await campoUrl.fill("https://valido.ejemplo.invalid/hook");
    await dialogo.getByRole("button", { name: "Añadir webhook", exact: true }).click();
    await expect(
      p.getByRole("alert").filter({
        hasText: "Los webhooks no están disponibles en este momento. Escribe al equipo de EVYDENTIA.",
      }),
    ).toBeVisible();
    await expect(page.getByText("Fernet WEBHOOKS_CLAVE_CIFRADO")).toHaveCount(0);
  });

  test("rotar secreto, desactivar definitivo y sin textos prohibidos", async ({ page }) => {
    const url = "https://rotar.ejemplo.invalid/hook";
    const servidor: ServidorSimulado = {
      maximo: 3,
      roles: ["admin_organizacion"],
      llamadasPost: [],
      webhooks: [
        {
          id: "wh-id-secreto-99",
          url,
          eventos: ["webhook.prueba"],
          activo: true,
          creada_en: "2026-11-18T10:00:00Z",
          rotada_en: null,
        },
      ],
    };

    await abrirIntegraciones(page, servidor);
    const p = panel(page);
    await expect(p.getByText("Sin cambios")).toBeVisible();

    // Rotar secreto
    await p.getByRole("button", { name: `Rotar el secreto del webhook ${url}` }).click();
    const dlgRotar = page.getByRole("dialog", { name: "¿Rotar el secreto de este webhook?" });
    await expect(dlgRotar).toBeVisible();
    await expect(dlgRotar.getByRole("button", { name: "Cancelar" })).toBeFocused();
    await dlgRotar.getByRole("button", { name: "Rotar el secreto" }).click();

    const dlgSecreto = page.getByRole("dialog", { name: "Copia el secreto ahora" });
    await expect(dlgSecreto.getByRole("textbox", { name: "Secreto del webhook" })).toHaveValue(SECRETO_ROTADO);
    await dlgSecreto.getByRole("checkbox", { name: "Guardé el secreto en un lugar seguro" }).check();
    await dlgSecreto.getByRole("button", { name: "Ya lo guardé" }).click();

    await expect(p.getByText("19/11/2026")).toBeVisible();

    // Desactivar definitivo
    await p.getByRole("button", { name: `Desactivar el webhook ${url}` }).click();
    const dlgDesactivar = page.getByRole("dialog", { name: "¿Desactivar este webhook?" });
    await expect(dlgDesactivar).toBeVisible();
    await expect(dlgDesactivar.getByRole("button", { name: "Cancelar" })).toBeFocused();
    await expect(
      dlgDesactivar.getByText(
        `Deja de enviar avisos a ${url} de inmediato y libera un lugar de tu plan. No se puede volver a activar: si lo necesitas otra vez, añade uno nuevo.`,
      ),
    ).toBeVisible();
    await dlgDesactivar.getByRole("button", { name: "Desactivar el webhook" }).click();

    await expect(p.getByRole("status").filter({ hasText: "Webhook desactivado." })).toBeVisible();
    await expect(p.getByRole("status").filter({ hasText: "0 de 3 webhooks activos" })).toBeVisible();
    await expect(p.getByText("Desactivado", { exact: true })).toBeVisible();
    await expect(p.getByRole("button", { name: `Probar el webhook ${url}` })).toHaveCount(0);
    await expect(p.getByRole("button", { name: `Rotar el secreto del webhook ${url}` })).toHaveCount(0);
    await expect(p.getByRole("button", { name: `Desactivar el webhook ${url}` })).toHaveCount(0);

    // Ningún texto visible contiene algoritmos, cabeceras, códigos internos ni ids
    const texto = await p.innerText();
    for (const prohibido of [
      "HMAC",
      "SHA-256",
      "SHA256",
      "Fernet",
      "webhook.prueba",
      "wh-id-secreto-99",
      "X-Evydentia",
      "169.254.169.254",
    ]) {
      expect(texto).not.toContain(prohibido);
    }
  });

  test("con 403 el panel no se pinta y fallo inicial ofrece volver a cargar", async ({ page }) => {
    const servidor: ServidorSimulado = {
      maximo: 2,
      roles: ["dpo"],
      llamadasPost: [],
      webhooks: [],
    };
    await abrirIntegraciones(page, servidor);
    await expect(panel(page)).toHaveCount(0);

    // Admin con fallo 500 inicial -> muestra alerta y botón Volver a cargar
    const pageAdmin = await page.context().newPage();
    const srvError: ServidorSimulado = {
      maximo: 2,
      roles: ["admin_organizacion"],
      estadoLista: 500,
      llamadasPost: [],
      webhooks: [],
    };
    await abrirIntegraciones(pageAdmin, srvError);
    const pAdmin = panel(pageAdmin);
    await expect(
      pAdmin.getByRole("alert").filter({ hasText: "No pudimos cargar los webhooks. Inténtalo de nuevo." }),
    ).toBeVisible();
    await expect(pageAdmin.getByText("Error interno del servidor simulado")).toHaveCount(0);

    srvError.estadoLista = 200;
    await pAdmin.getByRole("button", { name: "Volver a cargar" }).click();
    await expect(pAdmin.getByText("Aún no hay webhooks. Añade uno para avisar a otro sistema.")).toBeVisible();
    await pageAdmin.close();
  });

  test("sin desborde a 375 px y con contraste accesible", async ({ page }) => {
    const urlLarga = "https://integraciones.empresa.invalid/webhooks/receptor/canal-principal-muy-largo/v1";
    const servidor: ServidorSimulado = {
      maximo: 5,
      roles: ["admin_organizacion"],
      llamadasPost: [],
      webhooks: [
        {
          id: "wh-resp-1",
          url: urlLarga,
          eventos: ["webhook.prueba"],
          activo: true,
          creada_en: "2026-11-19T10:00:00Z",
          rotada_en: null,
        },
      ],
    };

    await abrirIntegraciones(page, servidor);
    const p = panel(page);
    await expect(p.getByRole("table", { name: "Webhooks" })).toBeVisible();
    await expect(p.getByTitle(urlLarga)).toBeVisible();

    const ilegibles = await medirContraste(page, '[data-panel="webhooks"]');
    expect(ilegibles).toEqual([]);

    await page.setViewportSize({ width: 375, height: 812 });
    await expect(p.getByRole("table", { name: "Webhooks" })).toBeVisible();
    const desborde = await page.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    );
    expect(desborde).toBeLessThanOrEqual(0);
  });
});
