"use client";

import React, { useState, useEffect, useTransition, useCallback } from "react";
import {
  GitCommit,
  Clock,
  ShieldCheck,
  AlertCircle,
  Hash,
  FileText,
  CheckCircle2,
  XCircle,
  Lock,
  RefreshCw,
  Search,
  Building2,
  ChevronRight,
  X,
  ShieldAlert,
  Layers,
  Database,
  Check,
} from "lucide-react";
import { useAuditStore } from "@/store/useAuditStore";
import { obtenerHistorialAuditorias } from "@/app/actions/auditActions";
import { AuditSnapshot } from "@/types";

export default function AuditHistory() {
  const razonSocial = useAuditStore((state) => state.companyData.razonSocial);
  const setActiveView = useAuditStore((state) => state.setActiveView);

  const [historial, setHistorial] = useState<AuditSnapshot[]>([]);
  const [selectedSnapshot, setSelectedSnapshot] = useState<AuditSnapshot | null>(null);
  const [searchTerm, setSearchTerm] = useState<string>("");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [hasCopiedHash, setHasCopiedHash] = useState<boolean>(false);

  // Hook nativo useTransition para transiciones asíncronas no bloqueantes
  const [isPending, startTransition] = useTransition();

  // Función de carga conectada a la Server Action
  const cargarHistorial = useCallback((empresaNombre?: string) => {
    startTransition(async () => {
      setErrorMsg(null);
      try {
        const respuesta = await obtenerHistorialAuditorias(empresaNombre);
        if (respuesta.success && respuesta.data) {
          setHistorial(respuesta.data);
        } else {
          setErrorMsg(respuesta.error || "No se pudo cargar el historial.");
        }
      } catch (err) {
        setErrorMsg(
          err instanceof Error ? err.message : "Error inesperado al conectar con el servidor."
        );
      }
    });
  }, []);

  // Suscripción reactiva: cada vez que cambia razonSocial en Zustand, dispara startTransition
  useEffect(() => {
    cargarHistorial(razonSocial);
  }, [razonSocial, cargarHistorial]);

  // Filtrado local por término de búsqueda (ID, versión o hash)
  const snapshotsFiltrados = historial.filter((item) => {
    if (!searchTerm.trim()) return true;
    const term = searchTerm.toLowerCase();
    return (
      item.id.toLowerCase().includes(term) ||
      item.normativa.toLowerCase().includes(term) ||
      item.empresa.razonSocial.toLowerCase().includes(term) ||
      (item.sha256Seal && item.sha256Seal.toLowerCase().includes(term))
    );
  });

  const formatearFecha = (isoString: string) => {
    try {
      const fecha = new Date(isoString);
      return new Intl.DateTimeFormat("es-EC", {
        day: "2-digit",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      }).format(fecha);
    } catch {
      return isoString;
    }
  };

  const copiarAlPortapapeles = (texto: string) => {
    if (navigator.clipboard) {
      navigator.clipboard.writeText(texto);
      setHasCopiedHash(true);
      setTimeout(() => setHasCopiedHash(false), 2000);
    }
  };

  // Convertir madurez a etiqueta de nivel (Nivel 0 - 3)
  const obtenerNivelMadurez = (madurezPct: number) => {
    if (madurezPct >= 85) return "Nivel 3 (Optimizado)";
    if (madurezPct >= 65) return "Nivel 2 (Gestionado)";
    if (madurezPct >= 40) return "Nivel 1 (Inicial)";
    return "Nivel 0 (No Conforme)";
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6 font-sans pb-12">
      {/* Encabezado Principal del Módulo 3 */}
      <div className="p-5 rounded-xl bg-[#141417] border border-[#26262b] shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-[#1e1e24] border border-[#26262b] flex items-center justify-center text-[#9a3bf1]">
              <GitCommit className="w-4 h-4" />
            </div>
            <div>
              <h1 className="text-base font-bold text-white tracking-tight flex items-center space-x-2">
                <span>Historial de Auditorías y Snapshots Congelados</span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#9a3bf1]/15 text-[#9a3bf1] border border-[#9a3bf1]/30">
                  Módulo 3 · Doctrina 10
                </span>
              </h1>
              <p className="text-xs text-zinc-400 flex items-center space-x-2 mt-0.5">
                <Building2 className="w-3.5 h-3.5 text-zinc-500" />
                <span>Organización activa:</span>
                <span className="text-zinc-200 font-semibold">
                  {razonSocial.trim() || "Todas las entidades (Vista Global)"}
                </span>
              </p>
            </div>
          </div>
        </div>

        {/* Barra de Acciones y Refresco */}
        <div className="flex items-center space-x-3">
          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-zinc-500" />
            <input
              type="text"
              placeholder="Filtrar por ID, norma o hash..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="h-8 pl-8 pr-3 text-xs rounded-lg bg-[#0a0a0c] border border-[#26262b] text-zinc-200 placeholder-zinc-500 focus:outline-none focus:border-[#9a3bf1] transition w-48 md:w-60"
            />
          </div>

          <button
            type="button"
            onClick={() => cargarHistorial(razonSocial)}
            disabled={isPending}
            className="h-8 px-3 text-xs rounded-lg bg-[#1e1e24] hover:bg-[#26262b] border border-[#26262b] text-zinc-300 hover:text-white flex items-center space-x-1.5 transition cursor-pointer disabled:opacity-50"
            title="Recargar historial desde el servidor"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isPending ? "animate-spin text-[#9a3bf1]" : "text-zinc-400"}`} />
            <span className="hidden sm:inline">{isPending ? "Sincronizando..." : "Actualizar"}</span>
          </button>
        </div>
      </div>

      {/* Alerta de Error si ocurre en la Server Action */}
      {errorMsg && (
        <div className="p-3 rounded-lg bg-[#ff1744]/10 border border-[#ff1744]/30 text-xs text-[#ff1744] flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* ========================================================================= */}
      {/* VISTA DE ESQUELETO ANIMADO (DURANTE useTransition isPending)             */}
      {/* ========================================================================= */}
      {isPending && historial.length === 0 ? (
        <div className="space-y-4 animate-pulse">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="p-5 rounded-xl bg-[#141417] border border-[#26262b] space-y-4 relative overflow-hidden"
            >
              <div className="flex items-center justify-between">
                <div className="h-4 bg-[#26262b] rounded w-1/4" />
                <div className="h-4 bg-[#26262b] rounded w-1/6" />
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <div className="h-10 bg-[#1e1e24] rounded-lg" />
                <div className="h-10 bg-[#1e1e24] rounded-lg" />
                <div className="h-10 bg-[#1e1e24] rounded-lg" />
                <div className="h-10 bg-[#1e1e24] rounded-lg" />
              </div>
            </div>
          ))}
        </div>
      ) : snapshotsFiltrados.length === 0 ? (
        /* ========================================================================= */
        /* ESTADO VACÍO (EMPTY STATE)                                                */
        /* ========================================================================= */
        <div className="p-10 rounded-xl bg-[#141417] border border-[#26262b] text-center space-y-4">
          <div className="w-12 h-12 rounded-full bg-[#1e1e24] border border-[#26262b] mx-auto flex items-center justify-center text-zinc-500">
            <Lock className="w-6 h-6" />
          </div>
          <div className="space-y-1">
            <h3 className="text-sm font-semibold text-zinc-200">
              No se encontraron snapshots sellados
            </h3>
            <p className="text-xs text-zinc-400 max-w-md mx-auto">
              {razonSocial.trim()
                ? `No existen auditorías congeladas registradas para la entidad "${razonSocial}". Completa una evaluación en el lienzo diagnóstico y ejecuta el congelamiento notarial.`
                : "Aún no se han completado ciclos de evaluación diagnóstica en el sistema."}
            </p>
          </div>
          <div className="pt-2 flex items-center justify-center space-x-3">
            <button
              type="button"
              onClick={() => setActiveView("diagnostico")}
              className="px-4 py-2 rounded-lg bg-[#9a3bf1] hover:bg-[#8529e0] text-white text-xs font-semibold flex items-center space-x-1.5 transition cursor-pointer shadow-sm"
            >
              <FileText className="w-3.5 h-3.5" />
              <span>Ir a Normativa</span>
            </button>
            {searchTerm && (
              <button
                type="button"
                onClick={() => setSearchTerm("")}
                className="px-3 py-2 rounded-lg bg-[#1e1e24] hover:bg-[#26262b] border border-[#26262b] text-zinc-300 text-xs transition cursor-pointer"
              >
                Limpiar filtro de búsqueda
              </button>
            )}
          </div>
        </div>
      ) : (
        /* ========================================================================= */
        /* LÍNEA DE TIEMPO VERTICAL ESTILO GIT / BITÁCORA NOTARIAL                   */
        /* ========================================================================= */
        <div className="relative pl-6 md:pl-8 space-y-6 before:absolute before:left-3 md:before:left-4 before:top-4 before:bottom-4 before:w-0.5 before:bg-[#26262b]">
          {snapshotsFiltrados.map((snapshot, index) => {
            const esConforme = snapshot.scoringFinal?.conformidadLegalBooleana;
            const madurezNivel = obtenerNivelMadurez(snapshot.scoringFinal?.madurez || 0);

            return (
              <div key={snapshot.id} className="relative group">
                {/* Nodo Circular Interconectado por Línea #26262b */}
                <div
                  className={`absolute -left-6 md:-left-8 top-4 w-6 h-6 rounded-full border flex items-center justify-center text-xs transition z-10 ${
                    esConforme
                      ? "bg-[#0a0a0c] border-[#00c853] text-[#00c853] shadow-[0_0_8px_rgba(0,200,83,0.3)]"
                      : "bg-[#0a0a0c] border-[#ff1744] text-[#ff1744] shadow-[0_0_8px_rgba(255,23,68,0.3)]"
                  }`}
                >
                  <GitCommit className="w-3.5 h-3.5" />
                </div>

                {/* Tarjeta de Snapshot (Fondo #141417, Borde #26262b) */}
                <div
                  onClick={() => setSelectedSnapshot(snapshot)}
                  className="p-5 rounded-xl bg-[#141417] border border-[#26262b] hover:border-[#9a3bf1]/60 transition-all duration-200 cursor-pointer shadow-sm group-hover:shadow-[0_4px_20px_rgba(0,0,0,0.5)] space-y-4"
                >
                  {/* Encabezado de la Tarjeta */}
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#26262b]/60 pb-3">
                    <div className="flex items-center space-x-2.5 flex-wrap gap-y-1">
                      <span className="font-mono text-xs font-bold text-white bg-[#0a0a0c] px-2 py-0.5 rounded border border-[#26262b]">
                        {snapshot.id}
                      </span>
                      <span className="text-xs font-semibold text-zinc-300">
                        {snapshot.empresa.razonSocial}
                      </span>
                      <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-[#9a3bf1]/15 text-[#9a3bf1] border border-[#9a3bf1]/30">
                        Norma {snapshot.normativa}
                      </span>
                      {index === 0 && (
                        <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-[#00c853]/15 text-[#00c853] border border-[#00c853]/30 font-semibold">
                          ÚLTIMO SELLADO
                        </span>
                      )}
                    </div>

                    <div className="flex items-center space-x-2 text-[11px] text-zinc-400 font-mono">
                      <Clock className="w-3 h-3 text-zinc-500" />
                      <span>{formatearFecha(snapshot.fechaCierre)}</span>
                    </div>
                  </div>

                  {/* Sello SHA-256 Truncado */}
                  {snapshot.sha256Seal && (
                    <div className="flex items-center space-x-2 text-[10px] text-zinc-400 font-mono bg-[#0a0a0c] px-2.5 py-1.5 rounded border border-[#26262b]/80">
                      <Lock className="w-3 h-3 text-[#00c853] shrink-0" />
                      <span className="text-zinc-500 uppercase font-semibold">Sello SHA-256:</span>
                      <span className="text-zinc-300 truncate font-mono">
                        {snapshot.sha256Seal}
                      </span>
                    </div>
                  )}

                  {/* CUADRÍCULA DE LAS 4 DIMENSIONES DE SCORING */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-2.5 pt-1">
                    {/* Dimensión 1: Conformidad Legal */}
                    <div
                      className={`p-2.5 rounded-lg border flex flex-col justify-between ${
                        esConforme
                          ? "bg-[#00c853]/10 border-[#00c853]/30 text-[#00c853]"
                          : "bg-[#ff1744]/10 border-[#ff1744]/30 text-[#ff1744]"
                      }`}
                    >
                      <span className="text-[10px] font-mono uppercase font-semibold text-zinc-400 flex items-center justify-between">
                        <span>Conformidad Legal</span>
                        {esConforme ? (
                          <CheckCircle2 className="w-3 h-3 text-[#00c853]" />
                        ) : (
                          <XCircle className="w-3 h-3 text-[#ff1744]" />
                        )}
                      </span>
                      <div className="mt-1 font-bold text-xs tracking-tight">
                        {esConforme ? "100% Conforme" : "Brecha Abierta"}
                      </div>
                    </div>

                    {/* Dimensión 2: Madurez SPDP (Etiqueta Acromática) */}
                    <div className="p-2.5 rounded-lg bg-[#1e1e24] border border-[#26262b] text-zinc-200 flex flex-col justify-between">
                      <span className="text-[10px] font-mono uppercase font-semibold text-zinc-400">
                        Madurez SPDP
                      </span>
                      <div className="mt-1 font-bold text-xs tracking-tight text-white flex items-baseline space-x-1">
                        <span>{madurezNivel}</span>
                        <span className="text-[10px] font-normal text-zinc-400">
                          ({snapshot.scoringFinal?.madurez || 0}%)
                        </span>
                      </div>
                    </div>

                    {/* Dimensión 3: Cobertura de Evidencias (Azul Render #3892f3) */}
                    <div className="p-2.5 rounded-lg bg-[#3892f3]/10 border border-[#3892f3]/30 text-[#3892f3] flex flex-col justify-between">
                      <span className="text-[10px] font-mono uppercase font-semibold text-zinc-400 flex items-center justify-between">
                        <span>Evidencias</span>
                        <Database className="w-3 h-3 text-[#3892f3]" />
                      </span>
                      <div className="mt-1 font-bold text-xs tracking-tight flex items-baseline space-x-1">
                        <span>
                          E{((((snapshot.scoringFinal?.coberturaEvidencias || 0) / 100) * 3).toFixed(1))} Promedio
                        </span>
                        <span className="text-[10px] font-normal text-[#3892f3]/80">
                          ({snapshot.scoringFinal?.coberturaEvidencias || 0}%)
                        </span>
                      </div>
                    </div>

                    {/* Dimensión 4: Riesgo Residual */}
                    <div className="p-2.5 rounded-lg bg-[#0a0a0c] border border-[#26262b] text-zinc-200 flex flex-col justify-between">
                      <span className="text-[10px] font-mono uppercase font-semibold text-zinc-400 flex items-center justify-between">
                        <span>Riesgo Residual</span>
                        <ShieldAlert className="w-3 h-3 text-amber-500" />
                      </span>
                      <div className="mt-1 font-bold text-xs tracking-tight text-white">
                        {snapshot.scoringFinal?.riesgoResidual !== undefined
                          ? `${snapshot.scoringFinal.riesgoResidual}%`
                          : "N/A"}
                      </div>
                    </div>
                  </div>

                  {/* Pie de Tarjeta: Indicador de Acción */}
                  <div className="flex items-center justify-between text-[11px] text-zinc-400 pt-1">
                    <span className="text-zinc-500 flex items-center space-x-1">
                      <Layers className="w-3 h-3" />
                      <span>{snapshot.respuestasSnapshot?.length || 0} preguntas congeladas</span>
                    </span>

                    <span className="text-[#9a3bf1] group-hover:text-white font-medium flex items-center space-x-1 transition text-xs">
                      <span>Inspeccionar Snapshot Congelado</span>
                      <ChevronRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* ========================================================================= */}
      {/* PANEL MODAL INVIOLABLE DE SOLO LECTURA (READ-ONLY INSPECTION DRAWER)       */}
      {/* ========================================================================= */}
      {selectedSnapshot && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-xs z-50 flex items-center justify-center p-3 sm:p-6 animate-in fade-in duration-150">
          <div className="bg-[#141417] border border-[#26262b] rounded-xl max-w-3xl w-full max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">
            {/* Cabecera del Modal */}
            <div className="h-12 bg-[#1e1e24] border-b border-[#26262b] px-4 flex items-center justify-between shrink-0">
              <div className="flex items-center space-x-2.5">
                <div className="w-6 h-6 rounded bg-[#00c853]/15 border border-[#00c853]/30 flex items-center justify-center text-[#00c853]">
                  <Lock className="w-3.5 h-3.5" />
                </div>
                <div>
                  <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center space-x-2">
                    <span>Snapshot Congelado Inmutable</span>
                    <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-[#26262b] text-zinc-400">
                      SOLO LECTURA
                    </span>
                  </h3>
                </div>
              </div>

              <button
                type="button"
                onClick={() => setSelectedSnapshot(null)}
                className="w-7 h-7 rounded-lg bg-[#141417] hover:bg-[#26262b] border border-[#26262b] text-zinc-400 hover:text-white flex items-center justify-center transition cursor-pointer"
                title="Cerrar inspección"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Banner de Garantía de Inviolabilidad (Doctrina 7 y 10) */}
            <div className="p-3 bg-[#0a0a0c] border-b border-[#26262b] flex items-center justify-between text-xs">
              <div className="flex items-center space-x-2 text-zinc-300">
                <ShieldCheck className="w-4 h-4 text-[#00c853] shrink-0" />
                <span className="text-[11px] text-zinc-400">
                  Registro sellado notarialmente. Todos los campos están físicamente bloqueados en el DOM (anti-mutación).
                </span>
              </div>
              <span className="font-mono text-[10px] text-zinc-500 shrink-0 hidden sm:inline">
                {selectedSnapshot.id}
              </span>
            </div>

            {/* Contenido Desplazable del Modal */}
            <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-5 bg-[#0a0a0c]">
              {/* Metadatos Generales */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                <div className="p-2.5 rounded-lg bg-[#141417] border border-[#26262b]">
                  <span className="text-[10px] uppercase font-mono text-zinc-500 block">Razón Social</span>
                  <span className="font-semibold text-white truncate block mt-0.5">
                    {selectedSnapshot.empresa.razonSocial}
                  </span>
                </div>
                <div className="p-2.5 rounded-lg bg-[#141417] border border-[#26262b]">
                  <span className="text-[10px] uppercase font-mono text-zinc-500 block">Normativa</span>
                  <span className="font-semibold text-[#9a3bf1] block mt-0.5">
                    {selectedSnapshot.normativa} ({selectedSnapshot.versionNormativa})
                  </span>
                </div>
                <div className="p-2.5 rounded-lg bg-[#141417] border border-[#26262b]">
                  <span className="text-[10px] uppercase font-mono text-zinc-500 block">Sector</span>
                  <span className="font-semibold text-zinc-300 block mt-0.5">
                    {selectedSnapshot.empresa.sector}
                  </span>
                </div>
                <div className="p-2.5 rounded-lg bg-[#141417] border border-[#26262b]">
                  <span className="text-[10px] uppercase font-mono text-zinc-500 block">Fecha Cierre</span>
                  <span className="font-semibold text-zinc-300 block mt-0.5 font-mono text-[11px]">
                    {formatearFecha(selectedSnapshot.fechaCierre)}
                  </span>
                </div>
              </div>

              {/* Sello Criptográfico SHA-256 Completo */}
              {selectedSnapshot.sha256Seal && (
                <div className="p-3 rounded-lg bg-[#141417] border border-[#26262b] space-y-1.5">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-[10px] uppercase font-mono text-zinc-400 font-semibold flex items-center space-x-1.5">
                      <Hash className="w-3.5 h-3.5 text-[#00c853]" />
                      <span>Sello de Integridad Criptográfica (SHA-256)</span>
                    </span>
                    <button
                      type="button"
                      onClick={() => copiarAlPortapapeles(selectedSnapshot.sha256Seal || "")}
                      className="text-[10px] font-mono text-zinc-400 hover:text-white flex items-center space-x-1 transition cursor-pointer"
                    >
                      {hasCopiedHash ? (
                        <>
                          <Check className="w-3 h-3 text-[#00c853]" />
                          <span className="text-[#00c853]">Copiado</span>
                        </>
                      ) : (
                        <>
                          <span>Copiar hash</span>
                        </>
                      )}
                    </button>
                  </div>
                  <div className="p-2 rounded bg-[#0a0a0c] border border-[#26262b] font-mono text-[11px] text-[#00c853] break-all select-all">
                    {selectedSnapshot.sha256Seal}
                  </div>
                </div>
              )}

              {/* Resumen 4D en Modal */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                <div className="p-3 rounded-lg bg-[#141417] border border-[#26262b] text-center">
                  <span className="text-[10px] font-mono uppercase text-zinc-500 block">Conformidad</span>
                  <span
                    className={`text-xs font-bold block mt-1 ${
                      selectedSnapshot.scoringFinal?.conformidadLegalBooleana
                        ? "text-[#00c853]"
                        : "text-[#ff1744]"
                    }`}
                  >
                    {selectedSnapshot.scoringFinal?.conformidadLegalBooleana
                      ? "100% Conforme"
                      : "Brecha Abierta"}
                  </span>
                </div>
                <div className="p-3 rounded-lg bg-[#141417] border border-[#26262b] text-center">
                  <span className="text-[10px] font-mono uppercase text-zinc-500 block">Madurez SPDP</span>
                  <span className="text-xs font-bold text-white block mt-1">
                    {selectedSnapshot.scoringFinal?.madurez || 0}%
                  </span>
                </div>
                <div className="p-3 rounded-lg bg-[#141417] border border-[#26262b] text-center">
                  <span className="text-[10px] font-mono uppercase text-zinc-500 block">Cobertura Evidencias</span>
                  <span className="text-xs font-bold text-[#3892f3] block mt-1">
                    {selectedSnapshot.scoringFinal?.coberturaEvidencias || 0}%
                  </span>
                </div>
                <div className="p-3 rounded-lg bg-[#141417] border border-[#26262b] text-center">
                  <span className="text-[10px] font-mono uppercase text-zinc-500 block">Riesgo Residual</span>
                  <span className="text-xs font-bold text-amber-400 block mt-1">
                    {selectedSnapshot.scoringFinal?.riesgoResidual || 0}%
                  </span>
                </div>
              </div>

              {/* Respuestas Congeladas (Inviolables, Inputs Físicamente Bloqueados) */}
              <div className="space-y-3">
                <div className="flex items-center justify-between border-b border-[#26262b] pb-2">
                  <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center space-x-2">
                    <FileText className="w-3.5 h-3.5 text-[#9a3bf1]" />
                    <span>Lienzo de Respuestas Selladas</span>
                  </h4>
                  <span className="text-[10px] font-mono text-zinc-400">
                    {selectedSnapshot.respuestasSnapshot?.length || 0} Registros Congelados
                  </span>
                </div>

                {/* Los controles permanecen deshabilitados y el texto puede copiarse. */}
                <div className="space-y-2">
                  {selectedSnapshot.respuestasSnapshot?.map((item, idx) => (
                    <div
                      key={item.id_pregunta || idx}
                      className="p-3 rounded-lg bg-[#141417] border border-[#26262b] flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 opacity-90"
                    >
                      <div className="space-y-1 min-w-0">
                        <div className="flex items-center space-x-2">
                          <span className="font-mono text-[10px] font-bold text-zinc-400 bg-[#0a0a0c] px-1.5 py-0.5 rounded border border-[#26262b]">
                            {item.id_pregunta}
                          </span>
                          <span className="text-xs font-medium text-zinc-200 truncate">
                            {item.rationale || "Pregunta de diagnóstico LOPDP"}
                          </span>
                        </div>
                      </div>

                      {/* Controles Bloqueados */}
                      <div className="flex items-center space-x-2 shrink-0">
                        {/* Indicador Booleano */}
                        <div
                          className={`px-2 py-1 rounded text-[10px] font-mono font-semibold border flex items-center space-x-1 ${
                            item.respuesta_afirmativa
                              ? "bg-[#00c853]/15 text-[#00c853] border-[#00c853]/30"
                              : "bg-[#ff1744]/15 text-[#ff1744] border-[#ff1744]/30"
                          }`}
                        >
                          <input
                            type="checkbox"
                            checked={item.respuesta_afirmativa}
                            disabled={true}
                            readOnly={true}
                            tabIndex={-1}
                            className="hidden"
                          />
                          <span>{item.respuesta_afirmativa ? "CONFORME" : "NO CONFORME"}</span>
                        </div>

                        {/* Nivel de Evidencia Bloqueado */}
                        <div className="px-2 py-1 rounded text-[10px] font-mono bg-[#1e1e24] border border-[#26262b] text-[#3892f3]">
                          <span>{item.nivel_evidencia || "E0"}</span>
                        </div>

                        {/* Candado de Inviolabilidad */}
                        <div className="p-1 rounded bg-[#0a0a0c] border border-[#26262b] text-zinc-500" title="Control bloqueado">
                          <Lock className="w-3 h-3" />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Pie del Modal */}
            <div className="h-12 bg-[#1e1e24] border-t border-[#26262b] px-4 flex items-center justify-between shrink-0 text-xs">
              <span className="text-[11px] text-zinc-400 font-mono flex items-center space-x-1.5">
                <Lock className="w-3 h-3 text-[#00c853]" />
                <span>Modo de Inspección Notarial Activo</span>
              </span>
              <button
                type="button"
                onClick={() => setSelectedSnapshot(null)}
                className="px-3 py-1.5 rounded-lg bg-[#26262b] hover:bg-[#323238] text-white text-xs font-medium transition cursor-pointer"
              >
                Cerrar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

