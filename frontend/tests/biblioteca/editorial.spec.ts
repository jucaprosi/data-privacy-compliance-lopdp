// ¤adpa
// ¤¤developer-architect
import { expect, test, type Page } from "@playwright/test";
import { readFileSync } from "node:fs";
import type { CatalogoEditorial } from "../../src/lib/biblioteca/editorial";

const ruta = "/harness-biblioteca/editorial";
const version = { id: "sintetica", codigo: "TEST-01", version: "1.0", formato: "DOCX", ficha: null,
  responsable_id: "editor", autores: ["editor"], estado: "en_revision", generacion: 1,
  sha256: null, nombre_archivo: null, sustituye_id: null, creada_en: "2026-10-25T12:00:00Z" };

async function listado(page: Page, capacidades: string[], actor = "editor", completa = false) {
  const v = completa ? { ...version, sha256: "a".repeat(64), nombre_archivo: "prueba.docx",
    ficha: { nombre: "Maestro prueba", objetivo: "Prueba", fuentes: "Prueba", fecha_revision: "2026-10-25",
      instrucciones: "Prueba", dependencias: "Ninguna", restricciones: "Solo prueba" } } : version;
  await page.route("**/api/v1/biblioteca/editorial", route => route.fulfill({ json: {
    actor_id: actor, capacidades, versiones: [v], revisiones: [],
  } }));
}

test.describe("Interfaz editorial con API simulada (no acredita persistencia/RLS)", () => {
  test.skip(process.env.BIB105_REAL_API === "1", "La aceptación real se ejecuta por separado");

  test("sin capacidad muestra denegación y no ofrece publicación", async ({ page }) => {
    await page.route("**/api/v1/biblioteca/editorial", route => route.fulfill({ status: 403,
      json: { code: "BIB_SIN_CAPACIDAD", detail: "No tienes capacidad editorial asignada." } }));
    await page.goto(ruta);
    await expect(page.getByRole("main", { name: "Administración editorial" }).getByRole("alert")).toContainText("No tienes capacidad editorial");
    await expect(page.getByRole("button", { name: "Publicar versión" })).toHaveCount(0);
  });

  test("editor crea siempre en revisión y no revisa su propia versión", async ({ page }) => {
    await listado(page, ["editor", "revisor_tecnico", "publicador"]);
    let enviada: Record<string, unknown> = {};
    await page.route("**/api/v1/biblioteca/editorial/versiones", async route => {
      enviada = route.request().postDataJSON();
      await route.fulfill({ status: 201, json: version });
    });
    await page.goto(ruta);
    await page.getByLabel("Código", { exact: true }).fill("TEST-01");
    await page.getByLabel("Versión nueva").fill("1.0");
    await page.getByRole("button", { name: "Crear versión en revisión" }).click();
    await expect(page.getByRole("main", { name: "Administración editorial" }).getByRole("status")).toContainText("no está publicada");
    expect(enviada).toEqual({ codigo: "TEST-01", version: "1.0", formato: "DOCX", sustituye_id: null });
    await expect(page.getByRole("button", { name: "Publicar versión" })).toHaveCount(0);
    await expect(page.getByRole("button", { name: "Registrar revisión técnica" })).toHaveCount(0);
  });

  test("publicador ve faltantes y publicación deshabilitada sin revisiones", async ({ page }) => {
    await listado(page, ["publicador"], "publicador", true);
    await page.goto(ruta);
    await page.getByRole("button", { name: /TEST-01 · 1.0/ }).click();
    await page.getByLabel("Motivo de la decisión").fill("Prueba");
    await expect(page.getByRole("button", { name: "Publicar versión" })).toBeDisabled();
    await expect(page.getByText(/Publicación pendiente:/)).toBeVisible();
  });

  test("dictamen usa API y presenta el error real sin simular éxito", async ({ page }) => {
    await listado(page, ["revisor_tecnico"], "tecnico");
    await page.route("**/api/v1/biblioteca/editorial/versiones/sintetica/revisiones", route => route.fulfill({
      status: 409, json: { code: "BIB_CONFLICTO_VERSION", detail: "La versión cambió; actualiza el listado." },
    }));
    await page.goto(ruta);
    await page.getByRole("button", { name: /TEST-01 · 1.0/ }).click();
    await page.getByLabel("Dictamen", { exact: true }).fill("Revisado");
    await page.getByRole("button", { name: "Registrar revisión técnica" }).click();
    await expect(page.getByRole("main", { name: "Administración editorial" }).getByRole("alert")).toContainText("La versión cambió");
    await expect(page.getByText("Dictamen registrado.", { exact: true })).toHaveCount(0);
  });

  test("archivo y ficha guardan datos reales por el cliente HTTP", async ({ page }) => {
    await listado(page, ["editor"]);
    let subida = false;
    await page.route("**/api/v1/biblioteca/editorial/versiones/sintetica/archivo", async route => {
      const cuerpo = route.request().postDataJSON();
      subida = cuerpo.generacion === 1 && cuerpo.nombre === "prueba.docx" && !!cuerpo.contenido_base64;
      await route.fulfill({ json: { ...version, generacion: 2 } });
    });
    await page.goto(ruta);
    await page.getByRole("button", { name: /TEST-01 · 1.0/ }).click();
    await page.getByLabel("Archivo maestro (máximo 10 MB)").setInputFiles({
      name: "prueba.docx", mimeType: "application/octet-stream", buffer: Buffer.from("fixture de cliente HTTP"),
    });
    await page.getByRole("button", { name: "Guardar archivo maestro" }).click();
    await expect(page.getByRole("main", { name: "Administración editorial" }).getByRole("status")).toContainText("Archivo guardado");
    expect(subida).toBe(true);
  });
});

// El manifiesto solo contiene puertos locales, IDs sintéticos y archivos de prueba, nunca URLs DB.
type EntornoReal = {
  codigo: string; neon: string; api_real: boolean; modo_auth: string; rol_conexion_backend: string;
  urls: Record<"editor" | "tecnico" | "juridico" | "publicador" | "denegado", string>;
  archivos: Record<string, string>;
};

function entornoReal(): EntornoReal | null {
  if (process.env.BIB105_REAL_API !== "1") return null;
  if (!process.env.BIB105_E2E_MANIFEST) throw new Error("Falta el manifiesto del arnés real; no se acepta omitir toda la prueba");
  let entorno: EntornoReal;
  try { entorno = JSON.parse(readFileSync(process.env.BIB105_E2E_MANIFEST, "utf8")) as EntornoReal; }
  catch { throw new Error("Manifiesto E2E ausente o inválido; detalles del archivo omitidos"); }
  if (entorno.neon !== "bib-105" || !entorno.api_real || entorno.modo_auth !== "headers"
      || entorno.rol_conexion_backend !== "lopdp_app" || !/^TEST-E2E-[A-Z0-9]+$/.test(entorno.codigo)) {
    throw new Error("Aceptación real requiere el arnés sintético de Neon bib-105");
  }
  for (const valor of Object.values(entorno.urls)) {
    let url: URL;
    try { url = new URL(valor); }
    catch { throw new Error("URL local del arnés no válida; valor omitido"); }
    if (url.protocol !== "http:" || url.hostname !== "127.0.0.1" || url.username || url.password
        || url.pathname !== ruta) throw new Error("Solo se permiten servidores locales del arnés real");
  }
  return entorno;
}

const real = entornoReal();

test.describe("Aceptación con navegador, API y Neon reales; sin rutas simuladas", () => {
  test.skip(!real, "Requiere BIB105_REAL_API=1 y manifiesto del arnés propio; no acredita E2E en CI simulado");

  test("deniega acceso sin capacidad editorial", async ({ page }) => {
    await page.goto(real!.urls.denegado);
    await expect(page.getByRole("main", { name: "Administración editorial" }).getByRole("alert"))
      .toContainText("No tienes capacidad editorial asignada.");
    await expect(page.getByRole("button", { name: "Crear versión en revisión" })).toHaveCount(0);
  });

  test("ciclo real: crear, cargar, revisar, publicar, sustituir, retirar y conservar", async ({ page, request }, info) => {
    test.setTimeout(240_000);
    const e = real!;
    const api = (actor: keyof EntornoReal["urls"], sufijo = "") =>
      new URL(`/api/v1/biblioteca/editorial${sufijo}`, e.urls[actor]).toString();
    const seleccionar = async (version: string) => {
      await page.getByRole("list", { name: "Versiones maestras" }).getByRole("button")
        .filter({ hasText: `${e.codigo} · ${version} ·` }).click();
    };
    const entrar = async (actor: keyof EntornoReal["urls"], version?: string) => {
      await page.goto(e.urls[actor]);
      await expect(page.getByText("Permisos editoriales:", { exact: false })).toBeVisible();
      if (version) await seleccionar(version);
    };
    const cargar = async (version: string) => {
      const ficha: Record<string, string> = { Nombre: `Maestro sintético ${version}`, Objetivo: "Aceptación E2E real",
        Fuentes: "Fixture sintética", "Fecha de revisión": "2026-10-25", Instrucciones: "Solo desarrollo",
        Dependencias: "Ninguna", Restricciones: "No contiene datos ni decisiones jurídicas reales" };
      for (const [label, value] of Object.entries(ficha)) await page.getByLabel(label, { exact: true }).fill(value);
      await page.getByRole("button", { name: "Guardar ficha", exact: true }).click();
      await expect(page.getByText("Ficha guardada; revisiones anteriores conservadas como historial.", { exact: true })).toBeVisible();
      await page.getByLabel("Archivo maestro (máximo 10 MB)").setInputFiles(e.archivos[version]);
      await page.getByRole("button", { name: "Guardar archivo maestro", exact: true }).click();
      await expect(page.getByText("Archivo guardado para revisión.", { exact: true })).toBeVisible();
    };
    const revisar = async (version: string) => {
      for (const [actor, boton] of [["tecnico", "Registrar revisión técnica"], ["juridico", "Registrar revisión jurídica"]] as const) {
        await entrar(actor, version);
        await page.getByLabel("Dictamen", { exact: true }).fill(`Dictamen sintético independiente ${actor} ${version}`);
        await page.getByRole("button", { name: boton, exact: true }).click();
        await expect(page.getByText("Dictamen registrado.", { exact: true })).toBeVisible();
      }
    };
    const obtener = async () => {
      const respuesta = await request.get(api("publicador"));
      expect(respuesta.status()).toBe(200);
      return await respuesta.json() as CatalogoEditorial;
    };
    const rechazar = async (actor: keyof EntornoReal["urls"], sufijo: string, datos: unknown, estado: number, codigo: string) => {
      const respuesta = await request.post(api(actor, sufijo), { data: datos });
      expect(respuesta.status()).toBe(estado);
      expect((await respuesta.json()).code).toBe(codigo);
    };
    expect((await obtener()).versiones.filter(v => v.codigo === e.codigo)).toEqual([]);
    await entrar("editor");
    await page.getByLabel("Código", { exact: true }).fill(e.codigo);
    await page.getByLabel("Versión nueva").fill("1.0");
    await page.getByRole("button", { name: "Crear versión en revisión", exact: true }).click();
    await expect(page.getByText("Versión creada en revisión; no está publicada.", { exact: true })).toBeVisible();
    await cargar("1.0");
    const v1 = (await obtener()).versiones.find(v => v.codigo === e.codigo && v.version === "1.0")!;
    expect(v1.estado).toBe("en_revision");
    for (const actor of ["denegado", "publicador"] as const) {
      await rechazar(actor, "/versiones", { codigo: e.codigo, version: "9.0", formato: "DOCX" }, 403, "BIB_SIN_CAPACIDAD");
    }
    await rechazar("tecnico", `/versiones/${v1.id}/revisiones`, {
      tipo: "juridica", aprobado: true, comentario: "Capacidad incorrecta", generacion: v1.generacion,
    }, 403, "BIB_SIN_CAPACIDAD");
    await rechazar("editor", `/versiones/${v1.id}/revisiones`, {
      tipo: "tecnica", aprobado: true, comentario: "Auto revisión prohibida", generacion: v1.generacion,
    }, 403, "BIB_AUTOR_NO_INDEPENDIENTE");
    await rechazar("editor", `/versiones/${v1.id}/publicar`, {
      motivo: "Auto publicación prohibida", generacion: v1.generacion,
    }, 403, "BIB_AUTOR_NO_INDEPENDIENTE");
    await entrar("publicador", "1.0");
    await page.getByRole("textbox", { name: "Motivo de la decisión", exact: true }).fill("Sin revisiones aún");
    await expect(page.getByRole("button", { name: "Publicar versión", exact: true })).toBeDisabled();
    await rechazar("publicador", `/versiones/${v1.id}/publicar`, {
      motivo: "Intento incompleto", generacion: v1.generacion,
    }, 409, "BIB_REVISION_PENDIENTE");
    await revisar("1.0");
    await entrar("publicador", "1.0");
    await page.getByRole("textbox", { name: "Motivo de la decisión", exact: true }).fill("Publicación sintética 1.0");
    await page.getByRole("button", { name: "Publicar versión", exact: true }).click();
    await expect(page.getByText("Versión publicada.", { exact: true })).toBeVisible();
    await page.screenshot({ path: info.outputPath("publicada.png"), fullPage: true });
    await entrar("editor", "1.0");
    await expect(page.getByRole("button", { name: "Guardar ficha", exact: true })).toHaveCount(0);
    const tamper = await request.put(api("editor", `/versiones/${v1.id}/ficha`), {
      data: { ficha: v1.ficha, generacion: v1.generacion },
    });
    expect(tamper.status()).toBe(409);
    expect((await tamper.json()).code).toBe("BIB_VERSION_INMUTABLE");
    await page.getByRole("button", { name: "Preparar versión sustituta", exact: true }).click();
    await page.getByLabel("Versión nueva").fill("2.0");
    await page.getByRole("button", { name: "Crear versión en revisión", exact: true }).click();
    await expect(page.getByText("Versión creada en revisión; no está publicada.", { exact: true })).toBeVisible();
    await cargar("2.0");
    expect((await obtener()).versiones.find(v => v.id === v1.id)?.estado).toBe("publicada");
    await revisar("2.0");
    await entrar("publicador", "2.0");
    await page.getByRole("textbox", { name: "Motivo de la decisión", exact: true }).fill("Sustitución sintética");
    await page.getByRole("button", { name: "Publicar versión", exact: true }).click();
    await expect(page.getByText("Versión publicada.", { exact: true })).toBeVisible();
    await page.getByRole("textbox", { name: "Motivo de la decisión", exact: true }).fill("Retiro sintético");
    await page.getByRole("button", { name: "Retirar versión", exact: true }).click();
    await expect(page.getByText("Versión retirada; se conserva su historial.", { exact: true })).toBeVisible();
    await page.getByRole("button", { name: "Ver historial editorial", exact: true }).click();
    await expect(page.getByRole("list", { name: "Historial editorial" })).toContainText("retirada");
    await page.screenshot({ path: info.outputPath("retirada.png"), fullPage: true });
    const finales = (await obtener()).versiones.filter(v => v.codigo === e.codigo);
    expect(finales).toHaveLength(2);
    expect(finales.find(v => v.version === "1.0")).toMatchObject({ estado: "sustituida", sha256: v1.sha256 });
    expect(finales.find(v => v.version === "2.0")).toMatchObject({ estado: "retirada", sustituye_id: v1.id });
    expect(finales.some(v => v.version === "0.1")).toBe(false);
    expect((await request.get(api("denegado"))).status()).toBe(403);
    // El arnés externo limpia el código y los IDs sintéticos aun si una aserción falla.
  });
});
