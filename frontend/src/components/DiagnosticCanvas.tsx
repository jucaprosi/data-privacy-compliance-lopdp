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
  SlidersHorizontal,
  BookmarkCheck,
  Layers,
  Lock,
  GitCommit,
  Link2,
  Unlink,
  BadgeCheck,
} from "lucide-react";
import { useAuditStore, RespuestaItemStore } from "@/store/useAuditStore";
import { respuestasSellables } from "@/lib/diagnostico/indicadores";
import {
  ESCALONES_EVIDENCIA,
  NIVELES_ASIGNADOS,
  evidenciaDesdeEscalaAnterior,
  nivelAsignadoDe,
  nivelMinimoDeEstado,
} from "@/lib/diagnostico/escala";
import { IndicadoresSelladosVista } from "@/components/AuditHistory";
import {
  consultarHistorial,
  sellarDiagnostico,
  type ResultadoSellado,
} from "@/lib/diagnostico/clienteResultados";
import { puedeSellar, rolesDelUsuario } from "@/lib/diagnostico/roles";
import {
  BANCO_PREGUNTAS,
  podarBancoPorTamano,
  normalizarTamano,
  respuestasPendientes,
} from "@/lib/bancoPreguntas";
import { ejemploDePregunta } from "@/lib/bancoPreguntas/ejemplos";
import dimensionCardStyles from "@/components/DimensionIdentity.module.css";
import {
  DIMENSION_POR_ID,
  type DimensionId,
} from "@/lib/dimensionesSGPDP";
import { resolverNormativa, usaBancoSGPDP } from "@/lib/normativas";
import { etiquetaEstadoCumplimiento } from "@/lib/estadosCumplimiento";
import PerfilOperacionForm from "@/components/PerfilOperacionForm";
import type { EvidenciaDocumental } from "@/lib/evidencias/tipos";
import DropEvidencia from "@/components/evidencias/DropEvidencia";
import AlertaDimension from "@/components/AlertaDimension";
import PanelPreanalisis from "@/components/preanalisis/PanelPreanalisis";
import PrellenadoMasivo from "@/components/preanalisis/PrellenadoMasivo";
import type { ControlParaAnalisis, PropuestaIA } from "@/lib/preanalisis/tipos";

const huellaCorta = (sha256: string) => sha256.slice(0, 12);

function describirRespaldoDocumental(porcentaje: number): string {
  if (porcentaje >= 75) return "Respaldo sólido: la mayoría de las respuestas tiene registros de aplicación o revisión de la dirección.";
  if (porcentaje >= 50) return "Respaldo medio: hay documentos formales y algunos registros de aplicación.";
  if (porcentaje >= 25) return "Respaldo básico: hay correos, capturas o documentos iniciales.";
  return "Casi sin respaldo: la mayoría de las respuestas no tiene evidencia que las pruebe.";
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
    reiniciarDiagnostico,
    setActiveView,
    evidencias,
    vincularEvidencia,
    desvincularEvidencia,
    propuestasIA,
  } = useAuditStore();

  const [finalizadoForzado, setFinalizadoForzado] = useState(false);
  const [nivelEnfocado, setNivelEnfocado] = useState<number | null>(null);
  const [nivelSugerido, setNivelSugerido] = useState<{ preguntaId: number; nivel: number } | null>(null);
  const [isPendingSnapshot, startSnapshotTransition] = useTransition();
  const [resultadoSellado, setResultadoSellado] = useState<ResultadoSellado | null>(null);
  const [errorSnapshot, setErrorSnapshot] = useState<string | null>(null);

  // DIAG-03: solo el DPO responde y sella; los demás roles ven el diagnóstico en modo lectura.
  // Mientras no se conocen los roles, no se habilita la escritura.
  const [roles, setRoles] = useState<string[] | null>(null);
  const [dpoVigente, setDpoVigente] = useState<boolean | null>(null);
  useEffect(() => {
    let vigente = true;
    rolesDelUsuario().then((r) => {
      if (vigente) setRoles(r);
    });
    consultarHistorial()
      .then((h) => {
        if (vigente) setDpoVigente(h.dpo_vigente);
      })
      .catch(() => undefined);
    return () => {
      vigente = false;
    };
  }, []);
  const puedeResponder = roles !== null && puedeSellar(roles);

  const resumenPrevioSellado = useMemo(
    () =>
      resumirSellado(
        respuestasSellables(respuestas, normativaSeleccionada, companyData.tamano, companyData.perfil),
        evidencias
      ),
    [respuestas, evidencias, normativaSeleccionada, companyData.tamano, companyData.perfil]
  );

  // El servidor sella lo que tiene guardado (DIAG-03): las respuestas de la organización y su propio
  // cálculo. Desde aquí solo viaja el perfil de operación de la ficha, que el DPO confirma.
  const handleCongelarSnapshot = () => {
    setErrorSnapshot(null);
    const respuestasPropias = respuestasSellables(
      respuestas,
      normativaSeleccionada,
      companyData.tamano,
      companyData.perfil
    );
    if (respuestasPropias.length === 0) {
      setErrorSnapshot(
        "Todavía no hay respuestas suyas registradas. Lo que muestra el tablero es un ejemplo de referencia y no se puede guardar como resultado."
      );
      return;
    }
    startSnapshotTransition(async () => {
      try {
        setResultadoSellado(await sellarDiagnostico(companyData.perfil));
      } catch (err) {
        setErrorSnapshot(err instanceof Error ? err.message : "No se pudo guardar el resultado. Inténtelo de nuevo.");
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
    nivelAsignado: null,
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

  // El estado (Implementado, Parcial, No implementado) no se elige: lo deriva el servidor del nivel.
  const handleSeleccionarNivel = (nivelAsignado: number) => {
    if (!puedeResponder) return;
    setRespuesta(preguntaActual.id, {
      ...metadatosPregunta,
      nivelAsignado,
      pendienteValidacion: false,
      ...rastroTrasCambio(nivelAsignado !== respuestaActual.nivelAsignado),
    });
  };

  const handleSeleccionarEvidencia = (nivel: number) => {
    if (!puedeResponder) return;
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
    if (!puedeResponder) return;
    setRespuesta(preguntaActual.id, {
      ...metadatosPregunta,
      // La propuesta trae un estado, no un nivel: no fija el nivel. Se ofrece el mínimo del estado
      // como sugerencia y la persona lo confirma o elige otro.
      // El máximo propuesto viene de la escala anterior (E1 = documentado); se lleva a los cinco escalones.
      evidenciaNivel: Math.max(
        respuestaActual.evidenciaNivel,
        evidenciaDesdeEscalaAnterior(propuesta.nivelEvidenciaMaximo)
      ),
      pendienteValidacion: false,
      preanalisis: {
        propuestaId: propuesta.id,
        evidenciaCodigo: propuesta.evidenciaCodigo,
        modelo: propuesta.modelo,
        decision: modo,
        fecha: new Date().toISOString(),
      },
    });
    const sugerido = propuesta.estado === "Sin sustento" ? null : nivelMinimoDeEstado(propuesta.estado);
    setNivelSugerido(sugerido === null ? null : { preguntaId: preguntaActual.id, nivel: sugerido });
  };

  const propuestasPendientes = Object.values(propuestasIA).filter(
    (p) => p.decision === "pendiente"
  ).length;

  const handleMarcarPendiente = () => {
    if (!puedeResponder) return;
    setRespuesta(preguntaActual.id, {
      ...metadatosPregunta,
      nivelAsignado: null,
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

  // Compuerta: las preguntas del perfil de operación son obligatorias. Mientras
  // alguna siga sin responder no se muestra ninguna pregunta del diagnóstico.
  const perfilPendiente =
    usaBancoSGPDP(normativaSeleccionada) && respuestasPendientes(companyData.perfil) > 0;
  if (perfilPendiente) {
    return (
      <div className="max-w-4xl mx-auto space-y-4 font-sans">
        <div className="rounded-xl border border-[#ffab00]/40 bg-[#ffab00]/10 p-4 text-xs text-zinc-700 dark:text-zinc-200 leading-relaxed">
          <strong className="block text-sm mb-1">Antes de empezar, complete el Perfil de Operación</strong>
          Estas preguntas son obligatorias: definen qué controles se evaluarán en su organización. El diagnóstico
          comenzará automáticamente cuando responda todas con Sí o No.
        </div>
        <PerfilOperacionForm resaltarPendientes />
      </div>
    );
  }

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
                <span className="text-[var(--ui-texto-suave)]">|</span>
                <span className="text-xs text-[var(--ui-texto-suave)] font-mono">
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
            {usaBancoSGPDP(normativaSeleccionada) && puedeResponder && <PrellenadoMasivo />}
            <div
              className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg border font-mono text-xs ${
                timeboxRestante <= 300
                  ? "bg-[#ff1744]/15 border-[#ff1744]/50 text-[#ff1744] animate-pulse"
                  : timeboxRestante <= 600
                  ? "bg-amber-500/15 border-amber-500/40 text-amber-400"
                  : `bg-[var(--ui-campo)] text-white ${dimensionCardStyles.frame}`
              }`}
              title="Temporizador Poka-Yoke: Cota de 60 minutos"
            >
              <Clock className="w-3.5 h-3.5" />
              <span className="font-semibold">{formatoTiempo(timeboxRestante)}</span>
              <span className="text-[10px] text-[var(--ui-texto-suave)]">timebox</span>
            </div>
          </div>
        </div>

        {/* Barra de progreso vinculada a la dimensión activa */}
        <div className="space-y-1.5">
          <div className="flex items-center justify-between text-[11px] text-[var(--ui-texto-suave)] font-mono">
            <span>
              Progreso: Pregunta <strong className="text-white">{indexSeguro + 1}</strong> de{" "}
              <strong>{totalPreguntas}</strong>
            </span>
            <span className="text-[var(--ui-texto-suave)]">
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

      {roles !== null && !puedeResponder && (
        <div
          role="status"
          className="rounded-xl border border-[var(--ui-borde)] bg-[var(--ui-campo)] p-4 text-xs leading-relaxed"
        >
          <strong className="block text-sm mb-1">Modo lectura: el diagnóstico lo responde y lo sella el DPO</strong>
          {dpoVigente === false
            ? "Esta organización todavía no tiene un DPO con rol vigente. El administrador debe designarlo (puede ser una persona externa) para que el diagnóstico pueda responderse y sellarse."
            : "Puede revisar las respuestas y los resultados, pero no cambiarlas."}
        </div>
      )}

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
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[var(--ui-boton)] text-[var(--ui-texto-suave)]">
                    Control Estándar
                  </span>
                )}
                <span className="text-[10px] font-mono text-[var(--ui-texto-suave)]">
                  Riesgo Base: {preguntaActual.riesgoBase}/10
                </span>
              </div>
            </div>

            <h3 className="text-base font-semibold text-white leading-relaxed pt-1">
              {preguntaActual.enunciado}
            </h3>
            <p className="text-sm leading-relaxed text-white">
              <span className="font-semibold text-sky-700 dark:text-sky-300">Ejemplo: </span>
              {ejemploDePregunta(preguntaActual.id, preguntaActual.evidenciaEsperada)}
            </p>

            <div className="flex items-center space-x-2 text-xs text-[var(--ui-texto-suave)] font-mono pt-1">
              <span className="text-blue-700 dark:text-blue-300">§</span>
              <span>{preguntaActual.referenciaNormativa}</span>
            </div>
          </div>

          {/* ===================================================================== */}
          {/* CONTROL 1: Nivel de madurez SMARTCIDI 1 a 5 (DIAG-09). El estado se deriva. */}
          {/* ===================================================================== */}
          <fieldset disabled={!puedeResponder} className="m-0 min-w-0 border-0 p-0 space-y-6">
          <div className={`${dimensionCardStyles.divider} space-y-2.5 pt-2 border-t`}>
            <div className="flex items-center justify-between">
              <label id="etiqueta-nivel" className="text-xs font-bold uppercase tracking-wider text-white font-mono flex items-center">
                <ShieldCheck className="w-3.5 h-3.5 mr-1.5 text-[#9a3bf1]" />
                1. Nivel de madurez
              </label>
              <span className="text-[10px] text-[var(--ui-texto-suave)] font-mono">
                Estado (lo calcula el servidor):{" "}
                <strong data-testid="estado-derivado" className="text-white">
                  {etiquetaEstadoCumplimiento(respuestaActual.cumple)}
                </strong>
              </span>
            </div>

            <div
              className="grid grid-cols-2 sm:grid-cols-5 gap-2"
              role="radiogroup"
              aria-labelledby="etiqueta-nivel"
              onKeyDown={(e) => {
                const delta = e.key === "ArrowRight" || e.key === "ArrowDown" ? 1 : e.key === "ArrowLeft" || e.key === "ArrowUp" ? -1 : 0;
                if (!delta) return;
                e.preventDefault();
                const actual = respuestaActual.nivelAsignado ?? (delta > 0 ? 0 : NIVELES_ASIGNADOS.length + 1);
                const siguiente = Math.min(NIVELES_ASIGNADOS.length, Math.max(1, actual + delta));
                handleSeleccionarNivel(siguiente);
                setNivelEnfocado(siguiente);
                (e.currentTarget.querySelector(`[data-nivel="${siguiente}"]`) as HTMLElement | null)?.focus();
              }}
            >
              {NIVELES_ASIGNADOS.map((opcion) => {
                const seleccionado = respuestaActual.nivelAsignado === opcion.nivel;
                const puedeEntrar = respuestaActual.nivelAsignado == null ? opcion.nivel === 1 : seleccionado;
                return (
                  <button
                    key={opcion.nivel}
                    type="button"
                    role="radio"
                    aria-checked={seleccionado}
                    data-nivel={opcion.nivel}
                    tabIndex={puedeEntrar ? 0 : -1}
                    title={opcion.criterio}
                    onClick={() => handleSeleccionarNivel(opcion.nivel)}
                    onFocus={() => setNivelEnfocado(opcion.nivel)}
                    onBlur={() => setNivelEnfocado(null)}
                    className={`p-2.5 rounded-lg border text-left transition flex flex-col space-y-1 cursor-pointer ${
                      seleccionado
                        ? "bg-[var(--ui-boton)] text-white border-[var(--ui-primario)] shadow-[0_0_8px_rgba(154,59,241,0.25)]"
                        : "bg-[var(--ui-campo)] hover:bg-[var(--ui-boton)] text-[var(--ui-texto-suave)] hover:text-white border-[var(--ui-borde)]"
                    }`}
                  >
                    <span
                      className={`self-start text-xs font-mono font-bold px-1.5 py-0.5 rounded ${
                        seleccionado
                          ? "bg-[var(--ui-primario)] text-[var(--ui-primario-texto)]"
                          : "bg-[var(--ui-boton)] text-[var(--ui-texto-suave)]"
                      }`}
                    >
                      {opcion.nivel}
                    </span>
                    <span className="text-[11px] font-semibold">{opcion.corto}</span>
                  </button>
                );
              })}
            </div>
            {nivelSugerido?.preguntaId === preguntaActual.id &&
              respuestaActual.nivelAsignado !== nivelSugerido.nivel &&
              puedeResponder && (
                <div data-testid="nivel-sugerido" className="flex flex-wrap items-center gap-2 text-[11px] text-[var(--ui-texto-suave)]">
                  <span>
                    La propuesta de la IA sugiere como mínimo el nivel {nivelSugerido.nivel} (
                    {nivelAsignadoDe(nivelSugerido.nivel)?.nombre}). No se aplica hasta que lo confirmes.
                  </span>
                  <button
                    type="button"
                    onClick={() => {
                      handleSeleccionarNivel(nivelSugerido.nivel);
                      setNivelSugerido(null);
                    }}
                    className="px-2 py-1 rounded border border-[var(--ui-borde)] bg-[var(--ui-boton)] text-white font-semibold cursor-pointer"
                  >
                    Confirmar nivel {nivelSugerido.nivel}
                  </button>
                </div>
              )}
            {(() => {
              const visible = nivelAsignadoDe(nivelEnfocado ?? respuestaActual.nivelAsignado);
              return (
                <p data-testid="criterio-nivel" className="text-[11px] text-[var(--ui-texto-suave)] leading-relaxed min-h-[2.5em]">
                  {visible ? (
                    <>
                      <strong className="text-white">
                        Nivel {visible.nivel} · {visible.nombre}:
                      </strong>{" "}
                      {visible.criterio}
                    </>
                  ) : (
                    "Elige el nivel que describe cómo está este control hoy; aquí verás su criterio."
                  )}
                </p>
              );
            })()}
          </div>

          {/* ===================================================================== */}
          {/* CONTROL 2: Evidencia, cinco escalones 0-4 (Doctrina 3 del PRD)         */}
          {/* ===================================================================== */}
          <div className={`${dimensionCardStyles.divider} space-y-2.5 pt-2 border-t`}>
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
              <label id="etiqueta-evidencia" className="text-xs font-bold uppercase tracking-wider text-white font-mono flex items-center">
                <FileCheck2 className="w-3.5 h-3.5 mr-1.5 text-[#3892f3]" />
                2. Evidencia
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
                      title="Sin documento vinculado, este control se sella con evidencia 0 (verbal)"
                    >
                      <AlertTriangle className="w-3 h-3 mr-1" />
                      Declarado · sin documento
                    </span>
                  ) : null)}
                <span className="text-[10px] text-[var(--ui-texto-suave)] font-mono">
                  Evidencia requerida: {preguntaActual.evidenciaEsperada}
                </span>
              </div>
            </div>

            <div
              className="grid grid-cols-2 sm:grid-cols-5 gap-2"
              role="radiogroup"
              aria-labelledby="etiqueta-evidencia"
            >
              {ESCALONES_EVIDENCIA.map((item) => {
                const seleccionado = respuestaActual.evidenciaNivel === item.nivel;
                return (
                  <button
                    key={item.nivel}
                    type="button"
                    role="radio"
                    aria-checked={seleccionado}
                    data-evidencia={item.nivel}
                    title={item.nombre}
                    onClick={() => handleSeleccionarEvidencia(item.nivel)}
                    className={`p-2.5 rounded-lg border text-left transition flex flex-col justify-between space-y-1 cursor-pointer ${
                      seleccionado
                        ? "bg-[var(--ui-boton)] text-white border-[var(--ui-primario)] shadow-[0_0_8px_rgba(154,59,241,0.25)]"
                        : "bg-[var(--ui-campo)] hover:bg-[var(--ui-superficie-2)] text-[var(--ui-texto-suave)] hover:text-white border-[var(--ui-borde)]"
                    }`}
                  >
                    <span
                      className={`self-start text-xs font-mono font-bold px-1.5 py-0.5 rounded ${
                        seleccionado
                          ? "bg-[var(--ui-primario)] text-[var(--ui-primario-texto)]"
                          : "bg-[var(--ui-boton)] text-[var(--ui-texto-suave)]"
                      }`}
                    >
                      {item.nivel}
                    </span>
                    <div>
                      <div className="text-[11px] font-semibold">{item.corto}</div>
                      <div className="text-[9px] text-[var(--ui-texto-suave)]">{item.detalle}</div>
                    </div>
                  </button>
                );
              })}
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
                  <span className="text-[10px] font-mono uppercase font-bold tracking-wider text-[var(--ui-texto-suave)] flex items-center">
                    <Link2 className="w-3 h-3 mr-1.5 text-[#3892f3]" />
                    Evidencias vinculadas ({evidenciasVinculadas.length})
                  </span>
                  {!controlVerificado && (
                    <span className="text-[10px] font-mono text-[var(--ui-texto-suave)]">
                      Sin documento vinculado se sella con evidencia 0 (verbal)
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
                          className="text-[11px] text-white truncate flex-1 min-w-0"
                          title={e.nombreArchivo}
                        >
                          {e.nombreArchivo}
                        </span>
                        <span
                          className="text-[10px] font-mono text-[var(--ui-texto-suave)] shrink-0 hidden sm:inline"
                          title={e.sha256}
                        >
                          SHA-256 {huellaCorta(e.sha256)}…
                        </span>
                        <button
                          type="button"
                          onClick={() => desvincularEvidencia(e.id, preguntaActual.id)}
                          className="p-1 rounded text-[var(--ui-texto-suave)] hover:text-[#ff1744] hover:bg-[#ff1744]/10 transition cursor-pointer shrink-0"
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
                    className="w-full px-2.5 py-1.5 rounded-md bg-[var(--ui-superficie)] border border-[var(--ui-borde)] text-[11px] text-white font-mono focus:outline-none focus:border-[#3892f3] cursor-pointer"
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
                  <p className="text-[10px] font-mono text-[var(--ui-texto-suave)]">
                    {evidencias.length === 0
                      ? respuestaActual.evidenciaNivel === 0
                        ? "Selecciona un escalón de evidencia (del 1 al 4) para habilitar la carga de un documento en esta pregunta."
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
          </fieldset>

          {/* ===================================================================== */}
          {/* BOTONES DE NAVEGACIÓN Y CRITERIO DE CIERRE TÉCNICO                   */}
          {/* ===================================================================== */}
          <div className={`${dimensionCardStyles.divider} flex flex-col sm:flex-row items-center justify-between pt-4 border-t gap-3`}>
            {/* Botón Poka-Yoke: Marcar como Pendiente de Validación */}
            <button
              type="button"
              onClick={handleMarcarPendiente}
              disabled={!puedeResponder}
              className="disabled:opacity-40 disabled:pointer-events-none w-full sm:w-auto px-3.5 py-2 rounded-lg bg-[var(--ui-campo)] hover:bg-[var(--ui-boton)] text-[var(--ui-texto-suave)] hover:text-amber-400 border border-[var(--ui-borde)] hover:border-amber-500/40 text-xs transition flex items-center justify-center space-x-1.5 cursor-pointer"
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
                className="px-3 py-2 rounded-lg bg-[var(--ui-campo)] hover:bg-[var(--ui-boton)] text-white border border-[var(--ui-borde)] text-xs transition flex items-center space-x-1 disabled:opacity-30 disabled:pointer-events-none cursor-pointer"
              >
                <ChevronLeft className="w-4 h-4" />
                <span>Anterior</span>
              </button>

              <button
                type="button"
                onClick={handleSiguiente}
                className="bg-[var(--ui-primario)] text-[var(--ui-primario-texto)] hover:bg-[var(--ui-primario-hover)] px-5 py-2 rounded-lg text-xs font-semibold flex items-center space-x-1.5 cursor-pointer shadow-md"
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
        <div className="bg-[var(--ui-superficie)] border border-[var(--ui-borde)] rounded-xl p-6 shadow-sm space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-[var(--ui-borde)] gap-2">
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-[10px] font-bold uppercase font-mono px-2 py-0.5 rounded bg-[#00c853]/15 text-[#00c853] border border-[#00c853]/30">
                  Resultado del diagnóstico
                </span>
                <span className="text-[var(--ui-texto-suave)] text-xs">|</span>
                <span className="text-[var(--ui-texto-suave)] text-xs font-mono">
                  {timeboxRestante <= 0 ? "Tiempo agotado (00:00)" : "Evaluación concluida"}
                </span>
              </div>
              <h2 className="text-lg font-bold text-white mt-1">
                Resultado del diagnóstico de protección de datos · {companyData.razonSocial || "Organización"}
              </h2>
              <p className="text-xs text-[var(--ui-texto-suave)] mt-1">
                Estas cuatro medidas resumen cómo está la organización frente a la ley de protección de datos personales.
              </p>
            </div>

            <button
              type="button"
              onClick={() => {
                setFinalizadoForzado(false);
                reiniciarDiagnostico();
              }}
              className="px-3 py-1.5 rounded-lg bg-[var(--ui-campo)] hover:bg-[var(--ui-boton)] text-white border border-[var(--ui-borde)] text-xs transition flex items-center space-x-1.5 cursor-pointer"
            >
              <RotateCcw className="w-3.5 h-3.5 text-[#9a3bf1]" />
              <span>Reiniciar Cuestionario</span>
            </button>
          </div>

          {/* Grid de las 4 Dimensiones Obligatorias */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* DIMENSIÓN 1: Conformidad Legal Booleana Bloqueante */}
            <div className="p-5 rounded-xl bg-[var(--ui-campo)] border border-[var(--ui-borde)] space-y-2">
              <div className="flex items-center justify-between text-xs font-mono text-[var(--ui-texto-suave)]">
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

                <p className="text-[11px] text-[var(--ui-texto-suave)] mt-1 leading-relaxed">
                  {!scoring.conformidadBooleana
                    ? `Se encontraron ${scoring.brechasCriticasAbiertas} incumplimiento(s) crítico(s): controles obligatorios marcados como «No Implementado». Mientras no se corrijan, no se puede afirmar que la organización cumple la ley.`
                    : "Resultado favorable: no hay incumplimientos críticos abiertos en los controles revisados."}
                </p>
              </div>
            </div>

            {/* Respaldo con documentos: describe la evidencia, no la madurez (DIAG-08 R5) */}
            <div className="p-5 rounded-xl bg-[var(--ui-campo)] border border-[var(--ui-borde)] space-y-2">
              <div className="flex items-center justify-between text-xs font-mono text-[var(--ui-texto-suave)]">
                <span>2 · Respaldo con documentos</span>
                <FileCheck2 className="w-4 h-4 text-[#3892f3]" />
              </div>

              <div className="pt-1">
                <div className="text-base font-bold text-white flex items-center space-x-2">
                  <span>{scoring.respaldoDocumental} %</span>
                </div>

                <p className="text-[11px] text-[var(--ui-texto-suave)] mt-1 leading-relaxed">
                  {describirRespaldoDocumental(scoring.respaldoDocumental)} La escala va de 0 (verbal, sin evidencia) a 4
                  (auditada o revisada por la dirección). Los niveles de madurez se ven por dimensión al sellar.
                </p>
              </div>
            </div>
          </div>

          {/* Resultado sellado por el servidor (DIAG-03): lo que queda en firme */}
          {resultadoSellado && (
            <div
              role="status"
              className="p-4 rounded-xl bg-[var(--ui-campo)] border border-[var(--ui-borde)] text-xs space-y-3"
            >
              <div className="flex flex-wrap items-center justify-between gap-2">
                <strong className="badge-render-success px-2 py-1 rounded flex items-center font-bold">
                  <ShieldCheck className="w-4 h-4 mr-1" />
                  Resultado sellado n.º {resultadoSellado.secuencia}: no se puede editar ni borrar
                </strong>
                <button
                  type="button"
                  onClick={() => setActiveView("auditoria")}
                  className="px-2.5 py-1 rounded border border-[var(--ui-borde)] bg-[var(--ui-boton)] hover:bg-[var(--ui-boton-hover)] text-[11px] font-bold flex items-center space-x-1 transition cursor-pointer"
                >
                  <GitCommit className="w-3 h-3" />
                  <span>Ver en el historial →</span>
                </button>
              </div>
              <IndicadoresSelladosVista indicadores={resultadoSellado.indicadores} />
              <p className="text-[11px] font-mono text-[var(--ui-texto-suave)]">
                Sellado el {new Date(resultadoSellado.sellado_en).toLocaleString()} · código de verificación{" "}
                <span title={resultadoSellado.huella}>{resultadoSellado.huella.slice(0, 16)}…</span> ·{" "}
                {resultadoSellado.respuestas.filter((r) => r.con_documento).length} de{" "}
                {resultadoSellado.respuestas.length} control(es) con un documento que el servidor pudo comprobar; el resto
                se selló sin respaldo (evidencia 0, verbal).
              </p>
            </div>
          )}

          {!resultadoSellado && puedeResponder && resumenPrevioSellado.verificados + resumenPrevioSellado.degradados > 0 && (
            <div className="flex items-start gap-2.5 p-3 rounded-lg border text-[11px] bg-[var(--ui-campo)] border-[var(--ui-borde)]">
              <FileCheck2 className="w-4 h-4 shrink-0 mt-0.5 text-[var(--ui-texto-suave)]" />
              <p className="leading-relaxed">
                Al sellar, el servidor usa las respuestas guardadas de la organización y solo cuenta el respaldo de los
                controles cuyo documento puede comprobar; los demás se sellan sin respaldo (evidencia 0, verbal). Los documentos
                adjuntos en esta pantalla todavía se guardan solo en este navegador, así que los{" "}
                <span className="font-mono font-semibold">
                  {resumenPrevioSellado.verificados + resumenPrevioSellado.degradados}
                </span>{" "}
                control(es) con nivel de respaldo indicado se sellarán con evidencia 0 (verbal).
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
          <div className="flex flex-col sm:flex-row items-center justify-between pt-4 border-t border-[var(--ui-borde)] gap-3">
            <div className="flex items-center space-x-2 w-full sm:w-auto">
              {onVolverConfiguracion && (
                <button
                  type="button"
                  onClick={onVolverConfiguracion}
                  className="px-4 py-2.5 rounded-lg bg-[var(--ui-campo)] hover:bg-[var(--ui-boton)] text-white border border-[var(--ui-borde)] text-xs transition flex items-center justify-center space-x-1.5 cursor-pointer"
                >
                  <SlidersHorizontal className="w-3.5 h-3.5 text-[#9a3bf1]" />
                  <span>Configuración</span>
                </button>
              )}

              <button
                type="button"
                onClick={() => setActiveView("auditoria")}
                className="px-4 py-2.5 rounded-lg bg-[var(--ui-campo)] hover:bg-[var(--ui-boton)] text-white border border-[var(--ui-borde)] text-xs transition flex items-center justify-center space-x-1.5 cursor-pointer"
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
                className="w-full sm:w-auto px-4 py-2.5 rounded-lg bg-[var(--ui-superficie)] hover:bg-[var(--ui-boton)] border border-[var(--ui-borde)] text-white text-xs transition flex items-center justify-center space-x-1.5 cursor-pointer"
              >
                <span>Revisar Respuestas</span>
              </button>

              {puedeResponder && !resultadoSellado && (
                <button
                  type="button"
                  onClick={handleCongelarSnapshot}
                  disabled={isPendingSnapshot}
                  className="w-full sm:w-auto px-5 py-2.5 rounded-lg bg-[var(--ui-primario)] text-[var(--ui-primario-texto)] hover:bg-[var(--ui-primario-hover)] text-xs font-semibold flex items-center justify-center space-x-2 transition cursor-pointer shadow-md disabled:opacity-50"
                >
                  <Lock className="w-3.5 h-3.5" />
                  <span>{isPendingSnapshot ? "Sellando…" : "Guardar resultado definitivo"}</span>
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

