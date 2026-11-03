"use client";

// ¤adpa ¤rbac-tenant
// ¤¤frontend-architect
/**
 * Sección de Plantillas recomendadas y motor de aplicabilidad explicable (BIB-204).
 *
 * Se monta en la pestaña «Plantillas» (ranura `pestana:plantillas`) a través de `vistas/index.ts`.
 * Evalúa deterministamente qué plantillas aplican, cuáles no, y cuáles mantienen
 * «Información insuficiente» con sus hechos faltantes y fuentes normativas.
 */
import React, { useEffect, useState } from "react";
import {
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Edit3,
  HelpCircle,
  RefreshCw,
  Search,
  ShieldCheck,
  XCircle,
} from "lucide-react";
import {
  consultarAplicabilidad,
  type ModificacionHumana,
  type PlantillaAplicable,
} from "@/lib/biblioteca/aplicabilidad";
import { useSeleccionBiblioteca, type PropsVistaBiblioteca } from "@/lib/biblioteca/registro";
import { useBibliotecaStore } from "@/store/useBibliotecaStore";
import ModalModificarAplicabilidad from "./ModalModificarAplicabilidad";

const FILTROS = ["Recomendadas", "Todas", "Información insuficiente", "No aplica"] as const;
type FiltroTab = (typeof FILTROS)[number];

export default function VistaRecomendados(_props: PropsVistaBiblioteca) {
  const organizacion = useBibliotecaStore((s) => s.organizacion);
  const elegirPlantilla = useSeleccionBiblioteca((s) => s.elegirPlantilla);
  const plantillaElegida = useSeleccionBiblioteca((s) => s.plantillaId);

  const [plantillas, setPlantillas] = useState<PlantillaAplicable[]>([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filtro, setFiltro] = useState<FiltroTab>("Recomendadas");
  const [busqueda, setBusqueda] = useState("");
  const [expandidas, setExpandidas] = useState<Record<string, boolean>>({});
  const [modificando, setModificando] = useState<PlantillaAplicable | null>(null);

  async function cargar() {
    setCargando(true);
    setError(null);
    const resp = await consultarAplicabilidad();
    setCargando(false);
    if (resp.estado === "listo") {
      setPlantillas(resp.plantillas);
    } else {
      setError(resp.mensaje);
    }
  }

  useEffect(() => {
    cargar();
  }, [organizacion]);

  function toggleExpandir(codigo: string) {
    setExpandidas((prev) => ({ ...prev, [codigo]: !prev[codigo] }));
  }

  function handleGuardado(mod: ModificacionHumana) {
    if (!modificando) return;
    setPlantillas((prev) =>
      prev.map((p) => {
        if (p.codigo === modificando.codigo) {
          return {
            ...p,
            resultado: mod.resultado_modificado,
            modificacion_humana: mod,
          };
        }
        return p;
      }),
    );
  }

  const visibles = plantillas.filter((p) => {
    if (filtro === "Recomendadas" && p.resultado !== "Aplica") return false;
    if (filtro === "Información insuficiente" && p.resultado !== "Información insuficiente") return false;
    if (filtro === "No aplica" && p.resultado !== "No aplica") return false;

    if (busqueda.trim()) {
      const q = busqueda.toLowerCase();
      const matchCodigo = p.codigo.toLowerCase().includes(q);
      const matchNombre = p.nombre.toLowerCase().includes(q);
      const matchMotivo = p.motivo_recomendacion.toLowerCase().includes(q);
      if (!matchCodigo && !matchNombre && !matchMotivo) return false;
    }
    return true;
  });

  return (
    <section
      data-testid="seccion-recomendados"
      aria-label="Plantillas recomendadas y aplicabilidad"
      className="mt-4 flex flex-col gap-3 rounded-lg border border-[var(--ui-borde)] bg-[var(--ui-campo)] p-4 text-xs"
    >
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[var(--ui-borde)] pb-3">
        <div>
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-[var(--ui-primario)]" />
            <h3 className="text-sm font-semibold text-[var(--ui-texto)]">
              Plantillas recomendadas y aplicabilidad (BIB-204)
            </h3>
          </div>
          <p className="text-[var(--ui-texto-suave)]">
            Evaluación determinista basada en hechos de Organización (ORG-14), RAT (RAT-01) y MTGE (MTGE-01).
          </p>
        </div>
        <button
          type="button"
          data-testid="boton-recargar-aplicabilidad"
          onClick={cargar}
          disabled={cargando}
          className="flex items-center gap-1 rounded border border-[var(--ui-borde)] px-2.5 py-1 text-[var(--ui-texto-suave)] hover:bg-[var(--ui-boton-hover)]"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${cargando ? "animate-spin" : ""}`} />
          Recargar
        </button>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-2">
        <div role="tablist" aria-label="Filtro de aplicabilidad" className="flex gap-1">
          {FILTROS.map((f) => {
            const activo = filtro === f;
            const testId = `filtro-${f.toLowerCase().replace(/\s+/g, "-")}`;
            return (
              <button
                key={f}
                type="button"
                role="tab"
                data-testid={testId}
                aria-selected={activo}
                onClick={() => setFiltro(f)}
                className={`rounded px-2.5 py-1 font-medium transition-colors ${
                  activo
                    ? "bg-[var(--ui-primario)] text-white"
                    : "border border-[var(--ui-borde)] text-[var(--ui-texto-suave)] hover:bg-[var(--ui-boton-hover)]"
                }`}
              >
                {f}
              </button>
            );
          })}
        </div>

        <div className="relative min-w-[200px]">
          <Search className="absolute left-2.5 top-2 h-3.5 w-3.5 text-[var(--ui-texto-suave)]" />
          <input
            type="search"
            data-testid="busqueda-aplicabilidad"
            placeholder="Buscar por código o nombre..."
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
            className="w-full rounded border border-[var(--ui-borde)] bg-[var(--ui-campo)] py-1 pl-8 pr-3 text-xs"
          />
        </div>
      </div>

      {cargando && (
        <div className="flex items-center justify-center p-8 text-[var(--ui-texto-suave)]">
          <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
          Evaluando aplicabilidad explicable...
        </div>
      )}

      {error && (
        <p role="alert" className="rounded border border-red-500/40 bg-red-500/10 p-3 text-red-700 dark:text-red-300 font-medium">
          {error}
        </p>
      )}

      {!cargando && !error && visibles.length === 0 && (
        <div className="rounded border border-dashed border-[var(--ui-borde)] p-6 text-center text-[var(--ui-texto-suave)]">
          No hay plantillas que coincidan con el filtro seleccionado.
        </div>
      )}

      {!cargando && !error && visibles.length > 0 && (
        <ul className="flex flex-col gap-2.5">
          {visibles.map((p) => {
            const expandida = Boolean(expandidas[p.codigo]);
            const elegida = plantillaElegida === p.codigo;
            return (
              <li
                key={p.codigo}
                data-testid={`tarjeta-aplicabilidad-${p.codigo}`}
                className={`rounded-md border p-3 transition-colors ${
                  elegida
                    ? "border-[var(--ui-primario)] bg-[var(--ui-primario)]/5"
                    : "border-[var(--ui-borde)] bg-[var(--ui-fondo)]"
                }`}
              >
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div className="flex flex-col gap-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-semibold text-sm text-[var(--ui-texto)]">{p.codigo}</span>
                      <span className="font-medium text-[var(--ui-texto)]">{p.nombre}</span>

                      {/* Badge resultado */}
                      {p.resultado === "Aplica" && (
                        <span
                          data-testid={`resultado-${p.codigo}`}
                          className="inline-flex items-center gap-1 rounded bg-emerald-500/15 px-2 py-0.5 text-emerald-700 dark:text-emerald-300 font-semibold text-[11px]"
                        >
                          <CheckCircle2 className="h-3 w-3" />
                          Aplica
                        </span>
                      )}
                      {p.resultado === "Información insuficiente" && (
                        <span
                          data-testid={`resultado-${p.codigo}`}
                          className="inline-flex items-center gap-1 rounded bg-amber-500/15 px-2 py-0.5 text-amber-800 dark:text-amber-200 font-semibold text-[11px]"
                        >
                          <HelpCircle className="h-3 w-3" />
                          Información insuficiente
                        </span>
                      )}
                      {p.resultado === "No aplica" && (
                        <span
                          data-testid={`resultado-${p.codigo}`}
                          className="inline-flex items-center gap-1 rounded bg-zinc-500/15 px-2 py-0.5 text-zinc-600 dark:text-zinc-400 font-medium text-[11px]"
                        >
                          <XCircle className="h-3 w-3" />
                          No aplica
                        </span>
                      )}

                      {p.es_obligacion && (
                        <span className="rounded bg-blue-500/10 px-1.5 py-0.5 text-blue-700 dark:text-blue-300 text-[10px] font-medium border border-blue-500/20">
                          Obligación confirmada
                        </span>
                      )}

                      {p.modificacion_humana && (
                        <span className="rounded bg-purple-500/15 px-1.5 py-0.5 text-purple-700 dark:text-purple-300 text-[10px] font-medium border border-purple-500/30">
                          Corregido manualmente
                        </span>
                      )}
                    </div>

                    <p className="text-[var(--ui-texto-suave)] leading-relaxed">
                      {p.motivo_recomendacion}
                    </p>

                    {p.hechos_faltantes.length > 0 && (
                      <p className="text-amber-700 dark:text-amber-300 font-medium text-[11px]">
                        Hechos faltantes requeridos: {p.hechos_faltantes.join(", ")}
                      </p>
                    )}
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      data-testid={`boton-modificar-${p.codigo}`}
                      onClick={() => setModificando(p)}
                      title="Registrar modificación manual"
                      className="flex items-center gap-1 rounded border border-[var(--ui-borde)] px-2 py-1 text-[var(--ui-texto-suave)] hover:bg-[var(--ui-boton-hover)]"
                    >
                      <Edit3 className="h-3 w-3" />
                      Corregir
                    </button>

                    <button
                      type="button"
                      onClick={() => elegirPlantilla(p.codigo)}
                      className={`rounded px-2.5 py-1 font-medium ${
                        elegida
                          ? "bg-[var(--ui-primario)] text-white"
                          : "border border-[var(--ui-borde)] text-[var(--ui-texto)] hover:bg-[var(--ui-boton-hover)]"
                      }`}
                    >
                      {elegida ? "Elegida" : "Seleccionar"}
                    </button>

                    <button
                      type="button"
                      aria-expanded={expandida}
                      onClick={() => toggleExpandir(p.codigo)}
                      aria-label={`Detalle explicable de ${p.codigo}`}
                      className="rounded p-1 text-[var(--ui-texto-suave)] hover:bg-[var(--ui-boton-hover)]"
                    >
                      {expandida ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                    </button>
                  </div>
                </div>

                {expandida && (
                  <div className="mt-3 border-t border-[var(--ui-borde)] pt-3 flex flex-col gap-2">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-[11px] text-[var(--ui-texto-suave)]">
                      <div>Tipo: <span className="font-medium text-[var(--ui-texto)]">{p.tipo}</span></div>
                      <div>Formato: <span className="font-medium text-[var(--ui-texto)]">{p.formato}</span></div>
                      <div>Versión regla: <span className="font-medium text-[var(--ui-texto)]">{p.version_regla}</span></div>
                      <div>Fuentes: <span className="font-medium text-[var(--ui-texto)]">{p.fuentes_normativas.join(", ") || "—"}</span></div>
                    </div>

                    {p.modificacion_humana && (
                      <div className="rounded border border-purple-500/30 bg-purple-500/10 p-2.5 flex flex-col gap-1 text-[11px]">
                        <p className="font-semibold text-purple-800 dark:text-purple-200">
                          Modificación humana registrada:
                        </p>
                        <p>
                          Resultado original: <span className="font-semibold">{p.modificacion_humana.resultado_original}</span> → Modificado: <span className="font-semibold">{p.modificacion_humana.resultado_modificado}</span>
                        </p>
                        <p>Motivo: {p.modificacion_humana.motivo}</p>
                        <p>Evidencia: {p.modificacion_humana.evidencia}</p>
                        <p className="text-[var(--ui-texto-suave)]">
                          Fecha: {new Date(p.modificacion_humana.fecha).toLocaleString()} · Autor: {p.modificacion_humana.autor_id}
                          {p.modificacion_humana.revisor_juridico_id ? ` · Revisor jurídico: ${p.modificacion_humana.revisor_juridico_id}` : ""}
                        </p>
                      </div>
                    )}

                    {p.reglas_evaluadas.length > 0 && (
                      <div className="flex flex-col gap-1.5 pt-1">
                        <p className="font-semibold text-[11px] text-[var(--ui-texto)]">Reglas evaluadas:</p>
                        <ul className="flex flex-col gap-1 text-[11px]">
                          {p.reglas_evaluadas.map((r) => (
                            <li key={r.regla_id} className="rounded bg-[var(--ui-campo)] p-2 border border-[var(--ui-borde)]">
                              <div className="flex items-center justify-between gap-2">
                                <span className="font-semibold">{r.regla_id} · {r.nombre}</span>
                                <span className="font-medium">{r.resultado}</span>
                              </div>
                              <p className="text-[var(--ui-texto-suave)] mt-0.5">{r.explicacion}</p>
                              <p className="text-[10px] text-[var(--ui-texto-suave)] mt-0.5">
                                Fuente: {r.fuente_normativa} · Versión: {r.version_regla}
                              </p>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}
              </li>
            );
          })}
        </ul>
      )}

      {modificando && (
        <ModalModificarAplicabilidad
          plantilla={modificando}
          onCerrar={() => setModificando(null)}
          onGuardado={handleGuardado}
        />
      )}
    </section>
  );
}
