"use client";

import React, { useCallback, useEffect, useMemo, useState } from "react";
import { AlertCircle, Loader2 } from "lucide-react";

import { fetchAutenticado } from "@/lib/auth/fetchAutenticado";
import { organizacionApi, roadmapApi } from "@/lib/roadmap/cliente";
import { useRoadmapStore } from "@/store/useRoadmapStore";
import { ApiError } from "@/types/roadmap";
import type { TaskStatus } from "@/types/roadmap";
import { accionesPermitidas, areasVisibles } from "../olas/permisos";
import { ESTADOS, TareaCard, type ErrorAccion } from "../olas/TareaCard";
import {
  agruparPorEstado,
  armarCronograma,
  esVencida,
  etiquetaOrigen,
  hoyGuayaquil,
  ORDEN_ESTADOS,
  VISTAS,
  type Vista,
} from "./logica";
import type { HallazgoItem, TareaConOrigen } from "./tipos";
import styles from "./VistasTareas.module.css";

export interface VistasTareasProps {
  roadmapId: string;
  /** Abre el hallazgo de origen de una tarea; sin él, el origen se muestra como texto. */
  onAbrirHallazgo?: (hallazgoId: string) => void;
}

const CLAVE_VISTA = "roadmap.vistas.vista";
const CON_FETCH = { customFetch: fetchAutenticado };

function vistaGuardada(): Vista {
  try {
    const v = window.sessionStorage.getItem(CLAVE_VISTA);
    if (v === "lista" || v === "tablero" || v === "cronograma") return v;
  } catch {
    /* sin sessionStorage: se usa la lista */
  }
  return "lista";
}

function aErrorAccion(err: unknown): ErrorAccion {
  if (err instanceof ApiError) return { mensaje: err.message, codigo: err.code, accion: err.action_required };
  return { mensaje: "No se pudo completar la acción. Inténtalo de nuevo." };
}

async function pedirHallazgos(): Promise<HallazgoItem[]> {
  // Un rol sin permiso de consulta recibe 403: las tarjetas simplemente no muestran origen.
  try {
    const r = await fetchAutenticado("/api/v1/roadmaps/hallazgos", { method: "GET" });
    if (!r.ok) return [];
    const cuerpo = (await r.json()) as { hallazgos?: HallazgoItem[] };
    return cuerpo.hallazgos ?? [];
  } catch {
    return [];
  }
}

export function VistasTareas({ roadmapId, onAbrirHallazgo }: VistasTareasProps) {
  const rol = useRoadmapStore((s) => s.session.role);
  const permisos = useMemo(() => ({ ...accionesPermitidas(rol), editar: false, asignar: false, verAuditoria: false, verEvidencia: false }), [rol]);

  const [vista, setVista] = useState<Vista>("lista");
  const [soloVencidas, setSoloVencidas] = useState(false);
  const [tareas, setTareas] = useState<TareaConOrigen[]>([]);
  const [hallazgos, setHallazgos] = useState<Record<string, HallazgoItem>>({});
  const [areasPermitidas, setAreasPermitidas] = useState<string[] | null>(null);
  const [cargando, setCargando] = useState(true);
  const [errorCarga, setErrorCarga] = useState<string | null>(null);
  const [acciones, setAcciones] = useState<Record<string, { ocupada: boolean; error: ErrorAccion | null }>>({});
  const [columnaSobre, setColumnaSobre] = useState<TaskStatus | null>(null);

  useEffect(() => setVista(vistaGuardada()), []);

  // R1 · una sola lectura: cambiar de vista no vuelve a pedir datos.
  useEffect(() => {
    let vigente = true;
    setCargando(true);
    setErrorCarga(null);
    (async () => {
      try {
        const [respuesta, lista, roles] = await Promise.all([
          roadmapApi.getRoadmap(roadmapId, CON_FETCH),
          pedirHallazgos(),
          rol === "responsable_area" ? organizacionApi.getMyRoles(CON_FETCH).catch(() => []) : Promise.resolve(null),
        ]);
        if (!vigente) return;
        setTareas((respuesta.waves ?? []).flatMap((w) => (w.tasks ?? []) as TareaConOrigen[]));
        setHallazgos(Object.fromEntries(lista.map((h) => [h.id, h])));
        setAreasPermitidas(roles === null ? null : areasVisibles(roles));
      } catch (err) {
        if (vigente) setErrorCarga(aErrorAccion(err).mensaje);
      } finally {
        if (vigente) setCargando(false);
      }
    })();
    return () => {
      vigente = false;
    };
  }, [roadmapId, rol]);

  const elegirVista = useCallback((v: Vista) => {
    setVista(v);
    try {
      window.sessionStorage.setItem(CLAVE_VISTA, v);
    } catch {
      /* la vista elegida sigue valiendo en esta pantalla */
    }
  }, []);

  const hoy = hoyGuayaquil();
  const alcance = useMemo(
    () => tareas.filter((t) => areasPermitidas === null || (t.area_id && areasPermitidas.includes(t.area_id))),
    [tareas, areasPermitidas],
  );
  const vencidas = alcance.filter((t) => esVencida(t, hoy)).length;
  const visibles = useMemo(() => (soloVencidas ? alcance.filter((t) => esVencida(t, hoy)) : alcance), [alcance, soloVencidas, hoy]);

  // R2 · arrastrar llama al cambio de estado existente; si falla, la tarjeta vuelve.
  async function cambiarEstado(tarea: TareaConOrigen, estado: TaskStatus) {
    if (tarea.status === estado || !permisos.cambiarEstado) return;
    const anterior = tarea.status;
    setAcciones((a) => ({ ...a, [tarea.id]: { ocupada: true, error: null } }));
    setTareas((ts) => ts.map((t) => (t.id === tarea.id ? { ...t, status: estado } : t)));
    try {
      await roadmapApi.updateTaskStatus(tarea.id, estado, CON_FETCH);
      setAcciones((a) => ({ ...a, [tarea.id]: { ocupada: false, error: null } }));
    } catch (err) {
      setTareas((ts) => ts.map((t) => (t.id === tarea.id ? { ...t, status: anterior } : t)));
      setAcciones((a) => ({ ...a, [tarea.id]: { ocupada: false, error: aErrorAccion(err) } }));
    }
  }

  function tarjeta(tarea: TareaConOrigen) {
    const h = tarea.hallazgo_id ? hallazgos[tarea.hallazgo_id] : undefined;
    const accion = acciones[tarea.id] ?? { ocupada: false, error: null };
    return (
      <TareaCard
        tarea={tarea}
        acciones={permisos}
        ocupada={accion.ocupada}
        error={accion.error}
        auditoria={null}
        origen={h ? { etiqueta: etiquetaOrigen(h.origen), onAbrir: onAbrirHallazgo ? () => onAbrirHallazgo(h.id) : undefined } : undefined}
        onCambiarEstado={(estado) => void cambiarEstado(tarea, estado)}
        onEditar={() => undefined}
        onAsignar={() => undefined}
        onVerAuditoria={() => undefined}
        onOcultarAuditoria={() => undefined}
      />
    );
  }

  if (cargando) {
    return (
      <div role="status" className="flex items-center gap-2 text-sm">
        <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" /> Cargando las tareas…
      </div>
    );
  }
  if (errorCarga) {
    return (
      <div role="alert" className="flex items-start gap-2 text-sm badge-render-danger rounded-md p-3">
        <AlertCircle className="w-4 h-4 mt-0.5" aria-hidden="true" /> {errorCarga}
      </div>
    );
  }

  const cronograma = armarCronograma(visibles);
  const grupos = agruparPorEstado(visibles);

  return (
    <section aria-label="Vistas del plan de acción" className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className={styles.selector} role="group" aria-label="Vista">
          {VISTAS.map((v) => (
            <button
              key={v.id}
              type="button"
              data-testid={`vista-${v.id}`}
              aria-pressed={vista === v.id}
              className={`${styles.boton} ${vista === v.id ? styles.activo : ""}`}
              onClick={() => elegirVista(v.id)}
            >
              {v.etiqueta}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-3 text-xs">
          <button
            type="button"
            data-testid="filtro-vencidas"
            aria-pressed={soloVencidas}
            className={`${styles.boton} ${soloVencidas ? styles.activo : ""}`}
            onClick={() => setSoloVencidas((v) => !v)}
          >
            Vencidas
          </button>
          <span data-testid="contador-vencidas" className="badge-render-danger rounded-full px-2 py-0.5 font-semibold" aria-label="Tareas vencidas">
            {vencidas}
          </span>
          <span data-testid="total-vistas" className={styles.suave}>
            {visibles.length} {visibles.length === 1 ? "tarea" : "tareas"}
          </span>
        </div>
      </div>

      {visibles.length === 0 && <p className={`text-sm ${styles.suave}`}>No hay tareas que mostrar.</p>}

      {vista === "lista" && (
        <ul className="space-y-3" aria-label="Lista de tareas">
          {visibles.map((t) => (
            <li key={t.id}>{tarjeta(t)}</li>
          ))}
        </ul>
      )}

      {vista === "tablero" && (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-3">
          {ORDEN_ESTADOS.map((estado) => (
            <div
              key={estado}
              data-testid={`columna-${estado}`}
              role="group"
              aria-label={ESTADOS[estado]}
              className={`${styles.columna} p-2 space-y-2 ${columnaSobre === estado ? styles.columnaSobre : ""}`}
              onDragOver={(e) => {
                if (!permisos.cambiarEstado) return;
                e.preventDefault();
                setColumnaSobre(estado);
              }}
              onDragLeave={() => setColumnaSobre((c) => (c === estado ? null : c))}
              onDrop={(e) => {
                e.preventDefault();
                setColumnaSobre(null);
                const tarea = tareas.find((t) => t.id === e.dataTransfer.getData("text/plain"));
                if (tarea) void cambiarEstado(tarea, estado);
              }}
            >
              <h3 className="text-xs font-semibold uppercase tracking-wider">
                {ESTADOS[estado]} <span data-testid={`cuenta-${estado}`}>({grupos[estado].length})</span>
              </h3>
              {grupos[estado].map((t) => (
                <div
                  key={t.id}
                  draggable={permisos.cambiarEstado}
                  className={permisos.cambiarEstado ? styles.arrastrable : undefined}
                  onDragStart={(e) => e.dataTransfer.setData("text/plain", t.id)}
                >
                  {tarjeta(t)}
                </div>
              ))}
            </div>
          ))}
        </div>
      )}

      {vista === "cronograma" && (
        <div className="space-y-3">
          {cronograma.barras.length > 0 && (
            <p className={`text-xs ${styles.suave}`}>
              Del {cronograma.inicio} al {cronograma.fin}
            </p>
          )}
          <ul className="space-y-2" aria-label="Cronograma">
            {cronograma.barras.map(({ tarea, izquierda, ancho }) => {
              const vencida = esVencida(tarea, hoy);
              const h = tarea.hallazgo_id ? hallazgos[tarea.hallazgo_id] : undefined;
              return (
                <li key={tarea.id} data-testid={`fila-${tarea.id}`} className={`${styles.fila} p-2 space-y-1`}>
                  <p className="text-xs font-semibold">
                    {tarea.title} <span className={styles.suave}>· {ESTADOS[tarea.status]} · {tarea.start_date} a {tarea.end_date}</span>
                    {h && <span className={styles.suave}> · Origen: {etiquetaOrigen(h.origen)}</span>}
                  </p>
                  <div className={styles.pista}>
                    <div
                      role="img"
                      data-testid={`barra-${tarea.id}`}
                      aria-label={`${tarea.title}: del ${tarea.start_date} al ${tarea.end_date}`}
                      className={`${styles.barra} ${vencida ? `badge-render-danger ${styles.barraVencida}` : ""}`}
                      style={{ left: `${izquierda}%`, width: `${ancho}%` }}
                    />
                  </div>
                </li>
              );
            })}
          </ul>
          {cronograma.sinFecha.length > 0 && (
            <section aria-label="Sin fecha" data-testid="sin-fecha" className="space-y-2">
              <h3 className="text-xs font-semibold uppercase tracking-wider">Sin fecha</h3>
              <ul className="space-y-2">
                {cronograma.sinFecha.map((t) => (
                  <li key={t.id} data-testid={`sinfecha-${t.id}`} className={`${styles.fila} p-2 text-xs`}>
                    {t.title} <span className={styles.suave}>· {ESTADOS[t.status]}</span>
                  </li>
                ))}
              </ul>
            </section>
          )}
        </div>
      )}
    </section>
  );
}

export default VistasTareas;
