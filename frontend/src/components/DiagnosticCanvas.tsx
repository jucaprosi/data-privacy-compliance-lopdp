"use client";

import React, { useEffect, useMemo, useState, useTransition } from "react";
import {
  Clock,
  ShieldCheck,
  AlertTriangle,
  FileCheck2,
  ChevronLeft,
  ChevronRight,
  RotateCcw,
  Sparkles,
  SlidersHorizontal,
  BookmarkCheck,
  Award,
  Layers,
  Lock,
  GitCommit,
  Link2,
  Unlink,
  BadgeCheck,
} from "lucide-react";
import {
  useAuditStore,
  EstadoCumplimiento,
  RespuestaItemStore,
  type NormativaAuditoria,
} from "@/store/useAuditStore";
import { congelarSnapshotAuditoria } from "@/app/actions/auditActions";
import { AuditSnapshot, NuevoSnapshotInput } from "@/types";
import {
  BANCO_PREGUNTAS,
  podarBancoPorTamano,
  normalizarTamano,
  type PerfilOperacion,
} from "@/lib/bancoPreguntas";
import { ejemploDePregunta } from "@/lib/bancoPreguntas/ejemplos";
import dimensionCardStyles from "@/components/DimensionIdentity.module.css";
import {
  DIMENSION_POR_ID,
  RANGO_EVIDENCIA_POR_CUMPLE,
  type DimensionId,
} from "@/lib/dimensionesSGPDP";
import { resolverNormativa, usaBancoSGPDP } from "@/lib/normativas";
import type { EvidenciaDocumental } from "@/lib/evidencias/tipos";
import DropEvidencia from "@/components/evidencias/DropEvidencia";
import AlertaDimension from "@/components/AlertaDimension";
import PanelPreanalisis from "@/components/preanalisis/PanelPreanalisis";
import PrellenadoMasivo from "@/components/preanalisis/PrellenadoMasivo";
import type { ControlParaAnalisis, PropuestaIA } from "@/lib/preanalisis/tipos";

const huellaCorta = (sha256: string) => sha256.slice(0, 12);

/**
 * Respuestas que entran a un snapshot: solo las propias del auditor y, en el
 * banco SGPDP, solo las de controles exigibles a la talla actual. Es el mismo
 * conjunto que evalúa el tablero, para que el sello y el tablero coincidan.
 */
function respuestasSellables(
  respuestas: RespuestaItemStore[],
  normativa: NormativaAuditoria,
  tamano: string,
  perfil?: PerfilOperacion
): RespuestaItemStore[] {
  const propias = respuestas.filter((r) => !r.esReferencia);
  if (!usaBancoSGPDP(normativa)) return propias;
  const exigibles = new Set(
    podarBancoPorTamano(BANCO_PREGUNTAS, normalizarTamano(tamano), perfil).map((p) => p.id)
  );
  return propias.filter((r) => r.dimensionId && exigibles.has(r.preguntaId));
}

/**
 * Traduce las etiquetas técnicas del scoring a lenguaje claro. Solo cambia la
 * presentación: los valores guardados en el store y en los snapshots no se tocan.
 */
function describirNivelMadurez(etiqueta: string): string {
  const numero = etiqueta.match(/Nivel (\d)/)?.[1];
  switch (numero) {
    case "3":
      return "Nivel 3 de 3 · Avanzado (medidas formales y comprobables)";
    case "2":
      return "Nivel 2 de 3 · En desarrollo (hay medidas definidas, falta consolidarlas)";
    case "1":
      return "Nivel 1 de 3 · Inicial (se actúa caso por caso, sin proceso formal)";
    default:
      return "Nivel 0 de 3 · Sin medidas (no hay evidencia de gestión)";
  }
}

function describirRespaldoDocumental(promedio: number): string {
  if (promedio >= 2.5) return "Respaldo sólido: los documentos fueron validados por un tercero.";
  if (promedio >= 1.5) return "Respaldo medio: hay registros que muestran que las medidas se aplican.";
  if (promedio >= 0.5) return "Respaldo básico: hay documentos, pero preliminares (políticas o borradores).";
  return "Casi sin respaldo: la mayoría de las respuestas no tiene documento que las pruebe.";
}

function describirExposicion(porcentaje: number): { texto: string; clase: string } {
  if (porcentaje > 40) return { texto: "Riesgo alto", clase: "text-[#ff1744]" };
  if (porcentaje > 20) return { texto: "Riesgo medio", clase: "text-amber-400" };
  return { texto: "Riesgo bajo", clase: "text-[#00c853]" };
}

interface ResumenSellado {
  verificados: number;
  degradados: number;
  sinSoporte: number;
}

function resumirSellado(
  respuestasPropias: RespuestaItemStore[],
  evidencias: EvidenciaDocumental[]
): ResumenSellado {
  const vinculados = new Set(evidencias.flatMap((e) => e.controlesVinculados));
  let verificados = 0;
  let degradados = 0;
  let sinSoporte = 0;
  for (const r of respuestasPropias) {
    if (vinculados.has(r.preguntaId)) verificados += 1;
    else if (r.evidenciaNivel > 0) degradados += 1;
    else sinSoporte += 1;
  }
  return { verificados, degradados, sinSoporte };
}

interface PreguntaAssessment {
  id: number;
  dominioId: string;
  dominioNombre: string;
  enunciado: string;
  referenciaNormativa: string;
  esCritica: boolean;
  riesgoBase: number;
  evidenciaEsperada: string;
  // Solo las preguntas del banco SGPDP pertenecen a una dimensión; sin estos
  // campos la respuesta no entra al cálculo del tablero.
  dimensionId?: DimensionId;
  criticidad?: number;
  control?: string;
}

// Poka-Yoke: Cota superior rígida de 80 preguntas visibles

const BANCO_PREGUNTAS_NIIF18: PreguntaAssessment[] = [
  {
    id: 101,
    dominioId: "N01",
    dominioNombre: "Estructura del Estado de Resultados",
    enunciado: "¿Se presentan los ingresos y gastos clasificados estrictamente en las 5 categorías requeridas: Operativa, Inversión, Financiación, Impuestos y Operaciones Discontinuadas?",
    referenciaNormativa: "IFRS 18 (Estructura)",
    esCritica: true,
    riesgoBase: 10,
    evidenciaEsperada: "Estado de resultados estructurado y log de mapeo de cuentas",
  },
  {
    id: 102,
    dominioId: "N01",
    dominioNombre: "Estructura del Estado de Resultados",
    enunciado: "¿El Estado de Resultados presenta el subtotal mandatorio 'Resultado Operativo' en la carátula principal?",
    referenciaNormativa: "IFRS 18 - Subtotales Mandatorios",
    esCritica: true,
    riesgoBase: 9,
    evidenciaEsperada: "Estados financieros finales emitidos",
  },
  {
    id: 103,
    dominioId: "N01",
    dominioNombre: "Estructura del Estado de Resultados",
    enunciado: "¿El Estado de Resultados presenta el subtotal 'Resultado antes de Financiación e Impuestos a las Ganancias'?",
    referenciaNormativa: "IFRS 18 - Subtotales Mandatorios",
    esCritica: true,
    riesgoBase: 9,
    evidenciaEsperada: "Estados financieros finales emitidos",
  },
  {
    id: 104,
    dominioId: "N02",
    dominioNombre: "Categoría Operativa Residual",
    enunciado: "¿Se ha verificado que la categoría 'Operativa' actúa como categoría residual tras asignar Inversión, Financiación e Impuestos?",
    referenciaNormativa: "IFRS 18 - Clasificación Operativa",
    esCritica: false,
    riesgoBase: 6,
    evidenciaEsperada: "Matriz de clasificación o políticas contables documentadas",
  },
  {
    id: 105,
    dominioId: "N03",
    dominioNombre: "Medidas de Rendimiento de la Gerencia (MPM)",
    enunciado: "¿Las medidas Non-GAAP (MPMs) comunicadas externamente están reconciliadas en una nota única auditada dentro de los estados financieros?",
    referenciaNormativa: "IFRS 18 - Párrafos MPM",
    esCritica: true,
    riesgoBase: 10,
    evidenciaEsperada: "Nota única a los EEFF con tabla de conciliación y efectos impositivos",
  },
  {
    id: 106,
    dominioId: "N03",
    dominioNombre: "Medidas de Rendimiento de la Gerencia (MPM)",
    enunciado: "¿Cada MPM declarada contiene justificación del por qué proporciona información útil y anclaje al subtotal IFRS más comparable?",
    referenciaNormativa: "IFRS 18 - Párrafos MPM",
    esCritica: true,
    riesgoBase: 8,
    evidenciaEsperada: "Extracto de Memoria Anual o Revelaciones en EEFF",
  },
];

const COTA_MAXIMA_PREGUNTAS = 80;

interface DiagnosticCanvasProps {
  onVolverConfiguracion?: () => void;
}

export default function DiagnosticCanvas({
  onVolverConfiguracion,
}: DiagnosticCanvasProps) {
  const {
    companyData,
    normativaSeleccionada,
    respuestas,
    preguntaActualIndex,
    timeboxRestante,
    setRespuesta,
    setPreguntaActualIndex,
    setTimeboxRestante,
    calcularScoring,
    calcularResultadoAssessment,
    reiniciarDiagnostico,
    setActiveView,
    evidencias,
    vincularEvidencia,
    desvincularEvidencia,
    propuestasIA,
  } = useAuditStore();

  const [finalizadoForzado, setFinalizadoForzado] = useState(false);
  const [isPendingSnapshot, startSnapshotTransition] = useTransition();
  const [snapshotGuardado, setSnapshotGuardado] = useState<AuditSnapshot | null>(null);
  const [errorSnapshot, setErrorSnapshot] = useState<string | null>(null);
  const [resumenSellado, setResumenSellado] = useState<ResumenSellado | null>(null);

  const resumenPrevioSellado = useMemo(
    () =>
      resumirSellado(
        respuestasSellables(respuestas, normativaSeleccionada, companyData.tamano, companyData.perfil),
        evidencias
      ),
    [respuestas, evidencias, normativaSeleccionada, companyData.tamano, companyData.perfil]
  );

  // Resumen sellado del banco SGPDP: se deriva del cálculo verificado del
  // tablero, de modo que ningún puntaje sellado use niveles no demostrados.
  // madurez y coberturaEvidencias van en porcentaje (0-100), la escala que
  // espera el historial de auditoría.
  const scoringSelladoVerificado = (sellables: RespuestaItemStore[]) => {
    const verificado = calcularResultadoAssessment("verificado");
    const vinculados = new Set(evidencias.flatMap((e) => e.controlesVinculados));
    const evaluadas = sellables.filter((r) => r.cumple !== "Pendiente");
    const sumaEvidenciaVerificada = evaluadas.reduce(
      (acc, r) => acc + (vinculados.has(r.preguntaId) ? r.evidenciaNivel : 0),
      0
    );
    return {
      madurez: verificado.scorePonderado,
      coberturaEvidencias:
        evaluadas.length > 0
          ? Math.round((sumaEvidenciaVerificada / evaluadas.length / 3) * 1000) / 10
          : 0,
      conformidadLegalBooleana: verificado.brechasCriticas === 0,
      riesgoResidual: Math.round((100 - verificado.scorePonderado) * 10) / 10,
      detalles: {
        brechasCriticas: verificado.brechasCriticas,
        preguntasRespondidas: evaluadas.length,
      },
    };
  };

  const handleCongelarSnapshot = () => {
    setErrorSnapshot(null);
    // Las respuestas del conjunto de referencia pueblan el tablero pero no son
    // declaraciones del auditor: sellarlas produciría un snapshot sin valor
    // probatorio con apariencia de auditoría cerrada.
    const respuestasPropias = respuestasSellables(
      respuestas,
      normativaSeleccionada,
      companyData.tamano,
      companyData.perfil
    );
    if (respuestasPropias.length === 0) {
      setErrorSnapshot(
        "No hay respuestas propias registradas. El tablero muestra el conjunto de referencia, que no puede sellarse como evidencia."
      );
      return;
    }

    const payload: NuevoSnapshotInput = {
      empresa: {
        razonSocial: companyData.razonSocial || "Organización en Auditoría",
        sector: companyData.sector || "General",
        tamano: companyData.tamano || "No especificado",
      },
      normativa: resolverNormativa(normativaSeleccionada).id,
      versionNormativa: "LOPDP-EC-2026.v1",
      // Solo se sella el nivel verificado: sin documento vinculado el control
      // queda en E0, aunque el auditor haya declarado un nivel superior.
      respuestasSnapshot: respuestasPropias.map((r) => {
        const vinculadas = evidencias.filter((e) =>
          e.controlesVinculados.includes(r.preguntaId)
        );
        const soporte =
          vinculadas.length > 0
            ? `Evidencias: ${vinculadas
                .map((e) => `${e.codigo} (SHA-256 ${huellaCorta(e.sha256)})`)
                .join(", ")}`
            : `Sin evidencia vinculada (nivel declarado: E${r.evidenciaNivel})`;
        return {
          id_pregunta: `P-${r.preguntaId}`,
          respuesta_afirmativa: r.cumple === "Conforme" || r.cumple === "Parcial",
          nivel_evidencia: vinculadas.length > 0 ? `E${r.evidenciaNivel}` : "E0",
          rationale: `Estado: ${r.cumple} | Criticidad: ${r.esCritica ? "Crítica" : "Normal"} | ${soporte}${
            r.preanalisis && r.cumple !== "Pendiente"
              ? ` | Pre-llenado con IA (${r.preanalisis.modelo}) sobre ${r.preanalisis.evidenciaCodigo}: propuesta ${r.preanalisis.decision} por el auditor`
              : ""
          }`,
        };
      }),
      scoringFinal: usaBancoSGPDP(normativaSeleccionada)
        ? scoringSelladoVerificado(respuestasPropias)
        : {
            madurez: scoring.madurezSPDP,
            coberturaEvidencias: (scoring.calidadEvidencias / 3) * 100,
            conformidadLegalBooleana: scoring.conformidadBooleana,
            riesgoResidual: scoring.riesgoResidualPorcentaje,
            detalles: {
              brechasCriticas: scoring.brechasCriticasAbiertas,
              preguntasRespondidas: scoring.totalRespondidas,
            },
          },
    };

    const resumen = resumirSellado(respuestasPropias, evidencias);

    startSnapshotTransition(async () => {
      const res = await congelarSnapshotAuditoria(payload);
      if (res.success && res.data) {
        setSnapshotGuardado(res.data);
        setResumenSellado(resumen);
      } else {
        setErrorSnapshot(res.error || "No se pudo congelar el snapshot.");
      }
    });
  };

  // Asegurar que el banco nunca exceda la cota de 80 preguntas
  // La talla de la ficha organizacional poda el banco SGPDP y fija la redacción
  // de cada control antes de formular ninguna pregunta (Doctrina 9).
  const tallaEmpresa = normalizarTamano(companyData.tamano);

  const preguntasLimitadas = useMemo<PreguntaAssessment[]>(() => {
    if (!usaBancoSGPDP(normativaSeleccionada)) {
      return BANCO_PREGUNTAS_NIIF18.slice(0, COTA_MAXIMA_PREGUNTAS);
    }
    return podarBancoPorTamano(BANCO_PREGUNTAS, tallaEmpresa, companyData.perfil)
      .slice(0, COTA_MAXIMA_PREGUNTAS)
      .map((p) => ({
        id: p.id,
        dominioId: p.dimensionId,
        dominioNombre: DIMENSION_POR_ID[p.dimensionId].nombre,
        enunciado: p.enunciadoVigente,
        referenciaNormativa: p.referenciaNormativa,
        esCritica: p.esCritica,
        riesgoBase: p.riesgoBase,
        evidenciaEsperada: p.evidenciaVigente,
        dimensionId: p.dimensionId,
        criticidad: p.criticidad,
        control: p.control,
      }));
  }, [normativaSeleccionada, tallaEmpresa]);

  const totalPreguntas = preguntasLimitadas.length;
  const indexSeguro = Math.min(preguntaActualIndex, totalPreguntas - 1);
  const preguntaActual = preguntasLimitadas[indexSeguro] || preguntasLimitadas[0];
  const esPrimeraPreguntaDimension = Boolean(
    preguntaActual.dimensionId &&
    preguntasLimitadas.findIndex((p) => p.dimensionId === preguntaActual.dimensionId) === indexSeguro
  );

  // Temporizador regresivo (Poka-Yoke de Tiempo 60 minutos)
  useEffect(() => {
    if (timeboxRestante <= 0 || finalizadoForzado) return;

    const timer = setInterval(() => {
      setTimeboxRestante((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          setFinalizadoForzado(true);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [timeboxRestante, finalizadoForzado, setTimeboxRestante]);

  // Formato mm:ss
  const formatoTiempo = (segundos: number) => {
    const mins = Math.floor(segundos / 60);
    const secs = segundos % 60;
    return `${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
  };

  // Respuesta actual de la pregunta
  // Las respuestas de referencia no se presentan como si el auditor las
  // hubiera dado: cada control arranca en blanco hasta que se conteste.
  const respuestaActual: RespuestaItemStore = respuestas.find(
    (r) => r.preguntaId === preguntaActual.id && !r.esReferencia
  ) || {
    preguntaId: preguntaActual.id,
    cumple: "Pendiente",
    evidenciaNivel: 0,
    esCritica: preguntaActual.esCritica,
    riesgoBase: preguntaActual.riesgoBase,
    pendienteValidacion: false,
  };

  const metadatosPregunta = {
    esCritica: preguntaActual.esCritica,
    riesgoBase: preguntaActual.riesgoBase,
    dimensionId: preguntaActual.dimensionId,
    criticidad: preguntaActual.criticidad,
    control: preguntaActual.control,
  };

  const controlConDimension = Boolean(preguntaActual.dimensionId);
  const evidenciasVinculadas = evidencias.filter((e) =>
    e.controlesVinculados.includes(preguntaActual.id)
  );
  const evidenciasDisponibles = evidencias.filter(
    (e) => !e.controlesVinculados.includes(preguntaActual.id)
  );
  const controlVerificado = evidenciasVinculadas.length > 0;

  // Si el auditor cambia por su cuenta lo que aceptó de una propuesta de la IA,
  // el rastro pasa de "aceptada" a "editada": lo sellado refleja su decisión final.
  const rastroTrasCambio = (cambia: boolean) =>
    cambia && respuestaActual.preanalisis?.decision === "aceptada"
      ? { preanalisis: { ...respuestaActual.preanalisis, decision: "editada" as const } }
      : {};

  const handleSeleccionarCumplimiento = (cumple: EstadoCumplimiento) => {
    // El nivel de evidencia no se toca si ya es coherente con el nuevo estado
    // (p. ej. venía en E2 y se pasa de Parcial a Conforme, donde E2 sigue
    // siendo válido). Solo se reajusta al mínimo del rango nuevo cuando el
    // valor actual quedaría en una combinación que se contradice a sí misma.
    const rango = cumple === "Pendiente" ? null : RANGO_EVIDENCIA_POR_CUMPLE[cumple];
    const dentroDelRango =
      !rango ||
      (respuestaActual.evidenciaNivel >= rango[0] && respuestaActual.evidenciaNivel <= rango[1]);
    const evidenciaCoherente = dentroDelRango ? respuestaActual.evidenciaNivel : rango[0];

    setRespuesta(preguntaActual.id, {
      ...metadatosPregunta,
      cumple,
      evidenciaNivel: evidenciaCoherente,
      pendienteValidacion: false,
      ...rastroTrasCambio(
        cumple !== respuestaActual.cumple || evidenciaCoherente !== respuestaActual.evidenciaNivel
      ),
    });
  };

  const handleSeleccionarEvidencia = (nivel: number) => {
    setRespuesta(preguntaActual.id, {
      ...metadatosPregunta,
      evidenciaNivel: nivel,
      ...rastroTrasCambio(nivel !== respuestaActual.evidenciaNivel),
    });
  };

  const controlParaAnalisis: ControlParaAnalisis = {
    control_id: preguntaActual.id,
    control: preguntaActual.control ?? preguntaActual.dominioNombre,
    enunciado: preguntaActual.enunciado,
    evidencia_esperada: preguntaActual.evidenciaEsperada,
    referencia_normativa: preguntaActual.referenciaNormativa,
  };

  // Aplica una propuesta de la IA solo tras la decisión explícita del auditor.
  // Nunca baja un nivel de evidencia que el auditor ya había declarado.
  const handleAplicarPropuesta = (propuesta: PropuestaIA, modo: "aceptada" | "editada") => {
    setRespuesta(preguntaActual.id, {
      ...metadatosPregunta,
      cumple: propuesta.estado === "Sin sustento" ? respuestaActual.cumple : propuesta.estado,
      evidenciaNivel: Math.max(respuestaActual.evidenciaNivel, propuesta.nivelEvidenciaMaximo),
      pendienteValidacion: false,
      preanalisis: {
        propuestaId: propuesta.id,
        evidenciaCodigo: propuesta.evidenciaCodigo,
        modelo: propuesta.modelo,
        decision: modo,
        fecha: new Date().toISOString(),
      },
    });
  };

  const propuestasPendientes = Object.values(propuestasIA).filter(
    (p) => p.decision === "pendiente"
  ).length;

  const handleMarcarPendiente = () => {
    setRespuesta(preguntaActual.id, {
      ...metadatosPregunta,
      cumple: "Pendiente",
      pendienteValidacion: true,
      // Una respuesta devuelta a "Pendiente" ya no es una propuesta aplicada.
      preanalisis: undefined,
    });
    // Avanzar de inmediato sin parar el reloj
    if (indexSeguro < totalPreguntas - 1) {
      setPreguntaActualIndex(indexSeguro + 1);
    }
  };

  const handleSiguiente = () => {
    if (indexSeguro < totalPreguntas - 1) {
      setPreguntaActualIndex(indexSeguro + 1);
    } else {
      setFinalizadoForzado(true);
    }
  };

  const handleAnterior = () => {
    if (indexSeguro > 0) {
      setPreguntaActualIndex(indexSeguro - 1);
    }
  };

  const estaFinalizado =
    finalizadoForzado || timeboxRestante <= 0 || indexSeguro >= totalPreguntas;

  // Cálculo del motor multidimensional
  // Se recalcula en cada render: la función del store es estable, así que
  // memoizarla por su referencia congelaba el resultado del primer render.
  const scoring = calcularScoring();

  const porcentajeProgreso = Math.min(
    100,
    Math.round(((indexSeguro + 1) / totalPreguntas) * 100)
  );

  return (
    <div className="max-w-4xl mx-auto space-y-5 font-sans">
      <AlertaDimension
        dimensionId={preguntaActual.dimensionId}
        esPrimeraPregunta={esPrimeraPreguntaDimension}
        activo={!estaFinalizado}
      />
      {/* ========================================================================= */}
      {/* BARRA SUPERIOR DE CONTROL: Poka-Yoke de Tiempo & Cota de 80 Preguntas    */}
      {/* ========================================================================= */}
      <div data-dimension={preguntaActual.dimensionId}
        className={`${dimensionCardStyles.identity} ${dimensionCardStyles.card} ${dimensionCardStyles.toolbarCard} border rounded-xl p-4 space-y-3`}>
        <div className={`${dimensionCardStyles.divider} flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b`}>
          <div className="flex items-center space-x-2.5">
            <div className={`${dimensionCardStyles.frame} ${dimensionCardStyles.iconTile} ${dimensionCardStyles.accentIcon} w-8 h-8 rounded-lg border flex items-center justify-center`}>
              <Layers className="w-4 h-4" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className={`${dimensionCardStyles.moduleBadge} text-[10px] font-mono uppercase font-bold tracking-wider px-2 py-0.5 rounded border`}>
                  Módulo 1: Assessment Adaptativo
                </span>
                <span className="text-zinc-600">|</span>
                <span className="text-xs text-zinc-400 font-mono">
                  {companyData.razonSocial || "Entidad en Evaluación"}
                </span>
              </div>
              <h2 className="text-sm font-bold text-white mt-0.5">
                {resolverNormativa(normativaSeleccionada).nombre}
              </h2>
            </div>
          </div>

          {/* Reloj de Cuenta Regresiva Timebox (60 min) */}
          <div className="flex items-center space-x-2 shrink-0">
            {propuestasPendientes > 0 && (
              <span
                className="text-[10px] font-mono font-semibold px-2 py-1 rounded-lg bg-[#9a3bf1]/15 text-[#9a3bf1] border border-[#9a3bf1]/30"
                title="Propuestas de la IA que aún no has aceptado, editado ni descartado"
              >
                {propuestasPendientes} propuesta{propuestasPendientes === 1 ? "" : "s"} de IA por revisar
              </span>
            )}
            {usaBancoSGPDP(normativaSeleccionada) && <PrellenadoMasivo />}
            <div
              className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg border font-mono text-xs ${
                timeboxRestante <= 300
                  ? "bg-[#ff1744]/15 border-[#ff1744]/50 text-[#ff1744] animate-pulse"
                  : timeboxRestante <= 600
                  ? "bg-amber-500/15 border-amber-500/40 text-amber-400"
                  : `bg-[#0a0a0c] text-zinc-300 ${dimensionCardStyles.frame}`
              }`}
              title="Temporizador Poka-Yoke: Cota de 60 minutos"
            >
              <Clock className="w-3.5 h-3.5" />
              <span className="font-semibold">{formatoTiempo(timeboxRestante)}</span>
              <span className="text-[10px] text-zinc-500">timebox</span>
            </div>
          </div>
        </div>

        {/* Barra de progreso vinculada a la dimensión activa */}
        <div className="space-y-1.5">
          <div className="flex items-center justify-between text-[11px] text-zinc-400 font-mono">
            <span>
              Progreso: Pregunta <strong className="text-white">{indexSeguro + 1}</strong> de{" "}
              <strong>{totalPreguntas}</strong>
            </span>
            <span className="text-zinc-400">
              {porcentajeProgreso}% Completado
            </span>
          </div>
          <div className={`${dimensionCardStyles.frame} ${dimensionCardStyles.progressTrack} w-full h-1.5 rounded-full overflow-hidden border`}>
            <div
              className={`${dimensionCardStyles.progressFill} h-full transition-all duration-300 rounded-full`}
              style={{ width: `${porcentajeProgreso}%` }}
            />
          </div>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* RENDERIZADO CONDICIONAL: Cuestionario Activo vs. Pantalla de Cierre      */}
      {/* ========================================================================= */}
      {!estaFinalizado ? (
        /* Tarjeta de la Pregunta Actual */
        <div data-dimension={preguntaActual.dimensionId}
          className={`${dimensionCardStyles.identity} ${dimensionCardStyles.card} ${dimensionCardStyles.questionCard} border rounded-xl p-6 space-y-6`}>
          {/* Cabecera de la Pregunta */}
          <div className="space-y-2">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <span className={`${dimensionCardStyles.dimensionBadge} text-[10px] font-mono px-2 py-0.5 rounded border`}>
                {preguntaActual.dominioId} · {preguntaActual.dominioNombre}
              </span>

              <div className="flex items-center space-x-2">
                {preguntaActual.esCritica ? (
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-[#ff1744]/15 text-[#ff1744] border border-[#ff1744]/30 font-mono flex items-center">
                    <AlertTriangle className="w-3 h-3 mr-1" />
                    Control Crítico Bloqueante
                  </span>
                ) : (
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-zinc-800 text-zinc-400">
                    Control Estándar
                  </span>
                )}
                <span className="text-[10px] font-mono text-zinc-500">
                  Riesgo Base: {preguntaActual.riesgoBase}/10
                </span>
              </div>
            </div>

            <h3 className="text-base font-semibold text-white leading-relaxed pt-1">
              {preguntaActual.enunciado}
            </h3>
            <p className="text-sm leading-relaxed text-zinc-700 dark:text-zinc-300">
              <span className="font-semibold text-sky-700 dark:text-sky-300">Ejemplo: </span>
              {ejemploDePregunta(preguntaActual.id, preguntaActual.evidenciaEsperada)}
            </p>

            <div className="flex items-center space-x-2 text-xs text-zinc-400 font-mono pt-1">
              <span className="text-[#3892f3]">§</span>
              <span>{preguntaActual.referenciaNormativa}</span>
            </div>
          </div>

          {/* ===================================================================== */}
          {/* CONTROL 1: Evaluación Booleana (Conforme, Parcial, No Conforme)       */}
          {/* ===================================================================== */}
          <div className={`${dimensionCardStyles.divider} space-y-2.5 pt-2 border-t`}>
            <div className="flex items-center justify-between">
              <label className="text-xs font-bold uppercase tracking-wider text-zinc-300 font-mono flex items-center">
                <ShieldCheck className="w-3.5 h-3.5 mr-1.5 text-[#9a3bf1]" />
                1. Evaluación de Conformidad
              </label>
              <span className="text-[10px] text-zinc-500 font-mono">
                Estado: <strong className="text-zinc-300">{respuestaActual.cumple}</strong>
              </span>
            </div>

            <div
              className="grid grid-cols-1 sm:grid-cols-3 gap-2.5"
              role="group"
              aria-label="Evaluación de conformidad del control"
            >
              {(["Conforme", "Parcial", "No Conforme"] as EstadoCumplimiento[]).map(
                (opcion) => {
                  const seleccionado = respuestaActual.cumple === opcion;
                  return (
                    <button
                      key={opcion}
                      type="button"
                      aria-pressed={seleccionado}
                      onClick={() => handleSeleccionarCumplimiento(opcion)}
                      className={`px-4 py-3 rounded-lg border text-xs font-semibold flex items-center justify-center space-x-2 transition cursor-pointer ${
                        seleccionado
                          ? opcion === "Conforme"
                            ? "bg-[#00c853]/15 text-[#00c853] border-[#00c853]/50 shadow-[0_0_10px_rgba(0,200,83,0.2)]"
                            : opcion === "Parcial"
                            ? "bg-amber-500/15 text-amber-400 border-amber-500/50 shadow-[0_0_10px_rgba(255,179,0,0.2)]"
                            : "bg-[#ff1744]/15 text-[#ff1744] border-[#ff1744]/50 shadow-[0_0_10px_rgba(255,23,68,0.2)]"
                          : "bg-[#0a0a0c] hover:bg-[#1e1e24] text-zinc-400 hover:text-zinc-200 border-[#26262b]"
                      }`}
                    >
                      <span className="w-2 h-2 rounded-full bg-current" />
                      <span>{opcion}</span>
                    </button>
                  );
                }
              )}
            </div>
          </div>

          {/* ===================================================================== */}
          {/* CONTROL 2: Soporte Documental E0-E3 (Doctrina 3 del PRD)               */}
          {/* ===================================================================== */}
          <div className={`${dimensionCardStyles.divider} space-y-2.5 pt-2 border-t`}>
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
              <label className="text-xs font-bold uppercase tracking-wider text-zinc-300 font-mono flex items-center">
                <FileCheck2 className="w-3.5 h-3.5 mr-1.5 text-[#3892f3]" />
                2. Nivel de Soporte Documental (Doctrina 3: Evidencias)
              </label>
              <div className="flex items-center gap-2 flex-wrap sm:justify-end">
                {controlConDimension &&
                  (controlVerificado ? (
                    <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-[#00c853]/15 text-[#00c853] border border-[#00c853]/30 flex items-center">
                      <BadgeCheck className="w-3 h-3 mr-1" />
                      Verificado
                    </span>
                  ) : respuestaActual.evidenciaNivel > 0 ? (
                    <span
                      className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-[#ffab00]/15 text-[#ffab00] border border-[#ffab00]/30 flex items-center"
                      title="Sin documento vinculado, este control se sella como E0"
                    >
                      <AlertTriangle className="w-3 h-3 mr-1" />
                      Declarado · sin documento
                    </span>
                  ) : null)}
                <span className="text-[10px] text-zinc-500 font-mono">
                  Evidencia requerida: {preguntaActual.evidenciaEsperada}
                </span>
              </div>
            </div>

            <div
              className="grid grid-cols-2 sm:grid-cols-4 gap-2"
              role="group"
              aria-label="Nivel de soporte documental"
            >
              {(() => {
                // El rango vigente restringe qué niveles de evidencia son
                // coherentes con la conformidad ya declarada, para no poder
                // registrar combinaciones que se contradicen a sí mismas (p.
                // ej. "No Conforme" sostenido en evidencia "Auditable /
                // Certificado"). Sin conformidad declarada (Pendiente), no
                // hay nada que el nivel de evidencia pueda contradecir.
                const rangoVigente =
                  respuestaActual.cumple === "Pendiente"
                    ? null
                    : RANGO_EVIDENCIA_POR_CUMPLE[respuestaActual.cumple];
                return [
                  { nivel: 0, tag: "E0", label: "Sin Soporte", sub: "Mera autodeclaración" },
                  { nivel: 1, tag: "E1", label: "Borrador / Política", sub: "Documento preliminar" },
                  { nivel: 2, tag: "E2", label: "Evidencia Operativa", sub: "Registros y ejecución" },
                  { nivel: 3, tag: "E3", label: "Auditable / Certificado", sub: "Validación externa" },
                ].map((item) => {
                  const seleccionado = respuestaActual.evidenciaNivel === item.nivel;
                  const fueraDeRango =
                    !!rangoVigente &&
                    (item.nivel < rangoVigente[0] || item.nivel > rangoVigente[1]);
                  return (
                    <button
                      key={item.nivel}
                      type="button"
                      disabled={fueraDeRango}
                      aria-pressed={seleccionado}
                      title={
                        fueraDeRango
                          ? `No coherente con "${respuestaActual.cumple}": elige entre E${rangoVigente![0]} y E${rangoVigente![1]}.`
                          : undefined
                      }
                      onClick={() => handleSeleccionarEvidencia(item.nivel)}
                      className={`p-2.5 rounded-lg border text-left transition flex flex-col justify-between space-y-1 ${
                        fueraDeRango
                          ? "bg-[#0a0a0c] text-zinc-600 border-[#1c1c20] opacity-40 cursor-not-allowed"
                          : seleccionado
                          ? "bg-[#1e1e24] text-white border-[#9a3bf1] shadow-[0_0_8px_rgba(154,59,241,0.25)] cursor-pointer"
                          : "bg-[#0a0a0c] hover:bg-[#18181d] text-zinc-400 hover:text-zinc-200 border-[#26262b] cursor-pointer"
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span
                          className={`text-xs font-mono font-bold px-1.5 py-0.5 rounded ${
                            seleccionado
                              ? "bg-[#9a3bf1] text-white"
                              : "bg-zinc-800 text-zinc-400"
                          }`}
                        >
                          {item.tag}
                        </span>
                        <span className="text-[10px] font-mono text-zinc-500">
                          {item.nivel}.0
                        </span>
                      </div>
                      <div>
                        <div className="text-[11px] font-semibold text-zinc-200 truncate">
                          {item.label}
                        </div>
                        <div className="text-[9px] text-zinc-500 truncate">{item.sub}</div>
                      </div>
                    </button>
                  );
                });
              })()}
            </div>

            {controlConDimension && respuestaActual.evidenciaNivel >= 1 && (
              <DropEvidencia
                key={`${preguntaActual.id}-${respuestaActual.evidenciaNivel}`}
                preguntaId={preguntaActual.id}
                nivel={respuestaActual.evidenciaNivel}
                evidenciaEsperada={preguntaActual.evidenciaEsperada}
                tieneEvidencia={controlVerificado}
              />
            )}

            {controlConDimension && (
              <div className={`${dimensionCardStyles.frame} ${dimensionCardStyles.evidencePanel} rounded-lg border p-3 space-y-2.5`}>
                <div className="flex items-center justify-between gap-2">
                  <span className="text-[10px] font-mono uppercase font-bold tracking-wider text-zinc-500 flex items-center">
                    <Link2 className="w-3 h-3 mr-1.5 text-[#3892f3]" />
                    Evidencias vinculadas ({evidenciasVinculadas.length})
                  </span>
                  {!controlVerificado && (
                    <span className="text-[10px] font-mono text-zinc-500">
                      Sin documento vinculado se sella como E0
                    </span>
                  )}
                </div>

                {evidenciasVinculadas.length > 0 && (
                  <ul className="space-y-1.5">
                    {evidenciasVinculadas.map((e) => (
                      <li
                        key={e.id}
                        className={`${dimensionCardStyles.frame} ${dimensionCardStyles.evidenceRow} flex items-center gap-2 px-2.5 py-1.5 rounded-md border`}
                      >
                        <span className="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded bg-[#3892f3]/15 text-[#3892f3] border border-[#3892f3]/30 shrink-0">
                          {e.codigo}
                        </span>
                        <span
                          className="text-[11px] text-zinc-200 truncate flex-1 min-w-0"
                          title={e.nombreArchivo}
                        >
                          {e.nombreArchivo}
                        </span>
                        <span
                          className="text-[10px] font-mono text-zinc-500 shrink-0 hidden sm:inline"
                          title={e.sha256}
                        >
                          SHA-256 {huellaCorta(e.sha256)}…
                        </span>
                        <button
                          type="button"
                          onClick={() => desvincularEvidencia(e.id, preguntaActual.id)}
                          className="p-1 rounded text-zinc-500 hover:text-[#ff1744] hover:bg-[#ff1744]/10 transition cursor-pointer shrink-0"
                          title="Desvincular de este control"
                          aria-label={`Desvincular ${e.codigo}`}
                        >
                          <Unlink className="w-3.5 h-3.5" />
                        </button>
                      </li>
                    ))}
                  </ul>
                )}

                {evidenciasDisponibles.length > 0 ? (
                  <select
                    value=""
                    onChange={(ev) => {
                      if (ev.target.value) {
                        vincularEvidencia(ev.target.value, preguntaActual.id);
                      }
                    }}
                    className="w-full px-2.5 py-1.5 rounded-md bg-[#141417] border border-[#26262b] text-[11px] text-zinc-300 font-mono focus:outline-none focus:border-[#3892f3] cursor-pointer"
                    aria-label="Vincular evidencia registrada"
                  >
                    <option value="">Vincular evidencia registrada…</option>
                    {evidenciasDisponibles.map((e) => (
                      <option key={e.id} value={e.id}>
                        {e.codigo} · {e.nombreArchivo} · {huellaCorta(e.sha256)}
                      </option>
                    ))}
                  </select>
                ) : (
                  <p className="text-[10px] font-mono text-zinc-500">
                    {evidencias.length === 0
                      ? respuestaActual.evidenciaNivel === 0
                        ? "Selecciona E1, E2 o E3 para habilitar la carga de un documento en esta pregunta."
                        : "Sube un documento en el campo de esta pregunta para vincularlo al control."
                      : "Todas las evidencias registradas ya están vinculadas a este control."}
                  </p>
                )}
              </div>
            )}

            {controlConDimension && controlVerificado && (
              <PanelPreanalisis
                key={preguntaActual.id}
                control={controlParaAnalisis}
                onAplicar={handleAplicarPropuesta}
              />
            )}
          </div>

          {/* ===================================================================== */}
          {/* BOTONES DE NAVEGACIÓN Y CRITERIO DE CIERRE TÉCNICO                   */}
          {/* ===================================================================== */}
          <div className={`${dimensionCardStyles.divider} flex flex-col sm:flex-row items-center justify-between pt-4 border-t gap-3`}>
            {/* Botón Poka-Yoke: Marcar como Pendiente de Validación */}
            <button
              type="button"
              onClick={handleMarcarPendiente}
              className="w-full sm:w-auto px-3.5 py-2 rounded-lg bg-[#0a0a0c] hover:bg-[#1e1e24] text-zinc-400 hover:text-amber-400 border border-[#26262b] hover:border-amber-500/40 text-xs transition flex items-center justify-center space-x-1.5 cursor-pointer"
              title="Avanza rápido sin pausar el reloj en controles complejos"
            >
              <BookmarkCheck className="w-3.5 h-3.5 text-amber-500" />
              <span>Pendiente de Validación</span>
            </button>

            {/* Controles de Avance Secuencial */}
            <div className="flex items-center space-x-2.5 w-full sm:w-auto justify-end">
              <button
                type="button"
                onClick={handleAnterior}
                disabled={indexSeguro === 0}
                className="px-3 py-2 rounded-lg bg-[#0a0a0c] hover:bg-[#1e1e24] text-zinc-300 border border-[#26262b] text-xs transition flex items-center space-x-1 disabled:opacity-30 disabled:pointer-events-none cursor-pointer"
              >
                <ChevronLeft className="w-4 h-4" />
                <span>Anterior</span>
              </button>

              <button
                type="button"
                onClick={handleSiguiente}
                className="btn-render-primary px-5 py-2 rounded-lg text-xs font-semibold flex items-center space-x-1.5 cursor-pointer shadow-md"
              >
                <span>
                  {indexSeguro === totalPreguntas - 1
                    ? "Finalizar Evaluación"
                    : "Siguiente"}
                </span>
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      ) : (
        /* ======================================================================= */
        /* PANTALLA DE CIERRE: Informe de Scoring Multidimensional Cuádruple       */
        /* ======================================================================= */
        <div className="bg-[#141417] border border-[#26262b] rounded-xl p-6 shadow-sm space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-[#26262b] gap-2">
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-[10px] font-bold uppercase font-mono px-2 py-0.5 rounded bg-[#00c853]/15 text-[#00c853] border border-[#00c853]/30">
                  Resultado del diagnóstico
                </span>
                <span className="text-zinc-500 text-xs">|</span>
                <span className="text-zinc-400 text-xs font-mono">
                  {timeboxRestante <= 0 ? "Tiempo agotado (00:00)" : "Evaluación concluida"}
                </span>
              </div>
              <h2 className="text-lg font-bold text-white mt-1">
                Resultado del diagnóstico de protección de datos · {companyData.razonSocial || "Organización"}
              </h2>
              <p className="text-xs text-zinc-400 mt-1">
                Estas cuatro medidas resumen cómo está la organización frente a la ley de protección de datos personales.
              </p>
            </div>

            <button
              type="button"
              onClick={() => {
                setFinalizadoForzado(false);
                reiniciarDiagnostico();
              }}
              className="px-3 py-1.5 rounded-lg bg-[#0a0a0c] hover:bg-[#1e1e24] text-zinc-300 border border-[#26262b] text-xs transition flex items-center space-x-1.5 cursor-pointer"
            >
              <RotateCcw className="w-3.5 h-3.5 text-[#9a3bf1]" />
              <span>Reiniciar Cuestionario</span>
            </button>
          </div>

          {/* Grid de las 4 Dimensiones Obligatorias */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* DIMENSIÓN 1: Conformidad Legal Booleana Bloqueante */}
            <div className="p-5 rounded-xl bg-[#0a0a0c] border border-[#26262b] space-y-2">
              <div className="flex items-center justify-between text-xs font-mono text-zinc-400">
                <span>1 · Cumplimiento de la ley</span>
                <ShieldCheck className="w-4 h-4 text-[#9a3bf1]" />
              </div>

              <div className="pt-1">
                <div
                  className={`text-base font-bold ${
                    !scoring.conformidadBooleana
                      ? "text-[#ff1744] flex items-center space-x-1.5"
                      : "text-[#00c853]"
                  }`}
                >
                  {!scoring.conformidadBooleana && (
                    <AlertTriangle className="w-4 h-4 shrink-0" />
                  )}
                  <span>
                    {scoring.conformidadBooleana ? "Cumple" : "No cumple: hay incumplimientos críticos"}
                  </span>
                </div>

                <p className="text-[11px] text-zinc-400 mt-1 leading-relaxed">
                  {!scoring.conformidadBooleana
                    ? `Se encontraron ${scoring.brechasCriticasAbiertas} incumplimiento(s) crítico(s): controles obligatorios marcados como «No Conforme». Mientras no se corrijan, no se puede afirmar que la organización cumple la ley.`
                    : `Resultado favorable: ${scoring.porcentajeConformidad}% de cumplimiento en los controles revisados.`}
                </p>
              </div>
            </div>

            {/* DIMENSIÓN 2: Nivel de Madurez SPDP (0 al 3) */}
            <div className="p-5 rounded-xl bg-[#0a0a0c] border border-[#26262b] space-y-2">
              <div className="flex items-center justify-between text-xs font-mono text-zinc-400">
                <span>2 · Nivel de madurez</span>
                <Award className="w-4 h-4 text-amber-400" />
              </div>

              <div className="pt-1">
                <div className="text-base font-bold text-white flex items-center space-x-2">
                  <span>{describirNivelMadurez(scoring.madurezNivelEtiqueta)}</span>
                  <span className="text-xs font-mono px-2 py-0.5 rounded bg-[#1e1e24] text-amber-400 border border-[#26262b]">
                    {scoring.madurezSPDP.toFixed(2)} / 3.00
                  </span>
                </div>

                <p className="text-[11px] text-zinc-400 mt-1 leading-relaxed">
                  {scoring.brechasCriticasAbiertas > 0
                    ? "El nivel no puede pasar de 1 mientras existan incumplimientos críticos sin corregir, aunque el resto de los controles vaya bien."
                    : "Combina qué tanto se cumple la ley y qué tan bien está respaldado con documentos. Mientras más cerca de 3, más madura es la gestión."}
                </p>
              </div>
            </div>

            {/* DIMENSIÓN 3: Calidad de Evidencias (E0-E3) */}
            <div className="p-5 rounded-xl bg-[#0a0a0c] border border-[#26262b] space-y-2">
              <div className="flex items-center justify-between text-xs font-mono text-zinc-400">
                <span>3 · Respaldo con documentos</span>
                <FileCheck2 className="w-4 h-4 text-[#3892f3]" />
              </div>

              <div className="pt-1">
                <div className="text-base font-bold text-white flex items-center space-x-2">
                  <span>Promedio: {scoring.calidadEvidenciasEtiqueta}</span>
                  <span className="text-xs font-mono px-2 py-0.5 rounded bg-[#1e1e24] text-sky-400 border border-[#26262b]">
                    {scoring.calidadEvidencias.toFixed(2)} / 3.00
                  </span>
                </div>

                <p className="text-[11px] text-zinc-400 mt-1 leading-relaxed">
                  {describirRespaldoDocumental(scoring.calidadEvidencias)} La escala va de E0 (ningún documento) a E3
                  (validado por un tercero). Sin documento, una respuesta cuenta solo como declaración.
                </p>
              </div>
            </div>

            {/* DIMENSIÓN 4: % de Riesgo Residual */}
            <div className="p-5 rounded-xl bg-[#0a0a0c] border border-[#26262b] space-y-2">
              <div className="flex items-center justify-between text-xs font-mono text-zinc-400">
                <span>4 · Riesgo que queda</span>
                <Sparkles className="w-4 h-4 text-[#9a3bf1]" />
              </div>

              <div className="pt-1">
                <div className="text-base font-bold text-white flex items-center space-x-2">
                  <span
                    className={
                      scoring.riesgoResidualPorcentaje > 40
                        ? "text-[#ff1744]"
                        : scoring.riesgoResidualPorcentaje > 20
                        ? "text-amber-400"
                        : "text-[#00c853]"
                    }
                  >
                    {scoring.riesgoResidualPorcentaje}%
                  </span>
                  <span className={`text-xs font-mono ${describirExposicion(scoring.riesgoResidualPorcentaje).clase}`}>
                    {describirExposicion(scoring.riesgoResidualPorcentaje).texto}
                  </span>
                </div>

                <p className="text-[11px] text-zinc-400 mt-1 leading-relaxed">
                  Parte del riesgo que sigue sin cubrir, después de considerar lo que ya se cumple y los documentos que lo
                  respaldan. Mientras más bajo, mejor.
                </p>
              </div>
            </div>
          </div>

          {/* Banner de Snapshot Sellado con Éxito */}
          {snapshotGuardado && (
            <div className="p-4 rounded-xl bg-[#00c853]/10 border border-[#00c853]/30 text-zinc-900 dark:text-zinc-100 text-xs shadow-xs space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <span className="w-2 h-2 rounded-full bg-[#00c853] animate-ping" />
                  <strong className="text-[#00c853] flex items-center font-bold">
                    <ShieldCheck className="w-4 h-4 mr-1" />
                    Snapshot Inmutable Sellado Exitosamente (Doctrina 10)
                  </strong>
                </div>
                <button
                  type="button"
                  onClick={() => setActiveView("auditoria")}
                  className="px-2.5 py-1 rounded bg-[#00c853] hover:bg-[#00b248] text-black text-[11px] font-bold flex items-center space-x-1 transition cursor-pointer"
                >
                  <GitCommit className="w-3 h-3" />
                  <span>Ver en Historial de Auditorías →</span>
                </button>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 pt-1 border-t border-[#00c853]/20 text-[11px] font-mono">
                <div>
                  <span className="text-zinc-500">ID Invariable:</span>{" "}
                  <span className="font-semibold text-white">{snapshotGuardado.id}</span>
                </div>
                <div>
                  <span className="text-zinc-500">Fecha Cierre:</span>{" "}
                  <span>{new Date(snapshotGuardado.fechaCierre).toLocaleString()}</span>
                </div>
                <div className="truncate">
                  <span className="text-zinc-500">Sello SHA-256:</span>{" "}
                  <span className="text-zinc-400" title={snapshotGuardado.sha256Seal}>
                    {snapshotGuardado.sha256Seal?.slice(0, 16)}...
                  </span>
                </div>
              </div>

              {resumenSellado && (
                <p className="pt-1 border-t border-[#00c853]/20 text-[11px] font-mono text-zinc-300">
                  <span className="text-[#00c853] font-semibold">
                    {resumenSellado.verificados} control(es) sellados como verificados
                  </span>
                  {" · "}
                  <span
                    className={
                      resumenSellado.degradados > 0
                        ? "text-[#ffab00] font-semibold"
                        : "text-zinc-400"
                    }
                  >
                    {resumenSellado.degradados} degradado(s) a E0 por falta de evidencia vinculada
                  </span>
                  {resumenSellado.sinSoporte > 0 &&
                    ` · ${resumenSellado.sinSoporte} declarado(s) en E0`}
                </p>
              )}
            </div>
          )}

          {!snapshotGuardado && resumenPrevioSellado.verificados + resumenPrevioSellado.degradados + resumenPrevioSellado.sinSoporte > 0 && (
            <div
              className={`flex items-start gap-2.5 p-3 rounded-lg border text-[11px] ${
                resumenPrevioSellado.degradados > 0
                  ? "bg-[#ffab00]/[0.06] border-[#ffab00]/30"
                  : "bg-[#0a0a0c] border-[#26262b]"
              }`}
            >
              <FileCheck2
                className={`w-4 h-4 shrink-0 mt-0.5 ${
                  resumenPrevioSellado.degradados > 0 ? "text-[#ffab00]" : "text-[#3892f3]"
                }`}
              />
              <p className="text-zinc-300 leading-relaxed">
                El snapshot registra solo niveles verificados.{" "}
                <span className="font-mono font-semibold text-[#00c853]">
                  {resumenPrevioSellado.verificados}
                </span>{" "}
                control(es) se sellarán con su nivel declarado por tener evidencia vinculada;{" "}
                <span
                  className={`font-mono font-semibold ${
                    resumenPrevioSellado.degradados > 0 ? "text-[#ffab00]" : "text-zinc-400"
                  }`}
                >
                  {resumenPrevioSellado.degradados}
                </span>{" "}
                con nivel declarado superior a E0 se sellarán como E0 por no tener documento vinculado.
              </p>
            </div>
          )}

          {/* Alerta de Error en Snapshot */}
          {errorSnapshot && (
            <div className="flex items-center space-x-2 p-3 rounded-lg bg-[#ff1744]/10 border border-[#ff1744]/40 text-[#ff1744] text-xs">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span className="flex-1">{errorSnapshot}</span>
              <button
                type="button"
                onClick={() => setErrorSnapshot(null)}
                className="text-xs underline hover:opacity-80 cursor-pointer"
              >
                Cerrar
              </button>
            </div>
          )}

          {/* Botones de Retorno y Planes de Acción */}
          <div className="flex flex-col sm:flex-row items-center justify-between pt-4 border-t border-[#26262b] gap-3">
            <div className="flex items-center space-x-2 w-full sm:w-auto">
              {onVolverConfiguracion && (
                <button
                  type="button"
                  onClick={onVolverConfiguracion}
                  className="px-4 py-2.5 rounded-lg bg-[#0a0a0c] hover:bg-[#1e1e24] text-zinc-300 border border-[#26262b] text-xs transition flex items-center justify-center space-x-1.5 cursor-pointer"
                >
                  <SlidersHorizontal className="w-3.5 h-3.5 text-[#9a3bf1]" />
                  <span>Configuración</span>
                </button>
              )}

              <button
                type="button"
                onClick={() => setActiveView("auditoria")}
                className="px-4 py-2.5 rounded-lg bg-[#0a0a0c] hover:bg-[#1e1e24] text-zinc-300 border border-[#26262b] text-xs transition flex items-center justify-center space-x-1.5 cursor-pointer"
              >
                <GitCommit className="w-3.5 h-3.5 text-[#9a3bf1]" />
                <span>Historial</span>
              </button>
            </div>

            <div className="flex items-center space-x-3 w-full sm:w-auto">
              <button
                type="button"
                onClick={() => {
                  setFinalizadoForzado(false);
                  setPreguntaActualIndex(0);
                }}
                className="w-full sm:w-auto px-4 py-2.5 rounded-lg bg-[#141417] hover:bg-[#1e1e24] border border-[#26262b] text-zinc-300 text-xs transition flex items-center justify-center space-x-1.5 cursor-pointer"
              >
                <span>Revisar Respuestas</span>
              </button>

              <button
                type="button"
                onClick={handleCongelarSnapshot}
                disabled={isPendingSnapshot}
                className="w-full sm:w-auto px-5 py-2.5 rounded-lg bg-gradient-to-r from-[#9a3bf1] to-[#3892f3] text-white text-xs font-semibold flex items-center justify-center space-x-2 transition cursor-pointer shadow-md hover:opacity-95 disabled:opacity-50"
              >
                <Lock className="w-3.5 h-3.5" />
                <span>{isPendingSnapshot ? "Sellando Snapshot..." : "Sellar Snapshot Inmutable"}</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

