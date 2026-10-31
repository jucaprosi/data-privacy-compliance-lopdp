/**
 * DIAG-09: la escala SMARTCIDI en la pantalla, con la API de DIAG-08 simulada.
 *
 * - Cinco niveles con su criterio y cinco escalones de evidencia; el estado no se envía.
 * - El estado sale del servidor como dato derivado.
 * - Ninguna cifra global en el panel ejecutivo; niveles por dimensión.
 * - Un resultado sellado con la escala anterior se muestra con el aviso, sin niveles.
 * - Una pregunta sin nivel asignado (migrada) queda sin selección y cuenta como pendiente.
 *
 * Mutación documentada: si el control vuelve a tres botones (Implementado, Parcial, No Implementado),
 * «cinco niveles» falla porque el grupo «Nivel de madurez» deja de tener cinco opciones.
 */
import { expect, test, type BrowserContext } from "@playwright/test";

import { AVISO_ESCALA_ANTERIOR } from "../../src/lib/diagnostico/indicadores";
import { ESCALONES_EVIDENCIA, NIVELES_ASIGNADOS, estadoDerivado } from "../../src/lib/diagnostico/escala";
import { BANCO_PREGUNTAS } from "../../src/lib/bancoPreguntas";
import { abrirAppLimpia, configurarProyecto, irASala, panelAssessment, responderControlActual } from "../utiles";
import { simularApiDiagnostico } from "./simulador";

interface FilaNueva {
  pregunta_id: number;
  control: string;
  dimension: string;
  nivel_asignado: number | null;
  estado?: string;
  nivel_evidencia: number;
  criticidad: number;
  es_critica: boolean;
  riesgo_base: number;
}

/** Sustituye las rutas de respuestas por las de DIAG-08: recibe `nivel_asignado` y devuelve `estado`. */
async function simularRespuestasDiagnostico08(context: BrowserContext, inicial: FilaNueva[] = []) {
  const servidor = { filas: [...inicial], envios: [] as Record<string, unknown>[][] };
  await context.route("**/api/v1/diagnostico/respuestas", async (route) => {
    if (route.request().method() === "PUT") {
      const { respuestas } = route.request().postDataJSON() as { respuestas: FilaNueva[] };
      servidor.envios.push(respuestas as unknown as Record<string, unknown>[]);
      for (const r of respuestas) {
        const fila = { ...r, estado: estadoDerivado(r.nivel_asignado) };
        servidor.filas = [...servidor.filas.filter((f) => f.pregunta_id !== r.pregunta_id), fila];
      }
    }
    await route.fulfill({ json: { respuestas: servidor.filas } });
  });
  return servidor;
}

const dimension = (id: string, nivel: number, etiqueta: string) => ({
  dimension: id,
  nombre: `Dimensión ${id}`,
  nivel,
  etiqueta,
  score: nivel * 18,
  cobertura: 100,
  brechas_criticas: 0,
  brechas_altas: 0,
});

async function simularHistorial(context: BrowserContext, indicadores: Record<string, unknown>) {
  await context.route("**/api/v1/diagnostico/resultados", (route) =>
    route.request().method() === "POST"
      ? route.fulfill({ status: 403, json: { detail: "no aplica" } })
      : route.fulfill({
          json: {
            resultados: [
              {
                id: "resultado-1",
                secuencia: 1,
                sellado_en: "2026-10-31T10:00:00+00:00",
                normativa: "LOPDP",
                version_normativa: "LOPDP-EC-2026.v1",
                tamano: "mediana",
                perfil: {},
                sellado_por: "usuario-prueba",
                respuestas: [],
                indicadores,
                huella_anterior: "0".repeat(64),
                huella: "1".repeat(64),
              },
            ],
            cadena_integra: true,
            primer_alterado: null,
            dpo_vigente: true,
          },
        })
  );
}

test.describe("Escala SMARTCIDI en la pantalla (DIAG-09)", () => {
  test("cinco niveles: criterio visible, cinco escalones de evidencia y nada de estado en el envío", async ({ page, context }) => {
    await simularApiDiagnostico(context, { roles: ["dpo"] });
    const servidor = await simularRespuestasDiagnostico08(context);
    await abrirAppLimpia(page);
    await configurarProyecto(page);
    await irASala(page, /Normativa/);

    const niveles = page.getByRole("radiogroup", { name: /Nivel de madurez/ });
    await expect(niveles.getByRole("radio")).toHaveCount(5);
    for (const n of NIVELES_ASIGNADOS) {
      await expect(niveles.getByRole("radio", { name: new RegExp(`^${n.nivel}\\s+${n.corto}$`) })).toBeVisible();
    }
    const evidencia = page.getByRole("radiogroup", { name: /Evidencia/ });
    await expect(evidencia.getByRole("radio")).toHaveCount(ESCALONES_EVIDENCIA.length);
    // Los tres botones de la escala anterior ya no existen.
    for (const antiguo of ["Implementado", "No Implementado"]) {
      await expect(page.getByRole("button", { name: antiguo, exact: true })).toHaveCount(0);
    }

    // El criterio del nivel enfocado se ve antes de elegirlo.
    await niveles.getByRole("radio", { name: /^4\s/ }).focus();
    await expect(page.getByTestId("criterio-nivel")).toContainText(NIVELES_ASIGNADOS[3].criterio);

    await responderControlActual(page, 2);
    await expect(page.getByTestId("criterio-nivel")).toContainText(NIVELES_ASIGNADOS[1].criterio);
    await expect.poll(() => servidor.envios.length).toBeGreaterThan(0);
    const enviada = servidor.envios.at(-1)![0];
    expect(enviada.nivel_asignado).toBe(2);
    expect(enviada).not.toHaveProperty("estado");
  });

  test("estado derivado: lo muestra el servidor como dato, no como botón", async ({ page, context }) => {
    await simularApiDiagnostico(context, { roles: ["dpo"] });
    await simularRespuestasDiagnostico08(context);
    await abrirAppLimpia(page);
    await configurarProyecto(page);
    await irASala(page, /Normativa/);

    await responderControlActual(page, 3);
    await expect(page.getByTestId("estado-derivado")).toHaveText("Parcial");
    await expect(page.getByRole("button", { name: "Parcial", exact: true })).toHaveCount(0);
    await expect(page.getByRole("radio", { name: "Parcial" })).toHaveCount(0);
  });

  test("sin cifra global: el panel ejecutivo muestra un nivel por dimensión", async ({ page, context }) => {
    await simularApiDiagnostico(context, { roles: ["dpo"] });
    await simularRespuestasDiagnostico08(context);
    await abrirAppLimpia(page);
    await configurarProyecto(page);
    await irASala(page, /Normativa/);
    await responderControlActual(page, 4);
    await irASala(page, /Dashboard Central/);

    const panel = panelAssessment(page);
    const filas = panel.getByRole("table", { name: "Nivel de madurez de cada dimensión" }).locator("tbody tr");
    await expect(filas).toHaveCount(10);
    await expect(panel.getByText("Sin evaluación suficiente").first()).toBeVisible();
    const texto = await panel.innerText();
    expect(texto).not.toContain("Puntaje según respuestas");
    expect(texto).not.toContain("Puntaje con evidencia vinculada");
    expect(texto).not.toMatch(/Nivel ajustado/i);
    expect(texto).not.toMatch(/Estado declarado|Score ponderado/i);
    // El único porcentaje que aparece es la cobertura de controles, que no es un nivel ni un puntaje.
    const porcentajes = new Set((texto.match(/\d+(\.\d+)? ?%/g) ?? []).map((p) => p.replace(" ", "")));
    expect(porcentajes.size).toBe(1);
  });

  test("sin cifra global: el historial muestra niveles por dimensión y ningún valor de la organización", async ({ page, context }) => {
    await simularApiDiagnostico(context, { roles: ["dpo"] });
    await simularHistorial(context, {
      escala: "smartcidi_1_5",
      cumplimiento: true,
      brechas_criticas: 0,
      brechas_altas: 1,
      por_dimension: [dimension("D01", 3, "Definido / Documentado"), dimension("D02", 0, "Sin evaluación suficiente")],
      respaldo_documental: 50,
      preguntas_evaluadas: 10,
      preguntas_aplicables: 70,
      cobertura: 14.3,
    });
    await abrirAppLimpia(page);
    await configurarProyecto(page);
    await irASala(page, /Auditorías/);

    const lista = page.getByRole("list", { name: "Nivel por dimensión" });
    await expect(lista.getByRole("listitem")).toHaveCount(2);
    await expect(lista).toContainText("Nivel 3 · Definido / Documentado");
    await expect(lista).toContainText("Sin evaluación suficiente");
    await expect(page.getByText(/Madurez|Riesgo que queda/)).toHaveCount(0);
  });

  test("escala anterior: aviso del contrato y ningún nivel", async ({ page, context }) => {
    await simularApiDiagnostico(context, { roles: ["dpo"] });
    await simularHistorial(context, {
      escala: "anterior",
      cumplimiento: false,
      brechas_criticas: 3,
      respaldo_documental: 10,
      preguntas_evaluadas: 10,
      preguntas_aplicables: 70,
      cobertura: 14.3,
      madurez: 40,
      nivel_madurez: 2,
    });
    await abrirAppLimpia(page);
    await configurarProyecto(page);
    await irASala(page, /Auditorías/);

    await expect(page.getByText(AVISO_ESCALA_ANTERIOR)).toBeVisible();
    await expect(page.getByRole("list", { name: "Nivel por dimensión" })).toHaveCount(0);
    await expect(page.getByText(/Nivel \d/)).toHaveCount(0);
  });

  test("pendientes por migración: sin nivel seleccionado y cuentan como pendientes", async ({ page, context }) => {
    const fila = (id: number, nivel: number | null): FilaNueva => ({
      pregunta_id: id,
      control: `Control ${id}`,
      dimension: "D01",
      nivel_asignado: nivel,
      estado: nivel === null ? "Pendiente" : estadoDerivado(nivel),
      nivel_evidencia: 2,
      criticidad: 3,
      es_critica: false,
      riesgo_base: 5,
    });
    await simularApiDiagnostico(context, { roles: ["dpo"] });
    await simularRespuestasDiagnostico08(context, [fila(BANCO_PREGUNTAS[0].id, null), fila(BANCO_PREGUNTAS[1].id, 3)]);
    await abrirAppLimpia(page);
    await configurarProyecto(page);
    // Pestaña nueva del mismo navegador: conserva la ficha y, al hidratarse, lee lo guardado en el servidor.
    const otra = await context.newPage();
    await otra.goto("/");
    await otra.getByRole("button", { name: "Cerrar alerta" }).click();
    await irASala(otra, /Normativa/);

    const niveles = otra.getByRole("radiogroup", { name: /Nivel de madurez/ });
    await expect(niveles.getByRole("radio", { checked: true })).toHaveCount(0);
    await expect(otra.getByTestId("estado-derivado")).toHaveText("Pendiente");

    await irASala(otra, /Dashboard Central/);
    // Dos filas guardadas, solo una con nivel: el avance cuenta 1, no 2.
    await expect(panelAssessment(otra).getByText(/^1 de \d+ controles aplicables$/)).toBeVisible();
  });

  test("propuesta de la IA: el nivel queda sin elegir y el rango del estado queda marcado", async ({ page, context }) => {
    await simularApiDiagnostico(context, { roles: ["dpo"] });
    await simularRespuestasDiagnostico08(context);
    await page.route("**/api/v1/preanalisis/**", async (route) => {
      const ruta = new URL(route.request().url()).pathname;
      if (ruta.endsWith("/preanalisis/estado")) {
        await route.fulfill({ json: { disponible: true, proveedor: "simulado", modelo: "qa-09", motivo: null } });
      } else if (ruta.endsWith("/preanalisis/preparar")) {
        await route.fulfill({
          json: {
            formato: "pdf",
            caracteres_totales: 49,
            fragmentos: [{ texto: "politica de privacidad y tratamiento", origen: "p. 1", relevancia: 1 }],
            pii_enmascarada: 0,
            advertencias: [],
          },
        });
      } else if (ruta.endsWith("/preanalisis/analizar")) {
        await route.fulfill({
          json: {
            estado: "Parcial",
            nivel_evidencia_maximo: 1,
            citas: [{ fragmento: "politica de privacidad y tratamiento", motivo: "Sustento simulado" }],
            citas_descartadas: 0,
            razonamiento: "La evidencia simulada sustenta el control en parte.",
            limitaciones: [],
            modelo: "qa-09",
          },
        });
      } else {
        await route.fallback();
      }
    });
    await abrirAppLimpia(page);
    await configurarProyecto(page);
    await expect(page.getByRole("heading", { name: "Normativa", exact: true })).toBeVisible();
    await page.locator('input[type="file"]').first().setInputFiles({
      name: "politica-privacidad.pdf",
      mimeType: "application/pdf",
      buffer: Buffer.from("%PDF-1.4 politica de privacidad y tratamiento"),
    });
    await page.locator("select").nth(1).selectOption("1");
    await page.getByRole("button", { name: "Analizar con IA" }).first().click();
    await page
      .getByRole("dialog", { name: "Confirmar envío al modelo de IA" })
      .getByRole("button", { name: "Enviar y analizar" })
      .click();
    await expect(page.getByText("Propuesta de la IA", { exact: true })).toBeVisible();
    await page.getByRole("button", { name: "Aceptar propuesta" }).click();

    const niveles = page.getByRole("radiogroup", { name: /Nivel de madurez/ });
    // Parcial = niveles 2 y 3: ninguno elegido, los dos marcados y los demás sin marca.
    await expect(niveles.getByRole("radio", { checked: true })).toHaveCount(0);
    await expect(niveles.locator("[data-sugerido]")).toHaveCount(2);
    await expect(niveles.locator('[data-nivel="2"]')).toHaveAttribute("data-sugerido", "true");
    await expect(niveles.locator('[data-nivel="3"]')).toHaveAttribute("data-sugerido", "true");
    await expect(page.getByTestId("rango-sugerido")).toContainText("entre 2 y 3");
    await expect(page.getByTestId("estado-derivado")).toHaveText("Pendiente");

    await responderControlActual(page, 3);
    await expect(niveles.locator('[data-nivel="3"]')).toHaveAttribute("aria-checked", "true");
  });
});
