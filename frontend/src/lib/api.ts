/**
 * Cliente API REST para Plataforma LOPDP 360.
 * Conecta con el proxy local /api/v1 y propaga errores legibles al consumidor.
 */
import {
  ActividadRAT,
  ResultadoMTGE,
  DictamenDPO,
  TicketCAPA,
} from "../types";
import { fetchAutenticado } from "./auth";

const API_BASE_URL = "/api/v1";

async function fetchJson<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };

  const res = await fetchAutenticado(`${API_BASE_URL}${endpoint}`, { ...options, headers });
  if (!res.ok) {
    // El servidor explica el motivo en «detail» (p. ej. la violación SoD); si no, se muestra el código.
    const cuerpo = await res.json().catch(() => null);
    const detalle = typeof cuerpo?.detail === "string" ? cuerpo.detail : res.statusText || "Error del servidor";
    throw new Error(`HTTP ${res.status}: ${detalle}`);
  }
  return await res.json();
}

// 1. RAT Maestro
export async function getActividadesRAT(): Promise<ActividadRAT[]> {
  const data = await fetchJson<{ actividades: ActividadRAT[] }>("/rat/actividades");
  return data.actividades;
}

export async function crearActividadRAT(act: ActividadRAT): Promise<ActividadRAT> {
  const data = await fetchJson<{ actividad: ActividadRAT }>("/rat/actividades", {
    method: "POST",
    body: JSON.stringify(act),
  });
  return data.actividad;
}

// 2. Riesgos MTGE (Res. SPDP-SPD-2026-0005-R). Lo calcula el servidor; si falla, el error sube.
export interface EntradaMTGE {
  actividad_rat_id: string;
  titulares_12_meses: number;
  tipos_datos_por_titular: number;
  categorias_datos: "BASICAS" | "UNA_ESPECIAL" | "VARIAS_ESPECIALES_VULNERABLES_O_PENALES";
  frecuencia: "PUNTUAL" | "PERIODICA" | "CONTINUA";
  permanencia: "OCASIONAL" | "TEMPORAL" | "PROLONGADA";
  alcance: "LOCAL" | "NACIONAL" | "GLOBAL_O_TRANSFRONTERIZO";
  supuestos_directos: string[];
}

export async function evaluarMTGE(entrada: EntradaMTGE): Promise<ResultadoMTGE> {
  return fetchJson<ResultadoMTGE>("/riesgos/mtge/evaluar", { method: "POST", body: JSON.stringify(entrada) });
}

// 3. DPO Cockpit
export async function getBitacoraDPO(): Promise<DictamenDPO[]> {
  const data = await fetchJson<{ dictamenes: DictamenDPO[] }>("/dpo/bitacora");
  return data.dictamenes;
}

// 4. Auditoría CAPA
export async function getTicketsCAPA(): Promise<TicketCAPA[]> {
  const data = await fetchJson<{ tickets: TicketCAPA[] }>("/capa/tickets");
  return data.tickets;
}

