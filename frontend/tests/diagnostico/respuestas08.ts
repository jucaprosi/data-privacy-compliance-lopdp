/**
 * API de respuestas de DIAG-08 simulada: recibe `nivel_asignado` y devuelve `estado` derivado.
 *
 * La comparten `escala.spec.ts` y `escala-activa.spec.ts` (FE-26). Este archivo no declara pruebas.
 */
import type { BrowserContext } from "@playwright/test";

import { estadoDerivado } from "../../src/lib/diagnostico/escala";

export interface FilaNueva {
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
export async function simularRespuestasDiagnostico08(context: BrowserContext, inicial: FilaNueva[] = []) {
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
