"use client";

/**
 * Encargados y terceros: contrato, garantía, criticidad y próxima revisión, con hallazgos automáticos (TER-01).
 * Textos fijos por caso (revisión UX/UI): nunca se muestra el texto del servidor.
 */
import React, { useCallback, useEffect, useRef, useState } from "react";
import { AlertTriangle, Globe, Loader2, Server } from "lucide-react";

import { useAuditStore, type ActiveView } from "@/store/useAuditStore";
import { cargarDocumentos } from "@/lib/evidencias/servidor";
import type { EvidenciaDocumental } from "@/lib/evidencias/tipos";
import {
  CODIGOS_PAIS,
  CRITICIDADES,
  ROLES,
  TEXTOS,
  TIPOS_GARANTIA,
  cargarTerceros,
  evaluarTerceros,
  formatearFecha,
  guardarGarantias,
  nombrePais,
  textoContrato,
  textoEvaluacion,
  textoGarantia,
  type Criticidad,
  type EntradaGarantias,
  type PermisosTerceros,
  type RolTercero,
  type TerceroGarantias,
  type TipoGarantia,
} from "@/lib/terceros/garantias";

// La Hoja de Ruta es una vista del tablero fuera de ActiveView; el tablero la convierte igual (dashboard/page.tsx).
const VISTA_HOJA_DE_RUTA = "roadmap" as unknown as ActiveView;
const HOY = () => new Date().toISOString().slice(0, 10);

function Distintivos({ t, onAbrir }: { t: TerceroGarantias; onAbrir: (id: string) => void }) {
  if (t.hallazgos.length === 0) return null;
  return (
    <div className="flex flex-col gap-1">
      {t.hallazgos.map((h) => (
        <a
          key={h.id}
          href={`#hallazgo-${h.id}`}
          aria-label={`Ver el hallazgo de ${t.nombre}`}
          data-testid={`distintivo-${h.regla}`}
          onClick={(e) => {
            e.preventDefault();
            onAbrir(h.id);
          }}
          className="inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-semibold badge-render-danger underline-offset-2 hover:underline"
        >
          <AlertTriangle className="w-3.5 h-3.5" aria-hidden="true" />
          {h.regla === "garantia" ? TEXTOS.hallazgoGarantia : TEXTOS.hallazgoContrato}
        </a>
      ))}
    </div>
  );
}

function Dato({ etiqueta, valor }: { etiqueta: string; valor: string }) {
  return (
    <div className="min-w-0">
      <div className="text-xs text-[var(--ui-texto-suave)]">{etiqueta}</div>
      <div className="text-sm text-zinc-200 break-words">{valor}</div>
    </div>
  );
}

interface ModalProps {
  tercero: TerceroGarantias;
  onCerrar: () => void;
  onGuardado: (t: TerceroGarantias) => void;
}

function ModalGarantias({ tercero, onCerrar, onGuardado }: ModalProps) {
  const dialogo = useRef<HTMLDivElement>(null);
  const cancelar = useRef<HTMLButtonElement>(null);
  const [rol, setRol] = useState<RolTercero>(tercero.rol);
  const [pais, setPais] = useState(tercero.pais ?? "");
  const [contrato, setContrato] = useState(tercero.contrato_sha256 ?? "");
  const [vigencia, setVigencia] = useState(tercero.contrato_vigente_hasta ?? "");
  const [tipo, setTipo] = useState<TipoGarantia | "">(tercero.garantia_tipo ?? "");
  const [garantia, setGarantia] = useState(tercero.garantia_sha256 ?? "");
  const [criticidad, setCriticidad] = useState<Criticidad | "">(tercero.criticidad ?? "");
  const [revision, setRevision] = useState(tercero.proxima_revision ?? "");
  const [documentos, setDocumentos] = useState<EvidenciaDocumental[]>([]);
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState(false);

  useEffect(() => {
    const previo = document.activeElement as HTMLElement | null;
    cancelar.current?.focus();
    cargarDocumentos().then(setDocumentos).catch(() => setDocumentos([]));
    return () => previo?.focus();
  }, []);

  const alTeclear = (e: React.KeyboardEvent) => {
    if (e.key === "Escape") {
      e.stopPropagation();
      onCerrar();
      return;
    }
    if (e.key !== "Tab" || !dialogo.current) return;
    const focos = dialogo.current.querySelectorAll<HTMLElement>("button, select, input");
    const primero = focos[0];
    const ultimo = focos[focos.length - 1];
    if (e.shiftKey && document.activeElement === primero) {
      e.preventDefault();
      ultimo.focus();
    } else if (!e.shiftKey && document.activeElement === ultimo) {
      e.preventDefault();
      primero.focus();
    }
  };

  const opcionesDocumento = (actual: string) => {
    const lista = documentos.map((d) => ({ sha: d.sha256, nombre: d.nombreArchivo }));
    if (actual && !lista.some((d) => d.sha === actual)) lista.unshift({ sha: actual, nombre: "Documento registrado" });
    return lista;
  };

  async function guardar(e: React.FormEvent) {
    e.preventDefault();
    setEnviando(true);
    setError(false);
    const entrada: EntradaGarantias = {
      rol,
      pais: pais || null,
      contrato_sha256: contrato || null,
      contrato_vigente_hasta: vigencia || null,
      garantia_tipo: tipo || null,
      garantia_sha256: garantia || null,
      criticidad: criticidad || null,
      proxima_revision: revision || null,
    };
    try {
      onGuardado(await guardarGarantias(tercero.id, entrada));
      onCerrar();
    } catch {
      setError(true);
    } finally {
      setEnviando(false);
    }
  }

  const campo = "w-full mt-1 px-2 py-1.5 rounded bg-[var(--ui-superficie)] border border-[var(--ui-borde)] text-sm text-zinc-200";
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
      <div
        ref={dialogo}
        role="dialog"
        aria-modal="true"
        aria-labelledby="titulo-garantias"
        onKeyDown={alTeclear}
        className="w-full max-w-lg max-h-[90vh] overflow-y-auto rounded-xl border border-[var(--ui-borde)] bg-[var(--ui-fondo,#0b0b0f)] p-5"
      >
        <h3 id="titulo-garantias" className="text-base font-semibold text-zinc-100 mb-4">
          Registrar garantías de {tercero.nombre}
        </h3>
        <form onSubmit={guardar} className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <label className="text-xs text-[var(--ui-texto-suave)]">
            Rol del tercero
            <select aria-label="Rol del tercero" className={campo} value={rol} onChange={(e) => setRol(e.target.value as RolTercero)}>
              {Object.entries(ROLES).map(([v, n]) => <option key={v} value={v}>{n}</option>)}
            </select>
          </label>
          <label className="text-xs text-[var(--ui-texto-suave)]">
            País
            <select aria-label="País" className={campo} value={pais} onChange={(e) => setPais(e.target.value)}>
              <option value="">Sin país declarado</option>
              {CODIGOS_PAIS.map((c) => <option key={c} value={c}>{nombrePais(c)}</option>)}
            </select>
          </label>
          <label className="text-xs text-[var(--ui-texto-suave)]">
            Contrato
            <select aria-label="Contrato" className={campo} value={contrato} onChange={(e) => setContrato(e.target.value)}>
              <option value="">{TEXTOS.sinContrato}</option>
              {opcionesDocumento(contrato).map((d) => <option key={d.sha} value={d.sha}>{d.nombre}</option>)}
            </select>
          </label>
          <label className="text-xs text-[var(--ui-texto-suave)]">
            Vigencia del contrato hasta
            <input type="date" aria-label="Vigencia del contrato hasta" className={campo} value={vigencia} onChange={(e) => setVigencia(e.target.value)} />
          </label>
          <label className="text-xs text-[var(--ui-texto-suave)]">
            Tipo de garantía
            <select aria-label="Tipo de garantía" className={campo} value={tipo} onChange={(e) => setTipo(e.target.value as TipoGarantia | "")}>
              <option value="">{TEXTOS.sinGarantia}</option>
              {Object.entries(TIPOS_GARANTIA).map(([v, n]) => <option key={v} value={v}>{n}</option>)}
            </select>
          </label>
          <label className="text-xs text-[var(--ui-texto-suave)]">
            Documento de la garantía
            <select aria-label="Documento de la garantía" className={campo} value={garantia} onChange={(e) => setGarantia(e.target.value)}>
              <option value="">{TEXTOS.sinGarantia}</option>
              {opcionesDocumento(garantia).map((d) => <option key={d.sha} value={d.sha}>{d.nombre}</option>)}
            </select>
          </label>
          <label className="text-xs text-[var(--ui-texto-suave)]">
            Criticidad
            <select aria-label="Criticidad" className={campo} value={criticidad} onChange={(e) => setCriticidad(e.target.value as Criticidad | "")}>
              <option value="">Sin definir</option>
              {Object.entries(CRITICIDADES).map(([v, n]) => <option key={v} value={v}>{n}</option>)}
            </select>
          </label>
          <label className="text-xs text-[var(--ui-texto-suave)]">
            Próxima revisión
            <input type="date" aria-label="Próxima revisión" className={campo} value={revision} onChange={(e) => setRevision(e.target.value)} />
          </label>
          {error && (
            <p role="alert" className="sm:col-span-2 text-sm text-[#ff1744]">{TEXTOS.errorGuardar}</p>
          )}
          <div className="sm:col-span-2 flex justify-end gap-2 mt-2">
            <button ref={cancelar} type="button" onClick={onCerrar}
              className="px-3 py-1.5 rounded border border-[var(--ui-borde)] text-sm text-zinc-200">
              Cancelar
            </button>
            <button type="submit" disabled={enviando} aria-busy={enviando}
              className="px-3 py-1.5 rounded bg-[#9a3bf1] text-sm font-medium text-white disabled:opacity-60">
              Guardar garantías
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function TercerosModule() {
  const setActiveView = useAuditStore((s) => s.setActiveView);
  const [terceros, setTerceros] = useState<TerceroGarantias[]>([]);
  const [permisos, setPermisos] = useState<PermisosTerceros>({ gestionar: false, evaluar: false });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [editando, setEditando] = useState<TerceroGarantias | null>(null);
  const [evaluando, setEvaluando] = useState(false);
  const [estadoEvaluacion, setEstadoEvaluacion] = useState<string | null>(null);

  const cargar = useCallback(async () => {
    setLoading(true);
    setError(false);
    try {
      const datos = await cargarTerceros();
      setTerceros(datos.terceros);
      setPermisos(datos.permisos);
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void cargar();
  }, [cargar]);

  async function evaluar() {
    setEvaluando(true);
    setEstadoEvaluacion(null);
    try {
      const r = await evaluarTerceros();
      setEstadoEvaluacion(textoEvaluacion(r.hallazgos_creados, r.cerrados));
      const datos = await cargarTerceros();
      setTerceros(datos.terceros);
    } catch {
      setEstadoEvaluacion(TEXTOS.errorEvaluar);
    } finally {
      setEvaluando(false);
    }
  }

  const hoy = HOY();
  return (
    <div className="space-y-6">
      <div className="pb-4 border-b border-[var(--ui-borde)] flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="text-xl font-bold text-zinc-100 flex items-center">
            <Server className="w-5 h-5 mr-2 text-[#9a3bf1]" aria-hidden="true" />
            Terceros, Encargados y Transferencias
          </h2>
          <p className="text-xs text-[var(--ui-texto-suave)] mt-1">
            Contrato de cada encargado y garantía de cada transferencia internacional.
          </p>
        </div>
        {permisos.evaluar && (
          <button type="button" onClick={evaluar} disabled={evaluando} aria-busy={evaluando}
            className="px-3 py-1.5 rounded bg-[#9a3bf1] text-sm font-medium text-white disabled:opacity-60">
            Evaluar terceros
          </button>
        )}
      </div>
      <div role="status" data-testid="estado-evaluacion" className="text-sm text-zinc-200">{estadoEvaluacion}</div>

      {loading ? (
        <div className="flex flex-col items-center justify-center py-12 space-y-3">
          <Loader2 className="w-8 h-8 text-[#9a3bf1] animate-spin" aria-hidden="true" />
          <span className="text-sm text-[var(--ui-texto-suave)]">{TEXTOS.cargando}</span>
        </div>
      ) : error ? (
        <div role="alert" data-testid="error-carga" className="badge-render-danger p-4 rounded-xl flex flex-wrap items-center gap-3 text-sm">
          <AlertTriangle className="w-5 h-5" aria-hidden="true" />
          {TEXTOS.errorCarga}
          <button type="button" onClick={() => void cargar()} className="underline">Volver a cargar</button>
        </div>
      ) : (
        <ul className="grid grid-cols-1 gap-4" aria-label="Terceros">
          {terceros.length === 0 && (
            <li className="p-8 text-center text-[var(--ui-texto-suave)] text-sm border border-dashed border-[var(--ui-borde)] rounded-xl">
              No hay terceros ni transferencias registradas.
            </li>
          )}
          {terceros.map((t) => {
            const conHallazgo = t.hallazgos.length > 0;
            return (
              <li key={t.id} data-testid={`tercero-${t.id}`}
                className={`p-4 bg-[var(--ui-superficie)] border ${conHallazgo ? "border-[#ff1744]/50" : "border-[var(--ui-borde)]"} rounded-xl space-y-3`}>
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="flex items-center gap-3 min-w-0">
                    <Globe className="w-5 h-5 text-[#9a3bf1] shrink-0" aria-hidden="true" />
                    <div className="min-w-0">
                      <h4 className="font-medium text-sm text-zinc-200 break-words">{t.nombre}</h4>
                      <div className="text-xs text-[var(--ui-texto-suave)] mt-0.5">
                        {ROLES[t.rol]} · {t.pais ? nombrePais(t.pais) : "Sin país declarado"}
                      </div>
                    </div>
                  </div>
                  <Distintivos t={t} onAbrir={() => setActiveView(VISTA_HOJA_DE_RUTA)} />
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  <Dato etiqueta="Contrato" valor={textoContrato(t, hoy)} />
                  <Dato etiqueta="Garantía" valor={textoGarantia(t)} />
                  <Dato etiqueta="Criticidad" valor={t.criticidad ? CRITICIDADES[t.criticidad] : "Sin definir"} />
                  <Dato etiqueta="Próxima revisión" valor={t.proxima_revision ? formatearFecha(t.proxima_revision) : "Sin fecha"} />
                </div>
                {permisos.gestionar && (
                  <button type="button" onClick={() => setEditando(t)}
                    className="px-3 py-1.5 rounded border border-[var(--ui-borde)] text-xs font-medium text-zinc-200">
                    Registrar garantías
                  </button>
                )}
              </li>
            );
          })}
        </ul>
      )}
      {editando && (
        <ModalGarantias
          tercero={editando}
          onCerrar={() => setEditando(null)}
          onGuardado={(nuevo) => setTerceros((lista) => lista.map((x) => (x.id === nuevo.id ? nuevo : x)))}
        />
      )}
    </div>
  );
}
