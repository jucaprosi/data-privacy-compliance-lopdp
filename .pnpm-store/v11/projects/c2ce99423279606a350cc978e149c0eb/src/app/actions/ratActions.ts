"use server";

import { promises as fs } from "fs";
import path from "path";
import { randomUUID } from "crypto";
import {
  ActividadTratamiento,
  ResultadoEvaluacionMTGE,
  ServerActionResponse,
} from "@/types/rat";

const UMBRAL_GRAN_ESCALA_PUNTOS = 100.0;

function obtenerRutaArchivo(): string {
  return path.join(process.cwd(), "data", "rat_master.json");
}

async function asegurarArchivoDatos(): Promise<string> {
  const ruta = obtenerRutaArchivo();
  const dir = path.dirname(ruta);
  await fs.mkdir(dir, { recursive: true });

  try {
    await fs.access(ruta);
  } catch {
    await fs.writeFile(ruta, JSON.stringify([], null, 2), "utf-8");
  }
  return ruta;
}

/**
 * Server Action 1: Ejecuta el algoritmo paramétrico MTGE
 * conforme a la Resolución SPDP-SPD-2026-0005-R y los Arts. 25, 44 y 48 de la LOPDP.
 */
export async function ejecutarAlgoritmoMTGE(
  actividad: ActividadTratamiento
): Promise<ResultadoEvaluacionMTGE> {
  const categorias = Array.isArray(actividad.categoriasDatos)
    ? actividad.categoriasDatos
    : [];

  const trataBiometricos = categorias.some((c) =>
    String(c).toLowerCase().includes("biom")
  );
  const trataSalud = categorias.some((c) =>
    String(c).toLowerCase().includes("salud")
  );
  const trataSensiblesDirectos = trataBiometricos || trataSalud;

  // 1. Caso Directo: Datos de Alta Sensibilidad (Salud o Biométricos)
  if (trataSensiblesDirectos) {
    return {
      actividadId: actividad.id || "temp-id",
      puntajeMTGE: 150.0,
      esGranEscala: true,
      requiereEIPD: true,
      alertaForzosaDPO: true,
      criterioActivacion: "CASO_DIRECTO_SENSIBLES",
      factores: {
        puntosVolumen: 50.0,
        puntosSensibilidad: 80.0,
        puntosPermanencia: 20.0,
      },
      rationale:
        "Calificación directa por tratamiento de datos de salud o biométricos conforme al Art. 25 LOPDP y Art. 12 de la Resolución SPDP-SPD-2026-0005-R. Detona forzosamente EIPD previa y designación obligatoria de DPO.",
    };
  }

  // 2. Caso Directo: Volumen Masivo de Titulares (> 10,000)
  const volumen = Number(actividad.volumenRegistros) || 0;
  if (volumen > 10000) {
    return {
      actividadId: actividad.id || "temp-id",
      puntajeMTGE: 120.0,
      esGranEscala: true,
      requiereEIPD: true,
      alertaForzosaDPO: true,
      criterioActivacion: "CASO_DIRECTO_VOLUMEN",
      factores: {
        puntosVolumen: 50.0,
        puntosSensibilidad: 50.0,
        puntosPermanencia: 20.0,
      },
      rationale: `Calificación directa por volumen masivo de titulares (${volumen.toLocaleString("es-EC")} > 10,000) según la Resolución SPDP-SPD-2026-0005-R. Activa forzosamente EIPD previa y supervisión del DPO.`,
    };
  }

  // 3. Cálculo Paramétrico Aditivo (Casos Generales)
  let puntosVolumen = 5.0;
  if (volumen > 50000) {
    puntosVolumen = 50.0;
  } else if (volumen > 10000) {
    puntosVolumen = 30.0;
  } else if (volumen > 1000) {
    puntosVolumen = 15.0;
  }

  let puntosSensibilidad = 0.0;
  const trataVulnerables = categorias.some((c) => {
    const s = String(c).toLowerCase();
    return s.includes("menor") || s.includes("nna") || s.includes("penal") || s.includes("judicial");
  });
  const trataFinancieroLaboral = categorias.some((c) => {
    const s = String(c).toLowerCase();
    return s.includes("financier") || s.includes("laboral") || s.includes("economic");
  });

  if (trataVulnerables) {
    puntosSensibilidad = 35.0;
  } else if (trataFinancieroLaboral) {
    puntosSensibilidad = 10.0;
  }

  const permanencia = Number(actividad.permanenciaAnos) || 1;
  let puntosPermanencia = 5.0;
  if (permanencia >= 5) {
    puntosPermanencia = 20.0;
  } else if (permanencia >= 2) {
    puntosPermanencia = 10.0;
  }

  const puntajeTotal = puntosVolumen + puntosSensibilidad + puntosPermanencia;
  const esGranEscala = puntajeTotal >= UMBRAL_GRAN_ESCALA_PUNTOS;

  return {
    actividadId: actividad.id || "temp-id",
    puntajeMTGE: puntajeTotal,
    esGranEscala,
    requiereEIPD: esGranEscala,
    alertaForzosaDPO: esGranEscala,
    criterioActivacion: esGranEscala ? "UMBRAL_PARAMETRICO" : "NO_ALCANZA",
    factores: {
      puntosVolumen,
      puntosSensibilidad,
      puntosPermanencia,
    },
    rationale: `Puntaje paramétrico obtenido: ${puntajeTotal} / ${UMBRAL_GRAN_ESCALA_PUNTOS}. ${
      esGranEscala
        ? "Supera el umbral de Gran Escala; activa DPD/DPO y EIPD obligatorios."
        : "Tratamiento ordinario sin activación forzosa."
    }`,
  };
}

/**
 * Server Action 2: Guarda o actualiza una actividad de tratamiento
 * en el archivo persistente local `data/rat_master.json`.
 */
export async function guardarActividadTratamiento(
  actividad: ActividadTratamiento
): Promise<ServerActionResponse<ActividadTratamiento>> {
  try {
    if (!actividad.nombre || !actividad.nombre.trim()) {
      return { success: false, error: "El nombre de la actividad es obligatorio." };
    }
    if (!actividad.finalidad || !actividad.finalidad.trim()) {
      return { success: false, error: "La finalidad de la actividad es obligatoria (Art. 10 num. 2 LOPDP)." };
    }

    const ruta = await asegurarArchivoDatos();
    const contenidoRaw = await fs.readFile(ruta, "utf-8");
    let actividades: ActividadTratamiento[] = [];
    try {
      actividades = JSON.parse(contenidoRaw);
      if (!Array.isArray(actividades)) actividades = [];
    } catch {
      actividades = [];
    }

    // Ejecución previa obligatoria del motor MTGE para congelar indicadores
    const evaluacionMTGE = await ejecutarAlgoritmoMTGE(actividad);

    const id = actividad.id && actividad.id.trim() !== "" ? actividad.id : randomUUID();
    const ahora = new Date().toISOString();

    const actividadProcesada: ActividadTratamiento = {
      ...actividad,
      id,
      nombre: actividad.nombre.trim(),
      finalidad: actividad.finalidad.trim(),
      baseJuridica: actividad.baseJuridica || "Obligación Legal",
      categoriasDatos: Array.isArray(actividad.categoriasDatos) ? actividad.categoriasDatos : ["Identificativos"],
      volumenRegistros: Number(actividad.volumenRegistros) || 0,
      permanenciaAnos: Number(actividad.permanenciaAnos) || 1,
      requiereEIPD: evaluacionMTGE.requiereEIPD,
      alertaForzosaDPO: evaluacionMTGE.alertaForzosaDPO,
      puntajeMTGE: evaluacionMTGE.puntajeMTGE,
      criterioActivacionMTGE: evaluacionMTGE.criterioActivacion,
      fechaCreacion: actividad.fechaCreacion || ahora,
      fechaActualizacion: ahora,
    };

    const indexExistente = actividades.findIndex((item) => item.id === id);
    if (indexExistente >= 0) {
      actividades[indexExistente] = actividadProcesada;
    } else {
      actividades.push(actividadProcesada);
    }

    await fs.writeFile(ruta, JSON.stringify(actividades, null, 2), "utf-8");

    console.log(
      `[RAT_MASTER] [SUCCESS] Actividad "${actividadProcesada.nombre}" guardada. ID=${id} | EIPD=${actividadProcesada.requiereEIPD} | DPO=${actividadProcesada.alertaForzosaDPO}`
    );

    return {
      success: true,
      data: actividadProcesada,
    };
  } catch (error) {
    console.error("[RAT_ACTION_ERROR]:", error);
    return {
      success: false,
      error: error instanceof Error ? error.message : "Error al guardar actividad en el RAT Maestro.",
    };
  }
}

/**
 * Server Action 3: Obtiene la lista completa de actividades de tratamiento
 * registradas en el RAT Maestro local.
 */
export async function obtenerActividadesRAT(): Promise<
  ServerActionResponse<ActividadTratamiento[]>
> {
  try {
    const ruta = await asegurarArchivoDatos();
    const contenidoRaw = await fs.readFile(ruta, "utf-8");
    let actividades: ActividadTratamiento[] = [];
    try {
      actividades = JSON.parse(contenidoRaw);
      if (!Array.isArray(actividades)) actividades = [];
    } catch {
      actividades = [];
    }

    return {
      success: true,
      data: actividades,
    };
  } catch (error) {
    console.error("[RAT_FETCH_ERROR]:", error);
    return {
      success: false,
      error: error instanceof Error ? error.message : "Error al leer el RAT Maestro.",
    };
  }
}

/**
 * Server Action 4: Elimina una actividad del RAT Maestro por su ID.
 */
export async function eliminarActividadTratamiento(
  id: string
): Promise<ServerActionResponse<{ eliminadoId: string }>> {
  try {
    const ruta = await asegurarArchivoDatos();
    const contenidoRaw = await fs.readFile(ruta, "utf-8");
    let actividades: ActividadTratamiento[] = [];
    try {
      actividades = JSON.parse(contenidoRaw);
      if (!Array.isArray(actividades)) actividades = [];
    } catch {
      actividades = [];
    }

    const actividadesRestantes = actividades.filter((item) => item.id !== id);
    await fs.writeFile(ruta, JSON.stringify(actividadesRestantes, null, 2), "utf-8");

    return {
      success: true,
      data: { eliminadoId: id },
    };
  } catch (error) {
    console.error("[RAT_DELETE_ERROR]:", error);
    return {
      success: false,
      error: error instanceof Error ? error.message : "Error al eliminar actividad del RAT Maestro.",
    };
  }
}
