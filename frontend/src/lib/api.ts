/**
 * Cliente API REST para Plataforma LOPDP 360.
 * Conecta con el proxy local /api/v1 y propaga errores legibles al consumidor.
 */
import {
  FichaOrganizacion,
  PreguntaDiagnostico,
  RespuestaDiagnosticoItem,
  ScoringDiagnostico,
  ActividadRAT,
  ResultadoMTGE,
  DictamenDPO,
  TicketCAPA,
  EvidenciaRegistro,
  RespuestaRAG,
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
    throw new Error(`HTTP ${res.status}: ${res.statusText || "Error del servidor"}`);
  }
  return await res.json();
}

// 1. Diagnóstico
export async function getPreguntasDiagnostico(ficha: FichaOrganizacion): Promise<{ total_preguntas: number; preguntas: PreguntaDiagnostico[] }> {
  return fetchJson<{ total_preguntas: number; preguntas: PreguntaDiagnostico[] }>("/diagnostico/preguntas", {
      method: "POST",
      body: JSON.stringify(ficha),
    });
}

export async function evaluarDiagnostico(respuestas: RespuestaDiagnosticoItem[]): Promise<{ scoring: ScoringDiagnostico }> {
  return fetchJson<{ scoring: ScoringDiagnostico }>("/diagnostico/evaluar", {
      method: "POST",
      body: JSON.stringify({ respuestas }),
    });
}

export async function getInformeMarkdown(ficha: FichaOrganizacion, respuestas: RespuestaDiagnosticoItem[]): Promise<string> {
  const data = await fetchJson<{ informe_markdown: string }>("/diagnostico/informe/markdown", {
      method: "POST",
      body: JSON.stringify({ ficha, respuestas }),
    });
  return data.informe_markdown;
}

// 2. RAT Maestro
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

// 3. Riesgos MTGE (Res. SPDP-SPD-2026-0005-R). Lo calcula el servidor; si falla, el error sube.
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

// 4. DPO Cockpit
export async function getBitacoraDPO(): Promise<DictamenDPO[]> {
  const data = await fetchJson<{ dictamenes: DictamenDPO[] }>("/dpo/bitacora");
  return data.dictamenes;
}

// 5. Auditoría CAPA
export async function getTicketsCAPA(): Promise<TicketCAPA[]> {
  const data = await fetchJson<{ tickets: TicketCAPA[] }>("/capa/tickets");
  return data.tickets;
}

// 6. Evidencias
export async function getEvidencias(): Promise<EvidenciaRegistro[]> {
  const data = await fetchJson<{ evidencias: EvidenciaRegistro[] }>("/evidencias");
  return data.evidencias;
}

// 7. Copiloto RAG Legal
export async function consultarCopilotoRAG(pregunta: string): Promise<RespuestaRAG> {
  return fetchJson<RespuestaRAG>("/rag/consulta", {
      method: "POST",
      body: JSON.stringify({ pregunta }),
    });
}

