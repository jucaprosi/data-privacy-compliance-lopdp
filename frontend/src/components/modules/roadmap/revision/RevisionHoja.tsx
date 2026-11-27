// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
"use client";

import React, { useCallback, useEffect, useId, useRef, useState } from "react";
import { CheckCircle2, Clock, Loader2 } from "lucide-react";

import {
  activarHojaRuta,
  formatearFechaRevision,
  mensajeErrorActivacion,
  obtenerRevision,
  type EstadoRevision,
} from "@/lib/roadmap/revision";
import { useRoadmapStore } from "@/store/useRoadmapStore";

export interface RevisionHojaProps {
  roadmapId: string;
  onEstadoCambio?: (estado: EstadoRevision | null) => void;
}

export function RevisionHoja({ roadmapId, onEstadoCambio }: RevisionHojaProps) {
  const rol = useRoadmapStore((s) => s.session.role);
  const tituloDialogoId = useId();
  const descDialogoId = useId();

  const [estado, setEstado] = useState<EstadoRevision | null>(null);
  const [cargando, setCargando] = useState(true);
  const [errorCarga, setErrorCarga] = useState(false);
  const [dialogoAbierto, setDialogoAbierto] = useState(false);
  const [activando, setActivando] = useState(false);
  const [errorDialogo, setErrorDialogo] = useState<string | null>(null);
  const [recienActivada, setRecienActivada] = useState(false);

  const botonActivarRef = useRef<HTMLButtonElement | null>(null);
  const cancelarRef = useRef<HTMLButtonElement | null>(null);
  const dialogoRef = useRef<HTMLDivElement | null>(null);
  const onEstadoCambioRef = useRef(onEstadoCambio);
  onEstadoCambioRef.current = onEstadoCambio;

  const cargar = useCallback(async () => {
    if (!roadmapId) {
      setEstado(null);
      setCargando(false);
      setErrorCarga(false);
      onEstadoCambioRef.current?.(null);
      return;
    }
    setCargando(true);
    setErrorCarga(false);
    try {
      const dato = await obtenerRevision(roadmapId);
      setEstado(dato);
      onEstadoCambioRef.current?.(dato);
    } catch {
      setErrorCarga(true);
      setEstado(null);
      onEstadoCambioRef.current?.(null);
    } finally {
      setCargando(false);
    }
  }, [roadmapId]);

  useEffect(() => {
    setRecienActivada(false);
    void cargar();
  }, [cargar, rol]);

  useEffect(() => {
    if (dialogoAbierto) {
      cancelarRef.current?.focus();
    }
  }, [dialogoAbierto]);

  const cerrarDialogo = useCallback(() => {
    if (activando) return;
    setDialogoAbierto(false);
    setErrorDialogo(null);
    requestAnimationFrame(() => {
      botonActivarRef.current?.focus();
    });
  }, [activando]);

  const manejarTeclasDialogo = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (e.key === "Escape") {
      e.preventDefault();
      e.stopPropagation();
      cerrarDialogo();
      return;
    }
    if (e.key !== "Tab" || !dialogoRef.current) return;
    const focales = Array.from(
      dialogoRef.current.querySelectorAll<HTMLElement>("button:not([disabled])"),
    );
    if (focales.length === 0) return;
    const primero = focales[0];
    const ultimo = focales[focales.length - 1];
    if (e.shiftKey && (document.activeElement === primero || document.activeElement === dialogoRef.current)) {
      e.preventDefault();
      ultimo.focus();
    } else if (!e.shiftKey && document.activeElement === ultimo) {
      e.preventDefault();
      primero.focus();
    }
  };

  const confirmarActivacion = async () => {
    setActivando(true);
    setErrorDialogo(null);
    try {
      const resp = await activarHojaRuta(roadmapId);
      let actualizado: EstadoRevision = {
        ...(estado ?? {
          status: "active",
          generado_por: null,
          generado_por_nombre: null,
          generado_en: null,
          revisado_por: null,
          revisado_por_nombre: null,
          revisado_en: null,
          puede_activar: false,
          es_autor: false,
          etiqueta: null,
        }),
        status: resp.status || "active",
        revisado_por: resp.revisado_por,
        revisado_por_nombre: resp.revisado_por_nombre ?? estado?.revisado_por_nombre ?? null,
        revisado_en: resp.revisado_en,
        puede_activar: false,
        etiqueta: null,
      };
      if (!actualizado.revisado_por_nombre) {
        try {
          const refresco = await obtenerRevision(roadmapId);
          if (refresco && refresco.status === "active") {
            actualizado = refresco;
          }
        } catch {
          // Conservamos el estado recibido de la activación.
        }
      }
      setEstado(actualizado);
      setRecienActivada(true);
      setDialogoAbierto(false);
      onEstadoCambioRef.current?.(actualizado);
    } catch (err) {
      const { mensaje, recargar } = mensajeErrorActivacion(err);
      setErrorDialogo(mensaje);
      if (recargar) {
        try {
          const refresco = await obtenerRevision(roadmapId);
          if (refresco) {
            setEstado(refresco);
            onEstadoCambioRef.current?.(refresco);
          }
        } catch {
          // Si la recarga falla, se mantiene el mensaje fijo en el diálogo.
        }
      }
    } finally {
      setActivando(false);
    }
  };

  if (!roadmapId) return null;

  if (cargando && !estado && !errorCarga) {
    return (
      <div
        role="status"
        className="flex items-center gap-2 rounded-lg border border-[var(--ui-borde)] bg-[var(--ui-superficie)] px-3.5 py-2.5 text-xs text-[var(--ui-texto-suave)]"
      >
        <Loader2 className="h-3.5 w-3.5 animate-spin shrink-0" aria-hidden="true" />
        <span>Cargando el estado de revisión…</span>
      </div>
    );
  }

  if (errorCarga) {
    return (
      <div
        role="alert"
        className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-[var(--ui-error-borde)] bg-[var(--ui-superficie)] px-3.5 py-2.5 text-xs text-[var(--foreground)]"
      >
        <span>No pudimos cargar el estado de revisión de la hoja de ruta.</span>
        <button
          type="button"
          onClick={() => void cargar()}
          className="rounded-md border border-[var(--ui-borde-control)] bg-[var(--ui-boton)] px-2.5 py-1 text-xs font-semibold text-[var(--foreground)] hover:bg-[var(--ui-boton-hover)] focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ui-enlace)]"
        >
          Volver a cargar
        </button>
      </div>
    );
  }

  if (!estado) return null;

  // Hoja anterior (sin autor ni revisor): la etiqueta se muestra junto al informe.
  if (estado.generado_por === null && estado.revisado_por === null) {
    return null;
  }

  const renderDialogo = () =>
    dialogoAbierto ? (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
        <div
          ref={dialogoRef}
          role="dialog"
          aria-modal="true"
          aria-labelledby={tituloDialogoId}
          aria-describedby={descDialogoId}
          onKeyDown={manejarTeclasDialogo}
          className="w-full max-w-md space-y-3 rounded-lg border border-[var(--ui-borde)] bg-[var(--ui-superficie)] p-5 text-xs text-[var(--foreground)] shadow-xl"
        >
          <h3 id={tituloDialogoId} className="text-sm font-semibold text-[var(--foreground)]">
            ¿Activar esta hoja de ruta?
          </h3>
          <p id={descDialogoId} className="text-[var(--ui-texto-suave)] leading-relaxed">
            Al activarla confirmas que la revisaste y pasa a ser el plan oficial de la organización. Queda registrado que la activaste tú, con la fecha.
          </p>

          {errorDialogo && (
            <p
              role="alert"
              className="rounded-md border border-[var(--ui-error-borde)] bg-[var(--ui-superficie-2)] px-3 py-2 text-xs text-[var(--foreground)]"
            >
              {errorDialogo}
            </p>
          )}

          <div className="flex flex-wrap justify-end gap-2 pt-1">
            <button
              ref={cancelarRef}
              type="button"
              disabled={activando}
              onClick={cerrarDialogo}
              className="rounded-md border border-[var(--ui-borde-control)] bg-[var(--ui-boton)] px-3 py-1.5 text-xs font-semibold text-[var(--foreground)] hover:bg-[var(--ui-boton-hover)] focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ui-enlace)] disabled:opacity-50"
            >
              Cancelar
            </button>
            <button
              type="button"
              disabled={activando || estado.status === "active"}
              aria-busy={activando ? "true" : undefined}
              onClick={() => void confirmarActivacion()}
              className="inline-flex items-center gap-1.5 rounded-md bg-[var(--ui-primario)] px-3 py-1.5 text-xs font-semibold text-[var(--ui-primario-texto)] hover:bg-[var(--ui-primario-hover)] focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ui-enlace)] disabled:opacity-50"
            >
              {activando && <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />}
              {activando ? "Activando…" : "Activar la hoja de ruta"}
            </button>
          </div>
        </div>
      </div>
    ) : null;

  if (estado.status === "generated" && estado.generado_por !== null) {
    const fechaGen = formatearFechaRevision(estado.generado_en);
    const lineaGeneracion =
      estado.generado_por_nombre && fechaGen
        ? `Generada por ${estado.generado_por_nombre} el ${fechaGen}.`
        : fechaGen
          ? `Generada el ${fechaGen}.`
          : estado.generado_por_nombre
            ? `Generada por ${estado.generado_por_nombre}.`
            : null;

    return (
      <div className="space-y-3">
        <div
          role="status"
          className="space-y-2.5 rounded-lg border border-[var(--ui-aviso-borde)] bg-[var(--ui-superficie)] p-3.5 text-xs text-[var(--foreground)]"
        >
          <div className="flex flex-wrap items-center gap-2">
            <span className="badge-render-warning inline-flex items-center gap-1.5 rounded px-2 py-0.5 text-[11px] font-semibold">
              <Clock className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
              Pendiente de revisión
            </span>
          </div>

          <p className="text-[var(--foreground)] leading-relaxed">
            Esta hoja de ruta aún no vale como plan oficial. Debe revisarla y activarla un coordinador o el DPO que no la haya generado.
          </p>

          {lineaGeneracion && (
            <p className="text-[var(--ui-texto-suave)]">{lineaGeneracion}</p>
          )}

          {estado.puede_activar ? (
            <div className="pt-0.5">
              <button
                ref={botonActivarRef}
                type="button"
                aria-label="Revisar y activar la hoja de ruta"
                onClick={() => {
                  setErrorDialogo(null);
                  setDialogoAbierto(true);
                }}
                className="inline-flex items-center gap-1.5 rounded-md bg-[var(--ui-primario)] px-3 py-1.5 text-xs font-semibold text-[var(--ui-primario-texto)] hover:bg-[var(--ui-primario-hover)] focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ui-enlace)]"
              >
                Revisar y activar
              </button>
            </div>
          ) : estado.es_autor ? (
            <p role="note" className="text-[var(--ui-texto-suave)]">
              Generaste esta hoja de ruta, así que debe activarla otra persona: un coordinador o el DPO. Así la revisan dos personas distintas.
            </p>
          ) : (
            <p className="text-[var(--ui-texto-suave)]">
              La activa un coordinador o el DPO de la organización.
            </p>
          )}
        </div>

        {renderDialogo()}
      </div>
    );
  }

  if (estado.status === "active") {
    const fechaRev = formatearFechaRevision(estado.revisado_en);
    const franjaActiva =
      estado.revisado_por_nombre && fechaRev
        ? `Activa · revisada por ${estado.revisado_por_nombre} el ${fechaRev}.`
        : fechaRev
          ? `Activa · revisada el ${fechaRev}.`
          : estado.revisado_por_nombre
            ? `Activa · revisada por ${estado.revisado_por_nombre}.`
            : "Activa.";

    return (
      <div className="space-y-2">
        {recienActivada && (
          <div
            role="status"
            className="rounded-lg border border-[var(--ui-exito-borde)] bg-[var(--ui-superficie)] px-3.5 py-2.5 text-xs text-[var(--foreground)]"
          >
            Hoja de ruta activada. Ya puedes descargar el informe.
          </div>
        )}
        <div
          role="status"
          className="flex flex-wrap items-center gap-2 rounded-lg border border-[var(--ui-borde)] bg-[var(--ui-superficie)] px-3.5 py-2.5 text-xs text-[var(--foreground)]"
        >
          <span className="badge-render-success inline-flex items-center gap-1.5 rounded px-2 py-0.5 text-[11px] font-semibold">
            <CheckCircle2 className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
            {franjaActiva}
          </span>
        </div>

        {renderDialogo()}
      </div>
    );
  }

  return null;
}

export default RevisionHoja;
