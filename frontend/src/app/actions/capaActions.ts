"use server";

/**
 * ¤capa-workflow
 * Server Actions para la Gestion de Hallazgos y CAPA
 * Normativa: LOPDP Arts. 10 num. 7, 41-44 | Doctrinas 3, 4 y 10 | Teorema 4 (SoD DPO)
 * Invariante Dura: INV_CAPA_SOD => auditorId !== usuarioQueSubioEvidencia
 */

import fs from "fs/promises";
import fsSync from "fs";
import path from "path";
import { randomUUID } from "crypto";
import type {
  TicketCAPA,
  CrearPlanCorrectivoInput,
  CambioEstadoCAPA,
  EstadoCAPA,
  ResultadoValidacionSoD,
} from "@/types/capa";
import type { ServerActionResponse } from "@/types/rat";

// ---------------------------------------------------------------------------
// Persistencia — capa_workflow.json
// ---------------------------------------------------------------------------

function getCapaWorkflowPath(): { dir: string; file: string } {
  const cwd = process.cwd();
  const frontendDataDir = path.join(cwd, "frontend", "data");
  const directDataDir = path.join(cwd, "data");
  if (fsSync.existsSync(frontendDataDir)) {
    return { dir: frontendDataDir, file: path.join(frontendDataDir, "capa_workflow.json") };
  }
  return { dir: directDataDir, file: path.join(directDataDir, "capa_workflow.json") };
}

async function asegurarArchivoCAPA(): Promise<string> {
  const { dir, file } = getCapaWorkflowPath();
  await fs.mkdir(dir, { recursive: true });
  try {
    await fs.access(file);
  } catch {
    await fs.writeFile(file, JSON.stringify([], null, 2), "utf-8");
  }
  return file;
}

async function leerTicketsCAPA(): Promise<TicketCAPA[]> {
  const file = await asegurarArchivoCAPA();
  try {
    const raw = await fs.readFile(file, "utf-8");
    return JSON.parse(raw) as TicketCAPA[];
  } catch {
    return [];
  }
}

async function guardarTicketsCAPA(tickets: TicketCAPA[]): Promise<void> {
  const file = await asegurarArchivoCAPA();
  await fs.writeFile(file, JSON.stringify(tickets, null, 2), "utf-8");
}

// ---------------------------------------------------------------------------
// Validador SoD — Teorema 4 | INV_CAPA_SOD | NIST RBAC 2000
// ---------------------------------------------------------------------------

/**
 * Comprueba de forma determinista y exogena que el auditor sea diferente
 * al usuario que subio la evidencia de mejora. Esta funcion es la unica
 * compuerta de paso hacia el cierre del ticket CAPA.
 *
 * Regla formal (Teorema 4):
 *   Permiso(u, Verificacion) = 0  si  u == usuarioQueSubioEvidencia
 */
function validarSoD(
  auditorId: string,
  usuarioEvidencia: string | null | undefined
): ResultadoValidacionSoD {
  const auditorNorm = auditorId.trim().toLowerCase();
  const evidenciaNorm = (usuarioEvidencia ?? "").trim().toLowerCase();

  if (!auditorNorm) {
    return {
      valido: false,
      auditorId,
      usuarioEvidencia,
      motivo: "El identificador del auditor no puede estar vacio.",
    };
  }

  if (!evidenciaNorm) {
    return {
      valido: false,
      auditorId,
      usuarioEvidencia,
      motivo:
        "BLOQUEO SOD (INV_CAPA_SOD): No existe usuario que haya subido evidencia. El ticket debe pasar por subirEvidenciaMejora antes de poder verificarse.",
    };
  }

  if (auditorNorm === evidenciaNorm) {
    return {
      valido: false,
      auditorId,
      usuarioEvidencia,
      motivo: `BLOQUEO SOD INVIOLABLE (INV_CAPA_SOD | Teorema 4 | NIST RBAC 2000): El auditor '${auditorId}' es el mismo usuario que subio la evidencia. La Separacion de Funciones exige verificadores estrictamente independientes. Asigne un auditor distinto.`,
    };
  }

  return { valido: true, auditorId, usuarioEvidencia };
}

// ---------------------------------------------------------------------------
// Server Action 1: crearPlanCorrectivo
// ---------------------------------------------------------------------------

/**
 * Transforma una brecha del diagnostico en un ticket CAPA en estado 'Abierto'
 * y lo persiste en data/capa_workflow.json.
 *
 * El servidor asigna id (UUID v4), fechaCreacion y estado inicial invariable.
 * Bloqueo preventivo SOD: responsableArea != auditorAsignado.
 */
export async function crearPlanCorrectivo(
  hallazgoData: CrearPlanCorrectivoInput
): Promise<ServerActionResponse<TicketCAPA>> {
  try {
    const requeridos: Array<[keyof CrearPlanCorrectivoInput, string]> = [
      ["preguntaIdOriginaria", "preguntaIdOriginaria"],
      ["descripcionHallazgo", "descripcionHallazgo"],
      ["accionCorrectiva", "accionCorrectiva"],
      ["responsableArea", "responsableArea"],
      ["auditorAsignado", "auditorAsignado"],
    ];

    for (const [campo, etiqueta] of requeridos) {
      const valor = hallazgoData[campo] as string | undefined;
      if (!valor?.trim()) {
        return { success: false, error: `El campo '${etiqueta}' es obligatorio para abrir un ticket CAPA.` };
      }
    }

    // Bloqueo SOD preventivo en la creacion
    if (
      hallazgoData.responsableArea.trim().toLowerCase() ===
      hallazgoData.auditorAsignado.trim().toLowerCase()
    ) {
      return {
        success: false,
        error:
          "BLOQUEO SOD PREVENTIVO (INV_CAPA_SOD): responsableArea y auditorAsignado no pueden ser el mismo rol o usuario. La independencia del auditor es un invariante estructural.",
      };
    }

    const ahora = new Date().toISOString();
    const nuevoTicket: TicketCAPA = {
      id: randomUUID(),
      preguntaIdOriginaria: hallazgoData.preguntaIdOriginaria.trim(),
      descripcionHallazgo: hallazgoData.descripcionHallazgo.trim(),
      accionCorrectiva: hallazgoData.accionCorrectiva.trim(),
      responsableArea: hallazgoData.responsableArea.trim(),
      auditorAsignado: hallazgoData.auditorAsignado.trim(),
      estado: "Abierto",
      evidenciaMitigacion: null,
      severidad: hallazgoData.severidad ?? "No Conformidad Menor",
      descripcionBrechaOriginal: hallazgoData.descripcionBrechaOriginal?.trim(),
      usuarioQueSubioEvidencia: null,
      fechaCreacion: ahora,
      fechaUltimaActualizacion: ahora,
      fechaCierreConforme: null,
      dictamenAuditor: null,
      historialCambios: [],
    };

    const tickets = await leerTicketsCAPA();
    tickets.push(nuevoTicket);
    await guardarTicketsCAPA(tickets);

    console.log(
      `[CAPA] Ticket abierto | id=${nuevoTicket.id} | brecha=${nuevoTicket.preguntaIdOriginaria} | auditor=${nuevoTicket.auditorAsignado}`
    );
    return { success: true, data: nuevoTicket };
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    console.error("[CAPA][ERROR] crearPlanCorrectivo:", msg);
    return { success: false, error: `Error interno al crear el plan correctivo: ${msg}` };
  }
}

// ---------------------------------------------------------------------------
// Server Action 2: subirEvidenciaMejora
// ---------------------------------------------------------------------------

/**
 * Permite al responsableArea adjuntar el registro probatorio (E1+) y
 * transicionar el ticket a "Pendiente de Verificacion".
 *
 * Invariante INV_CAPA_EVIDENCIA_E1: evidenciaUrl no puede estar vacio.
 * El servidor guarda usuarioId para el control SoD de la siguiente fase.
 */
export async function subirEvidenciaMejora(
  capaId: string,
  evidenciaUrl: string,
  usuarioId: string
): Promise<ServerActionResponse<TicketCAPA>> {
  try {
    if (!capaId?.trim()) {
      return { success: false, error: "El id del ticket CAPA es obligatorio." };
    }

    if (!evidenciaUrl?.trim()) {
      return {
        success: false,
        error:
          "BLOQUEO NORMATIVO (INV_CAPA_EVIDENCIA_E1): La URL del expediente probatorio es obligatoria. No se puede avanzar a Pendiente de Verificacion sin evidencia E1+.",
      };
    }

    if (!usuarioId?.trim()) {
      return {
        success: false,
        error: "El usuarioId es obligatorio para el control SoD en la fase de verificacion.",
      };
    }

    const tickets = await leerTicketsCAPA();
    const idx = tickets.findIndex((t) => t.id === capaId);

    if (idx === -1) {
      return { success: false, error: `Ticket CAPA no encontrado con id: ${capaId}.` };
    }

    const ticket = tickets[idx];

    if (ticket.estado === "Cerrado Conforme") {
      return {
        success: false,
        error: `El ticket ${capaId} esta 'Cerrado Conforme'. No se admiten modificaciones sobre un expediente sellado.`,
      };
    }

    if (ticket.estado === "Pendiente de Verificacion") {
      return {
        success: false,
        error: `El ticket ${capaId} ya esta en 'Pendiente de Verificacion'. Espere el dictamen del auditor antes de resubir evidencia.`,
      };
    }

    const ahora = new Date().toISOString();
    const cambio: CambioEstadoCAPA = {
      estadoAnterior: ticket.estado,
      estadoNuevo: "Pendiente de Verificacion",
      actor: usuarioId.trim(),
      timestamp: ahora,
      nota: `Evidencia: ${evidenciaUrl.trim()}`,
    };

    const actualizado: TicketCAPA = {
      ...ticket,
      estado: "Pendiente de Verificacion",
      evidenciaMitigacion: evidenciaUrl.trim(),
      usuarioQueSubioEvidencia: usuarioId.trim(),
      fechaUltimaActualizacion: ahora,
      historialCambios: [...(ticket.historialCambios ?? []), cambio],
    };

    tickets[idx] = actualizado;
    await guardarTicketsCAPA(tickets);

    console.log(`[CAPA] Evidencia subida | id=${capaId} | usuario=${usuarioId}`);
    return { success: true, data: actualizado };
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    console.error("[CAPA][ERROR] subirEvidenciaMejora:", msg);
    return { success: false, error: `Error interno al subir evidencia: ${msg}` };
  }
}

// ---------------------------------------------------------------------------
// Server Action 3: verificarCierreCapa  [RESTRICCION SOD INVIOLABLE]
// ---------------------------------------------------------------------------

/**
 * Dictamen final e independiente del auditor sobre el plan correctivo.
 *
 * RESTRICCION SOD INVIOLABLE (INV_CAPA_SOD | Teorema 4 | NIST RBAC 2000):
 *   auditorId DEBE ser != usuarioQueSubioEvidencia.
 *   Ninguna condicion, parametro ni flag puede desactivar esta compuerta.
 *
 * aprobado = true  => estado -> "Cerrado Conforme"
 *                     Actualiza Compliance Graph (pregunta -> Conforme E1+).
 * aprobado = false => estado -> "Rechazado"
 *                     El ticket retrocede para nueva accion correctiva.
 */
export async function verificarCierreCapa(
  capaId: string,
  dictamen: string,
  aprobado: boolean,
  auditorId: string
): Promise<ServerActionResponse<TicketCAPA & { complianceGraphActualizado?: boolean }>> {
  try {
    if (!capaId?.trim()) {
      return { success: false, error: "El id del ticket CAPA es obligatorio." };
    }
    if (!dictamen?.trim()) {
      return { success: false, error: "El dictamen tecnico del auditor no puede estar vacio." };
    }
    if (!auditorId?.trim()) {
      return { success: false, error: "El identificador del auditor es obligatorio." };
    }

    const tickets = await leerTicketsCAPA();
    const idx = tickets.findIndex((t) => t.id === capaId);

    if (idx === -1) {
      return { success: false, error: `Ticket CAPA no encontrado: ${capaId}.` };
    }

    const ticket = tickets[idx];

    if (ticket.estado !== "Pendiente de Verificacion") {
      return {
        success: false,
        error: `El ticket ${capaId} tiene estado '${ticket.estado}'. Solo tickets en 'Pendiente de Verificacion' aceptan dictamen.`,
      };
    }

    // ============================================================
    //  COMPUERTA SOD INVIOLABLE — INV_CAPA_SOD (Teorema 4)
    //  Esta es la unica ruta de acceso al cierre del ticket.
    //  Sin excepcion. Sin bypass. Sin flag de entorno.
    // ============================================================
    const sod = validarSoD(auditorId, ticket.usuarioQueSubioEvidencia);
    if (!sod.valido) {
      console.error(`[CAPA][SOD_VIOLATION] id=${capaId} | ${sod.motivo}`);
      return { success: false, error: sod.motivo };
    }

    const ahora = new Date().toISOString();
    const estadoNuevo: EstadoCAPA = aprobado ? "Cerrado Conforme" : "Rechazado";

    const cambio: CambioEstadoCAPA = {
      estadoAnterior: ticket.estado,
      estadoNuevo,
      actor: auditorId.trim(),
      timestamp: ahora,
      nota: dictamen.trim(),
    };

    const actualizado: TicketCAPA = {
      ...ticket,
      estado: estadoNuevo,
      dictamenAuditor: dictamen.trim(),
      fechaUltimaActualizacion: ahora,
      fechaCierreConforme: aprobado ? ahora : null,
      historialCambios: [...(ticket.historialCambios ?? []), cambio],
    };

    tickets[idx] = actualizado;
    await guardarTicketsCAPA(tickets);

    // Actualizacion reactiva del Compliance Graph si fue aprobado
    let complianceGraphActualizado = false;
    if (aprobado && actualizado.preguntaIdOriginaria) {
      try {
        complianceGraphActualizado = await _actualizarComplianceGraph(
          actualizado.preguntaIdOriginaria,
          actualizado.evidenciaMitigacion ?? ""
        );
      } catch (cgErr) {
        console.warn("[CAPA][COMPLIANCE_GRAPH_WARN]", cgErr);
      }
    }

    console.log(
      `[CAPA] Dictamen | id=${capaId} | estado=${estadoNuevo} | auditor=${auditorId} | cgActualizado=${complianceGraphActualizado}`
    );

    return { success: true, data: { ...actualizado, complianceGraphActualizado } };
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    console.error("[CAPA][ERROR] verificarCierreCapa:", msg);
    return { success: false, error: `Error interno al verificar cierre CAPA: ${msg}` };
  }
}

// ---------------------------------------------------------------------------
// Server Action 4: listarTicketsCAPA
// ---------------------------------------------------------------------------

export async function listarTicketsCAPA(
  filtroEstado?: TicketCAPA["estado"]
): Promise<ServerActionResponse<TicketCAPA[]>> {
  try {
    const todos = await leerTicketsCAPA();
    const filtrados = filtroEstado ? todos.filter((t) => t.estado === filtroEstado) : todos;
    const ordenados = [...filtrados].sort(
      (a, b) => new Date(b.fechaCreacion).getTime() - new Date(a.fechaCreacion).getTime()
    );
    return { success: true, data: ordenados };
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    return { success: false, error: `Error al listar tickets CAPA: ${msg}` };
  }
}

// ---------------------------------------------------------------------------
// Funcion interna: _actualizarComplianceGraph (Teorema 14 - DAG Lineage)
// ---------------------------------------------------------------------------

/**
 * Propaga el cierre conforme del CAPA al Compliance Graph del tenant.
 * Marca la pregunta originaria como respuesta_afirmativa=true / E1+ en
 * snapshots.json. Solo se invoca desde verificarCierreCapa cuando aprobado=true.
 */
async function _actualizarComplianceGraph(
  preguntaId: string,
  evidenciaUrl: string
): Promise<boolean> {
  const cwd = process.cwd();
  const frontendDataDir = path.join(cwd, "frontend", "data");
  const directDataDir = path.join(cwd, "data");
  const dataDir = fsSync.existsSync(frontendDataDir) ? frontendDataDir : directDataDir;
  const snapshotsFile = path.join(dataDir, "snapshots.json");

  try {
    await fs.access(snapshotsFile);
  } catch {
    return false;
  }

  const raw = await fs.readFile(snapshotsFile, "utf-8");
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const snapshots: any[] = JSON.parse(raw);
  let mutado = false;

  const actualizados = snapshots.map((snap) => {
    if (!Array.isArray(snap.respuestasSnapshot)) return snap;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const respActualizadas = snap.respuestasSnapshot.map((r: any) => {
      const match =
        r.id_pregunta === preguntaId ||
        r.idPregunta === preguntaId ||
        r.preguntaId === preguntaId;
      if (match && r.respuesta_afirmativa !== true) {
        mutado = true;
        return {
          ...r,
          respuesta_afirmativa: true,
          nivel_evidencia: "E1",
          rationale: `[CAPA CERRADO CONFORME] Evidencia: ${evidenciaUrl}. Fecha: ${new Date().toISOString()}`,
        };
      }
      return r;
    });
    return { ...snap, respuestasSnapshot: respActualizadas };
  });

  if (mutado) {
    await fs.writeFile(snapshotsFile, JSON.stringify(actualizados, null, 2), "utf-8");
    console.log(`[CAPA][COMPLIANCE_GRAPH] Pregunta ${preguntaId} -> Conforme E1+`);
  }
  return mutado;
}
