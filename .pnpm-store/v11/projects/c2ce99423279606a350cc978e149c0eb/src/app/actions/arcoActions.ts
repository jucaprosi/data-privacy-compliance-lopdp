"use server";

/**
 * ¤arco-server-actions
 * Server Actions para la Gestion de Derechos ARCO+
 * Normativa: LOPDP Arts. 21-24, 37 | Res. SPDP-SPD-2026-0005-R | Doctrina 3
 * Invariante: INV_ARCO_EVIDENCIA_E1 (resolucion bloqueada sin expediente probatorio)
 */

import fs from "fs/promises";
import fsSync from "fs";
import path from "path";
import { randomUUID } from "crypto";
import type {
  SolicitudARCO,
  CrearSolicitudArcoInput,
} from "@/types/arco";
import type { ServerActionResponse } from "@/types/rat";

// ---------------------------------------------------------------------------
// Constantes normativas (Art. 37 LOPDP: 15 dias laborables)
// ---------------------------------------------------------------------------
const SLA_DIAS_LABORABLES = 15;

// ---------------------------------------------------------------------------
// Utilidades de almacenamiento
// ---------------------------------------------------------------------------

/**
 * Resuelve la ruta del archivo arco_tickets.json de forma robusta,
 * admitiendo ejecucion desde la raiz del monorepo o desde /frontend.
 */
function getArcoTicketsPath(): { dir: string; file: string } {
  const cwd = process.cwd();
  const frontendDataDir = path.join(cwd, "frontend", "data");
  const directDataDir = path.join(cwd, "data");

  if (fsSync.existsSync(frontendDataDir)) {
    return {
      dir: frontendDataDir,
      file: path.join(frontendDataDir, "arco_tickets.json"),
    };
  }
  return {
    dir: directDataDir,
    file: path.join(directDataDir, "arco_tickets.json"),
  };
}

async function asegurarArchivoArco(): Promise<string> {
  const { dir, file } = getArcoTicketsPath();
  await fs.mkdir(dir, { recursive: true });
  try {
    await fs.access(file);
  } catch {
    await fs.writeFile(file, JSON.stringify([], null, 2), "utf-8");
  }
  return file;
}

async function leerTickets(): Promise<SolicitudARCO[]> {
  const file = await asegurarArchivoArco();
  try {
    const raw = await fs.readFile(file, "utf-8");
    return JSON.parse(raw) as SolicitudARCO[];
  } catch {
    return [];
  }
}

async function guardarTickets(tickets: SolicitudARCO[]): Promise<void> {
  const file = await asegurarArchivoArco();
  await fs.writeFile(file, JSON.stringify(tickets, null, 2), "utf-8");
}

// ---------------------------------------------------------------------------
// Motor de calculo SLA (dias laborables -> fecha ISO 8601)
// Art. 37 LOPDP: la empresa responsable dispone de 15 dias laborables
// ---------------------------------------------------------------------------
function calcularFechaLimiteSLA(
  fechaBase: Date,
  diasLaborables: number
): string {
  let conteo = 0;
  const cursor = new Date(fechaBase);
  cursor.setHours(23, 59, 59, 999); // Fin del dia de recepcion

  while (conteo < diasLaborables) {
    cursor.setDate(cursor.getDate() + 1);
    const diaSemana = cursor.getDay();
    // 0 = Domingo, 6 = Sabado — excluidos del computo laboral
    if (diaSemana !== 0 && diaSemana !== 6) {
      conteo++;
    }
  }
  return cursor.toISOString();
}

// ---------------------------------------------------------------------------
// Server Action 1: crearSolicitudArco
// ---------------------------------------------------------------------------

/**
 * Registra la solicitud del titular, calcula la fechaLimiteSLA en el servidor
 * y persiste el ticket de forma inmutable en data/arco_tickets.json.
 *
 * @param data - Payload tipado CrearSolicitudArcoInput
 * @returns ServerActionResponse<SolicitudARCO>
 */
export async function crearSolicitudArco(
  data: CrearSolicitudArcoInput
): Promise<ServerActionResponse<SolicitudARCO>> {
  try {
    if (!data.tipoDerecho) {
      return { success: false, error: "El tipo de derecho es obligatorio." };
    }

    const tiposValidos = [
      "Acceso",
      "Rectificacion",
      "Cancelacion",
      "Oposicion",
      "Portabilidad",
      "Eliminacion",
    ];
    if (!tiposValidos.includes(data.tipoDerecho)) {
      return {
        success: false,
        error: `Tipo de derecho invalido: '${data.tipoDerecho}'. Valores permitidos: ${tiposValidos.join(", ")}.`,
      };
    }

    const ahora = data.fechaSolicitud
      ? new Date(data.fechaSolicitud)
      : new Date();

    const nuevoTicket: SolicitudARCO = {
      id: randomUUID(),
      tipoDerecho: data.tipoDerecho,
      fechaSolicitud: ahora.toISOString(),
      // INVARIANTE: SLA calculado exclusivamente en el servidor (Art. 37 LOPDP)
      fechaLimiteSLA: calcularFechaLimiteSLA(ahora, SLA_DIAS_LABORABLES),
      estado: "Recibido",
      evidenciaRespuesta: null,
      titularNombre: data.titularNombre ?? undefined,
      titularIdentificacion: data.titularIdentificacion ?? undefined,
      titularEmail: data.titularEmail ?? undefined,
      detalleSolicitud: data.detalleSolicitud ?? undefined,
      canalRecepcion: data.canalRecepcion ?? "Web",
      fechaResolucion: null,
    };

    const tickets = await leerTickets();
    tickets.push(nuevoTicket);
    await guardarTickets(tickets);

    console.log(
      `[ARCO+] Solicitud registrada | id=${nuevoTicket.id} | tipo=${nuevoTicket.tipoDerecho} | SLA=${nuevoTicket.fechaLimiteSLA}`
    );

    return { success: true, data: nuevoTicket };
  } catch (err) {
    const mensaje = err instanceof Error ? err.message : String(err);
    console.error("[ARCO+][ERROR] crearSolicitudArco:", mensaje);
    return {
      success: false,
      error: `Error interno al registrar la solicitud: ${mensaje}`,
    };
  }
}

// ---------------------------------------------------------------------------
// Server Action 2: resolverSolicitudArco
// ---------------------------------------------------------------------------

/**
 * Cambia el estado del ticket a "Resuelto" y vincula de forma obligatoria
 * el soporte documental del expediente de respuesta (Doctrina 3 - E1+).
 *
 * BLOQUEO NORMATIVO: Si evidenciaUrl esta vacia o es nula, la accion aborta
 * con error explicito (Invariante INV_ARCO_EVIDENCIA_E1).
 *
 * @param id          - UUID del ticket ARCO+
 * @param evidenciaUrl - URL o path del expediente probatorio de respuesta
 * @param observaciones - Anotaciones opcionales del responsable
 * @returns ServerActionResponse<SolicitudARCO>
 */
export async function resolverSolicitudArco(
  id: string,
  evidenciaUrl: string,
  observaciones?: string
): Promise<ServerActionResponse<SolicitudARCO>> {
  try {
    // --- INVARIANTE INV_ARCO_EVIDENCIA_E1 ---
    if (!evidenciaUrl || evidenciaUrl.trim() === "") {
      return {
        success: false,
        error:
          "BLOQUEO NORMATIVO (Doctrina 3 - INV_ARCO_EVIDENCIA_E1): La resolucion de una solicitud ARCO+ requiere un expediente probatorio de respuesta (E1+). Provea el enlace o path del soporte documental.",
      };
    }

    if (!id || id.trim() === "") {
      return { success: false, error: "El identificador del ticket es obligatorio." };
    }

    const tickets = await leerTickets();
    const indice = tickets.findIndex((t) => t.id === id);

    if (indice === -1) {
      return {
        success: false,
        error: `Ticket ARCO+ no encontrado con id: ${id}.`,
      };
    }

    const ticket = tickets[indice];

    if (ticket.estado === "Resuelto") {
      return {
        success: false,
        error: `El ticket ${id} ya fue resuelto el ${ticket.fechaResolucion}. No es posible sobreescribir un expediente cerrado.`,
      };
    }

    const ahora = new Date();
    const ticketActualizado: SolicitudARCO = {
      ...ticket,
      estado: "Resuelto",
      evidenciaRespuesta: evidenciaUrl.trim(),
      fechaResolucion: ahora.toISOString(),
      observaciones: observaciones?.trim() ?? ticket.observaciones,
    };

    tickets[indice] = ticketActualizado;
    await guardarTickets(tickets);

    console.log(
      `[ARCO+] Solicitud resuelta | id=${id} | evidencia=${evidenciaUrl} | fecha=${ahora.toISOString()}`
    );

    return { success: true, data: ticketActualizado };
  } catch (err) {
    const mensaje = err instanceof Error ? err.message : String(err);
    console.error("[ARCO+][ERROR] resolverSolicitudArco:", mensaje);
    return {
      success: false,
      error: `Error interno al resolver la solicitud: ${mensaje}`,
    };
  }
}

// ---------------------------------------------------------------------------
// Server Action 3: listarSolicitudesArco
// ---------------------------------------------------------------------------

/**
 * Devuelve todos los tickets ARCO+ almacenados en el tenant actual.
 * Calcula automaticamente si el estado debe migrarse a "Excedido"
 * comparando la fecha actual contra la fechaLimiteSLA.
 *
 * @returns ServerActionResponse<SolicitudARCO[]>
 */
export async function listarSolicitudesArco(): Promise<
  ServerActionResponse<SolicitudARCO[]>
> {
  try {
    const tickets = await leerTickets();
    const ahora = new Date();
    let mutado = false;

    const actualizados = tickets.map((t) => {
      if (
        t.estado !== "Resuelto" &&
        t.estado !== "Excedido" &&
        new Date(t.fechaLimiteSLA) < ahora
      ) {
        mutado = true;
        return { ...t, estado: "Excedido" as const };
      }
      return t;
    });

    // Persiste la mutacion de estado "Excedido" si ocurrio
    if (mutado) {
      await guardarTickets(actualizados);
    }

    return { success: true, data: actualizados };
  } catch (err) {
    const mensaje = err instanceof Error ? err.message : String(err);
    console.error("[ARCO+][ERROR] listarSolicitudesArco:", mensaje);
    return { success: false, error: `Error al listar solicitudes: ${mensaje}` };
  }
}
