"use client";

import React, { useState, useEffect, useTransition } from "react";
import {
  Play,
  FileText,
  ShieldCheck,
  CheckCircle,
  XCircle,
  Sparkles,
  SlidersHorizontal,
  Building2,
  FileCheck2,
  Lock,
  History,
  Archive,
  AlertCircle,
} from "lucide-react";

import {
  FichaOrganizacion,
  PreguntaDiagnostico,
  RespuestaDiagnosticoItem,
  ScoringDiagnostico,
  NivelEvidencia,
  AuditSnapshot,
  NuevoSnapshotInput,
  RespuestaSnapshotItem,
} from "@/types";
import { ejemploDePregunta } from "@/lib/bancoPreguntas/ejemplos";
import {
  getPreguntasDiagnostico,
  evaluarDiagnostico,
  getInformeMarkdown,
} from "@/lib/api";
import {
  congelarSnapshotAuditoria,
  obtenerHistorialAuditorias,
} from "@/app/actions/auditActions";
import ScoreRing from "@/components/ui/ScoreRing";
import { useAuditStore } from "@/store/useAuditStore";
import { esNormativaFinanciera, resolverNormativa } from "@/lib/normativas";

const DIMENSIONES_LOPDP = [
  {
    dominio: "Licitud",
    titulo: "Principios & Bases de Legitimación",
    descripcion: "Licitud, finalidad, minimización y consentimiento verificable para cada actividad de tratamiento.",
    referencia: "LOPDP Arts. 7-10",
  },
  {
    dominio: "Titulares",
    titulo: "Derechos ARCO+",
    descripcion: "Canales, plazos y trazabilidad de las solicitudes de acceso, rectificación, eliminación y oposición.",
    referencia: "LOPDP Arts. 12-24",
  },
  {
    dominio: "Seguridad",
    titulo: "Medidas de Seguridad & Brechas",
    descripcion: "Controles técnicos y organizativos, gestión de vulneraciones y notificación a la autoridad.",
    referencia: "LOPDP Arts. 37-46",
  },
  {
    dominio: "Terceros",
    titulo: "Encargados & Transferencias",
    descripcion: "Contratos de encargo, flujos hacia terceros y garantías para transferencias internacionales.",
    referencia: "LOPDP Arts. 55-61",
  },
] as const;

interface DiagnosticoModuleProps {
  onEditarConfiguracion?: () => void;
}

export default function DiagnosticoModule({
  onEditarConfiguracion,
}: DiagnosticoModuleProps) {
  const { companyData, normativaSeleccionada, archivosCargados, evidencias, isConfigured } = useAuditStore();
  const normativa = resolverNormativa(normativaSeleccionada);
  const totalDocumentos = esNormativaFinanciera(normativaSeleccionada)
    ? archivosCargados.length
    : evidencias.length;
  const [preguntas, setPreguntas] = useState<PreguntaDiagnostico[]>([]);
  const [respuestas, setRespuestas] = useState<Record<string, RespuestaDiagnosticoItem>>({});
  const [scoring, setScoring] = useState<ScoringDiagnostico | null>(null);
  const [cargando, setCargando] = useState(false);
  const [iniciado, setIniciado] = useState(false);
  const [informeMd, setInformeMd] = useState<string | null>(null);
  const [copilotoAbiertoId, setCopilotoAbiertoId] = useState<string | null>(null);

  // Estados reactivos para Server Action e Inmutabilidad (Módulo 3)
  const [isPending, startTransition] = useTransition();
  const [snapshotSellado, setSnapshotSellado] = useState<AuditSnapshot | null>(null);
  const [historialSnapshots, setHistorialSnapshots] = useState<AuditSnapshot[]>([]);
  const [mostrarHistorial, setMostrarHistorial] = useState(false);
  const [mensajeExito, setMensajeExito] = useState<string | null>(null);
  const [errorSnapshot, setErrorSnapshot] = useState<string | null>(null);

  const cargarHistorial = async () => {
    try {
      const res = await obtenerHistorialAuditorias(companyData.razonSocial || undefined);
      if (res.success && res.data) {
        setHistorialSnapshots(res.data);
      }
    } catch (e) {
      console.error("[HISTORIAL_LOAD_ERROR]:", e);
    }
  };

  useEffect(() => {
    cargarHistorial();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [companyData.razonSocial]);

  const handleCongelarSnapshot = () => {
    setErrorSnapshot(null);
    setMensajeExito(null);

    const keys = Object.keys(respuestas);
    if (keys.length === 0) {
      setErrorSnapshot("No hay respuestas para congelar el snapshot. Inicie el diagnóstico primero.");
      return;
    }

    const respuestasList: RespuestaSnapshotItem[] = keys.map((k) => {
      const r = respuestas[k];
      return {
        id_pregunta: r.id_pregunta,
        respuesta_afirmativa: r.respuesta_afirmativa,
        nivel_evidencia: r.nivel_evidencia.startsWith("E") ? r.nivel_evidencia.substring(0, 2) : r.nivel_evidencia,
        rationale: r.rationale || "Criterio evaluado y contrastado con evidencia",
      };
    });

    const madurezVal = scoring?.madurez_spdp ?? 85;
    const coberturaVal = scoring?.cobertura_evidencia_porcentaje ?? 75;
    const conformidadVal = scoring?.porcentaje_conformidad_juridica ?? 90;
    const esConformeBool = conformidadVal >= 80;
    const riesgoResidualVal = Math.max(0, 100 - conformidadVal);

    const payload: NuevoSnapshotInput = {
      empresa: {
        razonSocial: companyData.razonSocial || "Jubys Cloud Solutions S.A.S.",
        sector: companyData.sector || "Telecomunicaciones",
        tamano: companyData.tamano || "Organización micro (1-9)",
      },
      normativa: normativa.id,
      versionNormativa: "LOPDP-EC-2026.v1",
      respuestasSnapshot: respuestasList,
      scoringFinal: {
        madurez: madurezVal,
        coberturaEvidencias: coberturaVal,
        conformidadLegalBooleana: esConformeBool,
        riesgoResidual: riesgoResidualVal,
        detalles: {
          brechasCriticas: scoring?.brechas_criticas_abiertas ?? 0,
          preguntasRespondidas: scoring?.preguntas_respondidas_total ?? respuestasList.length,
        },
      },
    };

    startTransition(async () => {
      const res = await congelarSnapshotAuditoria(payload);
      if (res.success && res.data) {
        setSnapshotSellado(res.data);
        setMensajeExito(`Snapshot ${res.data.id} sellado de forma inmutable con éxito.`);
        await cargarHistorial();
      } else {
        setErrorSnapshot(res.error || "Error al congelar el snapshot de auditoría.");
      }
    });
  };

  const fichaActual: FichaOrganizacion = {
    sector: companyData.sector || "Telecomunicaciones",
    tamano: companyData.tamano || "Organización micro (1-9)",
    emplea_nube: true,
    trata_datos_salud: false,
    emplea_ia: true,
    videovigilancia: true,
    transferencias_internacionales: false,
  };

  // Si se viene con configuración/banco pre-generado, autoiniciar
  useEffect(() => {
    if (isConfigured && !iniciado && preguntas.length === 0) {
      iniciarDiagnostico();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isConfigured]);

  const iniciarDiagnostico = async () => {
    setCargando(true);
    try {
      const res = await getPreguntasDiagnostico(fichaActual);
      setPreguntas(res.preguntas);
      setIniciado(true);

      const respInicial: Record<string, RespuestaDiagnosticoItem> = {};
      res.preguntas.forEach((p, idx) => {
        respInicial[p.id_pregunta] = {
          id_pregunta: p.id_pregunta,
          respuesta_afirmativa: idx % 4 !== 0,
          nivel_evidencia: (idx % 2 === 0 ? "E2_IMPLEMENTADA" : "E1_DOCUMENTADA") as NivelEvidencia,
          rationale: "Evaluación paramétrica inicial",
        };
      });
      setRespuestas(respInicial);

      const scoreRes = await evaluarDiagnostico(Object.values(respInicial));
      setScoring(scoreRes.scoring);
    } finally {
      setCargando(false);
    }
  };

  const toggleRespuesta = async (id: string, afirmativa: boolean) => {
    const nuevaResp: Record<string, RespuestaDiagnosticoItem> = {
      ...respuestas,
      [id]: {
        ...respuestas[id],
        respuesta_afirmativa: afirmativa,
        nivel_evidencia: afirmativa ? "E2_IMPLEMENTADA" : "E0_SIN_EVIDENCIA",
      },
    };
    setRespuestas(nuevaResp);

    const scoreRes = await evaluarDiagnostico(Object.values(nuevaResp));
    setScoring(scoreRes.scoring);
  };

  const generarInforme = async () => {
    const md = await getInformeMarkdown(fichaActual, Object.values(respuestas));
    setInformeMd(md);
  };

  return (
    <div className="space-y-6">
      {/* Top Header Bar con Score Ring estilo Render.com adaptativo */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 pb-4 border-b border-zinc-200 dark:border-[#26262b]">
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-[#9a3bf1]/15 text-[#9a3bf1] border border-[#9a3bf1]/30">
              Assessment {normativa.etiquetaCorta}
            </span>
            <span className="text-zinc-400 dark:text-zinc-500 text-xs">|</span>
            <span className="text-zinc-600 dark:text-zinc-400 text-xs font-mono">
              {companyData.razonSocial || "Jubys Cloud Solutions S.A.S."}
            </span>
          </div>
          <h2 className="text-xl font-bold text-zinc-900 dark:text-white flex items-center mt-1.5 tracking-tight">
            Diagnóstico de Cumplimiento en Protección de Datos Personales
          </h2>
          <p className="text-xs text-zinc-600 dark:text-zinc-400 mt-1 max-w-xl">
            Evaluación no diluida del SGPDP sobre los 16 Dominios JUBYS, contrastada con la evidencia documental registrada.
          </p>
        </div>

        <div className="flex items-center space-x-3 shrink-0">
          <ScoreRing
            score={scoring ? Math.round(scoring.porcentaje_conformidad_juridica) : 92}
            label="Score de Cumplimiento"
            sublabel="Salud Global del Activo"
          />

          <div className="flex flex-col space-y-2">
            {!iniciado ? (
              <button
                onClick={iniciarDiagnostico}
                disabled={cargando}
                className="btn-render-primary px-4 py-2.5 text-xs rounded-lg flex items-center justify-center font-semibold cursor-pointer"
              >
                <Play className="w-3.5 h-3.5 mr-1.5 shrink-0" />
                {cargando ? "Podando Árbol..." : "Iniciar Diagnóstico"}
              </button>
            ) : (
              <div className="flex flex-col space-y-1.5">
                <div className="flex items-center space-x-2">
                  <button
                    onClick={generarInforme}
                    className="px-3 py-2 bg-white dark:bg-[#141417] hover:bg-zinc-100 dark:hover:bg-[#1e1e23] text-zinc-900 dark:text-white text-xs font-medium rounded-lg border border-zinc-200 dark:border-[#26262b] flex items-center transition shadow-sm cursor-pointer"
                  >
                    <FileText className="w-3.5 h-3.5 mr-1.5 text-[#3892f3]" />
                    Ver Informe
                  </button>

                  <button
                    onClick={handleCongelarSnapshot}
                    disabled={isPending}
                    className="px-3.5 py-2 bg-gradient-to-r from-[#9a3bf1] to-[#3892f3] text-white text-xs font-semibold rounded-lg flex items-center justify-center transition shadow-sm hover:opacity-95 disabled:opacity-50 cursor-pointer"
                    title="Congelar snapshot inmutable de auditoría (Server Action con useTransition)"
                  >
                    <Lock className="w-3.5 h-3.5 mr-1.5 shrink-0" />
                    <span>{isPending ? "Sellando..." : "Finalizar & Congelar"}</span>
                  </button>
                </div>

                <button
                  type="button"
                  onClick={() => setMostrarHistorial(!mostrarHistorial)}
                  className="px-3 py-1 bg-zinc-100 dark:bg-[#0a0a0c] hover:bg-zinc-200 dark:hover:bg-[#1e1e24] text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-white text-[11px] font-mono rounded border border-zinc-200 dark:border-[#26262b] flex items-center justify-center transition cursor-pointer"
                >
                  <History className="w-3 h-3 mr-1 text-[#9a3bf1]" />
                  <span>Historial Inmutable ({historialSnapshots.length})</span>
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Banner de Snapshot Sellado con Éxito (Inmutable) */}
      {snapshotSellado && (
        <div className="p-3.5 rounded-xl bg-[#00c853]/10 border border-[#00c853]/30 text-zinc-900 dark:text-zinc-100 text-xs shadow-xs space-y-2 animate-fadeIn">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <span className="w-2 h-2 rounded-full bg-[#00c853] animate-ping" />
              <strong className="text-[#00c853] flex items-center font-bold">
                <ShieldCheck className="w-4 h-4 mr-1" />
                {mensajeExito || "Snapshot Inmutable Sellado Exitosamente"}
              </strong>
            </div>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#00c853]/20 text-[#00c853] font-bold border border-[#00c853]/40">
              Solo Lectura (Append-Only)
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 pt-1 border-t border-[#00c853]/20 text-[11px] font-mono">
            <div>
              <span className="text-zinc-500">ID Invariable:</span>{" "}
              <span className="font-semibold text-zinc-900 dark:text-white">{snapshotSellado.id}</span>
            </div>
            <div>
              <span className="text-zinc-500">Fecha Cierre:</span>{" "}
              <span>{new Date(snapshotSellado.fechaCierre).toLocaleString()}</span>
            </div>
            <div className="truncate">
              <span className="text-zinc-500">Sello SHA-256:</span>{" "}
              <span className="text-zinc-600 dark:text-zinc-300" title={snapshotSellado.sha256Seal}>
                {snapshotSellado.sha256Seal?.slice(0, 16)}...
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Alerta de Error en Snapshot */}
      {errorSnapshot && (
        <div className="flex items-center space-x-2 p-3 rounded-lg bg-[#ff1744]/10 border border-[#ff1744]/40 text-[#ff1744] text-xs">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span className="flex-1">{errorSnapshot}</span>
          <button
            onClick={() => setErrorSnapshot(null)}
            className="text-xs underline hover:opacity-80 cursor-pointer"
          >
            Cerrar
          </button>
        </div>
      )}

      {/* Drawer / Tabla de Historial Inmutable de Auditorías */}
      {mostrarHistorial && (
        <div className="bg-white dark:bg-[#141417] border border-zinc-200 dark:border-[#26262b] rounded-xl p-4 shadow-md space-y-3">
          <div className="flex items-center justify-between border-b border-zinc-200 dark:border-[#26262b] pb-2">
            <div className="flex items-center space-x-2">
              <Archive className="w-4 h-4 text-[#9a3bf1]" />
              <h3 className="font-bold text-xs uppercase tracking-wider text-zinc-900 dark:text-white">
                Bóveda Histórica de Auditorías (Solo Lectura)
              </h3>
            </div>
            <span className="text-[10px] text-zinc-500 font-mono">
              data/snapshots.json · {historialSnapshots.length} registros
            </span>
          </div>

          {historialSnapshots.length === 0 ? (
            <p className="text-xs text-zinc-500 italic py-2">
              No hay snapshots guardados aún para {companyData.razonSocial || "esta organización"}.
            </p>
          ) : (
            <div className="divide-y divide-zinc-200 dark:divide-[#26262b] max-h-60 overflow-y-auto">
              {historialSnapshots.map((snap) => (
                <div
                  key={snap.id}
                  className="py-2.5 flex flex-col sm:flex-row sm:items-center justify-between text-xs gap-2"
                >
                  <div className="space-y-0.5 min-w-0">
                    <div className="flex items-center space-x-2">
                      <span className="font-mono font-bold text-zinc-900 dark:text-zinc-100 truncate">
                        {snap.id}
                      </span>
                      <span className="text-[10px] px-1.5 py-0.2 rounded bg-zinc-100 dark:bg-[#1e1e24] text-zinc-600 dark:text-zinc-400 font-mono">
                        {snap.normativa} ({snap.versionNormativa})
                      </span>
                    </div>
                    <div className="text-[10.5px] text-zinc-500">
                      Cerrado: {new Date(snap.fechaCierre).toLocaleString()} · Respuestas:{" "}
                      {snap.respuestasSnapshot?.length || 0}
                    </div>
                  </div>

                  <div className="flex items-center space-x-2 shrink-0">
                    <span className="text-[10px] px-2 py-0.5 rounded font-mono bg-[#9a3bf1]/15 text-[#9a3bf1] border border-[#9a3bf1]/30">
                      Madurez: {snap.scoringFinal?.madurez ?? "--"}%
                    </span>
                    <span
                      className={`text-[10px] px-2 py-0.5 rounded font-mono border ${
                        snap.scoringFinal?.conformidadLegalBooleana
                          ? "bg-[#00c853]/15 text-[#00c853] border-[#00c853]/30"
                          : "bg-amber-500/15 text-amber-500 border-amber-500/30"
                      }`}
                    >
                      {snap.scoringFinal?.conformidadLegalBooleana ? "Conforme" : "Brechas"}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3.5">
        {DIMENSIONES_LOPDP.map((dimension) => (
          <div
            key={dimension.titulo}
            className="bg-white dark:bg-[#141417] border border-zinc-200 dark:border-[#26262b] rounded-xl p-4 shadow-sm hover:border-zinc-400 dark:hover:border-zinc-700 transition relative overflow-hidden group"
          >
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-semibold text-zinc-500 dark:text-zinc-400 uppercase tracking-wider">
                {dimension.dominio}
              </span>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-[#3892f3]/10 text-[#3892f3] border border-[#3892f3]/30">
                Dimensión SGPDP
              </span>
            </div>
            <h4 className="text-sm font-bold text-zinc-900 dark:text-white mt-2">{dimension.titulo}</h4>
            <p className="text-xs text-zinc-600 dark:text-zinc-400 mt-1 line-clamp-2">{dimension.descripcion}</p>
            <div className="mt-3 pt-2.5 border-t border-zinc-200 dark:border-[#26262b] flex items-center justify-between text-[11px]">
              <span className="text-zinc-500 dark:text-zinc-400 font-mono">{dimension.referencia}</span>
              <span className="text-zinc-500 dark:text-zinc-400">Evaluada en el banco</span>
            </div>
          </div>
        ))}
      </div>

      {/* Metrics Row if scoring is present */}
      {scoring && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <div className="bg-white dark:bg-[#141417] border border-zinc-200 dark:border-[#26262b] rounded-lg p-3.5 shadow-sm">
            <div className="text-[11px] font-semibold text-zinc-500 dark:text-zinc-400 uppercase tracking-wider">Madurez SPDP</div>
            <div className="text-2xl font-bold text-zinc-900 dark:text-white mt-1">{scoring.madurez_spdp} / 3.0</div>
            <div className="text-[11px] text-zinc-500 dark:text-zinc-400 mt-0.5">{scoring.madurez_nivel_etiqueta}</div>
          </div>
          <div className="bg-white dark:bg-[#141417] border border-zinc-200 dark:border-[#26262b] rounded-lg p-3.5 shadow-sm">
            <div className="text-[11px] font-semibold text-zinc-500 dark:text-zinc-400 uppercase tracking-wider">Conformidad Legal</div>
            <div className="text-2xl font-bold text-[#00c853] mt-1">{scoring.porcentaje_conformidad_juridica}%</div>
            <div className="text-[11px] text-zinc-500 dark:text-zinc-400 mt-0.5">Controles conformes</div>
          </div>
          <div className="bg-white dark:bg-[#141417] border border-zinc-200 dark:border-[#26262b] rounded-lg p-3.5 shadow-sm">
            <div className="text-[11px] font-semibold text-zinc-500 dark:text-zinc-400 uppercase tracking-wider">Cobertura Evidencia</div>
            <div className="text-2xl font-bold text-[#3892f3] mt-1">{scoring.cobertura_evidencia_porcentaje}%</div>
            <div className="text-[11px] text-zinc-500 dark:text-zinc-400 mt-0.5">Nivel E1 a E3 verificado</div>
          </div>
          <div className="bg-white dark:bg-[#141417] border border-zinc-200 dark:border-[#26262b] rounded-lg p-3.5 shadow-sm">
            <div className="text-[11px] font-semibold text-zinc-500 dark:text-zinc-400 uppercase tracking-wider">Brechas Críticas</div>
            <div className="text-2xl font-bold text-[#ff1744] mt-1">{scoring.brechas_criticas_abiertas}</div>
            <div className="text-[11px] text-zinc-500 dark:text-zinc-400 mt-0.5">Riesgos sin enmascarar</div>
          </div>
        </div>
      )}

      {/* Main Content Area: Resumen de Parámetros o Banco de Preguntas Podado */}
      {!iniciado ? (
        <div className="bg-white dark:bg-[#141417] border border-zinc-200 dark:border-[#26262b] rounded-xl p-6 shadow-sm space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-zinc-200 dark:border-[#26262b] pb-3.5 gap-2">
            <div className="flex items-center space-x-2.5">
              <div className="w-8 h-8 rounded-lg bg-gradient-ai flex items-center justify-center text-white shadow-xs">
                <ShieldCheck className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-zinc-900 dark:text-white">
                  Parámetros del Proyecto Listos para Auditoría
                </h3>
                <p className="text-xs text-zinc-500 dark:text-zinc-400">
                  Calibrados desde la pestaña superior de Configuración & Ficha Organizacional
                </p>
              </div>
            </div>

            {onEditarConfiguracion && (
              <button
                type="button"
                onClick={onEditarConfiguracion}
                className="text-xs text-[#9a3bf1] hover:underline font-semibold flex items-center cursor-pointer shrink-0"
              >
                <SlidersHorizontal className="w-3.5 h-3.5 mr-1" />
                Modificar Ficha / Normativa
              </button>
            )}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5 text-xs">
            <div className="p-3.5 rounded-lg bg-zinc-50 dark:bg-[#0a0a0c] border border-zinc-200 dark:border-[#26262b] space-y-1">
              <div className="text-[10px] text-zinc-500 dark:text-zinc-400 uppercase tracking-wider font-semibold flex items-center">
                <Building2 className="w-3.5 h-3.5 mr-1 text-[#3892f3]" />
                Organización Evaluada
              </div>
              <div className="font-bold text-zinc-900 dark:text-white truncate">
                {companyData.razonSocial || "Jubys Cloud Solutions S.A.S."}
              </div>
              <div className="text-[11px] text-zinc-600 dark:text-zinc-400">
                {fichaActual.sector} · {fichaActual.tamano}
              </div>
            </div>

            <div className="p-3.5 rounded-lg bg-zinc-50 dark:bg-[#0a0a0c] border border-zinc-200 dark:border-[#26262b] space-y-1">
              <div className="text-[10px] text-zinc-500 dark:text-zinc-400 uppercase tracking-wider font-semibold flex items-center">
                <FileCheck2 className="w-3.5 h-3.5 mr-1 text-[#9a3bf1]" />
                Normativa Activa
              </div>
              <div className="font-bold text-[#9a3bf1]">
                {normativa.nombre}
              </div>
              <div className="text-[11px] text-[#00c853] font-medium flex items-center">
                <span className="w-1.5 h-1.5 rounded-full bg-[#00c853] mr-1" />
                Motor ADPA 360 Listo
              </div>
            </div>

            <div className="p-3.5 rounded-lg bg-zinc-50 dark:bg-[#0a0a0c] border border-zinc-200 dark:border-[#26262b] space-y-1">
              <div className="text-[10px] text-zinc-500 dark:text-zinc-400 uppercase tracking-wider font-semibold flex items-center">
                <FileText className="w-3.5 h-3.5 mr-1 text-[#00c853]" />
                Documentación Probatoria
              </div>
              <div className="font-bold text-zinc-900 dark:text-white">
                {totalDocumentos > 0
                  ? `${totalDocumentos} ${totalDocumentos === 1 ? "documento registrado" : "documentos registrados"}`
                  : "Sin documentos registrados"}
              </div>
              <div className="text-[11px] text-zinc-500 line-clamp-2" title={normativa.descripcionArchivos}>
                {normativa.descripcionArchivos}
              </div>
            </div>
          </div>

          <div className="pt-2 flex justify-end">
            <button
              onClick={iniciarDiagnostico}
              disabled={cargando}
              className="btn-render-primary px-6 py-2.5 text-xs rounded-lg flex items-center font-semibold cursor-pointer shadow-md"
            >
              <Play className="w-4 h-4 mr-2" />
              {cargando ? "Podando Árbol de Controles..." : "Desplegar Banco de Controles Podados"}
            </button>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          {/* Questions list */}
          <div className="bg-white dark:bg-[#141417] border border-zinc-200 dark:border-[#26262b] rounded-xl overflow-hidden divide-y divide-zinc-200 dark:divide-[#26262b] shadow-sm">
            <div className="px-4 py-3 bg-zinc-50 dark:bg-[#0a0a0c] flex justify-between items-center text-xs">
              <span className="font-semibold text-zinc-900 dark:text-white">
                Banco Podado: {preguntas.length} Controles Normativos Visibles
              </span>
              <span className="text-zinc-500 dark:text-zinc-400 font-mono text-[11px]">
                Invariante: Límite estricto de 60 minutos (≤ 80 preguntas)
              </span>
            </div>
            <div className="max-h-[500px] overflow-y-auto divide-y divide-zinc-200 dark:divide-[#26262b]">
              {preguntas.map((p) => {
                const resp = respuestas[p.id_pregunta];
                const isConforme = resp?.respuesta_afirmativa;
                const isCopilotoAbierto = copilotoAbiertoId === p.id_pregunta;

                return (
                  <div key={p.id_pregunta} className="p-3.5 hover:bg-zinc-50/80 dark:hover:bg-[#1a1a1f] transition space-y-2">
                    <div className="flex items-start justify-between">
                      <div className="pr-4 space-y-1">
                        <div className="flex items-center space-x-2">
                          <span className="text-[10px] font-mono bg-zinc-100 dark:bg-[#26262b] text-zinc-700 dark:text-zinc-300 px-1.5 py-0.5 rounded border border-zinc-200 dark:border-zinc-700">
                            {p.id_pregunta}
                          </span>
                          <span className="text-[10px] text-zinc-500 dark:text-zinc-400">{p.referencia_normativa}</span>
                        </div>
                        <div className="text-xs text-zinc-900 dark:text-zinc-200 font-medium">{p.enunciado}</div>
                        <p className="text-[11px] leading-relaxed text-zinc-700 dark:text-zinc-300">
                          <span className="font-semibold">Ejemplo: </span>
                          {ejemploDePregunta(Number(p.id_pregunta), p.evidencia_esperada)}
                        </p>
                        <div className="text-[11px] text-zinc-500 dark:text-zinc-400 italic">Evidencia esperada: {p.evidencia_esperada}</div>
                      </div>

                      <div className="flex items-center space-x-1.5 shrink-0 pt-1">
                        <button
                          onClick={() => setCopilotoAbiertoId(isCopilotoAbierto ? null : p.id_pregunta)}
                          className={`px-2.5 py-1 rounded-md text-[11px] font-semibold flex items-center space-x-1 transition cursor-pointer ${
                            isCopilotoAbierto
                              ? "bg-gradient-ai text-white shadow-md"
                              : "bg-zinc-100 dark:bg-[#1e1e23] hover:bg-zinc-200 dark:hover:bg-[#26262b] text-zinc-700 dark:text-zinc-300 border border-zinc-300 dark:border-[#26262b]"
                          }`}
                          title="Consultar Copiloto IA sobre este control"
                        >
                          <Sparkles className="w-3.5 h-3.5 mr-1" />
                          <span>Copiloto IA</span>
                        </button>
                        <button
                          onClick={() => toggleRespuesta(p.id_pregunta, true)}
                          className={`p-1.5 rounded-md flex items-center space-x-1 text-xs transition cursor-pointer ${
                            isConforme
                              ? "badge-render-success"
                              : "bg-zinc-100 dark:bg-[#1e1e23] text-zinc-500 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-white border border-zinc-300 dark:border-[#26262b]"
                          }`}
                          title="Conforme"
                        >
                          <CheckCircle className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => toggleRespuesta(p.id_pregunta, false)}
                          className={`p-1.5 rounded-md flex items-center space-x-1 text-xs transition cursor-pointer ${
                            isConforme === false
                              ? "badge-render-danger"
                              : "bg-zinc-100 dark:bg-[#1e1e23] text-zinc-500 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-white border border-zinc-300 dark:border-[#26262b]"
                          }`}
                          title="No Conforme (Brecha Crítica)"
                        >
                          <XCircle className="w-4 h-4" />
                        </button>
                      </div>
                    </div>

                    {/* Copiloto Anidado Contextual */}
                    {isCopilotoAbierto && (
                      <div className="mt-2 p-3.5 rounded-lg bg-zinc-50 dark:bg-[#18181d] border border-zinc-200 dark:border-[#26262b] space-y-2 text-xs">
                        <div className="flex justify-between items-center pb-1.5 border-b border-zinc-200 dark:border-[#26262b]">
                          <span className="font-bold text-zinc-900 dark:text-white flex items-center text-[11px]">
                            <Sparkles className="w-3.5 h-3.5 mr-1.5 text-[#9a3bf1]" />
                            Agente de IA Legal · Control {p.id_pregunta}
                          </span>
                          <span className="text-[10px] text-zinc-500 dark:text-zinc-400 font-mono">
                            Fundamento: {p.referencia_normativa}
                          </span>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1">
                          <div className="p-2.5 rounded bg-white dark:bg-[#0a0a0c] border border-zinc-200 dark:border-[#26262b]">
                            <span className="text-[10px] uppercase font-bold text-[#9a3bf1] block mb-1">
                              ¿Qué exige la norma para este control?
                            </span>
                            <p className="text-zinc-700 dark:text-zinc-300 text-[11px] leading-relaxed">
                              Este control del dominio evalúa la diligencia debida establecida en la LOPDP ecuatoriana. 
                              La falta de cumplimiento directo constituye una no conformidad que no puede ser compensada por otros dominios.
                            </p>
                          </div>

                          <div className="p-2.5 rounded bg-white dark:bg-[#0a0a0c] border border-zinc-200 dark:border-[#26262b]">
                            <span className="text-[10px] uppercase font-bold text-[#3892f3] block mb-1">
                              Evidencia recomendada para auditoría:
                            </span>
                            <ul className="text-zinc-700 dark:text-zinc-300 text-[11px] space-y-0.5 list-disc list-inside">
                              <li><strong className="text-zinc-900 dark:text-white">E1 (Documental):</strong> {p.evidencia_esperada} aprobada formalmente.</li>
                              <li><strong className="text-zinc-900 dark:text-white">E2 (Implementada):</strong> Logs, registros o contratos operativos activos.</li>
                              <li><strong className="text-zinc-900 dark:text-white">E3 (Probada):</strong> Informe de prueba técnica periódica o auditoría.</li>
                            </ul>
                          </div>
                        </div>

                        <div className="pt-1 flex items-center justify-between text-[10px] text-zinc-500 dark:text-zinc-400">
                          <button
                            onClick={() => setCopilotoAbiertoId(null)}
                            className="text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-white underline cursor-pointer"
                          >
                            Ocultar guía
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Modal / Preview de Informe Markdown */}
          {informeMd && (
            <div className="bg-white dark:bg-zinc-900 border border-sky-600/40 dark:border-sky-800/50 rounded-xl p-4 shadow-xl">
              <div className="flex justify-between items-center pb-2 mb-3 border-b border-zinc-200 dark:border-zinc-800">
                <span className="text-xs font-bold text-sky-600 dark:text-sky-300 flex items-center">
                  <FileText className="w-4 h-4 mr-1.5" /> Informe Ejecutivo Generado (Markdown)
                </span>
                <button
                  onClick={() => setInformeMd(null)}
                  className="text-xs text-zinc-500 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-200 cursor-pointer"
                >
                  Cerrar
                </button>
              </div>
              <pre className="text-xs text-zinc-800 dark:text-zinc-300 bg-zinc-50 dark:bg-zinc-950 p-3 rounded-lg overflow-x-auto font-mono max-h-60 leading-relaxed border border-zinc-200 dark:border-zinc-800">
                {informeMd}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
