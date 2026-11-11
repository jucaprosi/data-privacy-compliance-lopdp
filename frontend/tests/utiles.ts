/**
 * Utilidades compartidas del arnés de interfaz.
 *
 * El estado del proyecto vive en localStorage, así que cada spec tiene que
 * partir de cero: un test que hereda la sesión del anterior comprueba el
 * arrastre, no la regla.
 */
import { createHash, randomBytes } from "node:crypto";

import { expect, type BrowserContext, type Page } from "@playwright/test";

import { nivelMinimoDeEstado } from "../src/lib/diagnostico/escala";

// Importar nuevas utilidades (inspiradas en ERP, Jubilo Pl, PDA)
export { ConsoleSentinel } from "./consoleSentinel";
export { AuditTrail, type ClickEntry, type SnapshotMetadata } from "./auditTrail";
export { LocatorResolver, L } from "./locatorResolver";

// Fixtures reales (inspiradas en PDA)
export {
  createTestProject,
  createTestAssessment,
  resetTestProject,
  getAssessmentPanel,
  waitForAppReady,
  type TestProjectConfig,
  type TestAssessmentConfig,
  type TestProject,
  type TestAssessment,
} from "./fixtures";

// Test Data Builders (patrón de PDA)
export {
  ProjectBuilder,
  ControlBuilder,
  AssessmentBuilder,
  ControlSetBuilder,
  TestScenario,
  type ProjectData,
  type ControlData,
  type AssessmentResultData,
} from "./testDataBuilder";

/** Claves de persistencia del store; se limpian antes de que la app arranque. */
const CLAVES_PERSISTENCIA = ["jubys-audit-storage", "jubys-proyectos-v1"];

/**
 * Abre la aplicación sobre un proyecto nuevo y vacío.
 *
 * Son dos limpiezas distintas y ambas hacen falta. Borrar localStorage descarta
 * la sesión anterior, pero el estado inicial del store trae un cuestionario de
 * referencia ya respondido; sin descartarlo, la cobertura arrancaría al 100 % y
 * ningún spec podría medir lo que él mismo responde. «Archivo › Nuevo» es la
 * vía que la propia aplicación ofrece para eso.
 *
 * La barra lateral arranca vacía hasta guardar la ficha organizacional
 * (`modulosNavegacion = !isConfigured ? [] : [...]` en dashboard/page.tsx), así
 * que "Dashboard Central" no existe todavía en este punto: la señal de
 * hidratación es el propio campo de la ficha, que es la vista con la que
 * arranca un proyecto sin configurar.
 */
export async function abrirAppLimpia(page: Page): Promise<void> {
  await page.addInitScript((claves: string[]) => {
    try {
      for (const clave of claves) window.localStorage.removeItem(clave);
    } catch {
      // Un navegador con almacenamiento bloqueado ya arranca limpio.
    }
  }, CLAVES_PERSISTENCIA);
  await page.goto("/");

  // Hasta que el store se hidrata, la ficha se dibuja como esqueleto y descarta
  // lo que se escriba en ella. El campo con su valor por defecto ya cargado es
  // la señal de que la hidratación terminó; interactuar antes produce fallos
  // intermitentes que no corresponden a ningún defecto del producto.
  await expect(page.getByRole("textbox", { name: /Razón Social/ })).toHaveValue(/.+/);

  // "Archivo" vive en la cabecera y está disponible aunque el proyecto no
  // esté configurado todavía.
  await page.getByRole("button", { name: "Archivo", exact: true }).click();
  await page.getByRole("menuitem", { name: "Nuevo" }).click();
  await expect(page.getByText("Nuevo proyecto creado")).toBeVisible();
}

// === FE-22 ===
import { MENUS, SUBMENUS, type Submenu } from "../src/components/layout/menus";

/**
 * Nombres con que la barra lateral plana mostraba cada vista antes de FE-22 (nombre y distintivo,
 * tal como los leía el nombre accesible del botón). Las pruebas siguen llamando a `irASala` con
 * ellos; aquí se traducen a la vista y la vista a su menú y submenú.
 */
const NOMBRES_ANTERIORES: ReadonlyArray<readonly [string, Submenu["vista"]]> = [
  ["Normativa Norma", "diagnostico"],
  ["Dashboard Central Módulo 1", "dashboard"],
  ["Hoja de Ruta Módulo 5", "roadmap"],
  ["RAT Maestro Art. 35", "rat"],
  ["Riesgos & MTGE ISO 27005", "riesgos"],
  ["Cockpit DPD / DPO Art. 48", "dpo"],
  ["Historial de Auditoría Módulo 3", "auditoria"],
  ["Bóveda Evidencias Sha-256", "evidencias"],
  ["Playbook Incidentes SLA 72h", "incidentes"],
  ["Derechos ARCO+ Art. 37", "arco"],
  ["MTGE Relacional EIPD", "mtge_relacional"],
  ["Transferencias Art. 60", "terceros"],
  ["Copiloto Mitigación AI", "mitigacion_ia"],
  ["Reportes PDF", "reportes"],
];

const escaparRegExp = (texto: string): string => texto.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

/** Submenú al que apunta un nombre, antiguo («RAT Maestro») o nuevo («Inventario › Tratamientos (RAT)»). */
export function submenuPorNombre(nombre: RegExp): Submenu | undefined {
  const coincide = (texto: string) => new RegExp(nombre.source, nombre.flags.replace("g", "")).test(texto);
  const anterior = NOMBRES_ANTERIORES.find(([texto]) => coincide(texto));
  if (anterior) return SUBMENUS.find((s) => s.vista === anterior[1]);
  return SUBMENUS.find((s) => {
    const menu = MENUS.find((m) => m.id === s.menu)?.nombre ?? "";
    return coincide(`${menu} › ${s.nombre}`) || coincide(s.nombre);
  });
}

/** Barra de los nueve menús. */
export function barraDeMenus(page: Page) {
  return page.getByRole("navigation", { name: "Menús principales" });
}

/** Abre un menú y, en el dock lateral, uno de sus submenús. */
export async function abrirSubmenu(page: Page, submenu: Submenu): Promise<void> {
  const menu = MENUS.find((m) => m.id === submenu.menu);
  if (!menu) throw new Error(`Menú desconocido: ${submenu.menu}`);
  await barraDeMenus(page).getByRole("button", { name: menu.nombre, exact: true }).click();
  await page
    .getByRole("group", { name: `Submenús de ${menu.nombre}` })
    .getByRole("button", { name: new RegExp(`^${escaparRegExp(submenu.nombre)}`) })
    .click();
}

/**
 * Navega a una sala operativa. Con LOPDP abre su menú y su submenú; donde no hay nueve menús
 * (NIIF 18) o el nombre no es de una vista (el pie «Ficha Organizacional»), pulsa el botón por su
 * nombre, como antes.
 */
export async function irASala(page: Page, nombre: RegExp): Promise<void> {
  const barra = barraDeMenus(page);
  const boton = page.getByRole("button", { name: nombre });
  await expect(barra.or(boton).first()).toBeVisible();
  const submenu = submenuPorNombre(nombre);
  if (submenu && (await barra.isVisible())) {
    await abrirSubmenu(page, submenu);
    return;
  }
  await boton.click();
}
// === fin FE-22 ===

/**
 * Completa la ficha organizacional, la guarda y elige la normativa LOPDP.
 *
 * Las tres cosas son necesarias para que la barra lateral deje de estar vacía:
 * sin ficha guardada no hay navegación, y sin normativa elegida el único
 * módulo disponible es "Normativa" (`!normativaSeleccionada → [moduloNormativa]`
 * en dashboard/page.tsx) — ni "Dashboard Central" ni el resto existen todavía.
 */
/**
 * Responde todas las preguntas del Perfil de Operación de la ficha.
 *
 * Desde que son obligatorias (commit c92490e), «Guardar Ficha y Continuar» sigue
 * desactivado mientras alguna esté sin responder. Cada pregunta es un grupo de
 * radio Sí/No (`role="radiogroup"` en PerfilOperacionForm.tsx). Las respuestas
 * definen qué controles se evalúan, así que se pueden elegir para un alcance
 * concreto; por defecto «No» a todo.
 */
export async function responderPerfilOperacion(
  page: Page,
  respuesta: "Sí" | "No" = "No"
): Promise<void> {
  const grupos = page.getByRole("radiogroup");
  const total = await grupos.count();
  expect(total, "la ficha debe traer las preguntas del perfil de operación").toBeGreaterThan(0);
  for (let i = 0; i < total; i += 1) {
    await grupos.nth(i).getByRole("radio", { name: respuesta, exact: true }).check();
  }
}

export async function configurarProyecto(
  page: Page,
  razonSocial = "Entidad de Prueba S.A.",
  perfil: "Sí" | "No" = "No"
): Promise<void> {
  // No hay que esperar hidratación aquí: abrirAppLimpia ya la esperó, y tras
  // "Archivo > Nuevo" el campo llega vacío a propósito (resetConfig() deja
  // razonSocial: ""), no con un valor previo que confirme que cargó.
  const campoRazonSocial = page.getByRole("textbox", { name: /Razón Social/ });
  await campoRazonSocial.fill(razonSocial);
  await responderPerfilOperacion(page, perfil);

  // CI-15: se espera la condición que persiste tras guardar, no el aviso de
  // éxito, que dura 700 ms (ProjectConfig.tsx) y con la máquina cargada se pierde.
  // Guardar la ficha deja la navegación en "Normativa", con el selector visible.
  await page.getByRole("button", { name: /Guardar Ficha y Continuar/ }).click();
  await expect(page.locator("#selector-normativa")).toBeVisible();
  await page.locator("#selector-normativa").selectOption("LOPDP");

  // La primera pregunta de D01 abre un <dialog> modal de "perspectiva
  // ejecutiva" (AlertaDimension.tsx, showModal()) que bloquea el resto de la
  // página hasta cerrarse; sin descartarlo, ningún clic posterior llega a su
  // destino real.
  await page.getByRole("button", { name: "Cerrar alerta" }).click();
  // === FE-22-configurarProyecto ===
  await expect(barraDeMenus(page).getByRole("button", { name: "Inicio", exact: true })).toBeVisible();
  // === fin FE-22-configurarProyecto ===
}

// === DIAG-09-responderControlActual ===
/**
 * Responde el control que el cuestionario tenga en pantalla con un nivel 1 a 5 de la escala.
 * Acepta también el estado de la escala anterior y lo lleva al nivel mínimo que le corresponde
 * (Conforme → 4, Parcial → 2, No Conforme → 1), para no reescribir las pruebas que solo necesitan
 * «una respuesta».
 */
export async function responderControlActual(
  page: Page,
  nivel: number | "Conforme" | "Parcial" | "No Conforme"
): Promise<void> {
  const numero = typeof nivel === "number" ? nivel : nivelMinimoDeEstado(nivel)!;
  const opcion = page
    .getByRole("radiogroup", { name: /Nivel de madurez/ })
    .getByRole("radio", { name: new RegExp(`^${numero}\\b`) });
  await opcion.click();
  await expect(opcion).toHaveAttribute("aria-checked", "true");
}
// === fin DIAG-09-responderControlActual ===

/** Panel de resultados del assessment dentro del tablero. */
export function panelAssessment(page: Page) {
  return page.locator('section[aria-labelledby="assessment-story-title"]');
}

// === EVI-01b ===
/**
 * Subida firmada simulada (EVI-01b): ÚNICA función de las pruebas que mockea las rutas nuevas de
 * evidencias y el PUT a la URL firmada. Ningún spec lo hace por su cuenta (lo vigila
 * `evidencias/sin-mocks-sueltos.spec.ts`); un spec que sube un archivo la llama con una línea.
 *
 * El mock del PUT comprueba que lleva `x-goog-if-generation-match: 0` y responde 412 si no, como el
 * almacén real; el de confirmar calcula la huella del archivo recibido y la compara con la del
 * navegador, como el servidor. Admite los dos errores que la pantalla debe mostrar tal cual.
 */
export type ErrorSubidaSimulado = "almacen-no-configurado" | "huella-distinta";

export interface OpcionesSubidaFirmada {
  /** Etapa del diagnóstico que devuelve el servidor (por omisión, sin sellar). */
  etapa?: "prueba" | "real" | null;
  error?: ErrorSubidaSimulado;
  /** Retraso del PUT al almacén, para probar lo que ocurre mientras hay una subida en curso. */
  retardoMs?: number;
}

export interface DocumentoSimulado {
  id: string;
  codigo: string;
  nombre_archivo: string;
  tipo_mime: string;
  tamano_bytes: number;
  sha256_hash: string;
  normativa: string;
  subido_por: string;
  subido_en: string;
  retencion_dias: number;
  controles_vinculados: number[];
}

export interface SubidaFirmadaSimulada {
  /** Documentos que el «servidor» tiene registrados. */
  documentos: DocumentoSimulado[];
  /** Subidas al almacén recibidas sin la cabecera de escritura única (debe quedar en 0). */
  subidasSinCabecera: number;
  /** Llamadas a «confirmar» recibidas. */
  confirmaciones: number;
}

export const HOST_ALMACEN_SIMULADO = "almacen.invalid";

export async function simularSubidaFirmada(
  destino: Page | BrowserContext,
  opciones: OpcionesSubidaFirmada = {}
): Promise<SubidaFirmadaSimulada> {
  const estado: SubidaFirmadaSimulada = { documentos: [], subidasSinCabecera: 0, confirmaciones: 0 };
  const objetos = new Map<string, Buffer>();
  const json = (status: number, cuerpo: unknown) => ({ status, contentType: "application/json", body: JSON.stringify(cuerpo) });

  await destino.route(`https://${HOST_ALMACEN_SIMULADO}/**`, async (route) => {
    const peticion = route.request();
    if (peticion.method() !== "PUT") return route.fulfill({ status: 405 });
    if (peticion.headers()["x-goog-if-generation-match"] !== "0") {
      estado.subidasSinCabecera += 1;
      return route.fulfill({ status: 412, body: "Falta la cabecera de escritura única" });
    }
    if (opciones.retardoMs) await new Promise((resolver) => setTimeout(resolver, opciones.retardoMs));
    const clave = new URL(peticion.url()).pathname.slice(1);
    if (objetos.has(clave)) return route.fulfill({ status: 412, body: "El objeto ya existe" });
    objetos.set(clave, peticion.postDataBuffer() ?? Buffer.alloc(0));
    return route.fulfill({ status: 200, body: "" });
  });

  await destino.route("**/api/v1/diagnostico/etapa", async (route) =>
    route.fulfill(json(200, { etapa: opciones.etapa ?? null, siguiente: opciones.etapa === "real" ? null : "prueba" }))
  );

  await destino.route("**/api/v1/evidencias/**", async (route) => {
    const peticion = route.request();
    const ruta = new URL(peticion.url()).pathname.replace(/^.*\/api\/v1\/evidencias/, "");
    const metodo = peticion.method();
    const cabecerasTenant = peticion.headers()["x-tenant-id"] ?? "org-prueba";
    if (ruta === "/estado") return route.fulfill(json(200, { subida_firmada: true }));
    if (ruta === "/subidas" && metodo === "POST") {
      if (opciones.error === "almacen-no-configurado") {
        return route.fulfill(
          json(503, { detail: "El almacén de documentos no está disponible en este entorno.", code: "EVI_ALMACEN_NO_DISPONIBLE" })
        );
      }
      const clave = `${cabecerasTenant}/${randomBytes(16).toString("hex")}`;
      return route.fulfill(
        json(200, {
          clave,
          url: `https://${HOST_ALMACEN_SIMULADO}/${clave}`,
          metodo: "PUT",
          cabeceras: {
            "x-goog-if-generation-match": "0",
            "Content-Type": (peticion.postDataJSON() as { tipo_mime: string }).tipo_mime,
          },
          caduca_en_segundos: 900,
        })
      );
    }
    if (ruta === "/subidas/confirmar" && metodo === "POST") {
      estado.confirmaciones += 1;
      const cuerpo = peticion.postDataJSON() as {
        clave: string;
        sha256_hash: string;
        nombre_archivo: string;
        tipo_mime: string;
        normativa: string;
      };
      const contenido = objetos.get(cuerpo.clave);
      if (!contenido) return route.fulfill(json(404, { detail: "No hay un archivo subido para esa clave en tu organización." }));
      const huella = createHash("sha256").update(contenido).digest("hex");
      if (opciones.error === "huella-distinta" || huella !== cuerpo.sha256_hash) {
        return route.fulfill(
          json(422, { detail: "La huella que calculó el navegador no coincide con la del archivo guardado.", code: "EVI_HUELLA_NO_COINCIDE" })
        );
      }
      const previo = estado.documentos.find((d) => d.sha256_hash === huella && d.normativa === cuerpo.normativa);
      if (previo) return route.fulfill(json(200, { status: "SUCCESS", duplicada: true, documento: previo }));
      const documento: DocumentoSimulado = {
        id: `doc-${estado.documentos.length + 1}`,
        codigo: `EVD-2026-${String(estado.documentos.length + 1).padStart(4, "0")}`,
        nombre_archivo: cuerpo.nombre_archivo,
        tipo_mime: cuerpo.tipo_mime,
        tamano_bytes: contenido.length,
        sha256_hash: huella,
        normativa: cuerpo.normativa,
        subido_por: "usuario-simulado",
        subido_en: new Date().toISOString(),
        retencion_dias: 1825,
        controles_vinculados: [],
      };
      estado.documentos.push(documento);
      return route.fulfill(json(200, { status: "SUCCESS", duplicada: false, documento }));
    }
    if (ruta === "/documentos" && metodo === "GET") {
      return route.fulfill(json(200, { total: estado.documentos.length, documentos: estado.documentos }));
    }
    const vinculo = /^\/documentos\/([^/]+)\/vinculos\/(\d+)$/.exec(ruta);
    if (vinculo && (metodo === "PUT" || metodo === "DELETE")) {
      const documento = estado.documentos.find((d) => d.id === vinculo[1]);
      if (!documento) return route.fulfill(json(404, { detail: "El documento no existe en tu organización." }));
      const control = Number(vinculo[2]);
      documento.controles_vinculados =
        metodo === "PUT"
          ? [...new Set([...documento.controles_vinculados, control])].sort((a, b) => a - b)
          : documento.controles_vinculados.filter((c) => c !== control);
      return route.fulfill(json(200, { status: "SUCCESS" }));
    }
    return route.fallback();
  });

  return estado;
}
// === fin EVI-01b ===
