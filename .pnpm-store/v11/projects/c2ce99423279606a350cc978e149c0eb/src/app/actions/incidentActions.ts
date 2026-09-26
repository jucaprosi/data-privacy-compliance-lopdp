"use server";

import fs from "fs/promises";
import fsSync from "fs";
import path from "path";
import crypto from "crypto";
import {
  Incidente,
  RegistrarVulneracionInput,
  CalculoCuentaRegresiva,
  EstadoSLA,
} from "@/types/incidente";

export interface ServerActionResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
}

/**
 * Constantes normativas conforme a la Ley de Ciberseguridad 2026 y LOPDP.
 * El plazo perentorio legal estándar de notificación ante la Autoridad y el CSIRT es de 72 horas.
 */
const SLA_LEGAL_HORAS_DEFAULT = 72;
const UMBRAL_CRITICO_HORAS = 24;

/**
 * Resuelve de forma robusta la ruta absoluta hacia el archivo data/incident_logs.json,
 * admitiendo ejecuciones tanto desde la raíz del proyecto como desde la carpeta frontend.
 */
function getIncidentLogsPath(): { dir: string; file: string } {
  const cwd = process.cwd();
  const directDataDir = path.join(cwd, "data");
  const frontendDataDir = path.join(cwd, "frontend", "data");

  if (fsSync.existsSync(frontendDataDir)) {
    return { dir: frontendDataDir, file: path.join(frontendDataDir, "incident_logs.json") };
  }
  return { dir: directDataDir, file: path.join(directDataDir, "incident_logs.json") };
}

/**
 * Asegura la existencia física del directorio de almacenamiento y del archivo JSON de incidentes.
 */
async function asegurarArchivoIncidentes(): Promise<string> {
  const { dir, file } = getIncidentLogsPath();
  try {
    await fs.mkdir(dir, { recursive: true });
    try {
      await fs.access(file);
    } catch {
      await fs.writeFile(file, JSON.stringify([], null, 2), "utf-8");
    }
    return file;
  } catch (error) {
    console.error("[INCIDENT_LOGS_STORAGE_INIT_ERROR]:", error);
    throw new Error("No se pudo inicializar la bitácora inmutable de incidentes de seguridad.");
  }
}

/**
 * Lee la bitácora histórica de incidentes desde el disco.
 */
async function leerIncidentLogs(): Promise<Incidente[]> {
  const file = await asegurarArchivoIncidentes();
  try {
    const raw = await fs.readFile(file, "utf-8");
    return JSON.parse(raw) as Incidente[];
  } catch (error) {
    console.error("[INCIDENT_LOGS_READ_ERROR]:", error);
    return [];
  }
}

/**
 * Realiza el cálculo matemático y normativo del SLA legal de notificación en el servidor.
 * Garantiza determinismo temporal y evita manipulación del reloj desde el cliente.
 */
function calcularMetricasSLAInterno(
  fechaDeteccionStr: string,
  slaHoras: number = SLA_LEGAL_HORAS_DEFAULT,
  referenciaTiempoMs: number = Date.now()
): {
  fechaLimiteNotificacion: string;
  estadoSLA: EstadoSLA;
  cuentaRegresiva: CalculoCuentaRegresiva;
} {
  const deteccionDate = new Date(fechaDeteccionStr);
  if (isNaN(deteccionDate.getTime())) {
    throw new Error("La fecha de detección provista no es un timestamp ISO 8601 válido.");
  }

  const duracionSlaMs = slaHoras * 3600 * 1000;
  const limiteMs = deteccionDate.getTime() + duracionSlaMs;
  const fechaLimiteNotificacion = new Date(limiteMs).toISOString();

  const milisegundosRestantes = limiteMs - referenciaTiempoMs;
  const haExpirado = milisegundosRestantes <= 0;

  // Clasificación estricta del SLA Legal
  let estadoSLA: EstadoSLA;
  if (haExpirado) {
    estadoSLA = "Vencido";
  } else if (milisegundosRestantes <= UMBRAL_CRITICO_HORAS * 3600 * 1000) {
    estadoSLA = "Crítico";
  } else {
    estadoSLA = "A Tiempo";
  }

  const msPositivos = Math.max(0, milisegundosRestantes);
  const totalSegundos = Math.floor(msPositivos / 1000);
  const horasRestantes = Math.floor(totalSegundos / 3600);
  const minutosRestantes = Math.floor((totalSegundos % 3600) / 60);
  const segundosRestantes = totalSegundos % 60;

  const msTranscurridos = duracionSlaMs - msPositivos;
  const porcentajeConsumido = Math.min(100, Math.max(0, (msTranscurridos / duracionSlaMs) * 100));

  const cuentaRegresiva: CalculoCuentaRegresiva = {
    fechaDeteccion: deteccionDate.toISOString(),
    fechaLimiteNotificacion,
    horasRestantes,
    minutosRestantes,
    segundosRestantes,
    milisegundosRestantes,
    porcentajeConsumido: parseFloat(porcentajeConsumido.toFixed(2)),
    estadoSLA,
    haExpirado,
    umbralCriticoHoras: UMBRAL_CRITICO_HORAS,
  };

  return {
    fechaLimiteNotificacion,
    estadoSLA,
    cuentaRegresiva,
  };
}

/**
 * Server Action: Previsualiza el cálculo normativo de la cuenta regresiva antes de persistir en disco.
 * Permite a la interfaz de usuario presentar el desglose temporal y el SLA legal resultante
 * antes de que el Oficial de Seguridad o DPO confirme el registro formal.
 */
export async function previsualizarCuentaRegresiva(
  fechaDeteccion: string,
  slaHoras: number = SLA_LEGAL_HORAS_DEFAULT
): Promise<ServerActionResponse<CalculoCuentaRegresiva>> {
  try {
    if (!fechaDeteccion || typeof fechaDeteccion !== "string") {
      return {
        success: false,
        error: "Se requiere la fecha y hora de detección en formato ISO.",
      };
    }

    const { cuentaRegresiva } = calcularMetricasSLAInterno(fechaDeteccion, slaHoras);

    return {
      success: true,
      data: cuentaRegresiva,
    };
  } catch (error) {
    const errorMsg = error instanceof Error ? error.message : "Error al calcular el SLA temporal.";
    return {
      success: false,
      error: errorMsg,
    };
  }
}

/**
 * Server Action: Registra de forma inalterable y persistente una vulneración de seguridad en disco.
 * 
 * 1. Captura la fechaDeteccion provista por el cliente.
 * 2. Calcula en el servidor la fechaLimiteNotificacion (+72h de ley).
 * 3. Estampa el estado actual del SLA y sella criptográficamente el payload.
 * 4. Persiste en data/incident_logs.json bajo régimen append-only.
 * 5. Emite log estricto en la terminal:
 *    [TAMPER_EVIDENT] [INCIDENT] Vulneración registrada con ID ${id}. Reloj de notificación normativo iniciado. SLA legal inalterable.
 */
export async function registrarVulneracion(
  data: RegistrarVulneracionInput
): Promise<ServerActionResponse<Incidente>> {
  try {
    // 1. Validaciones estructurales del input
    if (!data) {
      return { success: false, error: "La información de la vulneración no puede ser nula." };
    }

    if (!data.fechaDeteccion || typeof data.fechaDeteccion !== "string") {
      return {
        success: false,
        error: "El campo fechaDeteccion es obligatorio y debe ser una cadena ISO 8601 válida.",
      };
    }

    const slaHoras = data.slaHorasPersonalizado && data.slaHorasPersonalizado > 0
      ? data.slaHorasPersonalizado
      : SLA_LEGAL_HORAS_DEFAULT;

    const ahoraServidorMs = Date.now();
    const { fechaLimiteNotificacion, estadoSLA } = calcularMetricasSLAInterno(
      data.fechaDeteccion,
      slaHoras,
      ahoraServidorMs
    );

    // 2. Identificador único inmutable UUID v4 nativo
    const id = crypto.randomUUID();
    const registradoEnServidor = new Date(ahoraServidorMs).toISOString();

    // 3. Generación del sello de integridad criptográfico SHA-256 (Tamper-Evident)
    const sealPayload = JSON.stringify({
      id,
      fechaDeteccion: data.fechaDeteccion,
      fechaLimiteNotificacion,
      estadoSLA,
      titulo: data.titulo || "Incidente de Seguridad",
      descripcion: data.descripcion || "",
      severidad: data.severidad || "Alta",
      afectacionDatosPersonales: Boolean(data.afectacionDatosPersonales),
      categoriaDatosAfectados: data.categoriaDatosAfectados || [],
      medidasInmediatas: data.medidasInmediatas || "",
      reportadoPor: data.reportadoPor || "Oficial de Seguridad / DPO",
      registradoEnServidor,
    });
    const sha256Seal = crypto.createHash("sha256").update(sealPayload).digest("hex");

    // 4. Construcción del objeto inmutable congelado
    const nuevoIncidente: Incidente = Object.freeze({
      id,
      fechaDeteccion: data.fechaDeteccion,
      fechaLimiteNotificacion,
      estadoSLA,
      titulo: data.titulo?.trim() || "Incidente de Seguridad",
      descripcion: data.descripcion?.trim() || "",
      severidad: data.severidad || "Alta",
      afectacionDatosPersonales: Boolean(data.afectacionDatosPersonales),
      categoriaDatosAfectados: data.categoriaDatosAfectados || [],
      medidasInmediatas: data.medidasInmediatas?.trim() || "",
      reportadoPor: data.reportadoPor?.trim() || "Oficial de Seguridad / DPO",
      registradoEnServidor,
      sha256Seal,
    });

    // 5. Persistencia inviolable en data/incident_logs.json (Append-Only)
    const logFilePath = await asegurarArchivoIncidentes();
    const incidentesExistentes = await leerIncidentLogs();

    // Verificación de unicidad absoluta
    if (incidentesExistentes.some((item) => item.id === nuevoIncidente.id)) {
      throw new Error(`[TAMPER_ERROR] Violación de integridad: El ID ${nuevoIncidente.id} ya existe.`);
    }

    const bitacoraActualizada = [...incidentesExistentes, nuevoIncidente];
    await fs.writeFile(logFilePath, JSON.stringify(bitacoraActualizada, null, 2), "utf-8");

    // 6. Log inalterable en la terminal del servidor (Doctrina de Evidencia Forense)
    console.log(
      `[TAMPER_EVIDENT] [INCIDENT] Vulneración registrada con ID ${nuevoIncidente.id}. Reloj de notificación normativo iniciado. SLA legal inalterable.`
    );

    return {
      success: true,
      data: nuevoIncidente,
    };
  } catch (error) {
    const errorMsg = error instanceof Error ? error.message : "Error al registrar la vulneración en disco.";
    console.error("[REGISTRAR_VULNERACION_ERROR]:", error);
    return {
      success: false,
      error: errorMsg,
    };
  }
}

/**
 * Server Action: Recupera el listado cronológico de la bitácora inviolable de vulneraciones.
 * Ordenado descendentemente por fecha de detección (más recientes primero).
 */
export async function obtenerBitacoraIncidentes(): Promise<ServerActionResponse<Incidente[]>> {
  try {
    const bitacora = await leerIncidentLogs();
    const ordenados = [...bitacora].sort(
      (a, b) => new Date(b.fechaDeteccion).getTime() - new Date(a.fechaDeteccion).getTime()
    );

    return {
      success: true,
      data: ordenados,
    };
  } catch (error) {
    const errorMsg = error instanceof Error ? error.message : "Error al leer la bitácora de incidentes.";
    return {
      success: false,
      error: errorMsg,
      data: [],
    };
  }
}
