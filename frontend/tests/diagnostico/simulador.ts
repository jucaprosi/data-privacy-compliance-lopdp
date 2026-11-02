/**
 * API simulada del diagnóstico (DIAG-01 y DIAG-03), compartida por todas las pestañas del contexto.
 *
 * - /organizacion/me/roles devuelve los roles indicados: solo el DPO responde y sella.
 * - /diagnostico/respuestas guarda en memoria lo que se envía.
 * - /diagnostico/resultados sella lo que hay en memoria (como el servidor: el cuerpo solo trae el
 *   perfil) y devuelve el historial del más reciente al más antiguo.
 */
import { expect, type BrowserContext, type Page } from "@playwright/test";
import { estadoDerivado } from "../../src/lib/diagnostico/escala";
import { irASala } from "../utiles";

export interface FilaRespuesta {
  pregunta_id: number;
  control: string;
  dimension: string;
  /** Entrada (DIAG-08): nivel asignado SMARTCIDI 1 a 5. */
  nivel_asignado: number | null;
  /** Dato derivado: lo pone el servidor simulado, como el real (DIAG-08 R3). */
  estado?: string;
  nivel_evidencia: number;
  criticidad: number;
  es_critica: boolean;
  riesgo_base: number;
}

interface Sellado {
  id: string;
  secuencia: number;
  sellado_en: string;
  normativa: string;
  version_normativa: string;
  tamano: string;
  perfil: Record<string, string | null>;
  sellado_por: string;
  respuestas: unknown[];
  indicadores: Record<string, unknown>;
  huella_anterior: string;
  huella: string;
}

export async function simularApiDiagnostico(
  context: BrowserContext,
  { roles, dpoVigente = true, filas = [] }: { roles: string[]; dpoVigente?: boolean; filas?: FilaRespuesta[] }
) {
  const servidor = {
    filas: [...filas],
    envios: [] as FilaRespuesta[][],
    cuerposSellado: [] as unknown[],
    sellados: [] as Sellado[],
  };

  await context.route("**/api/v1/organizacion/me/roles", (route) =>
    route.fulfill({ json: { user_id: "usuario-prueba", tenant_id: "tenant-corp-demo", roles: roles.map((role) => ({ role })) } })
  );

  await context.route("**/api/v1/diagnostico/respuestas", async (route) => {
    if (route.request().method() === "PUT") {
      const { respuestas } = route.request().postDataJSON() as { respuestas: FilaRespuesta[] };
      servidor.envios.push(respuestas);
      for (const r of respuestas) {
        const fila = { ...r, estado: estadoDerivado(r.nivel_asignado) };
        servidor.filas = [...servidor.filas.filter((f) => f.pregunta_id !== r.pregunta_id), fila];
      }
    }
    await route.fulfill({ json: { respuestas: servidor.filas } });
  });

  await context.route("**/api/v1/diagnostico/resultados", async (route) => {
    if (route.request().method() === "POST") {
      const cuerpo = route.request().postDataJSON() as { perfil: Record<string, string | null> };
      servidor.cuerposSellado.push(cuerpo);
      const secuencia = servidor.sellados.length + 1;
      const sellado: Sellado = {
        id: `resultado-${secuencia}`,
        secuencia,
        sellado_en: "2026-10-28T10:00:00+00:00",
        normativa: "LOPDP",
        version_normativa: "LOPDP-EC-2026.v1",
        tamano: "mediana",
        perfil: cuerpo.perfil,
        sellado_por: "usuario-prueba",
        respuestas: servidor.filas.map((f) => ({
          pregunta_id: f.pregunta_id,
          control: f.control,
          dimension: f.dimension,
          estado: f.estado,
          criticidad: f.criticidad,
          nivel_declarado: f.nivel_evidencia,
          nivel_sellado: 0,
          con_documento: false,
        })),
        indicadores: {
          escala: "smartcidi_1_5",
          cumplimiento: false,
          brechas_criticas: 65,
          brechas_altas: 2,
          por_dimension: [],
          respaldo_documental: 0,
          preguntas_evaluadas: servidor.filas.length,
          preguntas_aplicables: 73,
          cobertura: 1.4,
        },
        huella_anterior: servidor.sellados.at(-1)?.huella ?? "0".repeat(64),
        huella: String(secuencia).repeat(64).slice(0, 64),
      };
      servidor.sellados.push(sellado);
      await route.fulfill({ status: 201, json: sellado });
      return;
    }
    await route.fulfill({
      json: {
        resultados: [...servidor.sellados].reverse(),
        cadena_integra: true,
        primer_alterado: null,
        dpo_vigente: dpoVigente,
      },
    });
  });

  return servidor;
}

export function filaDePrueba(pregunta_id = 1, nivel_asignado = 3): FilaRespuesta {
  return {
    pregunta_id,
    control: "Control de prueba",
    dimension: "D01",
    nivel_asignado,
    estado: estadoDerivado(nivel_asignado),
    nivel_evidencia: 2,
    criticidad: 3,
    es_critica: false,
    riesgo_base: 5,
  };
}

/**
 * Abre otra pestaña del mismo navegador con el reloj del diagnóstico agotado, para llegar a la
 * pantalla de cierre sin recorrer las preguntas. La ficha y lo respondido siguen en el navegador.
 *
 * La pestaña anterior se cierra antes: su reloj guarda el estado cada segundo y pisaría el reloj
 * agotado de la nueva.
 */
export async function abrirCierreDelDiagnostico(context: BrowserContext, anterior: Page): Promise<Page> {
  await anterior.close();
  const pestana = await context.newPage();
  await pestana.addInitScript(() => {
    const clave = "jubys-audit-storage";
    const datos = JSON.parse(window.localStorage.getItem(clave) ?? "{}");
    if (datos.state) {
      datos.state.timeboxRestante = 0;
      window.localStorage.setItem(clave, JSON.stringify(datos));
    }
  });
  await pestana.goto("/");
  // Antes de hidratarse, el cuestionario abre el aviso de la dimensión; al leer el reloj agotado
  // pasa al cierre y lo cierra solo (AlertaDimension con activo=false).
  await expect(pestana.locator("dialog[open]")).toHaveCount(0);
  await irASala(pestana, /Normativa/);
  await expect(pestana.getByText("Resultado del diagnóstico", { exact: true })).toBeVisible();
  return pestana;
}
