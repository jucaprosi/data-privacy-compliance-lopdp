"use client";

// ¤adpa ¤rbac-tenant
// ¤¤frontend-architect
/**
 * Biblioteca: aplicabilidad determinista y plantillas recomendadas (BIB-204).
 *
 * Consume /api/v1/biblioteca/aplicabilidad y /api/v1/biblioteca/recomendados.
 * El tenant y el rol viajan exclusivamente en las cabeceras (`cabecerasDeMiembro`, BIB-115).
 */
import { fetchAutenticado } from "@/lib/auth";
import { cabecerasDeMiembro } from "@/lib/auth/cabeceras";
import { falloDeRol, mensajeDelServidor, rechazoDeIdentidad, ROLES_EDITORES } from "@/lib/biblioteca/http";

export type ResultadoAplicabilidad = "Aplica" | "No aplica" | "Información insuficiente";

export interface ReglaEvaluada {
  regla_id: string;
  nombre: string;
  resultado: ResultadoAplicabilidad;
  explicacion: string;
  fuente_normativa: string;
  version_regla: string;
  hechos_analizados: Record<string, unknown>;
  hechos_faltantes: string[];
}

export interface ModificacionHumana {
  resultado_original: ResultadoAplicabilidad;
  resultado_modificado: "Aplica" | "No aplica";
  motivo: string;
  evidencia: string;
  autor_id: string;
  fecha: string;
  es_obligacion_confirmada: boolean;
  revisor_juridico_id?: string | null;
}

export interface PlantillaAplicable {
  codigo: string;
  nombre: string;
  resultado: ResultadoAplicabilidad;
  resultado_calculado: ResultadoAplicabilidad;
  tipo: string;
  familia: string;
  formato: string;
  naturaleza: string;
  es_obligacion: boolean;
  fuentes_normativas: string[];
  version_regla: string;
  motivo_recomendacion: string;
  hechos_relevantes: Record<string, unknown>;
  hechos_faltantes: string[];
  reglas_evaluadas: ReglaEvaluada[];
  modificacion_humana?: ModificacionHumana | null;
}

export type ResultadoConsultaAplicabilidad =
  | { estado: "listo"; plantillas: PlantillaAplicable[] }
  | { estado: "denegado"; mensaje: string }
  | { estado: "error"; mensaje: string };

export async function consultarAplicabilidad(
  filtroResultado?: ResultadoAplicabilidad,
): Promise<ResultadoConsultaAplicabilidad> {
  const params = filtroResultado ? `?resultado=${encodeURIComponent(filtroResultado)}` : "";
  const ruta = `/api/v1/biblioteca/aplicabilidad${params}`;
  try {
    const resp = await fetchAutenticado(ruta, { cache: "no-store" }, cabecerasDeMiembro());
    const cuerpo = await resp.json().catch(() => null);
    const rechazo = rechazoDeIdentidad(resp.status, cuerpo, "Sin acceso a aplicabilidad de esta organización.");
    if (rechazo) return { estado: "denegado", mensaje: rechazo };
    if (!resp.ok || !Array.isArray(cuerpo)) {
      return { estado: "error", mensaje: "No se pudo consultar la aplicabilidad de plantillas." };
    }
    return { estado: "listo", plantillas: cuerpo };
  } catch (error) {
    const sinRol = falloDeRol(error);
    if (sinRol) return { estado: "denegado", mensaje: sinRol };
    return { estado: "error", mensaje: "Fallo de conexión al consultar aplicabilidad." };
  }
}

export async function consultarRecomendados(): Promise<ResultadoConsultaAplicabilidad> {
  const ruta = "/api/v1/biblioteca/recomendados";
  try {
    const resp = await fetchAutenticado(ruta, { cache: "no-store" }, cabecerasDeMiembro());
    const cuerpo = await resp.json().catch(() => null);
    const rechazo = rechazoDeIdentidad(resp.status, cuerpo, "Sin acceso a plantillas recomendadas.");
    if (rechazo) return { estado: "denegado", mensaje: rechazo };
    if (!resp.ok || !Array.isArray(cuerpo)) {
      return { estado: "error", mensaje: "No se pudieron obtener las plantillas recomendadas." };
    }
    return { estado: "listo", plantillas: cuerpo };
  } catch (error) {
    const sinRol = falloDeRol(error);
    if (sinRol) return { estado: "denegado", mensaje: sinRol };
    return { estado: "error", mensaje: "Fallo de conexión al consultar plantillas recomendadas." };
  }
}

export async function registrarModificacion(
  codigo: string,
  resultadoModificado: "Aplica" | "No aplica",
  motivo: string,
  evidencia: string,
  revisorJuridicoId?: string,
): Promise<{ ok: boolean; modificacion?: ModificacionHumana; error?: string }> {
  const ruta = `/api/v1/biblioteca/aplicabilidad/${encodeURIComponent(codigo)}/modificar`;
  try {
    const resp = await fetchAutenticado(
      ruta,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          resultado_modificado: resultadoModificado,
          motivo,
          evidencia,
          revisor_juridico_id: revisorJuridicoId || null,
        }),
      },
      cabecerasDeMiembro(ROLES_EDITORES),
    );
    const cuerpo = await resp.json().catch(() => null);
    if (!resp.ok) {
      return { ok: false, error: mensajeDelServidor(cuerpo, "Error al guardar corrección.") };
    }
    return { ok: true, modificacion: cuerpo };
  } catch (error) {
    const sinRol = falloDeRol(error);
    if (sinRol) return { ok: false, error: sinRol };
    return { ok: false, error: "Error de conexión al guardar corrección." };
  }
}
