// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
// ¤adpa ¤arbitro
// ¤¤developer-architect
/**
 * BIB-414 · «Capacidades editoriales» en /plataforma/capacidades (governance/especificaciones/BIB-414.md). API simulada.
 * Corre en el proyecto «desarrollo» (usa `fijarAjustes`).
 *
 * Mutaciones (cada una hace fallar la prueba que se indica):
 *  - m1: una cuarta casilla «Revisor jurídico» -> «la tabla muestra a los dos operadores…».
 *  - m2: enviar sin motivo -> «sin motivo no se envía nada».
 *  - m3: dejar activa la fila propia -> «la fila propia está desactivada…».
 *  - m4: mostrar el texto crudo del servidor -> «un 403 BIB_AUTOCONCESION muestra su texto fijo…».
 *  - m5: dejar el botón «Registrar revisión jurídica» en la Administración editorial -> «la Administración editorial no ofrece…».
 */
import { expect, test, type Page, type Request } from "@playwright/test";
import { medirContraste } from "../contraste";
import { fijarAjustes, ruta, TENANT_PRUEBA } from "../auth/utilesAuth";

const PROPIA = { usuario_id: "operador-plataforma-dev", nombre: "Operadora Propia", email: "operador@plataforma.test",
  ha_entrado: true, capacidades: ["editor"] };
const OTRO = { usuario_id: "u-otro", nombre: "Operador Nuevo", email: "nuevo@plataforma.test", ha_entrado: false, capacidades: ["revisor_tecnico"] };
const BASE = "**/api/v1/biblioteca/capacidades/equipo";

interface Opciones {
  error?: { estado: number; code: string; detail: string }; resultado?: string;
  /** Historial por `usuario_id`; el que no figure responde lista vacía. */
  historiales?: Record<string, unknown[]>;
  /** Estado con el que responde el historial de ese miembro (por defecto, 200). */
  fallaHistorial?: { usuario_id: string; estado: number };
}

const EVENTOS_OTRO = [
  { id: 1, usuario_id: "u-otro", capacidad: "revisor_tecnico", accion: "concedida", por: PROPIA.usuario_id,
    motivo: "Revisa el contenido técnico", en: "2026-11-20T10:00:00Z" },
  { id: 2, usuario_id: "u-otro", capacidad: "editor", accion: "retirada", por: PROPIA.usuario_id,
    motivo: "Ya no edita plantillas", en: "2026-11-25T10:00:00Z" }];

/** Peticiones de historial que llegaron al mock (con su `usuario_id`, o `null` si faltaba). */
type PeticionHistorial = string | null;

async function simular(page: Page, { error, resultado = "alta", historiales = { "u-otro": EVENTOS_OTRO }, fallaHistorial }: Opciones = {},
  peticionesHistorial: PeticionHistorial[] = []): Promise<Request[]> {
  const envios: Request[] = [];
  await page.route("**/api/v1/**", (r) => r.fulfill({ status: 404, json: { detail: "No simulado" } }));
  await page.route(BASE, (r) => r.fulfill({ json: [PROPIA, OTRO] }));
  // BIB-416 R4: como el backend, `usuario_id` es obligatorio; sin él, 422.
  await page.route(/\/api\/v1\/biblioteca\/capacidades\/equipo\/historial(\?.*)?$/, (r) => {
    const usuario = new URL(r.request().url()).searchParams.get("usuario_id");
    peticionesHistorial.push(usuario);
    if (!usuario) return r.fulfill({ status: 422, json: { detail: [{ type: "missing", loc: ["query", "usuario_id"], msg: "Field required" }] } });
    if (fallaHistorial?.usuario_id === usuario) return r.fulfill({ status: fallaHistorial.estado, json: { detail: "Error simulado" } });
    return r.fulfill({ json: historiales[usuario] ?? [] });
  });
  await page.route(new RegExp(`/api/v1/biblioteca/capacidades/equipo/[^/]+/(conceder|retirar)$`), (r) => {
    envios.push(r.request());
    return error ? r.fulfill({ status: error.estado, json: { code: error.code, detail: error.detail } })
      : r.fulfill({ json: { resultado } });
  });
  return envios;
}

async function abrir(page: Page, opciones?: Opciones, peticionesHistorial?: PeticionHistorial[]): Promise<Request[]> {
  await fijarAjustes(page, { modo: "headers", tenant: TENANT_PRUEBA });
  const envios = await simular(page, opciones, peticionesHistorial);
  await page.goto("/plataforma/capacidades");
  await expect(page.getByRole("heading", { name: "Capacidades editoriales", level: 1 })).toBeVisible();
  return envios;
}

const fila = (page: Page, id: string) => page.getByTestId(`operador-${id}`);

test.describe("Capacidades editoriales (BIB-414)", () => {
  test("la tabla muestra a los dos operadores, el segundo sin entrar, con las tres casillas", async ({ page }) => {
    await abrir(page);
    await expect(page.getByRole("table")).toContainText("Operadores de la plataforma");
    await expect(fila(page, PROPIA.usuario_id)).toContainText("Vinculado a Google");
    await expect(fila(page, "u-otro")).toContainText("Aún no ha entrado");
    await expect(fila(page, "u-otro")).toContainText("Operador Nuevo");
    await expect(fila(page, "u-otro")).toContainText("nuevo@plataforma.test");
    await fila(page, "u-otro").getByRole("button", { name: "Conceder capacidad" }).click();
    const dialogo = page.getByRole("dialog", { name: "Conceder capacidad a Operador Nuevo" });
    await expect(dialogo.getByRole("checkbox")).toHaveCount(3);
    for (const c of ["Editor", "Revisor técnico", "Publicador"]) await expect(dialogo.getByLabel(c, { exact: false }).first()).toBeVisible();
    await expect(page.getByText(/jurídic/i)).toHaveCount(0);
    await expect(dialogo.getByRole("button", { name: "Cancelar" })).toBeFocused();
    await page.keyboard.press("Escape");
    await expect(dialogo).toHaveCount(0);
    await expect(fila(page, "u-otro").getByRole("button", { name: "Conceder capacidad" })).toBeFocused();
  });

  test("sin motivo no se envía nada", async ({ page }) => {
    const envios = await abrir(page);
    await fila(page, "u-otro").getByRole("button", { name: "Conceder capacidad" }).click();
    const dialogo = page.getByRole("dialog");
    await dialogo.getByLabel("Publicador", { exact: false }).check();
    await dialogo.getByLabel("Motivo").fill("corto");
    await dialogo.getByRole("button", { name: "Conceder", exact: true }).click();
    await expect(dialogo.getByRole("alert")).toHaveText("Escribe el motivo (al menos 10 caracteres).");
    expect(envios).toHaveLength(0);
    await dialogo.getByLabel("Motivo").fill("Publica las plantillas aprobadas");
    await dialogo.getByRole("button", { name: "Conceder", exact: true }).click();
    await expect(dialogo.getByRole("status")).toHaveText("Capacidad concedida a Operador Nuevo.");
    expect(envios).toHaveLength(1);
    expect(envios[0].postDataJSON()).toEqual({ capacidad: "publicador", motivo: "Publica las plantillas aprobadas" });
    expect(ruta(envios[0].url())).toBe("/biblioteca/capacidades/equipo/u-otro/conceder");
  });

  test("retirar pide motivo y lleva el nombre accesible completo", async ({ page }) => {
    const envios = await abrir(page, { resultado: "revocacion" });
    await fila(page, "u-otro").getByRole("button", { name: "Retirar revisor técnico a Operador Nuevo" }).click();
    const dialogo = page.getByRole("dialog", { name: "Retirar revisor técnico a Operador Nuevo" });
    await dialogo.getByLabel("Motivo").fill("Cambia de funciones");
    await dialogo.getByRole("button", { name: "Retirar", exact: true }).click();
    await expect(dialogo.getByRole("status")).toHaveText("Capacidad retirada a Operador Nuevo.");
    expect(envios[0].postDataJSON()).toEqual({ capacidad: "revisor_tecnico", motivo: "Cambia de funciones" });
    expect(ruta(envios[0].url())).toBe("/biblioteca/capacidades/equipo/u-otro/retirar");
  });

  test("la fila propia está desactivada, con su texto fijo", async ({ page }) => {
    const envios = await abrir(page);
    const propia = fila(page, PROPIA.usuario_id);
    const conceder = propia.getByRole("button", { name: "Conceder capacidad" });
    await expect(conceder).toHaveAttribute("aria-disabled", "true");
    await expect(conceder).toHaveAccessibleDescription("No puedes concederte ni retirarte capacidades a ti mismo.");
    await conceder.click({ force: true });
    await expect(page.getByRole("dialog")).toHaveCount(0);
    await propia.getByRole("button", { name: /^Retirar/ }).click({ force: true });
    await expect(page.getByRole("dialog")).toHaveCount(0);
    expect(envios).toHaveLength(0);
  });

  test("un 403 BIB_AUTOCONCESION muestra su texto fijo y no el del servidor", async ({ page }) => {
    await abrir(page, { error: { estado: 403, code: "BIB_AUTOCONCESION", detail: "TEXTO CRUDO DEL SERVIDOR" } });
    await fila(page, "u-otro").getByRole("button", { name: "Conceder capacidad" }).click();
    const dialogo = page.getByRole("dialog");
    await dialogo.getByLabel("Editor", { exact: false }).first().check();
    await dialogo.getByLabel("Motivo").fill("Motivo suficiente");
    await dialogo.getByRole("button", { name: "Conceder", exact: true }).click();
    await expect(dialogo.getByRole("alert")).toHaveText("No puedes concederte ni retirarte capacidades a ti mismo.");
    await expect(page.getByText("TEXTO CRUDO DEL SERVIDOR")).toHaveCount(0);
  });

  test("repetir no es un error: «vigente» se muestra como estado", async ({ page }) => {
    await abrir(page, { resultado: "vigente" });
    await fila(page, "u-otro").getByRole("button", { name: "Conceder capacidad" }).click();
    const dialogo = page.getByRole("dialog");
    await dialogo.getByLabel("Revisor técnico", { exact: false }).first().check();
    await dialogo.getByLabel("Motivo").fill("Motivo suficiente");
    await dialogo.getByRole("button", { name: "Conceder", exact: true }).click();
    await expect(dialogo.getByRole("status")).toHaveText("Esta persona ya tiene esa capacidad.");
    await expect(dialogo.getByRole("alert")).toHaveCount(0);
  });

  test("el historial va del más reciente al más antiguo, con quién, motivo y fecha", async ({ page }) => {
    await abrir(page);
    const historial = page.getByRole("region", { name: "Historial de concesiones" });
    const items = historial.getByRole("listitem");
    await expect(items).toHaveCount(2);
    await expect(items.nth(0)).toContainText("Operadora Propia retiró editor a Operador Nuevo");
    await expect(items.nth(0)).toContainText("Ya no edita plantillas");
    await expect(items.nth(1)).toContainText("Operadora Propia concedió revisor técnico a Operador Nuevo");
    await expect(items.nth(1)).toContainText("noviembre de 2026");
  });

  test("BIB-416 R1: se pide el historial de cada miembro con su usuario_id y se une del más reciente al más antiguo", async ({ page }) => {
    const peticiones: PeticionHistorial[] = [];
    await abrir(page, { historiales: {
      [PROPIA.usuario_id]: [{ id: 3, usuario_id: PROPIA.usuario_id, capacidad: "editor", accion: "concedida", por: "u-otro",
        motivo: "Alta inicial", en: "2026-11-22T10:00:00Z" }],
      "u-otro": EVENTOS_OTRO } }, peticiones);
    const items = page.getByRole("region", { name: "Historial de concesiones" }).getByRole("listitem");
    await expect(items).toHaveCount(3);
    await expect(items.nth(0)).toContainText("Ya no edita plantillas");
    await expect(items.nth(1)).toContainText("Alta inicial");
    await expect(items.nth(2)).toContainText("Revisa el contenido técnico");
    expect([...peticiones].sort()).toEqual([PROPIA.usuario_id, "u-otro"].sort());
  });

  test("BIB-416 R2: si un historial responde 500, la tabla del equipo se ve y solo el historial avisa", async ({ page }) => {
    await abrir(page, { fallaHistorial: { usuario_id: "u-otro", estado: 500 } });
    await expect(fila(page, PROPIA.usuario_id)).toBeVisible();
    await expect(fila(page, "u-otro")).toContainText("Operador Nuevo");
    const historial = page.getByRole("region", { name: "Historial de concesiones" });
    await expect(historial.getByRole("alert")).toHaveText("No se pudo cargar el historial. Inténtalo de nuevo.");
    await expect(page.getByText("No se pudo guardar. Inténtalo de nuevo.")).toHaveCount(0);
    await expect(page.getByRole("main").getByRole("alert")).toHaveCount(1);
  });

  test("la navegación de Plataforma ofrece «Capacidades editoriales» y la marca activa", async ({ page }) => {
    await abrir(page);
    const enlace = page.getByRole("navigation", { name: "Plataforma" }).getByRole("link", { name: "Capacidades editoriales" });
    await expect(enlace).toHaveAttribute("aria-current", "page");
    await expect(enlace).toHaveAttribute("href", "/plataforma/capacidades");
  });

  test("la Administración editorial no ofrece revisión jurídica", async ({ page }) => {
    await fijarAjustes(page, { modo: "headers", tenant: TENANT_PRUEBA });
    await page.route("**/api/v1/**", (r) => r.fulfill({ status: 404, json: { detail: "No simulado" } }));
    await page.route("**/api/v1/biblioteca/editorial", (r) => r.fulfill({ json: { actor_id: "x", capacidades: ["editor", "revisor_tecnico", "publicador"],
      versiones: [{ id: "v1", codigo: "BIB-001", version: "1.0", formato: "DOCX", ficha: null, responsable_id: "otro", autores: ["otro"],
        estado: "en_revision", generacion: 1, sha256: null, nombre_archivo: null, sustituye_id: null, creada_en: "2026-11-25T12:00:00Z" }], revisiones: [] } }));
    await page.goto("/plataforma/biblioteca");
    await page.getByRole("button", { name: /BIB-001 · 1.0/ }).click();
    await expect(page.getByRole("button", { name: "Registrar revisión técnica" })).toBeVisible();
    await expect(page.getByText(/jurídic/i)).toHaveCount(0);
    await expect(page.getByText("Guardar cambios exige una nueva revisión técnica.")).toBeVisible();
  });

  for (const tema of ["theme-light", "theme-dark"]) {
    test(`contraste AA y «Retirar» con --ui-peligro-texto en ${tema}`, async ({ page }) => {
      // QA-15: el tema lo aplica la app (`ThemeRootSync` desde el store guardado), no la prueba: se fija en el estado
      // guardado de `jubys-audit-storage` (versión 6 del store) antes de cargar.
      await page.addInitScript((t) => {
        localStorage.setItem("jubys-audit-storage", JSON.stringify({ state: { theme: t === "theme-dark" ? "dark" : "light" }, version: 6 }));
      }, tema);
      await abrir(page, { error: { estado: 403, code: "BIB_AUTOCONCESION", detail: "x" } });
      await expect(page.locator("html")).toHaveClass(new RegExp(tema));
      const retirar = fila(page, "u-otro").getByRole("button", { name: /^Retirar revisor/ });
      const esperado = await page.evaluate(() => {
        const e = document.createElement("span"); e.style.color = "var(--ui-peligro-texto)"; document.body.append(e);
        const c = getComputedStyle(e).color; e.remove(); return c;
      });
      await expect(retirar).toHaveCSS("color", esperado);
      expect(await medirContraste(page, "main")).toEqual([]);
      await fila(page, "u-otro").getByRole("button", { name: "Conceder capacidad" }).click();
      const dialogo = page.getByRole("dialog");
      await dialogo.getByLabel("Editor", { exact: false }).first().check();
      await dialogo.getByLabel("Motivo").fill("Motivo suficiente");
      await dialogo.getByRole("button", { name: "Conceder", exact: true }).click();
      await expect(dialogo.getByRole("alert")).toBeVisible();
      expect(await medirContraste(page, "[role='dialog']")).toEqual([]);
    });
  }
});
