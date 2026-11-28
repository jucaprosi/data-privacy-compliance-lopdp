// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
// ¤frontend-ide ¤arbitro
import type { Page } from "@playwright/test";

/**
 * FE-38 · Las vistas NIIF no son submenús: necesitan la normativa NIIF 18 y datos de balance en el almacén (`niif18Data`).
 * `APERTURAS` (clave `vista:<id>`) dice cómo abrir cada una, como lo haría una persona: elegir NIIF 18, subir un balance
 * simulado en la ingesta y pulsar el botón del lateral. `medirVista` de `rutas.spec.ts` las usa cuando la vista no está en
 * SUBMENUS. `ESTADOS` (clave «<vista:id> · <estado>») se ejecuta con la vista ya abierta; la prueba mide después de cada paso.
 * La API se simula con `page.route`; no hay backend.
 */
export const APERTURAS: Record<string, (page: Page) => Promise<void>> = {
  "vista:niif_ingesta": async (page) => { await conDatos(page, "Ingesta de Balance"); },
  "vista:niif_reclasificacion": async (page) => { await conDatos(page, "Matriz Reclasificación"); },
  "vista:niif_subtotales": async (page) => { await conDatos(page, "Árbol de EEFF"); },
  "vista:niif_mpm": async (page) => { await conDatos(page, "Conciliación MPM"); },
  "vista:niif_diagnostico": async (page) => { await conDatos(page, "Diagnóstico y Plan"); },
  "vista:niif_exportacion": async (page) => { await conDatos(page, "Centro de Exportación"); },
  "vista:niif_doctrina": async (page) => { await conDatos(page, "Visor Doctrinal"); },
};

export const ESTADOS: Record<string, (page: Page) => Promise<void>> = {
  "vista:niif_ingesta · archivo cargado": async (page) => { await subirBalance(page, "balance.csv"); },
  "vista:niif_ingesta · formato no válido": async (page) => { await subirBalance(page, "balance.txt"); },
  "vista:niif_ingesta · procesando": async (page) => {
    await subirBalance(page, "balance.csv");
    await page.route("**/api/v1/niif18/procesar-balance", () => undefined); // la petición queda abierta
    await page.getByRole("button", { name: /Clasificar Balance/ }).click();
    await sinTransiciones(page);
  },
  "vista:niif_mpm · con una medida registrada": async (page) => {
    await page.route("**/api/v1/niif18/mpm", (r) => r.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(MPM) }));
    await page.getByPlaceholder("Ej. EBITDA Ajustado").fill(MPM.nombre);
    await page.getByPlaceholder("Ej. 1200000").fill(String(MPM.ajuste));
    await page.getByPlaceholder(/Explique cómo este MPM/).fill(MPM.justificacion);
    await page.getByRole("button", { name: "Añadir Ajuste MPM" }).click();
    await page.getByText(MPM.nombre, { exact: true }).waitFor();
  },
};

// Datos de balance de prueba (forma de `ProcesamientoResultNIIF18` y `MpmRecord` del almacén).
const BALANCE = {
  inferencia_columnas: { cuenta: "Cuenta", descripcion: "Descripción", saldo: "Saldo", confianza_porcentaje: 96.5 },
  subtotales: { "1_resultado_operativo": 125000, "2_resultado_antes_fin_imp": 98000, "3_resultado_periodo": 73500 },
  cuentas: [
    { cuenta: "4101", descripcion: "Ventas", saldo_original: 250000, categoria: "1. Operación (Ingresos / Gastos Operativos)", pl_neto: 250000 },
    { cuenta: "5101", descripcion: "Costo de ventas", saldo_original: -125000, categoria: "1. Operación (Ingresos / Gastos Operativos)", pl_neto: -125000 },
    { cuenta: "5301", descripcion: "Intereses", saldo_original: -27000, categoria: "3. Financiación (Costos / Pasivos Financieros)", pl_neto: -27000 },
  ],
};
const MPM = { nombre: "EBITDA Ajustado", subtotal_base: "1. Resultado Operativo", valor_base: 125000, ajuste: 12000, efecto_fiscal: 3000, total_mpm: 134000, justificacion: "Excluye un gasto no recurrente." };

/** Elige NIIF 18 (confirmando el cambio) y abre la sala por su nombre en el lateral. */
async function abrirSala(page: Page, sala: string) {
  const selector = page.locator("#selector-normativa");
  if ((await selector.inputValue()) !== "NIIF") {
    await selector.selectOption("NIIF");
    const confirmacion = page.getByRole("alertdialog");
    if (await confirmacion.count()) await confirmacion.getByRole("button", { name: "Cambiar normativa" }).click();
  }
  await pulsarSala(page, sala);
}

/** Pulsa el botón del lateral; por debajo de md el menú va en un cajón que se abre con «Menú». */
async function pulsarSala(page: Page, sala: string) {
  const boton = page.getByRole("button", { name: new RegExp(sala) });
  if (!(await boton.isVisible())) await page.getByRole("button", { name: "Menú", exact: true }).click();
  await boton.click();
}

/** Espera a que terminen las transiciones CSS de color (las animaciones infinitas, como el pulso de «procesando», no cuentan) (el medidor lee el color calculado, no el final). */
async function sinTransiciones(page: Page) {
  await page.waitForFunction(() => document.getAnimations().every((a) => !(a instanceof CSSTransition)));
}

async function subirBalance(page: Page, nombre: string) {
  await page.locator('input[type="file"]').setInputFiles({ name: nombre, mimeType: "text/csv", buffer: Buffer.from("cuenta,descripcion,saldo\n4101,Ventas,250000\n") });
  await sinTransiciones(page);
}

/** Procesa el balance simulado (deja `niif18Data` en el almacén) y abre la sala pedida. */
async function conDatos(page: Page, sala: string) {
  await page.route("**/api/v1/niif18/procesar-balance", (r) => r.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(BALANCE) }));
  await abrirSala(page, "Ingesta de Balance");
  await subirBalance(page, "balance.csv");
  await page.getByRole("button", { name: /Clasificar Balance/ }).click();
  await page.getByText("Matriz de Reclasificación NIIF 18").waitFor();
  if (!/Reclasificación/.test(sala)) await pulsarSala(page, sala);
}
