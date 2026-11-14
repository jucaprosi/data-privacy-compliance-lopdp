/**
 * Consultas de la organización al DPO (DPO-03, governance/especificaciones/DPO-03.md §5 y los criterios de
 * prueba cerrados por UX/UI en governance/tareas/DPO-03.md). API simulada.
 *
 * Verifica:
 * 1. El coordinador ve la bandeja sin «Responder y cerrar».
 * 2. El dpo responde y cierra: «Cerrada», el autor ve la respuesta y desaparece el campo de mensaje.
 * 3. Un mensaje tras el cierre muestra el texto fijo del 409 CONSULTA_CERRADA.
 * 4. Un rol sin acceso a la bandeja no ve «Consultas atendidas».
 * 5. Sin «dictamen», «OPINION_CONSULTIVA», «hash», ids ni caracteres de gobernanza en pantalla.
 * 6. A 375 px, sin desplazamiento horizontal.
 */
import { expect, test, type Page } from "@playwright/test";

import { abrirAppLimpia, configurarProyecto, irASala } from "../utiles";

type Estado = "abierta" | "respondida" | "cerrada";
interface Mensaje {
  secuencia: number;
  autor_rol: string;
  autor_nombre: string | null;
  es_mio: boolean;
  texto: string;
  creado_en: string;
}
interface Consulta {
  id: string;
  asunto: string;
  estado: Estado;
  creado_en: string;
  cerrada_en: string | null;
  huella_hilo: string | null;
  mensajes: Mensaje[];
}

const HUELLA = "abcdef0123456789".repeat(4);

function consulta(autorEsElUsuario: boolean): Consulta {
  return {
    id: "11111111-2222-3333-4444-555555555555",
    asunto: "Conservación de currículos",
    estado: "abierta",
    creado_en: "2026-11-13T15:00:00+00:00",
    cerrada_en: null,
    huella_hilo: null,
    mensajes: [
      {
        secuencia: 1,
        autor_rol: "responsable_area",
        autor_nombre: "Ana Pérez",
        es_mio: autorEsElUsuario,
        texto: "¿Hasta cuándo conservo los currículos de quienes no fueron contratados?",
        creado_en: "2026-11-13T15:00:00+00:00",
      },
    ],
  };
}

async function simularApi(page: Page, userId: string, roles: string[], consultas: Consulta[]) {
  const estado = { consultas, cerrados: [] as string[], mensajes: [] as string[] };
  await page.route("**/api/v1/**", async (route) => {
    const peticion = route.request();
    const url = new URL(peticion.url());
    const ruta = url.pathname.replace(/^\/api\/v1/, "");
    const metodo = peticion.method();
    const responder = (status: number, cuerpo: unknown) =>
      route.fulfill({ status, contentType: "application/json", body: JSON.stringify(cuerpo) });

    if (ruta === "/organizacion/me/roles") {
      return responder(200, {
        user_id: userId,
        tenant_id: "tenant-consultas-e2e",
        roles: roles.map((role) => ({ role, area_id: null, area_nombre: null, valid_to: null })),
      });
    }
    if (ruta === "/dpo/consultas" && metodo === "GET") return responder(200, { consultas: estado.consultas });
    const cierre = ruta.match(/^\/dpo\/consultas\/([^/]+)\/cerrar$/);
    if (cierre && metodo === "POST") {
      if (!roles.includes("dpo")) return responder(403, { code: "CONSULTA_SOLO_DPO_RESPONDE" });
      const c = estado.consultas.find((x) => x.id === cierre[1])!;
      const { respuesta } = JSON.parse(peticion.postData() ?? "{}") as { respuesta: string };
      c.mensajes.push({
        secuencia: c.mensajes.length + 1,
        autor_rol: "dpo",
        autor_nombre: "Luis Mora",
        es_mio: true,
        texto: respuesta,
        creado_en: "2026-11-13T16:00:00+00:00",
      });
      Object.assign(c, { estado: "cerrada", cerrada_en: "2026-11-13T16:00:00+00:00", huella_hilo: HUELLA });
      estado.cerrados.push(c.id);
      return responder(200, { dictamen_id: "d-1", evidencia_sha256: HUELLA, ...c });
    }
    const mensaje = ruta.match(/^\/dpo\/consultas\/([^/]+)\/mensajes$/);
    if (mensaje && metodo === "POST") {
      const c = estado.consultas.find((x) => x.id === mensaje[1])!;
      if (c.estado === "cerrada") return responder(409, { code: "CONSULTA_CERRADA" });
      estado.mensajes.push(c.id);
      return responder(201, {});
    }
    return responder(200, {});
  });
  return estado;
}

async function abrir(page: Page, sala: RegExp) {
  await abrirAppLimpia(page);
  await configurarProyecto(page, "Clínica DPO-03");
  // El menú DPO arranca abierto para quien tiene el rol dpo: pulsarlo de nuevo lo cerraría.
  const dock = page.getByRole("group", { name: "Submenús de DPO" });
  if (sala.test("Consultas atendidas") && (await dock.isVisible())) {
    await dock.getByRole("button", { name: /^Consultas atendidas/ }).click();
    return;
  }
  await irASala(page, sala);
}

test.describe("Consultas de la organización al DPO (DPO-03)", () => {
  test("el coordinador ve la bandeja sin «Responder y cerrar»", async ({ page }) => {
    await simularApi(page, "coord-1", ["coordinador"], [consulta(false)]);
    await abrir(page, /Consultas atendidas/);

    await expect(page.getByRole("main", { name: "Consultas atendidas" })).toBeVisible();
    await expect(page.getByRole("list", { name: "Consultas de la organización" })).toContainText("Conservación de currículos");
    await expect(page.getByText("Solo el DPO responde y cierra las consultas.")).toBeVisible();
    await expect(page.getByRole("button", { name: /Responder y cerrar/ })).toHaveCount(0);
  });

  test("el dpo responde y cierra; la consulta queda cerrada y sin campo de mensaje", async ({ page }) => {
    const estado = await simularApi(page, "dpo-1", ["dpo"], [consulta(false)]);
    await abrir(page, /Consultas atendidas/);

    await page.getByRole("button", { name: "Responder y cerrar la consulta Conservación de currículos" }).click();
    const dialogo = page.getByRole("dialog", { name: "Responder y cerrar la consulta" });
    await expect(dialogo.getByRole("button", { name: "Cancelar" })).toBeFocused();
    await dialogo.getByRole("button", { name: "Responder y cerrar" }).click();
    await expect(dialogo.getByText("Escribe tu respuesta final.")).toBeVisible();
    await dialogo.getByLabel("Tu respuesta final").fill("Solo el plazo que fije el RAT.");
    await dialogo.getByRole("button", { name: "Responder y cerrar" }).click();

    await expect(page.getByRole("main", { name: "Consultas atendidas" }).getByRole("status")).toHaveText("Consulta cerrada. Tu respuesta quedó guardada en la bitácora.");
    expect(estado.cerrados).toHaveLength(1);
    await page.getByRole("main", { name: "Consultas atendidas" }).getByRole("combobox", { name: "Estado" }).selectOption("cerrada");
    await expect(page.getByText("Cerrada", { exact: true }).first()).toBeVisible();
    await expect(page.getByLabel("Huella de integridad")).toHaveText(HUELLA.slice(0, 8));
    await expect(page.getByText("Respuesta guardada como evidencia de asesoría")).toBeVisible();
    await expect(page.getByLabel("Tu mensaje")).toHaveCount(0);
  });

  test("la autora de una consulta cerrada ve la respuesta y no el campo de mensaje", async ({ page }) => {
    const cerrada = consulta(true);
    Object.assign(cerrada, { estado: "cerrada", huella_hilo: HUELLA });
    cerrada.mensajes.push({
      secuencia: 2,
      autor_rol: "dpo",
      autor_nombre: "Luis Mora",
      es_mio: false,
      texto: "Solo el plazo que fije el RAT.",
      creado_en: "2026-11-13T16:00:00+00:00",
    });
    await simularApi(page, "ana-1", ["responsable_area"], [cerrada]);
    await abrir(page, /Consultas al DPO/);

    await expect(page.getByRole("heading", { name: "Consultas al DPO", level: 1 })).toBeVisible();
    const hilo = page.getByRole("list", { name: "Mensajes de la consulta" });
    await expect(hilo).toContainText("Tú · Responsable de área");
    await expect(hilo).toContainText("Luis Mora · DPO");
    await expect(hilo).toContainText("Solo el plazo que fije el RAT.");
    await expect(page.getByText("Esta consulta está cerrada. Para otra pregunta, crea una nueva consulta.")).toBeVisible();
    await expect(page.getByLabel("Tu mensaje")).toHaveCount(0);
  });

  test("un mensaje tras el cierre muestra el texto fijo del 409", async ({ page }) => {
    const c = consulta(true);
    await simularApi(page, "ana-1", ["responsable_area"], [c]);
    await abrir(page, /Consultas al DPO/);

    await page.getByLabel("Tu mensaje").fill("Una duda más.");
    // Mientras escribe, el DPO cierra la consulta: el servidor ya la tiene cerrada.
    Object.assign(c, { estado: "cerrada", huella_hilo: HUELLA });
    await page.getByRole("button", { name: "Enviar mensaje" }).click();
    await expect(page.getByRole("alert").filter({ hasText: "ya está cerrada" })).toHaveText(
      "Esta consulta ya está cerrada. Para otra pregunta, crea una nueva consulta.",
    );
  });

  test("un rol sin acceso a la bandeja no ve «Consultas atendidas»", async ({ page }) => {
    await simularApi(page, "impl-1", ["implementador"], [consulta(false)]);
    await abrir(page, /Consultas atendidas/);

    await expect(page.getByRole("heading", { name: "Consultas atendidas" })).toHaveCount(0);
    await expect(page.getByText("Conservación de currículos")).toHaveCount(0);
  });

  test("la pantalla no muestra términos internos ni ids y no desborda a 375 px", async ({ page }) => {
    await simularApi(page, "dpo-1", ["dpo"], [consulta(false)]);
    await abrir(page, /Consultas atendidas/);
    await page.setViewportSize({ width: 375, height: 800 });

    const main = page.getByRole("main", { name: "Consultas atendidas" });
    await expect(main).toBeVisible();
    const texto = (await main.innerText()) + (await main.innerHTML());
    for (const prohibido of [/dictamen/i, /OPINION_CONSULTIVA/, /hash/i, /11111111-2222/, /[¤¦]/]) {
      expect(texto).not.toMatch(prohibido);
    }
    const desborda = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
    expect(desborda).toBe(false);
  });
});
