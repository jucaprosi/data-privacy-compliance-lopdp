"use client";

import React, { useId, useState } from "react";
import { AlertCircle, CheckCircle2, CircleDashed, Loader2, OctagonAlert, Timer } from "lucide-react";

import type {
  AuditLogItem,
  RoadmapTask,
  TaskDetailsUpdate,
  TaskPriority,
  TaskStatus,
} from "@/types/roadmap";
import type { AccionesTarea } from "./permisos";

export const ESTADOS: Record<TaskStatus, string> = {
  pendiente: "Pendiente",
  en_progreso: "En progreso",
  completada: "Completada",
  bloqueada: "Bloqueada",
};

export const PRIORIDADES: Record<TaskPriority, string> = {
  critica: "Crítica",
  alta: "Alta",
  media: "Media",
};

const ICONO_ESTADO: Record<TaskStatus, React.ReactNode> = {
  pendiente: <CircleDashed className="w-3.5 h-3.5" aria-hidden="true" />,
  en_progreso: <Timer className="w-3.5 h-3.5" aria-hidden="true" />,
  completada: <CheckCircle2 className="w-3.5 h-3.5" aria-hidden="true" />,
  bloqueada: <OctagonAlert className="w-3.5 h-3.5" aria-hidden="true" />,
};

const TONO_ESTADO: Record<TaskStatus, string> = {
  pendiente: "border-zinc-500/50 text-zinc-300",
  en_progreso: "border-[#3892f3]/60 text-[#7db7f7]",
  completada: "border-[#00c853]/60 text-[#5fe39a]",
  bloqueada: "border-[#ff1744]/60 text-[#ff7b92]",
};

export interface ErrorAccion {
  mensaje: string;
  codigo?: string;
  accion?: string | null;
}

export interface TareaCardProps {
  tarea: RoadmapTask;
  acciones: AccionesTarea;
  ocupada: boolean;
  error: ErrorAccion | null;
  auditoria: AuditLogItem[] | null;
  nombreArea?: string;
  onCambiarEstado: (estado: TaskStatus) => void;
  onEditar: (detalles: TaskDetailsUpdate) => void;
  onAsignar: (usuarioId: string) => void;
  onVerAuditoria: () => void;
  onOcultarAuditoria: () => void;
  onVerEvidencia?: () => void;
}

const CAMPO =
  "w-full rounded-md bg-[#0a0a0c] border border-[#26262b] px-2.5 py-1.5 text-xs text-zinc-100 " +
  "focus:outline-none focus:ring-2 focus:ring-[#3892f3] disabled:opacity-60";
const BOTON =
  "inline-flex items-center gap-1.5 rounded-md border border-[#26262b] bg-[#1b1b20] px-2.5 py-1.5 text-xs " +
  "font-semibold text-zinc-100 hover:bg-[#23232a] focus:outline-none focus-visible:ring-2 focus-visible:ring-[#3892f3] " +
  "disabled:opacity-50 disabled:cursor-not-allowed";

export function TareaCard(props: TareaCardProps) {
  const { tarea, acciones, ocupada, error, auditoria, nombreArea } = props;
  const idBase = useId();
  const id = (campo: string) => `${idBase}-${campo}`;

  const [editando, setEditando] = useState(false);
  const [asignando, setAsignando] = useState(false);
  const [nuevoEstado, setNuevoEstado] = useState<TaskStatus>(tarea.status);
  const [usuarioId, setUsuarioId] = useState("");
  const [errorLocal, setErrorLocal] = useState<string | null>(null);
  const [edicion, setEdicion] = useState({
    title: tarea.title,
    priority: tarea.priority,
    start_date: tarea.start_date ?? "",
    end_date: tarea.end_date ?? "",
    kpi: tarea.kpi ?? "",
    deliverable: tarea.deliverable ?? "",
  });

  function guardarEdicion(evento: React.FormEvent) {
    evento.preventDefault();
    if (edicion.title.trim() === "") {
      setErrorLocal("El título no puede quedar vacío.");
      return;
    }
    if (edicion.start_date && edicion.end_date && edicion.end_date < edicion.start_date) {
      setErrorLocal("La fecha de fin no puede ser anterior a la de inicio.");
      return;
    }
    setErrorLocal(null);
    props.onEditar({
      title: edicion.title.trim(),
      priority: edicion.priority,
      start_date: edicion.start_date || null,
      end_date: edicion.end_date || null,
      kpi: edicion.kpi,
      deliverable: edicion.deliverable,
    });
    setEditando(false);
  }

  function guardarAsignacion(evento: React.FormEvent) {
    evento.preventDefault();
    if (usuarioId.trim() === "") {
      setErrorLocal("Indica el identificador de la persona responsable.");
      return;
    }
    setErrorLocal(null);
    props.onAsignar(usuarioId.trim());
    setAsignando(false);
    setUsuarioId("");
  }

  const tituloId = id("titulo");

  return (
    <article
      aria-labelledby={tituloId}
      data-testid={`tarea-${tarea.id}`}
      className="rounded-lg bg-[#0a0a0c] border border-[#26262b] p-4 space-y-3"
    >
      <header className="flex flex-wrap items-start justify-between gap-2">
        <div className="min-w-0">
          <h4 id={tituloId} className="text-sm font-semibold text-white">
            {tarea.title}
          </h4>
          <p className="text-[11px] text-zinc-500 mt-0.5">
            Control {tarea.control_ref} · Dimensión {tarea.dimension}
            {nombreArea ? ` · ${nombreArea}` : ""}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span
            data-testid={`estado-${tarea.id}`}
            className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[11px] font-semibold ${TONO_ESTADO[tarea.status]}`}
          >
            {ICONO_ESTADO[tarea.status]}
            {ESTADOS[tarea.status]}
          </span>
          <span className="inline-flex items-center rounded-full border border-[#ffb300]/50 px-2 py-0.5 text-[11px] font-semibold text-[#ffd166]">
            Prioridad {PRIORIDADES[tarea.priority].toLowerCase()}
          </span>
        </div>
      </header>

      <dl className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-1 text-xs text-zinc-300">
        <div className="flex gap-1.5">
          <dt className="text-zinc-500">Responsable:</dt>
          <dd data-testid={`responsable-${tarea.id}`}>{tarea.owner || "Sin asignar"}</dd>
        </div>
        <div className="flex gap-1.5">
          <dt className="text-zinc-500">Fechas:</dt>
          <dd>
            {tarea.start_date ?? "sin inicio"} a {tarea.end_date ?? "sin fin"}
          </dd>
        </div>
        {tarea.kpi && (
          <div className="flex gap-1.5 sm:col-span-2">
            <dt className="text-zinc-500">Indicador:</dt>
            <dd>{tarea.kpi}</dd>
          </div>
        )}
        {tarea.deliverable && (
          <div className="flex gap-1.5 sm:col-span-2">
            <dt className="text-zinc-500">Entregable:</dt>
            <dd>{tarea.deliverable}</dd>
          </div>
        )}
      </dl>

      <div className="flex flex-wrap items-center gap-2">
        {acciones.cambiarEstado && (
          <div className="flex items-center gap-1.5">
            <label htmlFor={id("estado")} className="sr-only">
              Nuevo estado de {tarea.title}
            </label>
            <select
              id={id("estado")}
              value={nuevoEstado}
              disabled={ocupada}
              onChange={(e) => setNuevoEstado(e.target.value as TaskStatus)}
              className={CAMPO + " !w-auto"}
            >
              {(Object.keys(ESTADOS) as TaskStatus[]).map((estado) => (
                <option key={estado} value={estado}>
                  {ESTADOS[estado]}
                </option>
              ))}
            </select>
            <button
              type="button"
              className={BOTON}
              disabled={ocupada || nuevoEstado === tarea.status}
              onClick={() => props.onCambiarEstado(nuevoEstado)}
            >
              Cambiar estado
            </button>
          </div>
        )}
        {acciones.editar && (
          <button type="button" className={BOTON} disabled={ocupada} onClick={() => setEditando((v) => !v)}>
            Editar detalles
          </button>
        )}
        {acciones.asignar && (
          <button type="button" className={BOTON} disabled={ocupada} onClick={() => setAsignando((v) => !v)}>
            Asignar responsable
          </button>
        )}
        {acciones.verEvidencia && props.onVerEvidencia && (
          <button type="button" className={BOTON} onClick={props.onVerEvidencia}>
            Ver evidencia
          </button>
        )}
        {acciones.verAuditoria && (
          <button
            type="button"
            className={BOTON}
            onClick={auditoria ? props.onOcultarAuditoria : props.onVerAuditoria}
            aria-expanded={Boolean(auditoria)}
          >
            {auditoria ? "Ocultar auditoría" : "Ver auditoría"}
          </button>
        )}
        {ocupada && <Loader2 className="w-4 h-4 animate-spin text-[#3892f3]" role="status" aria-label="Aplicando el cambio" />}
      </div>

      {editando && acciones.editar && (
        <form onSubmit={guardarEdicion} aria-label={`Editar ${tarea.title}`} className="grid grid-cols-1 sm:grid-cols-2 gap-3 border-t border-[#26262b] pt-3">
          <div className="sm:col-span-2">
            <label htmlFor={id("titulo-edicion")} className="block text-[11px] font-semibold text-zinc-300 mb-1">
              Título
            </label>
            <input
              id={id("titulo-edicion")}
              className={CAMPO}
              value={edicion.title}
              onChange={(e) => setEdicion({ ...edicion, title: e.target.value })}
            />
          </div>
          <div>
            <label htmlFor={id("prioridad")} className="block text-[11px] font-semibold text-zinc-300 mb-1">
              Prioridad
            </label>
            <select
              id={id("prioridad")}
              className={CAMPO}
              value={edicion.priority}
              onChange={(e) => setEdicion({ ...edicion, priority: e.target.value as TaskPriority })}
            >
              {(Object.keys(PRIORIDADES) as TaskPriority[]).map((p) => (
                <option key={p} value={p}>
                  {PRIORIDADES[p]}
                </option>
              ))}
            </select>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label htmlFor={id("inicio")} className="block text-[11px] font-semibold text-zinc-300 mb-1">
                Inicio
              </label>
              <input
                id={id("inicio")}
                type="date"
                className={CAMPO}
                value={edicion.start_date}
                onChange={(e) => setEdicion({ ...edicion, start_date: e.target.value })}
              />
            </div>
            <div>
              <label htmlFor={id("fin")} className="block text-[11px] font-semibold text-zinc-300 mb-1">
                Fin
              </label>
              <input
                id={id("fin")}
                type="date"
                className={CAMPO}
                value={edicion.end_date}
                onChange={(e) => setEdicion({ ...edicion, end_date: e.target.value })}
              />
            </div>
          </div>
          <div>
            <label htmlFor={id("kpi")} className="block text-[11px] font-semibold text-zinc-300 mb-1">
              Indicador
            </label>
            <input id={id("kpi")} className={CAMPO} value={edicion.kpi} onChange={(e) => setEdicion({ ...edicion, kpi: e.target.value })} />
          </div>
          <div>
            <label htmlFor={id("entregable")} className="block text-[11px] font-semibold text-zinc-300 mb-1">
              Entregable
            </label>
            <input
              id={id("entregable")}
              className={CAMPO}
              value={edicion.deliverable}
              onChange={(e) => setEdicion({ ...edicion, deliverable: e.target.value })}
            />
          </div>
          <div className="sm:col-span-2 flex gap-2">
            <button type="submit" className={BOTON} disabled={ocupada}>
              Guardar cambios
            </button>
            <button type="button" className={BOTON} onClick={() => setEditando(false)}>
              Cancelar
            </button>
          </div>
        </form>
      )}

      {asignando && acciones.asignar && (
        <form onSubmit={guardarAsignacion} aria-label={`Asignar ${tarea.title}`} className="flex flex-wrap items-end gap-2 border-t border-[#26262b] pt-3">
          <div className="flex-1 min-w-[12rem]">
            <label htmlFor={id("usuario")} className="block text-[11px] font-semibold text-zinc-300 mb-1">
              Identificador de la persona responsable
            </label>
            <input id={id("usuario")} className={CAMPO} value={usuarioId} onChange={(e) => setUsuarioId(e.target.value)} />
          </div>
          <button type="submit" className={BOTON} disabled={ocupada}>
            Confirmar asignación
          </button>
          <button type="button" className={BOTON} onClick={() => setAsignando(false)}>
            Cancelar
          </button>
        </form>
      )}

      {errorLocal && (
        <p role="alert" className="text-[11px] text-[#ff6b86]">
          {errorLocal}
        </p>
      )}

      {error && (
        <div role="alert" data-testid={`error-${tarea.id}`} className="flex items-start gap-2 p-2.5 rounded-md bg-[#ff1744]/10 border border-[#ff1744]/40 text-xs">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-[#ff1744]" aria-hidden="true" />
          <div className="space-y-0.5">
            <p>{error.mensaje}</p>
            {error.codigo && <p className="text-zinc-400">Código: {error.codigo}</p>}
            {error.accion && <p className="text-zinc-400">Acción requerida: {error.accion}</p>}
          </div>
        </div>
      )}

      {auditoria && (
        <section aria-label={`Auditoría de ${tarea.title}`} className="border-t border-[#26262b] pt-3 space-y-1.5">
          <h5 className="text-[11px] font-semibold uppercase tracking-wider text-zinc-400">Auditoría</h5>
          {auditoria.length === 0 ? (
            <p className="text-xs text-zinc-500">Esta tarea aún no tiene eventos registrados.</p>
          ) : (
            <ul className="space-y-1">
              {auditoria.map((evento) => (
                <li key={evento.id} className="text-xs text-zinc-300">
                  <span className="font-semibold">{evento.action}</span> · {evento.user_id ?? "sistema"} ·{" "}
                  {new Date(evento.timestamp).toLocaleString("es-EC")}
                </li>
              ))}
            </ul>
          )}
        </section>
      )}
    </article>
  );
}

export default TareaCard;
