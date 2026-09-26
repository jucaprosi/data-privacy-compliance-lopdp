"use client";

import React, { useCallback, useEffect, useRef, useState } from "react";
import {
  ChevronDown,
  ChevronRight,
  FilePlus2,
  FolderOpen,
  History,
  Save,
  X,
  AlertTriangle,
  FileText,
} from "lucide-react";
import { useAuditStore } from "@/store/useAuditStore";
import {
  abrirProyecto,
  guardarProyecto,
  listarProyectos,
  listarRecientes,
  type ResumenProyecto,
} from "@/lib/proyectos";

type Dialogo =
  | { tipo: "abrir"; proyectos: ResumenProyecto[] }
  | { tipo: "guardar"; nombre: string }
  | { tipo: "confirmar"; accion: AccionPendiente };

/** Acción que se ejecuta tras confirmar el descarte de cambios sin guardar. */
type AccionPendiente = { tipo: "nuevo" } | { tipo: "abrir"; id: string } | { tipo: "listar" };

interface Aviso {
  texto: string;
  error: boolean;
}

function formatearFecha(iso: string): string {
  const fecha = new Date(iso);
  if (Number.isNaN(fecha.getTime())) return "";
  return fecha.toLocaleString("es-EC", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function FileMenu() {
  const {
    proyectoActivo,
    cambiosSinGuardar,
    companyData,
    obtenerInstantanea,
    cargarProyecto,
    nuevoProyecto,
    marcarGuardado,
  } = useAuditStore();

  const [abierto, setAbierto] = useState(false);
  const [submenuRecientes, setSubmenuRecientes] = useState(false);
  const [recientes, setRecientes] = useState<ResumenProyecto[]>([]);
  const [dialogo, setDialogo] = useState<Dialogo | null>(null);
  const [aviso, setAviso] = useState<Aviso | null>(null);
  const contenedorRef = useRef<HTMLDivElement>(null);

  const cerrarMenu = useCallback(() => {
    setAbierto(false);
    setSubmenuRecientes(false);
  }, []);

  const mostrarAviso = useCallback((texto: string, error = false) => {
    setAviso({ texto, error });
  }, []);

  useEffect(() => {
    if (!aviso) return;
    const t = setTimeout(() => setAviso(null), 2800);
    return () => clearTimeout(t);
  }, [aviso]);

  // Cierre del desplegable al hacer clic fuera de él.
  useEffect(() => {
    if (!abierto) return;
    const alPulsar = (e: MouseEvent) => {
      if (!contenedorRef.current?.contains(e.target as Node)) cerrarMenu();
    };
    document.addEventListener("mousedown", alPulsar);
    return () => document.removeEventListener("mousedown", alPulsar);
  }, [abierto, cerrarMenu]);

  /* ----------------------------------------------------------------------- */
  /* Acciones                                                                 */
  /* ----------------------------------------------------------------------- */

  const persistir = useCallback(
    (nombre: string, id?: string): boolean => {
      const guardado = guardarProyecto(obtenerInstantanea(), nombre, id);
      if (!guardado) {
        mostrarAviso("No se pudo guardar: el almacenamiento del navegador no está disponible.", true);
        return false;
      }
      marcarGuardado({ id: guardado.id, nombre: guardado.nombre });
      mostrarAviso(`Proyecto «${guardado.nombre}» guardado`);
      return true;
    },
    [obtenerInstantanea, marcarGuardado, mostrarAviso]
  );

  const ejecutarAccion = useCallback(
    (accion: AccionPendiente) => {
      if (accion.tipo === "nuevo") {
        nuevoProyecto();
        setDialogo(null);
        mostrarAviso("Nuevo proyecto creado");
        return;
      }
      if (accion.tipo === "listar") {
        setDialogo({ tipo: "abrir", proyectos: listarProyectos() });
        return;
      }
      const proyecto = abrirProyecto(accion.id);
      if (!proyecto) {
        setDialogo(null);
        mostrarAviso("El proyecto ya no existe o está dañado.", true);
        return;
      }
      cargarProyecto(proyecto);
      setDialogo(null);
      mostrarAviso(`Proyecto «${proyecto.nombre}» abierto`);
    },
    [nuevoProyecto, cargarProyecto, mostrarAviso]
  );

  /** Antes de reemplazar el trabajo en curso, pide confirmación si hay cambios. */
  const conConfirmacion = useCallback(
    (accion: AccionPendiente) => {
      cerrarMenu();
      if (cambiosSinGuardar) {
        setDialogo({ tipo: "confirmar", accion });
      } else {
        ejecutarAccion(accion);
      }
    },
    [cambiosSinGuardar, cerrarMenu, ejecutarAccion]
  );

  const handleGuardar = useCallback(() => {
    cerrarMenu();
    if (proyectoActivo) {
      persistir(proyectoActivo.nombre, proyectoActivo.id);
    } else {
      setDialogo({
        tipo: "guardar",
        nombre: companyData.razonSocial.trim() || "Nuevo assessment",
      });
    }
  }, [cerrarMenu, proyectoActivo, persistir, companyData.razonSocial]);

  const handleAbrir = useCallback(() => {
    conConfirmacion({ tipo: "listar" });
  }, [conConfirmacion]);

  // Atajos de teclado: Ctrl/Cmd+S guarda y Ctrl/Cmd+O abre.
  useEffect(() => {
    const alTeclear = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        cerrarMenu();
        return;
      }
      if (!(e.ctrlKey || e.metaKey) || e.altKey || e.shiftKey) return;
      const tecla = e.key.toLowerCase();
      if (tecla === "s") {
        e.preventDefault();
        handleGuardar();
      } else if (tecla === "o") {
        e.preventDefault();
        handleAbrir();
      }
    };
    window.addEventListener("keydown", alTeclear);
    return () => window.removeEventListener("keydown", alTeclear);
  }, [cerrarMenu, handleGuardar, handleAbrir]);

  const alternarMenu = () => {
    if (!abierto) setRecientes(listarRecientes());
    setAbierto((v) => !v);
    setSubmenuRecientes(false);
  };

  /* ----------------------------------------------------------------------- */
  /* Render                                                                   */
  /* ----------------------------------------------------------------------- */

  const claseItem =
    "w-full flex items-center justify-between gap-6 px-2.5 py-1.5 rounded text-[11px] text-zinc-300 hover:bg-[#1e1e24] hover:text-white focus:bg-[#1e1e24] focus:text-white focus:outline-none cursor-pointer transition";

  return (
    <div ref={contenedorRef} className="relative flex items-center space-x-2">
      <button
        type="button"
        onClick={alternarMenu}
        aria-haspopup="menu"
        aria-expanded={abierto}
        className={`flex items-center space-x-1 px-2 py-1 rounded text-[11px] font-medium transition cursor-pointer ${
          abierto
            ? "bg-[#1e1e24] text-white"
            : "text-zinc-400 hover:text-white hover:bg-[#1e1e24]"
        }`}
      >
        <span>Archivo</span>
        <ChevronDown className="w-3 h-3" />
      </button>

      {/* Proyecto activo e indicador de cambios sin guardar */}
      <span
        className="hidden md:flex items-center space-x-1.5 text-[11px] text-zinc-400 max-w-[180px]"
        title={cambiosSinGuardar ? "Hay cambios sin guardar" : "Todos los cambios guardados"}
      >
        <FileText className="w-3 h-3 shrink-0 text-zinc-500" />
        <span className="truncate">{proyectoActivo?.nombre ?? "Sin guardar"}</span>
        {cambiosSinGuardar && (
          <span className="w-1.5 h-1.5 rounded-full bg-[#ffab00] shrink-0" aria-label="Cambios sin guardar" />
        )}
      </span>

      {abierto && (
        <div
          role="menu"
          className="absolute left-0 top-full mt-1.5 w-60 p-1 rounded-lg bg-[#141417] border border-[#26262b] shadow-2xl shadow-black/50 z-50"
        >
          <button type="button" role="menuitem" className={claseItem} onClick={() => conConfirmacion({ tipo: "nuevo" })}>
            <span className="flex items-center space-x-2">
              <FilePlus2 className="w-3.5 h-3.5 text-zinc-500" />
              <span>Nuevo</span>
            </span>
          </button>

          <button type="button" role="menuitem" className={claseItem} onClick={handleAbrir}>
            <span className="flex items-center space-x-2">
              <FolderOpen className="w-3.5 h-3.5 text-zinc-500" />
              <span>Abrir…</span>
            </span>
            <kbd className="font-mono text-[10px] text-zinc-500">Ctrl+O</kbd>
          </button>

          <div
            className="relative"
            onMouseEnter={() => setSubmenuRecientes(true)}
            onMouseLeave={() => setSubmenuRecientes(false)}
          >
            <button
              type="button"
              role="menuitem"
              aria-haspopup="menu"
              aria-expanded={submenuRecientes}
              className={`${claseItem} ${submenuRecientes ? "bg-[#1e1e24] text-white" : ""}`}
              onClick={() => setSubmenuRecientes((v) => !v)}
              onKeyDown={(e) => {
                if (e.key === "ArrowRight") setSubmenuRecientes(true);
                if (e.key === "ArrowLeft") setSubmenuRecientes(false);
              }}
            >
              <span className="flex items-center space-x-2">
                <History className="w-3.5 h-3.5 text-zinc-500" />
                <span>Abrir reciente</span>
              </span>
              <ChevronRight className="w-3 h-3 text-zinc-500" />
            </button>

            {submenuRecientes && (
              // El relleno izquierdo (en lugar de margen) mantiene el puntero
              // dentro del área del submenú al desplazarse hacia él.
              <div className="absolute left-full top-0 pl-1">
                <div
                  role="menu"
                  className="w-64 p-1 rounded-lg bg-[#141417] border border-[#26262b] shadow-2xl shadow-black/50"
                >
                  {recientes.length === 0 ? (
                    <p className="px-2.5 py-2 text-[11px] text-zinc-500">No hay proyectos recientes</p>
                  ) : (
                    recientes.map((r) => (
                      <button
                        key={r.id}
                        type="button"
                        role="menuitem"
                        className="w-full flex flex-col items-start px-2.5 py-1.5 rounded text-[11px] text-zinc-300 hover:bg-[#1e1e24] hover:text-white focus:bg-[#1e1e24] focus:text-white focus:outline-none cursor-pointer transition"
                        onClick={() => conConfirmacion({ tipo: "abrir", id: r.id })}
                      >
                        <span className="w-full truncate text-left">{r.nombre}</span>
                        <span className="text-[10px] text-zinc-500 font-mono">
                          {formatearFecha(r.actualizadoEn)}
                        </span>
                      </button>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>

          <div className="my-1 h-px bg-[#26262b]" />

          <button type="button" role="menuitem" className={claseItem} onClick={handleGuardar}>
            <span className="flex items-center space-x-2">
              <Save className="w-3.5 h-3.5 text-zinc-500" />
              <span>Guardar</span>
            </span>
            <kbd className="font-mono text-[10px] text-zinc-500">Ctrl+S</kbd>
          </button>
        </div>
      )}

      {/* Aviso transitorio de resultado */}
      {aviso && (
        <span
          role="status"
          className={`absolute left-0 top-full mt-1.5 whitespace-nowrap px-2.5 py-1 rounded text-[11px] border z-40 ${
            aviso.error
              ? "bg-[#ff1744]/15 text-[#ff1744] border-[#ff1744]/30"
              : "bg-[#00c853]/15 text-[#00c853] border-[#00c853]/30"
          } ${abierto ? "hidden" : ""}`}
        >
          {aviso.texto}
        </span>
      )}

      {dialogo && (
        <DialogoProyecto
          dialogo={dialogo}
          proyectoActivoId={proyectoActivo?.id}
          puedeGuardarDirecto={Boolean(proyectoActivo)}
          onCerrar={() => setDialogo(null)}
          onAbrir={(id) => ejecutarAccion({ tipo: "abrir", id })}
          onGuardarConNombre={(nombre) => {
            if (persistir(nombre)) setDialogo(null);
          }}
          onDescartar={(accion) => ejecutarAccion(accion)}
          onGuardarYContinuar={(accion) => {
            if (proyectoActivo && persistir(proyectoActivo.nombre, proyectoActivo.id)) {
              ejecutarAccion(accion);
            }
          }}
          onCambiarNombre={(nombre) => setDialogo({ tipo: "guardar", nombre })}
        />
      )}
    </div>
  );
}

/* ========================================================================= */
/* Diálogo modal: abrir, guardar con nombre y confirmación de descarte        */
/* ========================================================================= */

interface DialogoProyectoProps {
  dialogo: Dialogo;
  proyectoActivoId?: string;
  puedeGuardarDirecto: boolean;
  onCerrar: () => void;
  onAbrir: (id: string) => void;
  onGuardarConNombre: (nombre: string) => void;
  onDescartar: (accion: AccionPendiente) => void;
  onGuardarYContinuar: (accion: AccionPendiente) => void;
  onCambiarNombre: (nombre: string) => void;
}

function DialogoProyecto({
  dialogo,
  proyectoActivoId,
  puedeGuardarDirecto,
  onCerrar,
  onAbrir,
  onGuardarConNombre,
  onDescartar,
  onGuardarYContinuar,
  onCambiarNombre,
}: DialogoProyectoProps) {
  const titulo =
    dialogo.tipo === "abrir"
      ? "Abrir proyecto"
      : dialogo.tipo === "guardar"
      ? "Guardar proyecto"
      : "Cambios sin guardar";

  useEffect(() => {
    const alTeclear = (e: KeyboardEvent) => {
      if (e.key === "Escape") onCerrar();
    };
    window.addEventListener("keydown", alTeclear);
    return () => window.removeEventListener("keydown", alTeclear);
  }, [onCerrar]);

  const botonSecundario =
    "px-3.5 py-1.5 rounded-lg bg-[#1e1e24] hover:bg-[#26262b] border border-[#26262b] text-zinc-300 hover:text-white text-xs font-medium transition cursor-pointer";
  const botonPrimario =
    "px-3.5 py-1.5 rounded-lg bg-[#9a3bf1] hover:bg-[#8529e0] text-white text-xs font-semibold transition cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed";

  return (
    <div
      className="fixed inset-0 z-[60] flex items-center justify-center bg-black/60 px-4"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onCerrar();
      }}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label={titulo}
        className="w-full max-w-md rounded-xl bg-[#141417] border border-[#26262b] shadow-2xl"
      >
        <div className="flex items-center justify-between px-4 py-3 border-b border-[#26262b]">
          <h2 className="text-xs font-bold text-white uppercase tracking-wider">{titulo}</h2>
          <button
            type="button"
            onClick={onCerrar}
            className="text-zinc-500 hover:text-white transition cursor-pointer"
            aria-label="Cerrar"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {dialogo.tipo === "abrir" && (
          <div className="p-2 max-h-[360px] overflow-y-auto">
            {dialogo.proyectos.length === 0 ? (
              <p className="px-3 py-6 text-center text-[11px] text-zinc-500">
                Aún no hay proyectos guardados. Usa Archivo › Guardar para crear el primero.
              </p>
            ) : (
              dialogo.proyectos.map((p) => (
                <button
                  key={p.id}
                  type="button"
                  onClick={() => onAbrir(p.id)}
                  className="w-full text-left px-3 py-2.5 rounded-lg hover:bg-[#1e1e24] border border-transparent hover:border-[#26262b] transition cursor-pointer"
                >
                  <div className="flex items-center justify-between gap-3">
                    <span className="text-xs font-semibold text-white truncate">{p.nombre}</span>
                    {p.id === proyectoActivoId && (
                      <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-[#9a3bf1]/15 text-[#9a3bf1] border border-[#9a3bf1]/30 shrink-0">
                        Activo
                      </span>
                    )}
                  </div>
                  <div className="mt-0.5 flex items-center justify-between gap-3 text-[10px] text-zinc-500 font-mono">
                    <span className="truncate">{p.razonSocial || "Sin razón social"}</span>
                    <span className="shrink-0">
                      {p.respuestas} resp. · {formatearFecha(p.actualizadoEn)}
                    </span>
                  </div>
                </button>
              ))
            )}
          </div>
        )}

        {dialogo.tipo === "guardar" && (
          <form
            className="p-4 space-y-4"
            onSubmit={(e) => {
              e.preventDefault();
              onGuardarConNombre(dialogo.nombre);
            }}
          >
            <label className="block space-y-1.5">
              <span className="text-[11px] text-zinc-400 font-medium">Nombre del proyecto</span>
              <input
                autoFocus
                value={dialogo.nombre}
                onChange={(e) => onCambiarNombre(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && dialogo.nombre.trim()) {
                    e.preventDefault();
                    onGuardarConNombre(dialogo.nombre);
                  }
                }}
                maxLength={120}
                className="w-full bg-[#0a0a0c] border border-[#26262b] rounded-lg px-3 py-2 text-zinc-100 text-xs focus:outline-none focus:border-[#9a3bf1] transition select-text"
              />
            </label>
            <p className="text-[10px] text-zinc-500 leading-relaxed">
              El proyecto se guarda en este navegador. Los datos del assessment no se envían a
              ningún servidor.
            </p>
            <div className="flex justify-end gap-2">
              <button type="button" onClick={onCerrar} className={botonSecundario}>
                Cancelar
              </button>
              <button type="submit" disabled={!dialogo.nombre.trim()} className={botonPrimario}>
                Guardar
              </button>
            </div>
          </form>
        )}

        {dialogo.tipo === "confirmar" && (
          <div className="p-4 space-y-4">
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-4 h-4 text-[#ffab00] shrink-0 mt-0.5" />
              <p className="text-[11px] text-zinc-300 leading-relaxed">
                El proyecto actual tiene cambios sin guardar. Si continúas sin guardarlos, se
                perderán.
                {!puedeGuardarDirecto && (
                  <span className="block mt-1.5 text-zinc-500">
                    Para conservarlos, cancela y usa Archivo › Guardar antes de continuar.
                  </span>
                )}
              </p>
            </div>
            <div className="flex flex-wrap justify-end gap-2">
              <button type="button" onClick={onCerrar} className={botonSecundario}>
                Cancelar
              </button>
              <button
                type="button"
                onClick={() => onDescartar(dialogo.accion)}
                className="px-3.5 py-1.5 rounded-lg bg-[#ff1744]/15 hover:bg-[#ff1744]/25 border border-[#ff1744]/30 text-[#ff1744] text-xs font-semibold transition cursor-pointer"
              >
                Descartar cambios
              </button>
              {puedeGuardarDirecto && (
                <button
                  type="button"
                  onClick={() => onGuardarYContinuar(dialogo.accion)}
                  className={botonPrimario}
                >
                  Guardar y continuar
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
