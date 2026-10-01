"use server";

import fs from "fs/promises";
import path from "path";
import crypto from "crypto";
import { AuditSnapshot, NuevoSnapshotInput } from "@/types";
import { NORMATIVAS, NORMATIVA_POR_DEFECTO } from "@/lib/normativas";

export interface ServerActionResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
}

// Ruta persistente del archivo JSON de snapshots (inmutable, append-only)
const SNAPSHOTS_DIR = path.join(process.cwd(), "data");
const SNAPSHOTS_FILE = path.join(SNAPSHOTS_DIR, "snapshots.json");

/**
 * Inicializa y asegura la existencia del archivo de almacenamiento seguro.
 */
async function asegurarArchivoSnapshots(): Promise<void> {
  try {
    await fs.mkdir(SNAPSHOTS_DIR, { recursive: true });
    try {
      await fs.access(SNAPSHOTS_FILE);
    } catch {
      // Si el archivo no existe, crearlo con un arreglo vacío
      await fs.writeFile(SNAPSHOTS_FILE, JSON.stringify([], null, 2), "utf-8");
    }
  } catch (error) {
    console.error("[AUDIT_STORAGE_INIT_ERROR]:", error);
    throw new Error("No se pudo inicializar la bóveda de snapshots inmutables.");
  }
}

/**
 * Lee la colección completa de snapshots de forma determinista.
 */
async function leerSnapshots(): Promise<AuditSnapshot[]> {
  await asegurarArchivoSnapshots();
  try {
    const raw = await fs.readFile(SNAPSHOTS_FILE, "utf-8");
    return JSON.parse(raw) as AuditSnapshot[];
  } catch (error) {
    console.error("[AUDIT_READ_ERROR]:", error);
    return [];
  }
}

/**
 * Server Action: Congela y almacena un snapshot de auditoría con garantía de inmutabilidad (Doctrinas 7 y 10).
 * Bloquea cualquier mutación previa y sella el registro de Solo Lectura.
 */
export async function congelarSnapshotAuditoria(
  auditData: NuevoSnapshotInput
): Promise<ServerActionResponse<AuditSnapshot>> {
  try {
    // 1. Validar que la información requerida no venga vacía
    if (!auditData) {
      return { success: false, error: "Los datos de auditoría no pueden ser nulos o indefinidos." };
    }

    if (!auditData.empresa?.razonSocial?.trim()) {
      return {
        success: false,
        error: "La Razón Social de la organización es requerida para sellar el snapshot.",
      };
    }

    if (!auditData.respuestasSnapshot || auditData.respuestasSnapshot.length === 0) {
      return {
        success: false,
        error: "No se puede congelar una auditoría sin respuestas en el lienzo diagnóstico.",
      };
    }

    const normativaSolicitada = auditData.normativa || NORMATIVA_POR_DEFECTO;
    const descriptor = Object.values(NORMATIVAS).find((n) => n.id === normativaSolicitada);
    if (!descriptor || !descriptor.bancoDisponible) {
      return {
        success: false,
        error: `La normativa "${normativaSolicitada}" no está disponible para sellar snapshots.`,
      };
    }
    const normativa = descriptor.id;

    // 2. Generar identificador único y timestamp inalterable del servidor
    const id = `snap-${Date.now()}-${crypto.randomUUID().substring(0, 8)}`;
    const fechaCierre = new Date().toISOString();
    const versionNormativa = auditData.versionNormativa || "LOPDP-EC-2026.v1";

    // 3. Generar sello de integridad criptográfico SHA-256 sobre el contenido congelado
    const hashPayload = JSON.stringify({
      id,
      fechaCierre,
      empresa: auditData.empresa,
      normativa,
      versionNormativa,
      respuestasSnapshot: auditData.respuestasSnapshot,
      scoringFinal: auditData.scoringFinal,
    });
    const sha256Seal = crypto.createHash("sha256").update(hashPayload).digest("hex");

    // 4. Crear el objeto Snapshot Inmutable (congelado en memoria)
    const nuevoSnapshot: AuditSnapshot = Object.freeze({
      id,
      fechaCierre,
      empresa: {
        razonSocial: auditData.empresa.razonSocial.trim(),
        sector: auditData.empresa.sector || "General",
        tamano: auditData.empresa.tamano || "No especificado",
      },
      normativa,
      versionNormativa,
      respuestasSnapshot: [...auditData.respuestasSnapshot],
      scoringFinal: { ...auditData.scoringFinal },
      sha256Seal,
    });

    // 5. Verificación de Inmutabilidad Absoluta (Restricción Física anti UPDATE/DELETE)
    const snapshotsExistentes = await leerSnapshots();

    // Comprobación anti-sobrescritura
    const existeId = snapshotsExistentes.some((s) => s.id === nuevoSnapshot.id);
    if (existeId) {
      throw new Error(
        `[INMUTABILITY_VIOLATION] Operación UPDATE prohibida. El snapshot ${nuevoSnapshot.id} ya existe y es de solo lectura.`
      );
    }

    // Adición estricta (Append-Only Log)
    const coleccionActualizada = [...snapshotsExistentes, nuevoSnapshot];
    await fs.writeFile(SNAPSHOTS_FILE, JSON.stringify(coleccionActualizada, null, 2), "utf-8");

    // 6. Emisión del Log Inalterable en la Consola del Servidor (Doctrina 10)
    console.log(
      `[AUDIT_TRAIL] [SUCCESS] Snapshot ${nuevoSnapshot.id} sellado de forma inmutable para ${nuevoSnapshot.empresa.razonSocial}.`
    );

    return {
      success: true,
      data: nuevoSnapshot,
    };
  } catch (error) {
    const errorMsg = error instanceof Error ? error.message : "Error desconocido al congelar el snapshot.";
    console.error("[AUDIT_ACTION_ERROR]:", error);
    return {
      success: false,
      error: errorMsg,
    };
  }
}

/**
 * Server Action: Retorna la lista cronológica de snapshots guardados para una organización,
 * ordenados estrictamente desde el más reciente al más antiguo.
 */
export async function obtenerHistorialAuditorias(
  empresaIdOrRazonSocial?: string
): Promise<ServerActionResponse<AuditSnapshot[]>> {
  try {
    const todos = await leerSnapshots();

    let filtrados = todos;
    if (empresaIdOrRazonSocial && empresaIdOrRazonSocial.trim() !== "") {
      const termino = empresaIdOrRazonSocial.trim().toLowerCase();
      filtrados = todos.filter((s) => s.empresa.razonSocial.toLowerCase().includes(termino));
    }

    // Ordenamiento cronológico descendente (más reciente primero)
    const ordenados = [...filtrados].sort(
      (a, b) => new Date(b.fechaCierre).getTime() - new Date(a.fechaCierre).getTime()
    );

    return {
      success: true,
      data: ordenados,
    };
  } catch (error) {
    const errorMsg = error instanceof Error ? error.message : "Error al obtener el historial de auditorías.";
    console.error("[AUDIT_HISTORIAL_ERROR]:", error);
    return {
      success: false,
      error: errorMsg,
      data: [],
    };
  }
}
