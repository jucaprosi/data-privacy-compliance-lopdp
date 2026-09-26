"use server";

/**
 * ¤mtge-granescala-relacional
 * Motor MTGE Relacional a Gran Escala - Server Actions
 * Normativa: Res. SPDP-SPD-2026-0005-R | LOPDP Arts. 25, 44, 48 | Doctrina 5 (SSOT)
 * Invariante: INV_LOPDP_MTGE_DETERMINISTIC_TRIGGER
 *
 * Diferencia clave con ratActions.ts:
 *   ratActions.ts  -> evaluacion MTGE por actividad individual (por fila del RAT)
 *   mtgeActions.ts -> evaluacion MTGE RELACIONAL a nivel de tenant completo:
 *                     lee todo el rat_master.json y decide si el tenant como
 *                     entidad juridica supera umbrales de Gran Escala agregados.
 */

import fs from "fs/promises";
import fsSync from "fs";
import path from "path";
import type { ActividadTratamiento } from "@/types/rat";
import type { ServerActionResponse } from "@/types/rat";

// ---------------------------------------------------------------------------
// Constantes normativas - Res. SPDP-SPD-2026-0005-R Art. 12 y 13
// ---------------------------------------------------------------------------

/** Umbral de volumen total de titulares que define Gran Escala a nivel empresa */
const UMBRAL_VOLUMEN_GRAN_ESCALA = 10_000;

/** Permanencia en anos que, combinada con datos sensibles, activa EIPD forzosa */
const UMBRAL_PERMANENCIA_SENSIBLE_ANOS = 3;

/** Categorias de datos que activan el supuesto normativo de datos sensibles (Art. 25 LOPDP) */
const CATEGORIAS_SENSIBLES_CRITICAS = ["biom", "salud", "health", "biometric"];

// ---------------------------------------------------------------------------
// Resultado del motor MTGE Relacional
// ---------------------------------------------------------------------------

export interface ResultadoMTGERelacional {
  /** Volumen total acumulado de titulares en el RAT */
  volumenTotalTitulares: number;
  /** ¿El tenant supera el umbral de 10.000 titulares? (Criterio A) */
  superaUmbralVolumen: boolean;
  /** ¿Existe al menos un tratamiento sensible (Bio/Salud) con retencion > 3 anos? (Criterio B) */
  tieneTratamientoSensibleLargo: boolean;
  /** Flag global que activa EIPD forzosa. Persiste de forma permanente en rat_master.json */
  requiereEIPDForzoso: boolean;
  /** Criterio normativo que activo la bandera (trazabilidad) */
  criterioActivacion:
    | "CRITERIO_A_VOLUMEN_MASIVO"
    | "CRITERIO_B_SENSIBLE_LONG_RETENTION"
    | "CRITERIO_A_Y_B"
    | "NINGUNO";
  /** IDs de actividades que aportaron al criterio de activacion */
  actividadesQueDetonan: string[];
  /** Timestamp de la evaluacion */
  evaluadoEn: string;
  /** Resumen en lenguaje natural de la decision normativa */
  rationale: string;
}

// ---------------------------------------------------------------------------
// Utilidades de ruta
// ---------------------------------------------------------------------------

function getRatMasterPath(): string {
  const cwd = process.cwd();
  const frontendPath = path.join(cwd, "frontend", "data", "rat_master.json");
  const directPath = path.join(cwd, "data", "rat_master.json");
  return fsSync.existsSync(path.join(cwd, "frontend", "data"))
    ? frontendPath
    : directPath;
}

async function leerRatMaster(): Promise<ActividadTratamiento[]> {
  const filePath = getRatMasterPath();
  try {
    await fs.access(filePath);
    const raw = await fs.readFile(filePath, "utf-8");
    return JSON.parse(raw) as ActividadTratamiento[];
  } catch {
    return [];
  }
}

async function guardarRatMaster(
  actividades: ActividadTratamiento[]
): Promise<void> {
  const filePath = getRatMasterPath();
  await fs.writeFile(filePath, JSON.stringify(actividades, null, 2), "utf-8");
}

// ---------------------------------------------------------------------------
// Helpers del algoritmo
// ---------------------------------------------------------------------------

function esSensible(categorias: string[]): boolean {
  if (!Array.isArray(categorias)) return false;
  return categorias.some((c) => {
    const lower = String(c).toLowerCase();
    return CATEGORIAS_SENSIBLES_CRITICAS.some((k) => lower.includes(k));
  });
}

// ---------------------------------------------------------------------------
// Server Action: evaluarNecesidadEIPD
// ---------------------------------------------------------------------------

/**
 * Motor MTGE Relacional a Gran Escala.
 *
 * Lee el rat_master.json en tiempo real y evalua dos criterios normativos:
 *
 * CRITERIO A (Volumen Masivo):
 *   Si la suma total del volumenRegistros del tenant supera los 10.000 titulares,
 *   el sistema fija requiereEIPDForzoso=true en TODAS las actividades afectadas.
 *
 * CRITERIO B (Sensibilidad + Larga Retencion):
 *   Si existe al menos una actividad que trata datos Biometricos o de Salud
 *   con una permanencia superior a 3 anos, activa requiereEIPDForzoso=true.
 *
 * EFECTO PERMANENTE: El flag requiereEIPDForzoso se muta de forma irreversible
 * en el rat_master.json (no puede revertirse sin aprobacion del DPO - SoD).
 *
 * @returns ServerActionResponse<ResultadoMTGERelacional>
 */
export async function evaluarNecesidadEIPD(): Promise<
  ServerActionResponse<ResultadoMTGERelacional>
> {
  try {
    const actividades = await leerRatMaster();

    if (actividades.length === 0) {
      return {
        success: false,
        error:
          "El RAT Maestro esta vacio. Registre al menos una actividad de tratamiento antes de ejecutar la evaluacion MTGE Relacional.",
      };
    }

    // --- CRITERIO A: Volumen total de titulares ---
    const volumenTotal = actividades.reduce((acc, a) => {
      return acc + (Number(a.volumenRegistros) || 0);
    }, 0);
    const superaUmbralVolumen = volumenTotal > UMBRAL_VOLUMEN_GRAN_ESCALA;

    // --- CRITERIO B: Tratamientos sensibles con retencion prolongada ---
    const actividadesCriterioB = actividades.filter((a) => {
      const sensible = esSensible(a.categoriasDatos ?? []);
      const retencionLarga =
        (Number(a.permanenciaAnos) || 0) > UMBRAL_PERMANENCIA_SENSIBLE_ANOS;
      return sensible && retencionLarga;
    });
    const tieneTratamientoSensibleLargo = actividadesCriterioB.length > 0;

    // --- Determinacion del criterio de activacion ---
    const requiereEIPDForzoso = superaUmbralVolumen || tieneTratamientoSensibleLargo;

    let criterioActivacion: ResultadoMTGERelacional["criterioActivacion"] =
      "NINGUNO";
    if (superaUmbralVolumen && tieneTratamientoSensibleLargo) {
      criterioActivacion = "CRITERIO_A_Y_B";
    } else if (superaUmbralVolumen) {
      criterioActivacion = "CRITERIO_A_VOLUMEN_MASIVO";
    } else if (tieneTratamientoSensibleLargo) {
      criterioActivacion = "CRITERIO_B_SENSIBLE_LONG_RETENTION";
    }

    // IDs de actividades que contribuyeron al disparo
    const actividadesQueDetonan: string[] = [];
    if (superaUmbralVolumen) {
      actividades.forEach((a) => {
        if ((Number(a.volumenRegistros) || 0) > 0) {
          actividadesQueDetonan.push(a.id);
        }
      });
    }
    actividadesCriterioB.forEach((a) => {
      if (!actividadesQueDetonan.includes(a.id)) {
        actividadesQueDetonan.push(a.id);
      }
    });

    // --- MUTACION GLOBAL PERMANENTE (si se activo el flag) ---
    if (requiereEIPDForzoso) {
      const actividadesActualizadas = actividades.map((a) => {
        const debeActivar =
          superaUmbralVolumen ||
          actividadesCriterioB.some((b) => b.id === a.id);
        if (debeActivar && !a.requiereEIPD) {
          return {
            ...a,
            requiereEIPD: true,
            criterioActivacionMTGE: criterioActivacion,
            fechaActualizacion: new Date().toISOString(),
          };
        }
        return a;
      });
      await guardarRatMaster(actividadesActualizadas);
      console.log(
        `[MTGE_RELACIONAL] Flag requiereEIPDForzoso=true aplicado. Criterio: ${criterioActivacion} | Volumen total: ${volumenTotal.toLocaleString("es-EC")}`
      );
    }

    // --- Rationale en lenguaje natural ---
    let rationale = "";
    if (criterioActivacion === "NINGUNO") {
      rationale = `Evaluacion completada. El tenant no supera el umbral de ${UMBRAL_VOLUMEN_GRAN_ESCALA.toLocaleString("es-EC")} titulares (volumen actual: ${volumenTotal.toLocaleString("es-EC")}) y no registra tratamientos con datos sensibles de larga retencion. No se activa EIPD forzosa segun la Res. SPDP-SPD-2026-0005-R.`;
    } else if (criterioActivacion === "CRITERIO_A_VOLUMEN_MASIVO") {
      rationale = `CRITERIO A ACTIVADO: El volumen acumulado de titulares del tenant (${volumenTotal.toLocaleString("es-EC")}) supera el umbral legal de ${UMBRAL_VOLUMEN_GRAN_ESCALA.toLocaleString("es-EC")} establecido en la Res. SPDP-SPD-2026-0005-R Art. 12. Se ha fijado requiereEIPDForzoso=true de forma permanente en el RAT Maestro.`;
    } else if (criterioActivacion === "CRITERIO_B_SENSIBLE_LONG_RETENTION") {
      rationale = `CRITERIO B ACTIVADO: Se detectaron ${actividadesCriterioB.length} tratamiento(s) con datos Biometricos o de Salud (Art. 25 LOPDP) con retencion superior a ${UMBRAL_PERMANENCIA_SENSIBLE_ANOS} anos. Conforme al Art. 44 LOPDP y Res. SPDP-SPD-2026-0005-R, se activa EIPD previa obligatoria. Flag requiereEIPDForzoso=true persiste en RAT Maestro.`;
    } else {
      rationale = `CRITERIOS A Y B ACTIVADOS SIMULTANEAMENTE: Volumen masivo (${volumenTotal.toLocaleString("es-EC")} titulares) y tratamientos con datos sensibles de larga retencion. Maximo nivel de riesgo normativo. EIPD forzosa e inmediata, DPO debe ser notificado (Art. 48 LOPDP).`;
    }

    const resultado: ResultadoMTGERelacional = {
      volumenTotalTitulares: volumenTotal,
      superaUmbralVolumen,
      tieneTratamientoSensibleLargo,
      requiereEIPDForzoso,
      criterioActivacion,
      actividadesQueDetonan,
      evaluadoEn: new Date().toISOString(),
      rationale,
    };

    return { success: true, data: resultado };
  } catch (err) {
    const mensaje = err instanceof Error ? err.message : String(err);
    console.error("[MTGE_RELACIONAL][ERROR] evaluarNecesidadEIPD:", mensaje);
    return {
      success: false,
      error: `Error interno en el motor MTGE Relacional: ${mensaje}`,
    };
  }
}
