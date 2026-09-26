"use client";

import React, { useState, useEffect, useTransition, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import {
  Clock,
  AlertTriangle,
  CheckCircle2,
  Copy,
  Check,
  Plus,
  RefreshCw,
  Search,
  AlertOctagon,
  Shield,
  Send,
  UploadCloud,
  File,
  X,
} from "lucide-react";
import {
  Incidente,
  RegistrarVulneracionInput,
  CalculoCuentaRegresiva,
} from "@/types/incidente";
import {
  registrarVulneracion,
  previsualizarCuentaRegresiva,
  obtenerBitacoraIncidentes,
} from "@/app/actions/incidentActions";

export default function IncidentPlaybook() {
  // Estados de datos
  const [incidentes, setIncidentes] = useState<Incidente[]>([]);
  const [searchTerm, setSearchTerm] = useState<string>("");
  const [filtroSeveridad, setFiltroSeveridad] = useState<string>("TODAS");
  const [hasCopiedId, setHasCopiedId] = useState<string | null>(null);
  const [mostrarFormulario, setMostrarFormulario] = useState<boolean>(false);
  const [notificacionExito, setNotificacionExito] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // useTransition para ejecuciones asíncronas no bloqueantes
  const [isPending, startTransition] = useTransition();

  // Formulario reactivo
  const ahoraIsoLocal = () => {
    const d = new Date();
    d.setMinutes(d.getMinutes() - d.getTimezoneOffset());
    return d.toISOString().slice(0, 16);
  };

  const [fechaDeteccionLocal, setFechaDeteccionLocal] = useState<string>(ahoraIsoLocal());
  const [titulo, setTitulo] = useState<string>("");
  const [descripcion, setDescripcion] = useState<string>("");
  const [severidad, setSeveridad] = useState<"Baja" | "Media" | "Alta" | "Crítica">("Alta");
  const [afectaDatos, setAfectaDatos] = useState<boolean>(true);
  const [categoriasSeleccionadas, setCategoriasSeleccionadas] = useState<string[]>([
    "Identificativos (Cédula / Nombres)",
    "Contacto (Email / Teléfono)",
  ]);
  const [medidasInmediatas, setMedidasInmediatas] = useState<string>("");
  const [reportadoPor, setReportadoPor] = useState<string>("Oficial de Seguridad / DPO");

  // Poka-Yoke: Evidencia (Purgada al cambiar severidad)
  const [evidencia, setEvidencia] = useState<globalThis.File | null>(null);
  useEffect(() => {
    setEvidencia(null);
  }, [severidad]);

  // Previsualización del reloj normativo
  const [previewSLA, setPreviewSLA] = useState<CalculoCuentaRegresiva | null>(null);

  const categoriasDisponibles = [
    "Identificativos (Cédula / Nombres)",
    "Contacto (Email / Teléfono)",
    "Financieros / Bancarios",
    "Datos de Salud / Sensibles",
    "Biométricos",
    "Credenciales de Acceso",
  ];

  const alternarCategoria = (cat: string) => {
    if (categoriasSeleccionadas.includes(cat)) {
      setCategoriasSeleccionadas(categoriasSeleccionadas.filter((c) => c !== cat));
    } else {
      setCategoriasSeleccionadas([...categoriasSeleccionadas, cat]);
    }
  };

  // Cargar bitácora
  const cargarBitacora = useCallback(() => {
    startTransition(async () => {
      setErrorMsg(null);
      try {
        const res = await obtenerBitacoraIncidentes();
        if (res.success && res.data) {
          setIncidentes(res.data);
        } else {
          setErrorMsg(res.error || "No se pudo recuperar la bitácora.");
        }
      } catch (err) {
        setErrorMsg(err instanceof Error ? err.message : "Error de comunicación con el servidor.");
      }
    });
  }, []);

  useEffect(() => {
    cargarBitacora();
  }, [cargarBitacora]);

  // Actualizar cálculo de cuenta regresiva al modificar fecha
  useEffect(() => {
    let cancelado = false;
    const actualizarPreview = async () => {
      try {
        const iso = new Date(fechaDeteccionLocal).toISOString();
        const res = await previsualizarCuentaRegresiva(iso);
        if (!cancelado && res.success && res.data) {
          setPreviewSLA(res.data);
        }
      } catch {
        // Ignorar fallas transitorias de parseo
      }
    };
    actualizarPreview();
    return () => {
      cancelado = true;
    };
  }, [fechaDeteccionLocal]);

  // Manejo de envío
  const handleRegistrar = (e: React.FormEvent) => {
    e.preventDefault();
    if (!titulo.trim()) {
      setErrorMsg("Debe especificar un título o descripción breve del incidente.");
      return;
    }

    startTransition(async () => {
      setErrorMsg(null);
      setNotificacionExito(null);
      try {
        const payload: RegistrarVulneracionInput = {
          fechaDeteccion: new Date(fechaDeteccionLocal).toISOString(),
          titulo: titulo.trim(),
          descripcion: descripcion.trim(),
          severidad,
          afectacionDatosPersonales: afectaDatos,
          categoriaDatosAfectados: categoriasSeleccionadas,
          medidasInmediatas: medidasInmediatas.trim(),
          reportadoPor: reportadoPor.trim(),
        };

        const res = await registrarVulneracion(payload);
        if (res.success && res.data) {
          setNotificacionExito(
            `[TAMPER_EVIDENT] Vulneración registrada con ID: ${res.data.id}. SLA legal 72h activado con éxito.`
          );
          setTitulo("");
          setDescripcion("");
          setMedidasInmediatas("");
          setMostrarFormulario(false);
          await cargarBitacora();
        } else {
          setErrorMsg(res.error || "No se pudo registrar la vulneración.");
        }
      } catch (err) {
        setErrorMsg(err instanceof Error ? err.message : "Error registrando vulneración.");
      }
    });
  };

  const copiarTexto = (texto: string, id: string) => {
    if (navigator.clipboard) {
      navigator.clipboard.writeText(texto);
      setHasCopiedId(id);
      setTimeout(() => setHasCopiedId(null), 2000);
    }
  };

  const formatearFecha = (iso: string) => {
    try {
      const d = new Date(iso);
      return new Intl.DateTimeFormat("es-EC", {
        day: "2-digit",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      }).format(d);
    } catch {
      return iso;
    }
  };

  // Filtrado de incidentes
  const incidentesFiltrados = incidentes.filter((inc) => {
    const matchTerm =
      !searchTerm.trim() ||
      inc.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (inc.titulo && inc.titulo.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (inc.sha256Seal && inc.sha256Seal.toLowerCase().includes(searchTerm.toLowerCase()));

    const matchSev =
      filtroSeveridad === "TODAS" || inc.severidad === filtroSeveridad;

    return matchTerm && matchSev;
  });

  return (
    <div className="max-w-5xl mx-auto space-y-6 font-sans pb-12 animate-in fade-in duration-200">
      {/* ========================================================================= */}
      {/* ENCABEZADO PRINCIPAL Y REGLA DE SLA LEGAL DE 72 HORAS                      */}
      {/* ========================================================================= */}
      <div className="p-5 rounded-xl bg-[#141417] border border-[#26262b] shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-lg bg-[#1e1e24] border border-[#26262b] flex items-center justify-center text-[#ff1744] shadow-inner">
            <AlertOctagon className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-base font-bold text-white tracking-tight">
                Playbook de Incidentes & Bitácora Inviolable
              </h1>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#ff1744]/15 text-[#ff1744] border border-[#ff1744]/30 font-semibold">
                SLA Legal 72h
              </span>
            </div>
            <p className="text-xs text-zinc-400 mt-0.5">
              Cómputo perentorio de notificación de brechas conforme a la{" "}
              <strong className="text-zinc-200">Ley de Ciberseguridad 2026</strong> y Art. 40 LOPDP.
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2.5">
          <button
            type="button"
            onClick={cargarBitacora}
            disabled={isPending}
            className="p-2 rounded-lg bg-[#1e1e24] hover:bg-[#26262b] border border-[#26262b] text-zinc-400 hover:text-white transition cursor-pointer"
            title="Refrescar bitácora desde disco"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isPending ? "animate-spin text-[#9a3bf1]" : ""}`} />
          </button>

          <button
            type="button"
            onClick={() => setMostrarFormulario(!mostrarFormulario)}
            className="px-4 py-2 rounded-lg bg-[#9a3bf1] hover:bg-[#8529e0] text-white text-xs font-semibold flex items-center space-x-1.5 transition cursor-pointer shadow-lg shadow-[#9a3bf1]/20 hover:scale-[1.02]"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>{mostrarFormulario ? "Ocultar Reporte" : "Reportar Vulneración"}</span>
          </button>
        </div>
      </div>

      {/* Banner de Éxito / Alerta de Auditoría */}
      {notificacionExito && (
        <div className="p-3.5 rounded-lg bg-[#00c853]/10 border border-[#00c853]/30 text-[#00c853] text-xs font-mono flex items-center justify-between animate-in fade-in">
          <div className="flex items-center space-x-2">
            <CheckCircle2 className="w-4 h-4 shrink-0" />
            <span>{notificacionExito}</span>
          </div>
          <button
            type="button"
            onClick={() => setNotificacionExito(null)}
            className="text-zinc-400 hover:text-white"
          >
            ✕
          </button>
        </div>
      )}

      {errorMsg && (
        <div className="p-3.5 rounded-lg bg-[#ff1744]/10 border border-[#ff1744]/30 text-[#ff1744] text-xs font-mono flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 shrink-0" />
            <span>{errorMsg}</span>
          </div>
          <button
            type="button"
            onClick={() => setErrorMsg(null)}
            className="text-zinc-400 hover:text-white"
          >
            ✕
          </button>
        </div>
      )}

      {/* ========================================================================= */}
      {/* FORMULARIO DE REPORTE Y PREVISUALIZACIÓN DE CUENTA REGRESIVA              */}
      {/* ========================================================================= */}
      {mostrarFormulario && (
        <form
          onSubmit={handleRegistrar}
          className="p-6 rounded-xl bg-[#141417] border border-[#9a3bf1]/40 shadow-xl space-y-6 animate-in slide-in-from-top-2 duration-300"
        >
          <div className="flex items-center justify-between border-b border-[#26262b] pb-3">
            <div className="flex items-center space-x-2">
              <Shield className="w-4 h-4 text-[#9a3bf1]" />
              <h2 className="text-sm font-bold text-white tracking-tight">
                Declaración Formal de Vulneración de Seguridad
              </h2>
            </div>
            <span className="text-[10px] font-mono text-zinc-400">
              Reloj legal sellado por el servidor
            </span>
          </div>

          {/* Tarjeta de Cuenta Regresiva Previsualizada */}
          {previewSLA && (
            <div className="p-4 rounded-lg bg-[#0a0a0c] border border-[#26262b] flex flex-col md:flex-row items-center justify-between gap-4">
              <div className="space-y-1">
                <div className="flex items-center space-x-2">
                  <Clock className="w-3.5 h-3.5 text-[#9a3bf1]" />
                  <span className="text-xs font-bold text-zinc-200">
                    SLA Legal de Notificación (72 Horas Perentorias):
                  </span>
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                      previewSLA.estadoSLA === "A Tiempo"
                        ? "bg-[#00c853]/15 text-[#00c853] border border-[#00c853]/30"
                        : previewSLA.estadoSLA === "Crítico"
                        ? "bg-[#ffb300]/15 text-[#ffb300] border border-[#ffb300]/30 animate-pulse"
                        : "bg-[#ff1744]/15 text-[#ff1744] border border-[#ff1744]/30"
                    }`}
                  >
                    {previewSLA.estadoSLA.toUpperCase()}
                  </span>
                </div>
                <p className="text-[11px] text-zinc-400 font-mono">
                  Límite legal:{" "}
                  <strong className="text-white">
                    {formatearFecha(previewSLA.fechaLimiteNotificacion)}
                  </strong>
                </p>
              </div>

              {/* Display de Tiempo Restante */}
              <div className="flex items-center space-x-3">
                <div className="text-center px-3 py-1.5 rounded-lg bg-[#141417] border border-[#26262b]">
                  <div className="text-lg font-extrabold text-white font-mono">
                    {previewSLA.horasRestantes}h
                  </div>
                  <div className="text-[9px] text-zinc-500 font-mono uppercase">Horas</div>
                </div>
                <span className="text-zinc-600 font-mono font-bold">:</span>
                <div className="text-center px-3 py-1.5 rounded-lg bg-[#141417] border border-[#26262b]">
                  <div className="text-lg font-extrabold text-white font-mono">
                    {previewSLA.minutosRestantes}m
                  </div>
                  <div className="text-[9px] text-zinc-500 font-mono uppercase">Minutos</div>
                </div>
                <span className="text-zinc-600 font-mono font-bold">:</span>
                <div className="text-center px-3 py-1.5 rounded-lg bg-[#141417] border border-[#26262b]">
                  <div className="text-lg font-extrabold text-white font-mono">
                    {previewSLA.segundosRestantes}s
                  </div>
                  <div className="text-[9px] text-zinc-500 font-mono uppercase">Segundos</div>
                </div>
              </div>
            </div>
          )}

          {/* Campos del Formulario */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-zinc-300">
                Título del Incidente *
              </label>
              <input
                type="text"
                required
                value={titulo}
                onChange={(e) => setTitulo(e.target.value)}
                placeholder="ej: Exfiltración de base de datos de clientes por API desprotegida"
                className="w-full px-3 py-2 text-xs bg-[#0a0a0c] border border-[#26262b] rounded-lg text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-[#9a3bf1]"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-zinc-300">
                Momento de Detección (Fecha y Hora) *
              </label>
              <input
                type="datetime-local"
                required
                value={fechaDeteccionLocal}
                onChange={(e) => setFechaDeteccionLocal(e.target.value)}
                className="w-full px-3 py-2 text-xs bg-[#0a0a0c] border border-[#26262b] rounded-lg text-zinc-100 focus:outline-none focus:border-[#9a3bf1]"
              />
            </div>
          </div>

          {/* Matriz de Severidad */}
          <div className="space-y-2">
            <label className="text-xs font-semibold text-zinc-300 block">
              Matriz de Clasificación de Severidad Técnica
            </label>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {(["Baja", "Media", "Alta", "Crítica"] as const).map((nivel) => {
                const activo = severidad === nivel;
                let bgActive = "";
                let borderActive = "";
                
                if (nivel === "Baja") { bgActive = "bg-[#141417]"; borderActive = "border-zinc-500"; }
                if (nivel === "Media") { bgActive = "bg-amber-950/20"; borderActive = "border-amber-500/50"; }
                if (nivel === "Alta") { bgActive = "bg-orange-950/20"; borderActive = "border-orange-500/50"; }
                if (nivel === "Crítica") { bgActive = "bg-rose-950/20"; borderActive = "border-rose-500/50"; }

                return (
                  <div
                    key={nivel}
                    onClick={() => setSeveridad(nivel)}
                    className={`p-3 rounded-lg border cursor-pointer transition-all ${
                      activo 
                        ? `${bgActive} ${borderActive} shadow-sm shadow-[#9a3bf1]/5` 
                        : "bg-[#0a0a0c] border-[#26262b] hover:border-[#3a3a42] opacity-60 hover:opacity-100"
                    }`}
                  >
                    <div className={`font-bold text-xs mb-1 ${activo ? "text-white" : "text-zinc-400"}`}>
                      {nivel}
                    </div>
                    <div className="text-[10px] text-zinc-500 leading-tight">
                      {nivel === "Baja" && "Sin impacto en titulares"}
                      {nivel === "Media" && "Afectación acotada interna"}
                      {nivel === "Alta" && "Riesgo significativo"}
                      {nivel === "Crítica" && "Fuga masiva / Sensibles"}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-zinc-300">
              Oficial / DPO que Reporta
            </label>
            <input
              type="text"
              value={reportadoPor}
              onChange={(e) => setReportadoPor(e.target.value)}
              placeholder="Nombre o cargo del responsable"
              className="w-full px-3 py-2 text-xs bg-[#0a0a0c] border border-[#26262b] rounded-lg text-zinc-100 focus:outline-none focus:border-[#9a3bf1]"
            />
          </div>

          {/* Checkbox Afectación de Datos Personales */}
          <div className="p-3 rounded-lg bg-[#0a0a0c] border border-[#26262b] space-y-2">
            <label className="flex items-center space-x-2.5 cursor-pointer">
              <input
                type="checkbox"
                checked={afectaDatos}
                onChange={(e) => setAfectaDatos(e.target.checked)}
                className="rounded border-[#26262b] text-[#9a3bf1] focus:ring-0 cursor-pointer"
              />
              <span className="text-xs font-semibold text-zinc-200">
                Compromete Datos Personales de Titulares (Activa notificación imperativa SPDP)
              </span>
            </label>

            {afectaDatos && (
              <div className="pt-2">
                <span className="text-[11px] text-zinc-400 font-mono block mb-1.5">
                  Categorías de datos afectados:
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {categoriasDisponibles.map((cat) => {
                    const activa = categoriasSeleccionadas.includes(cat);
                    return (
                      <button
                        key={cat}
                        type="button"
                        onClick={() => alternarCategoria(cat)}
                        className={`px-2.5 py-1 rounded text-[10px] font-mono transition cursor-pointer ${
                          activa
                            ? "bg-[#9a3bf1]/20 text-[#9a3bf1] border border-[#9a3bf1]/40 font-semibold"
                            : "bg-[#141417] text-zinc-400 border border-[#26262b] hover:text-white"
                        }`}
                      >
                        {activa ? "✓ " : "+ "}
                        {cat}
                      </button>
                    );
                  })}
                </div>
              </div>
            )}
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-zinc-300">
              Descripción del Vector de Ataque y Acciones Inmediatas de Contención
            </label>
            <textarea
              rows={3}
              value={medidasInmediatas}
              onChange={(e) => setMedidasInmediatas(e.target.value)}
              placeholder="Describa el vector de vulneración identificado, puertos cerrados, credenciales revocadas o aislamiento perimetral..."
              className="w-full px-3 py-2 text-xs bg-[#0a0a0c] border border-[#26262b] rounded-lg text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-[#9a3bf1]"
            />
          </div>

          {/* Área Dropzone de Evidencia (Poka-Yoke) */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-zinc-300">
              Evidencia del Incidente (Logs, Capturas) *
            </label>
            {!evidencia ? (
              <DropzoneArea onUpload={(f) => setEvidencia(f)} />
            ) : (
              <div className="p-3 bg-[#0a0a0c] border border-[#26262b] rounded-lg flex items-center justify-between">
                <div className="flex items-center space-x-2 truncate">
                  <File className="w-4 h-4 text-[#9a3bf1] shrink-0" />
                  <span className="text-xs text-zinc-300 truncate font-mono">
                    {evidencia.name}
                  </span>
                  <span className="text-[10px] text-zinc-500">
                    ({(evidencia.size / 1024).toFixed(1)} KB)
                  </span>
                </div>
                <button
                  type="button"
                  onClick={() => setEvidencia(null)}
                  className="p-1 text-zinc-500 hover:text-[#ff1744] transition"
                  title="Eliminar evidencia"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            )}
            <p className="text-[10px] text-zinc-500 italic mt-1 border-l-2 border-[#3892f3] pl-2">
              Poka-Yoke: La evidencia adjunta será purgada automáticamente si cambias el Nivel de Severidad Técnica, forzando re-validación.
            </p>
          </div>

          <div className="flex items-center justify-end space-x-3 pt-2">
            <button
              type="button"
              onClick={() => setMostrarFormulario(false)}
              className="px-4 py-2 rounded-lg bg-[#1e1e24] hover:bg-[#26262b] text-zinc-300 text-xs font-medium transition cursor-pointer"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={isPending || !evidencia}
              className="px-5 py-2 rounded-lg bg-[#ff1744] hover:bg-[#d50000] text-white text-xs font-bold flex items-center space-x-1.5 transition cursor-pointer shadow-lg shadow-[#ff1744]/20 disabled:opacity-50"
              title={!evidencia ? "Requiere adjuntar evidencia para continuar" : ""}
            >
              <Send className="w-3.5 h-3.5" />
              <span>{isPending ? "Sellando en Servidor..." : "Registrar Vulneración e Iniciar SLA"}</span>
            </button>
          </div>
        </form>
      )}

      {/* ========================================================================= */}
      {/* LISTADO DE LA BITÁCORA INVIOLABLE (APPEND-ONLY CON SELLO SHA-256)         */}
      {/* ========================================================================= */}
      <div className="p-5 rounded-xl bg-[#141417] border border-[#26262b] shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#26262b] pb-3">
          <div>
            <h3 className="text-sm font-bold text-white tracking-tight flex items-center space-x-2">
              <span>Bitácora Histórica de Incidentes (Tamper-Evident)</span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#1e1e24] text-zinc-300 border border-[#26262b]">
                {incidentesFiltrados.length} Registros
              </span>
            </h3>
            <p className="text-[11px] text-zinc-400 font-mono mt-0.5">
              Almacenamiento append-only en <code className="text-zinc-300">data/incident_logs.json</code> con sellado criptográfico SHA-256.
            </p>
          </div>

          {/* Filtro y Buscador */}
          <div className="flex items-center space-x-2">
            <div className="relative">
              <Search className="w-3 h-3 text-zinc-500 absolute left-2.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Buscar por ID, título o hash..."
                className="pl-7 pr-2.5 py-1 text-xs bg-[#0a0a0c] border border-[#26262b] rounded-md text-zinc-200 placeholder-zinc-500 focus:outline-none focus:border-[#9a3bf1] w-48"
              />
            </div>

            <select
              value={filtroSeveridad}
              onChange={(e) => setFiltroSeveridad(e.target.value)}
              className="px-2 py-1 text-xs bg-[#0a0a0c] border border-[#26262b] rounded-md text-zinc-300 focus:outline-none focus:border-[#9a3bf1]"
            >
              <option value="TODAS">Todas las Severidades</option>
              <option value="Crítica">Crítica</option>
              <option value="Alta">Alta</option>
              <option value="Media">Media</option>
              <option value="Baja">Baja</option>
            </select>
          </div>
        </div>

        {/* Estado Vacío */}
        {incidentesFiltrados.length === 0 ? (
          <div className="py-12 text-center space-y-3">
            <div className="w-12 h-12 rounded-xl bg-[#1e1e24] border border-[#26262b] mx-auto flex items-center justify-center text-zinc-500">
              <Shield className="w-6 h-6" />
            </div>
            <p className="text-xs text-zinc-400">
              No se han registrado vulneraciones activas en la bitácora.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {incidentesFiltrados.map((inc) => (
              <div
                key={inc.id}
                className="p-4 rounded-lg bg-[#0a0a0c] border border-[#26262b] hover:border-zinc-700 transition space-y-2.5 text-xs shadow-xs"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-center space-x-2">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                        inc.estadoSLA === "A Tiempo"
                          ? "bg-[#00c853]/15 text-[#00c853] border border-[#00c853]/30"
                          : inc.estadoSLA === "Crítico"
                          ? "bg-[#ffb300]/15 text-[#ffb300] border border-[#ffb300]/30 animate-pulse"
                          : "bg-[#ff1744]/15 text-[#ff1744] border border-[#ff1744]/30"
                      }`}
                    >
                      SLA: {inc.estadoSLA}
                    </span>

                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-mono font-semibold ${
                        inc.severidad === "Crítica"
                          ? "bg-rose-950/60 text-rose-300 border border-rose-800"
                          : inc.severidad === "Alta"
                          ? "bg-orange-950/60 text-orange-300 border border-orange-800"
                          : "bg-zinc-800 text-zinc-300 border border-zinc-700"
                      }`}
                    >
                      {inc.severidad}
                    </span>

                    <h4 className="font-bold text-white text-xs truncate max-w-md">
                      {inc.titulo}
                    </h4>
                  </div>

                  <span className="text-[10px] font-mono text-zinc-500">
                    Detectado: {formatearFecha(inc.fechaDeteccion)}
                  </span>
                </div>

                {/* Detalles y Medidas */}
                {inc.medidasInmediatas && (
                  <p className="text-[11px] text-zinc-400 bg-[#141417] p-2.5 rounded border border-[#26262b] leading-relaxed">
                    <strong className="text-zinc-300">Medidas de Contención:</strong>{" "}
                    {inc.medidasInmediatas}
                  </p>
                )}

                {/* Categorías de datos */}
                {inc.categoriaDatosAfectados && inc.categoriaDatosAfectados.length > 0 && (
                  <div className="flex flex-wrap items-center gap-1.5 text-[10px] font-mono text-zinc-400">
                    <span className="text-zinc-500">Datos Afectados:</span>
                    {inc.categoriaDatosAfectados.map((cat, idx) => (
                      <span
                        key={idx}
                        className="px-1.5 py-0.5 rounded bg-[#1e1e24] text-zinc-300 border border-[#26262b]"
                      >
                        {cat}
                      </span>
                    ))}
                  </div>
                )}

                {/* Footer del Registro: UUID y Sello SHA-256 */}
                <div className="pt-2 border-t border-[#26262b]/80 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-[10px] font-mono text-zinc-500">
                  <div className="flex items-center space-x-2 truncate">
                    <span className="text-zinc-400">UUID:</span>
                    <span className="text-zinc-300 truncate max-w-[200px]">{inc.id}</span>
                    <button
                      type="button"
                      onClick={() => copiarTexto(inc.id, `uuid-${inc.id}`)}
                      className="text-zinc-500 hover:text-white transition"
                      title="Copiar UUID"
                    >
                      {hasCopiedId === `uuid-${inc.id}` ? (
                        <Check className="w-3 h-3 text-[#00c853]" />
                      ) : (
                        <Copy className="w-3 h-3" />
                      )}
                    </button>
                  </div>

                  <div className="flex items-center space-x-2">
                    <span className="text-zinc-400">SHA-256:</span>
                    <span className="text-zinc-300 truncate max-w-[140px]" title={inc.sha256Seal}>
                      {inc.sha256Seal.slice(0, 16)}...
                    </span>
                    <button
                      type="button"
                      onClick={() => copiarTexto(inc.sha256Seal, `hash-${inc.id}`)}
                      className="text-zinc-500 hover:text-white transition"
                      title="Copiar Sello SHA-256 completo"
                    >
                      {hasCopiedId === `hash-${inc.id}` ? (
                        <Check className="w-3 h-3 text-[#00c853]" />
                      ) : (
                        <Copy className="w-3 h-3" />
                      )}
                    </button>
                    <span className="text-zinc-600">|</span>
                    <span className="text-zinc-400">Límite 72h:</span>
                    <span className="text-zinc-200 font-semibold">
                      {formatearFecha(inc.fechaLimiteNotificacion)}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// Subcomponente Dropzone para Poka-Yoke
function DropzoneArea({ onUpload }: { onUpload: (f: globalThis.File) => void }) {
  const onDrop = useCallback(
    (acceptedFiles: globalThis.File[]) => {
      if (acceptedFiles.length > 0) {
        onUpload(acceptedFiles[0]);
      }
    },
    [onUpload]
  );

  const { getRootProps, getInputProps, isDragActive, fileRejections } = useDropzone({
    onDrop,
    maxFiles: 1,
    accept: {
      'application/pdf': ['.pdf'],
      'image/png': ['.png'],
      'image/jpeg': ['.jpg', '.jpeg'],
      'text/plain': ['.log', '.txt'],
      'text/csv': ['.csv'],
      'application/json': ['.json']
    }
  });

  return (
    <div className="space-y-2">
      <div
        {...getRootProps()}
        className={`h-20 w-full rounded-lg border border-dashed flex flex-col items-center justify-center text-center cursor-pointer transition-colors px-2 ${
          isDragActive
            ? "border-[#9a3bf1] bg-[#9a3bf1]/10 text-[#9a3bf1]"
            : "border-[#3a3a42] bg-[#0a0a0c] hover:border-[#9a3bf1]/50 text-zinc-400 hover:text-zinc-300"
        }`}
      >
        <input {...getInputProps()} />
        <UploadCloud className="w-5 h-5 mb-1.5" />
        <span className="text-xs">
          {isDragActive ? "Suelta la evidencia aquí..." : "Clic o arrastra (PDF, LOG, PNG, JSON)"}
        </span>
      </div>
      
      {fileRejections.length > 0 && (
        <div className="text-[10px] text-[#ff1744] flex items-center mt-1">
          <AlertTriangle className="w-3 h-3 mr-1" />
          Archivo no permitido. Usa formatos autorizados.
        </div>
      )}
    </div>
  );
}
