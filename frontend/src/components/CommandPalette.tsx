"use client";

import React, { useEffect, useState, useCallback } from "react";
import { usePathname } from "next/navigation";
import { Command, defaultFilter } from "cmdk";
import {
  Search,
  Command as CommandIcon,
  SlidersHorizontal,
  Clock,
  Bot,
  BookOpen,
  ShieldCheck,
  Scale,
  Sparkles,
  Download,
  FileSpreadsheet,
  X,
  GitCommit,
  LayoutDashboard,
  Sun,
  Moon,
  ShieldAlert,
} from "lucide-react";
import { useAuditStore, ActiveView, NormativaAuditoria } from "@/store/useAuditStore";

interface CommandPaletteProps {
  isOpen?: boolean;
  onClose?: () => void;
  onSelectModulo?: (modulo: string) => void;
  isDarkMode?: boolean;
  onToggleTheme?: () => void;
}

/** Quita diacríticos (tildes, diéresis) para comparar texto en español sin distinguirlos. */
const quitarDiacriticos = (texto: string): string =>
  texto.normalize("NFD").replace(/[̀-ͯ]/g, "");

/**
 * El filtro por defecto de cmdk distingue "ó" de "o": buscar "Diagnóstico"
 * —la forma natural de escribirlo en español— no encontraba comandos cuya
 * palabra clave está indexada sin tilde ("diagnostico"). Se envuelve el
 * mismo algoritmo de coincidencia difusa con texto normalizado en ambos
 * lados, sin reimplementarlo.
 */
const filtrarSinAcentos = (value: string, search: string, keywords?: string[]): number =>
  defaultFilter(
    quitarDiacriticos(value),
    quitarDiacriticos(search),
    keywords?.map(quitarDiacriticos)
  );

export default function CommandPalette({
  isOpen: externalIsOpen,
  onClose: externalOnClose,
  onSelectModulo,
}: CommandPaletteProps) {
  const [internalOpen, setInternalOpen] = useState(false);
  const [mensajeAccion, setMensajeAccion] = useState<string | null>(null);
  const pathname = usePathname() || "";

  // Zustand state and actions
  const {
    isCommandPaletteOpen,
    setCommandPaletteOpen,
    activeView,
    setActiveView,
    setIsConfigured,
    setNormativa,
    evidencias,
    companyData,
    theme,
    toggleTheme,
  } = useAuditStore();

  const isDpoContext = pathname.includes("dpo") || activeView === "dpo";
  const isDiagnosticoContext = pathname.includes("diagnostico") || activeView === "diagnostico";

  // Determine effective open state (supports autonomous mode, Zustand store, or props)
  const isControlledByProp = externalIsOpen !== undefined;
  const isOpen = isControlledByProp
    ? externalIsOpen
    : isCommandPaletteOpen || internalOpen;

  const handleClose = useCallback(() => {
    if (externalOnClose) {
      externalOnClose();
    }
    setInternalOpen(false);
    setCommandPaletteOpen(false);
  }, [externalOnClose, setCommandPaletteOpen]);

  const handleOpen = useCallback(() => {
    setInternalOpen(true);
    setCommandPaletteOpen(true);
  }, [setCommandPaletteOpen]);

  // Listener global para Ctrl+K / Cmd+K y Escape
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        if (isOpen) {
          handleClose();
        } else {
          handleOpen();
        }
      } else if (e.key === "Escape" && isOpen) {
        e.preventDefault();
        handleClose();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, handleClose, handleOpen]);

  const ejecutarAccionNavegacion = (view: ActiveView, moduloNombre?: string) => {
    setActiveView(view);
    if (onSelectModulo && moduloNombre) {
      onSelectModulo(moduloNombre);
    }
    handleClose();
  };

  const ejecutarGenerarBancoPodado = () => {
    setIsConfigured(true);
    setMensajeAccion("✓ Banco podado con éxito para inferencia del Agente IA.");
    setTimeout(() => {
      setMensajeAccion(null);
      handleClose();
    }, 1200);
  };

  const ejecutarCambioNormativa = (normativa: NormativaAuditoria) => {
    // Con evidencias registradas, el cambio las purgaría: se deriva al selector
    // de Configuración, que pide confirmación explícita antes de purgar.
    if (evidencias.length > 0) {
      setActiveView("configuracion");
      setMensajeAccion(
        `Hay ${evidencias.length} evidencia(s) registrada(s): cambia la normativa desde Configuración para confirmar su eliminación.`
      );
      setTimeout(() => {
        setMensajeAccion(null);
        handleClose();
      }, 2200);
      return;
    }
    setNormativa(normativa);
    setMensajeAccion(`✓ Normativa calibrada a: ${normativa}`);
    setTimeout(() => {
      setMensajeAccion(null);
      handleClose();
    }, 1000);
  };

  const ejecutarExportarPdf = () => {
    setMensajeAccion("✓ Generando Informe Técnico de Brechas LOPDP (PDF)...");
    setTimeout(() => {
      setMensajeAccion(null);
      handleClose();
    }, 1400);
  };

  const ejecutarAlternarTema = () => {
    toggleTheme();
    setMensajeAccion(`✓ Tema conmutado a: ${theme === "dark" ? "Claro Purificado" : "Oscuro Técnico"}`);
    setTimeout(() => {
      setMensajeAccion(null);
      handleClose();
    }, 1000);
  };

  if (!isOpen) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      className="fixed inset-0 z-50 flex items-start justify-center pt-20 px-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-150"
      onClick={(e) => {
        if (e.target === e.currentTarget) {
          handleClose();
        }
      }}
    >
      <div className="w-full max-w-xl bg-[#141417] border border-[#26262b] rounded-xl shadow-[0_20px_60px_rgba(0,0,0,0.85)] overflow-hidden font-sans flex flex-col">
        <Command
          label="Paleta de Comandos Universal JUBYS LOPDP 360"
          className="w-full text-zinc-100 flex flex-col"
          filter={filtrarSinAcentos}
        >
          {/* Input de Búsqueda Estilo Render (#0a0a0c, bordes limpios) */}
          <div className="flex items-center px-4 py-3 border-b border-[#26262b] bg-[#0a0a0c] shrink-0">
            <Search className="w-4 h-4 text-zinc-400 mr-3 shrink-0" />
            <Command.Input
              autoFocus
              placeholder="Escribe un comando o busca un artículo de la LOPDP..."
              className="w-full bg-transparent border-none outline-none text-zinc-100 placeholder-zinc-500 text-xs font-medium"
            />
            <button
              type="button"
              onClick={handleClose}
              className="p-1 text-zinc-500 hover:text-zinc-200 rounded hover:bg-[#1e1e24] transition cursor-pointer shrink-0 ml-2"
              title="Cerrar (Esc)"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Notificación de Acción Temporal */}
          {mensajeAccion && (
            <div className="px-4 py-2 bg-[#00c853]/15 border-b border-[#00c853]/30 text-[#00c853] text-xs font-medium flex items-center justify-between animate-in fade-in">
              <span>{mensajeAccion}</span>
              <span className="text-[10px] font-mono opacity-80">Procesado</span>
            </div>
          )}

          {/* Lista de Comandos con Categorías del PRD */}
          <Command.List className="max-h-84 overflow-y-auto p-2 space-y-1 text-xs">
            <Command.Empty className="py-10 text-center text-zinc-500 text-xs">
              <div className="flex flex-col items-center justify-center space-y-1.5">
                <CommandIcon className="w-6 h-6 text-zinc-600 mb-1" />
                <span>No se encontraron comandos o artículos coincidentes.</span>
                <span className="text-[11px] text-zinc-600">
                  Prueba buscando por &quot;LOPDP&quot;, &quot;ISO&quot;, &quot;NIIF&quot;, &quot;ARCO&quot; o &quot;Normativa&quot;
                </span>
              </div>
            </Command.Empty>

            {/* =================================================================== */}
            {/* GRUPO 0: Acciones Contextuales Topológicas                          */}
            {/* =================================================================== */}
            {(isDpoContext || isDiagnosticoContext) && (
              <Command.Group
                heading="Acciones Contextuales (O(1))"
                className="text-[10px] uppercase font-bold text-[#9a3bf1] px-2.5 py-1 tracking-wider font-mono mb-2 bg-[#9a3bf1]/5 rounded-t"
              >
                {isDpoContext && (
                  <>
                    <Command.Item
                      keywords={["revisar", "sla", "vencidos", "dpo", "cockpit", "pendientes"]}
                      onSelect={() => {
                        setMensajeAccion("✓ Abriendo panel de SLAs Vencidos...");
                        setTimeout(() => {
                          setMensajeAccion(null);
                          handleClose();
                        }, 1200);
                      }}
                      className="flex items-center justify-between px-3 py-2 rounded-lg cursor-pointer transition text-zinc-300 hover:bg-[#1e1e24] hover:text-white data-[selected=true]:bg-[#1e1e24] data-[selected=true]:text-[#9a3bf1] data-[selected=true]:border data-[selected=true]:border-[#9a3bf1]/40"
                    >
                      <div className="flex items-center space-x-2.5">
                        <div className="p-1.5 rounded-md bg-[#0a0a0c] border border-[#ff1744]/40 text-[#ff1744]">
                          <Clock className="w-3.5 h-3.5" />
                        </div>
                        <div>
                          <span className="font-medium text-xs text-white">Revisar SLAs Vencidos</span>
                          <p className="text-[10px] text-zinc-400">Atender derechos ARCO+ con plazo expirado</p>
                        </div>
                      </div>
                      <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-[#ff1744]/15 border border-[#ff1744]/30 text-[#ff1744]">
                        DPO
                      </span>
                    </Command.Item>
                    <Command.Item
                      keywords={["aprobar", "dictamen", "dpo", "cockpit", "firmar"]}
                      onSelect={() => {
                        setMensajeAccion("✓ Dictamen aprobado e incorporado a la bitácora.");
                        setTimeout(() => {
                          setMensajeAccion(null);
                          handleClose();
                        }, 1200);
                      }}
                      className="flex items-center justify-between px-3 py-2 rounded-lg cursor-pointer transition text-zinc-300 hover:bg-[#1e1e24] hover:text-white data-[selected=true]:bg-[#1e1e24] data-[selected=true]:text-[#9a3bf1] data-[selected=true]:border data-[selected=true]:border-[#9a3bf1]/40"
                    >
                      <div className="flex items-center space-x-2.5">
                        <div className="p-1.5 rounded-md bg-[#0a0a0c] border border-[#00c853]/40 text-[#00c853]">
                          <ShieldCheck className="w-3.5 h-3.5" />
                        </div>
                        <div>
                          <span className="font-medium text-xs text-white">Aprobar Dictamen Técnico</span>
                          <p className="text-[10px] text-zinc-400">Sellar la evaluación de impacto (EIPD) actual</p>
                        </div>
                      </div>
                      <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-[#00c853]/15 border border-[#00c853]/30 text-[#00c853]">
                        DPO
                      </span>
                    </Command.Item>
                  </>
                )}
                {isDiagnosticoContext && (
                  <Command.Item
                    keywords={["exportar", "informe", "pdf", "diagnostico", "descargar"]}
                    onSelect={ejecutarExportarPdf}
                    className="flex items-center justify-between px-3 py-2 rounded-lg cursor-pointer transition text-zinc-300 hover:bg-[#1e1e24] hover:text-white data-[selected=true]:bg-[#1e1e24] data-[selected=true]:text-[#9a3bf1] data-[selected=true]:border data-[selected=true]:border-[#9a3bf1]/40"
                  >
                    <div className="flex items-center space-x-2.5">
                      <div className="p-1.5 rounded-md bg-[#0a0a0c] border border-[#3892f3]/40 text-[#3892f3]">
                        <Download className="w-3.5 h-3.5" />
                      </div>
                      <div>
                        <span className="font-medium text-xs text-white">Exportar Informe PDF</span>
                        <p className="text-[10px] text-zinc-400">Descargar dictamen de brechas del diagnóstico activo</p>
                      </div>
                    </div>
                    <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-[#3892f3]/15 border border-[#3892f3]/30 text-[#3892f3]">
                      Export
                    </span>
                  </Command.Item>
                )}
              </Command.Group>
            )}

            {/* =================================================================== */}
            {/* GRUPO 1: Navegación del IDE                                         */}
            <Command.Group
              heading="Navegación del IDE"
              className="text-[10px] uppercase font-bold text-zinc-500 px-2.5 py-1 tracking-wider font-mono"
            >
              <Command.Item
                keywords={["dashboard", "scoring", "metricas", "central", "resumen", "modulo 1", "madurez", "evidencias"]}
                onSelect={() => ejecutarAccionNavegacion("dashboard", "dashboard")}
                className="flex items-center justify-between px-3 py-2 rounded-lg cursor-pointer transition text-zinc-300 hover:bg-[#1e1e24] hover:text-white data-[selected=true]:bg-[#1e1e24] data-[selected=true]:text-[#9a3bf1] data-[selected=true]:border data-[selected=true]:border-[#9a3bf1]/40"
              >
                <div className="flex items-center space-x-2.5">
                  <div className="p-1.5 rounded-md bg-[#0a0a0c] border border-[#26262b] text-zinc-400">
                    <LayoutDashboard className="w-3.5 h-3.5 text-[#9a3bf1]" />
                  </div>
                  <div>
                    <span className="font-medium text-xs text-white">
                      Ir a Dashboard Central (Módulo 1)
                    </span>
                    <p className="text-[10px] text-zinc-400">
                      Scoring Multidimensional 4D y estado de conformidad notarial
                    </p>
                  </div>
                </div>
                <kbd className="bg-[#0a0a0c] px-1.5 py-0.5 rounded border border-[#26262b] font-mono text-[10px] text-zinc-400">
                  ⌥1
                </kbd>
              </Command.Item>

              <Command.Item
                keywords={["configuracion", "ficha", "organizacion", "empresa", "datos", "proyecto"]}
                onSelect={() => ejecutarAccionNavegacion("configuracion", "configuracion")}
                className="flex items-center justify-between px-3 py-2 rounded-lg cursor-pointer transition text-zinc-300 hover:bg-[#1e1e24] hover:text-white data-[selected=true]:bg-[#1e1e24] data-[selected=true]:text-[#9a3bf1] data-[selected=true]:border data-[selected=true]:border-[#9a3bf1]/40"
              >
                <div className="flex items-center space-x-2.5">
                  <div className="p-1.5 rounded-md bg-[#0a0a0c] border border-[#26262b] text-zinc-400">
                    <SlidersHorizontal className="w-3.5 h-3.5 text-[#9a3bf1]" />
                  </div>
                  <div>
                    <span className="font-medium text-xs text-white">
                      Ir a Configuración de Ficha Organizacional
                    </span>
                    <p className="text-[10px] text-zinc-400">
                      Parametriza Razón Social ({companyData.razonSocial || "Entidad"}) y normativas
                    </p>
                  </div>
                </div>
                <kbd className="bg-[#0a0a0c] px-1.5 py-0.5 rounded border border-[#26262b] font-mono text-[10px] text-zinc-400">
                  ⌥C
                </kbd>
              </Command.Item>

              <Command.Item
                keywords={["normativa", "diagnostico", "evaluacion", "evidencias", "preguntas"]}
                onSelect={() => ejecutarAccionNavegacion("diagnostico", "diagnostico")}
                className="flex items-center justify-between px-3 py-2 rounded-lg cursor-pointer transition text-zinc-300 hover:bg-[#1e1e24] hover:text-white data-[selected=true]:bg-[#1e1e24] data-[selected=true]:text-[#9a3bf1] data-[selected=true]:border data-[selected=true]:border-[#9a3bf1]/40"
              >
                <div className="flex items-center space-x-2.5">
                  <div className="p-1.5 rounded-md bg-[#0a0a0c] border border-[#26262b] text-zinc-400">
                    <Clock className="w-3.5 h-3.5 text-[#3892f3]" />
                  </div>
                  <div>
                    <span className="font-medium text-xs text-white">
                      Ir a Normativa
                    </span>
                    <p className="text-[10px] text-zinc-400">
                      Evaluación rápida en 60 minutos (16 Dominios SPDP)
                    </p>
                  </div>
                </div>
                <kbd className="bg-[#0a0a0c] px-1.5 py-0.5 rounded border border-[#26262b] font-mono text-[10px] text-zinc-400">
                  ⌥D
                </kbd>
              </Command.Item>

              <Command.Item
                keywords={["ia", "chat", "copiloto", "legal", "agente", "rag", "spdp", "preguntas"]}
                onSelect={() => ejecutarAccionNavegacion("ia_chat", "regulacion_rag")}
                className="flex items-center justify-between px-3 py-2 rounded-lg cursor-pointer transition text-zinc-300 hover:bg-[#1e1e24] hover:text-white data-[selected=true]:bg-[#1e1e24] data-[selected=true]:text-[#9a3bf1] data-[selected=true]:border data-[selected=true]:border-[#9a3bf1]/40"
              >
                <div className="flex items-center space-x-2.5">
                  <div className="p-1.5 rounded-md bg-[#0a0a0c] border border-[#26262b] text-zinc-400">
                    <Bot className="w-3.5 h-3.5 text-[#9a3bf1]" />
                  </div>
                  <div>
                    <span className="font-medium text-xs text-white">
                      Ver Chat del Agente de IA Legal
                    </span>
                    <p className="text-[10px] text-zinc-400">
                      Consultas jurídicas asistidas con citas LOPDP y resoluciones SPDP
                    </p>
                  </div>
                </div>
                <kbd className="bg-[#0a0a0c] px-1.5 py-0.5 rounded border border-[#26262b] font-mono text-[10px] text-zinc-400">
                  ⌥A
                </kbd>
              </Command.Item>

              <Command.Item
                keywords={["historial", "auditoria", "snapshots", "congelados", "modulo 3", "bitacora", "sha256", "timeline"]}
                onSelect={() => ejecutarAccionNavegacion("auditoria", "auditoria")}
                className="flex items-center justify-between px-3 py-2 rounded-lg cursor-pointer transition text-zinc-300 hover:bg-[#1e1e24] hover:text-white data-[selected=true]:bg-[#1e1e24] data-[selected=true]:text-[#9a3bf1] data-[selected=true]:border data-[selected=true]:border-[#9a3bf1]/40"
              >
                <div className="flex items-center space-x-2.5">
                  <div className="p-1.5 rounded-md bg-[#0a0a0c] border border-[#26262b] text-zinc-400">
                    <GitCommit className="w-3.5 h-3.5 text-[#00c853]" />
                  </div>
                  <div>
                    <span className="font-medium text-xs text-white">
                      Ir a Historial de Auditorías y Snapshots Congelados
                    </span>
                    <p className="text-[10px] text-zinc-400">
                      Línea de tiempo de auditorías selladas y scoring 4D (Módulo 3)
                    </p>
                  </div>
                </div>
                <kbd className="bg-[#0a0a0c] px-1.5 py-0.5 rounded border border-[#26262b] font-mono text-[10px] text-zinc-400">
                  ⌥H
                </kbd>
              </Command.Item>

              <Command.Item
                keywords={["incidentes", "playbook", "vulneracion", "sla", "72h", "ciberseguridad", "brechas", "seguridad"]}
                onSelect={() => ejecutarAccionNavegacion("incidentes", "incidentes")}
                className="flex items-center justify-between px-3 py-2 rounded-lg cursor-pointer transition text-zinc-300 hover:bg-[#1e1e24] hover:text-white data-[selected=true]:bg-[#1e1e24] data-[selected=true]:text-[#9a3bf1] data-[selected=true]:border data-[selected=true]:border-[#9a3bf1]/40"
              >
                <div className="flex items-center space-x-2.5">
                  <div className="p-1.5 rounded-md bg-[#0a0a0c] border border-[#26262b] text-zinc-400">
                    <ShieldAlert className="w-3.5 h-3.5 text-[#ff1744]" />
                  </div>
                  <div>
                    <span className="font-medium text-xs text-white">
                      Ir a Playbook de Incidentes &amp; SLA 72h
                    </span>
                    <p className="text-[10px] text-zinc-400">
                      Cómputo perentorio de notificación de brechas (Ley de Ciberseguridad 2026)
                    </p>
                  </div>
                </div>
                <kbd className="bg-[#0a0a0c] px-1.5 py-0.5 rounded border border-[#26262b] font-mono text-[10px] text-zinc-400">
                  ⌥I
                </kbd>
              </Command.Item>

              <Command.Item
                keywords={["arco", "derechos", "acceso", "rectificacion", "cancelacion", "oposicion", "portabilidad", "eliminacion", "titular", "solicitud", "art 21", "art 22", "art 23", "art 24", "art 37", "sla 15 dias"]}
                onSelect={() => ejecutarAccionNavegacion("arco", "arco")}
                className="flex items-center justify-between px-3 py-2 rounded-lg cursor-pointer transition text-zinc-300 hover:bg-[#1e1e24] hover:text-white data-[selected=true]:bg-[#1e1e24] data-[selected=true]:text-[#9a3bf1] data-[selected=true]:border data-[selected=true]:border-[#9a3bf1]/40"
              >
                <div className="flex items-center space-x-2.5">
                  <div className="p-1.5 rounded-md bg-[#0a0a0c] border border-[#26262b] text-zinc-400">
                    <ShieldCheck className="w-3.5 h-3.5 text-[#9a3bf1]" />
                  </div>
                  <div>
                    <span className="font-medium text-xs text-white">
                      Ir a Gestión de Derechos ARCO+
                    </span>
                    <p className="text-[10px] text-zinc-400">
                      Tickets de Acceso/Rectificación/Cancelación · SLA 15 días laborables (Art. 37 LOPDP)
                    </p>
                  </div>
                </div>
                <kbd className="bg-[#0a0a0c] px-1.5 py-0.5 rounded border border-[#26262b] font-mono text-[10px] text-zinc-400">
                  ⌥R
                </kbd>
              </Command.Item>

              <Command.Item
                keywords={["mtge", "relacional", "gran escala", "eipd", "evaluacion", "volumne", "10000", "titulares", "rat maestro", "criterio a", "criterio b", "sensibles", "retencion"]}
                onSelect={() => ejecutarAccionNavegacion("mtge_relacional", "mtge_relacional")}
                className="flex items-center justify-between px-3 py-2 rounded-lg cursor-pointer transition text-zinc-300 hover:bg-[#1e1e24] hover:text-white data-[selected=true]:bg-[#1e1e24] data-[selected=true]:text-[#9a3bf1] data-[selected=true]:border data-[selected=true]:border-[#9a3bf1]/40"
              >
                <div className="flex items-center space-x-2.5">
                  <div className="p-1.5 rounded-md bg-[#0a0a0c] border border-[#26262b] text-zinc-400">
                    <Scale className="w-3.5 h-3.5 text-amber-400" />
                  </div>
                  <div>
                    <span className="font-medium text-xs text-white">
                      Ir a Motor MTGE Relacional · Gran Escala
                    </span>
                    <p className="text-[10px] text-zinc-400">
                      Evalúa RAT Maestro completo · Activa EIPD forzosa (Res. SPDP-SPD-2026-0005-R)
                    </p>
                  </div>
                </div>
                <kbd className="bg-[#0a0a0c] px-1.5 py-0.5 rounded border border-[#26262b] font-mono text-[10px] text-zinc-400">
                  ⌥M
                </kbd>
              </Command.Item>
            </Command.Group>

            {/* =================================================================== */}
            {/* GRUPO 2: Regulation as Code (Accesos Rápidos LOPDP & Normativas)   */}
            {/* =================================================================== */}
            <Command.Group
              heading="Regulation as Code (Accesos Rápidos LOPDP)"
              className="text-[10px] uppercase font-bold text-zinc-500 px-2.5 py-1 tracking-wider font-mono mt-2"
            >
              <Command.Item
                keywords={["corpus", "lopdp", "ley", "decretos", "reglamentos", "ecuador", "asamblea"]}
                onSelect={() => ejecutarAccionNavegacion("ia_chat", "regulacion_rag")}
                className="flex items-center justify-between px-3 py-2 rounded-lg cursor-pointer transition text-zinc-300 hover:bg-[#1e1e24] hover:text-white data-[selected=true]:bg-[#1e1e24] data-[selected=true]:text-[#9a3bf1] data-[selected=true]:border data-[selected=true]:border-[#9a3bf1]/40"
              >
                <div className="flex items-center space-x-2.5">
                  <div className="p-1.5 rounded-md bg-[#0a0a0c] border border-[#26262b] text-zinc-400">
                    <BookOpen className="w-3.5 h-3.5 text-[#3892f3]" />
                  </div>
                  <div>
                    <span className="font-medium text-xs text-white">
                      Buscar en Corpus LOPDP (Leyes/Decretos)
                    </span>
                    <p className="text-[10px] text-zinc-400">
                      Texto oficial codificado de la Ley Orgánica y Reglamento General
                    </p>
                  </div>
                </div>
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-[#0a0a0c] border border-[#26262b] text-zinc-400">
                  LOPDP
                </span>
              </Command.Item>

              <Command.Item
                keywords={["arco", "derechos", "acceso", "rectificacion", "cancelacion", "oposicion", "portabilidad", "art 21", "lopdp"]}
                onSelect={() => ejecutarAccionNavegacion("dpo", "dpo_cockpit")}
                className="flex items-center justify-between px-3 py-2 rounded-lg cursor-pointer transition text-zinc-300 hover:bg-[#1e1e24] hover:text-white data-[selected=true]:bg-[#1e1e24] data-[selected=true]:text-[#9a3bf1] data-[selected=true]:border data-[selected=true]:border-[#9a3bf1]/40"
              >
                <div className="flex items-center space-x-2.5">
                  <div className="p-1.5 rounded-md bg-[#0a0a0c] border border-[#26262b] text-zinc-400">
                    <ShieldCheck className="w-3.5 h-3.5 text-[#00c853]" />
                  </div>
                  <div>
                    <span className="font-medium text-xs text-white">
                      Ver Artículos Críticos de Derechos ARCO+
                    </span>
                    <p className="text-[10px] text-zinc-400">
                      Plazos obligatorios (15 días), excepciones legales y flujos de respuesta
                    </p>
                  </div>
                </div>
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-[#0a0a0c] border border-[#26262b] text-zinc-400">
                  Art. 21-28
                </span>
              </Command.Item>

              <Command.Item
                keywords={["resoluciones", "spdp", "2024", "2025", "2026", "mtge", "superintendencia", "2026-0005-r", "lopdp"]}
                onSelect={() => ejecutarAccionNavegacion("riesgos", "riesgos_mtge")}
                className="flex items-center justify-between px-3 py-2 rounded-lg cursor-pointer transition text-zinc-300 hover:bg-[#1e1e24] hover:text-white data-[selected=true]:bg-[#1e1e24] data-[selected=true]:text-[#9a3bf1] data-[selected=true]:border data-[selected=true]:border-[#9a3bf1]/40"
              >
                <div className="flex items-center space-x-2.5">
                  <div className="p-1.5 rounded-md bg-[#0a0a0c] border border-[#26262b] text-zinc-400">
                    <Scale className="w-3.5 h-3.5 text-amber-400" />
                  </div>
                  <div>
                    <span className="font-medium text-xs text-white">
                      Consultar Resoluciones SPDP 2024-2026
                    </span>
                    <p className="text-[10px] text-zinc-400">
                      Criterios vinculantes de Gran Escala MTGE y Registro Nacional
                    </p>
                  </div>
                </div>
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-[#0a0a0c] border border-[#26262b] text-zinc-400">
                  SPDP 2026
                </span>
              </Command.Item>

              <Command.Item
                keywords={["niif", "nic 38", "erp", "estados financieros", "intangibles", "normativa"]}
                onSelect={() => ejecutarCambioNormativa("NIIF")}
                className="flex items-center justify-between px-3 py-2 rounded-lg cursor-pointer transition text-zinc-300 hover:bg-[#1e1e24] hover:text-white data-[selected=true]:bg-[#1e1e24] data-[selected=true]:text-[#9a3bf1] data-[selected=true]:border data-[selected=true]:border-[#9a3bf1]/40"
              >
                <div className="flex items-center space-x-2.5">
                  <div className="p-1.5 rounded-md bg-[#0a0a0c] border border-[#26262b] text-zinc-400">
                    <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-400" />
                  </div>
                  <div>
                    <span className="font-medium text-xs text-white">
                      Filtrar por Normativa NIIF / NIC 38 (ERP)
                    </span>
                    <p className="text-[10px] text-zinc-400">
                      Auditoría de activos intangibles y logs contables
                    </p>
                  </div>
                </div>
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-[#0a0a0c] border border-[#26262b] text-zinc-400">
                  NIC 38
                </span>
              </Command.Item>
            </Command.Group>

            {/* =================================================================== */}
            {/* GRUPO 3: Acciones Globales                                          */}
            {/* =================================================================== */}
            <Command.Group
              heading="Acciones Globales"
              className="text-[10px] uppercase font-bold text-zinc-500 px-2.5 py-1 tracking-wider font-mono mt-2"
            >
              <Command.Item
                keywords={["generar", "banco", "podado", "podar", "zustand", "calibrar", "criterios"]}
                onSelect={ejecutarGenerarBancoPodado}
                className="flex items-center justify-between px-3 py-2 rounded-lg cursor-pointer transition text-zinc-300 hover:bg-[#1e1e24] hover:text-white data-[selected=true]:bg-[#1e1e24] data-[selected=true]:text-[#9a3bf1] data-[selected=true]:border data-[selected=true]:border-[#9a3bf1]/40"
              >
                <div className="flex items-center space-x-2.5">
                  <div className="p-1.5 rounded-md bg-[#0a0a0c] border border-[#26262b] text-zinc-400">
                    <Sparkles className="w-3.5 h-3.5 text-[#9a3bf1]" />
                  </div>
                  <div>
                    <span className="font-medium text-xs text-white">
                      Generar Banco Podado
                    </span>
                    <p className="text-[10px] text-zinc-400">
                      Activa el motor Zustand y habilita la inferencia del Agente IA Legal
                    </p>
                  </div>
                </div>
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-[#9a3bf1]/15 text-[#9a3bf1] border border-[#9a3bf1]/30">
                  Mutación Zustand
                </span>
              </Command.Item>

              <Command.Item
                keywords={["exportar", "informe", "reporte", "tecnico", "brechas", "pdf", "descargar"]}
                onSelect={ejecutarExportarPdf}
                className="flex items-center justify-between px-3 py-2 rounded-lg cursor-pointer transition text-zinc-300 hover:bg-[#1e1e24] hover:text-white data-[selected=true]:bg-[#1e1e24] data-[selected=true]:text-[#9a3bf1] data-[selected=true]:border data-[selected=true]:border-[#9a3bf1]/40"
              >
                <div className="flex items-center space-x-2.5">
                  <div className="p-1.5 rounded-md bg-[#0a0a0c] border border-[#26262b] text-zinc-400">
                    <Download className="w-3.5 h-3.5 text-[#3892f3]" />
                  </div>
                  <div>
                    <span className="font-medium text-xs text-white">
                      Exportar Informe Técnico de Brechas (PDF)
                    </span>
                    <p className="text-[10px] text-zinc-400">
                      Descarga el dictamen consolidado con hashes de trazabilidad SHA-256
                    </p>
                  </div>
                </div>
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-[#0a0a0c] border border-[#26262b] text-zinc-400">
                  PDF / SHA-256
                </span>
              </Command.Item>

              <Command.Item
                keywords={["tema", "theme", "claro", "oscuro", "dark", "light", "modo", "color", "acromatico"]}
                onSelect={ejecutarAlternarTema}
                className="flex items-center justify-between px-3 py-2 rounded-lg cursor-pointer transition text-zinc-300 hover:bg-[#1e1e24] hover:text-white data-[selected=true]:bg-[#1e1e24] data-[selected=true]:text-[#9a3bf1] data-[selected=true]:border data-[selected=true]:border-[#9a3bf1]/40"
              >
                <div className="flex items-center space-x-2.5">
                  <div className="p-1.5 rounded-md bg-[#0a0a0c] border border-[#26262b] text-zinc-400">
                    {theme === "dark" ? (
                      <Sun className="w-3.5 h-3.5 text-amber-400" />
                    ) : (
                      <Moon className="w-3.5 h-3.5 text-zinc-300" />
                    )}
                  </div>
                  <div>
                    <span className="font-medium text-xs text-white">
                      Alternar Tema ({theme === "dark" ? "Cambiar a Claro" : "Cambiar a Oscuro"})
                    </span>
                    <p className="text-[10px] text-zinc-400">
                      Modo acromático de alta legibilidad para erradicación de fatiga visual
                    </p>
                  </div>
                </div>
                <kbd className="bg-[#0a0a0c] px-1.5 py-0.5 rounded border border-[#26262b] font-mono text-[10px] text-zinc-400">
                  ⌥T
                </kbd>
              </Command.Item>
            </Command.Group>
          </Command.List>

          {/* Footer de la Paleta de Comandos Estilo Render (#0a0a0c, bordes #26262b) */}
          <div className="flex items-center justify-between px-4 py-2.5 bg-[#0a0a0c] border-t border-[#26262b] text-[10px] text-zinc-500 shrink-0">
            <div className="flex items-center space-x-2">
              <CommandIcon className="w-3.5 h-3.5 text-[#9a3bf1]" />
              <span className="font-medium text-zinc-400">
                cmdk · JUBYS LOPDP 360
              </span>
            </div>

            <div className="flex items-center space-x-3 text-zinc-500">
              <span className="hidden sm:inline">
                Navegar <kbd className="bg-[#141417] px-1 py-0.5 rounded border border-[#26262b] text-zinc-400 font-mono">↑↓</kbd>
              </span>
              <span className="hidden sm:inline">
                Seleccionar <kbd className="bg-[#141417] px-1 py-0.5 rounded border border-[#26262b] text-zinc-400 font-mono">↵</kbd>
              </span>
              <span>
                Salir <kbd className="bg-[#141417] px-1.5 py-0.5 rounded border border-[#26262b] text-zinc-400 font-mono">ESC</kbd>
              </span>
            </div>
          </div>
        </Command>
      </div>
    </div>
  );
}

