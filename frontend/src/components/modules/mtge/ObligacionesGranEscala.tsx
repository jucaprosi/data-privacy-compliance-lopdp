"use client";

import React, { useEffect, useState } from "react";

import { fetchAutenticado } from "@/lib/auth";
import { AlertCircle, Calendar, CheckCircle2, Clock, FileCheck, Info, ShieldAlert } from "lucide-react";

export interface ResumenObligacion {
  obligacion: string;
  articulo_fuente: string;
  estado: "AL_DIA" | "POR_VENCER" | "VENCIDA" | "NO_APLICA" | "FALTA_FECHA_VIGENCIA" | "RECORDATORIO";
  dias_restantes?: number | null;
  fecha_limite?: string | null;
  descripcion: string;
  accion_siguiente: string;
}

export interface EstadoObligacionesResponse {
  tiene_gran_escala: boolean;
  cantidad_tratamientos_gran_escala: number;
  fecha_vigencia_norma?: string | null;
  obligaciones: ResumenObligacion[];
}

export default function ObligacionesGranEscala() {
  const [datos, setDatos] = useState<EstadoObligacionesResponse | null>(null);
  const [cargando, setCargando] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [sinPermiso, setSinPermiso] = useState<boolean>(false);

  useEffect(() => {
    async function cargarObligaciones() {
      try {
        setCargando(true);
        const res = await fetchAutenticado("/api/v1/riesgos/mtge/obligaciones");
        // Solo dpo, coordinador y admin_organizacion consultan las obligaciones; los demás roles no ven el panel.
        if (res.status === 403) {
          setSinPermiso(true);
          return;
        }
        if (!res.ok) {
          throw new Error(`Error ${res.status}: no se pudo cargar el estado de obligaciones`);
        }
        const data = await res.json();
        setDatos(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Error al conectar con el servidor");
      } finally {
        setCargando(false);
      }
    }
    cargarObligaciones();
  }, []);

  if (sinPermiso) {
    return null;
  }

  if (cargando) {
    return (
      <div className="p-6 text-center text-sm text-[var(--ui-texto-suave)]" data-testid="mtge-cargando">
        Cargando estado de obligaciones de gran escala…
      </div>
    );
  }

  if (error) {
    return (
      <div role="alert" className="p-4 rounded-lg badge-render-danger text-sm">
        <p className="font-semibold flex items-center gap-2">
          <AlertCircle className="w-4 h-4" /> Error al consultar obligaciones
        </p>
        <p className="text-xs mt-1">{error}</p>
      </div>
    );
  }

  const insignias = {
    AL_DIA: {
      clase: "badge-render-success",
      icono: CheckCircle2,
      texto: "Al día",
    },
    POR_VENCER: {
      clase: "badge-render-warning",
      icono: Clock,
      texto: "Por vencer",
    },
    VENCIDA: {
      clase: "badge-render-danger",
      icono: ShieldAlert,
      texto: "Vencida",
    },
    NO_APLICA: {
      clase: "bg-[var(--ui-superficie-2)] text-[var(--ui-texto-suave)] border-[var(--ui-borde)]",
      icono: Info,
      texto: "No aplica",
    },
    FALTA_FECHA_VIGENCIA: {
      clase: "badge-render-warning",
      icono: Calendar,
      texto: "Falta fecha de vigencia",
    },
    RECORDATORIO: {
      clase: "bg-[var(--ui-superficie-2)] text-[var(--ui-texto-suave)] border-[var(--ui-borde)]",
      icono: Info,
      texto: "Recordatorio",
    },
  };

  return (
    <section aria-label="Obligaciones del tratamiento a gran escala" className="space-y-6">
      <header className="pb-3 border-b border-[var(--ui-borde)]">
        <h2 className="text-lg font-bold flex items-center gap-2">
          <FileCheck className="w-5 h-5 text-[var(--ui-primario)]" aria-hidden="true" />
          Obligaciones del Tratamiento a Gran Escala
        </h2>
        <p className="text-xs text-[var(--ui-texto-suave)] mt-1">
          Res. SPDP-SPD-2026-0005-R · Arts. 16, 17, 18 y Disposición Transitoria
        </p>
      </header>

      {datos && !datos.tiene_gran_escala && (
        <div
          data-testid="mtge-no-gran-escala-banner"
          className="rounded-lg border border-[var(--ui-borde)] bg-[var(--ui-superficie)] p-4 text-xs text-[var(--ui-texto-suave)] flex items-start gap-3"
        >
          <Info className="w-4 h-4 text-sky-400 shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold">
              La organización no registra tratamientos calificados a gran escala en el RAT.
            </p>
            <p className="mt-1">
              Las obligaciones reforzadas de auditoría periódica, informe anual y designación específica
              aplican como <em>«No aplica»</em>. Si incorpora actividades con más de 100.000 titulares o bajo los
              supuestos directos del Art. 14, se activarán automáticamente.
            </p>
          </div>
        </div>
      )}

      {datos && datos.tiene_gran_escala && (
        <div
          data-testid="mtge-gran-escala-banner"
          className="rounded-lg badge-render-warning p-4 text-xs flex items-start gap-3"
        >
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold">
              Tratamientos a gran escala detectados: {datos.cantidad_tratamientos_gran_escala}
            </p>
            <p className="mt-1">
              Conforme a los Arts. 12, 17 y 18 de la Res. SPDP-SPD-2026-0005-R, la organización debe cumplir con
              auditorías al menos cada 12 meses, informes anuales conservados 5 años y designación de DPO.
            </p>
          </div>
        </div>
      )}

      <div className="space-y-4" data-testid="mtge-lista-obligaciones">
        {datos?.obligaciones.map((ob, idx) => {
          const cfg = insignias[ob.estado] || insignias.NO_APLICA;
          const Icono = cfg.icono;
          return (
            <article
              key={idx}
              data-testid={`mtge-obligacion-card-${idx}`}
              className="rounded-xl border border-[var(--ui-borde)] bg-[var(--ui-superficie)] p-4 space-y-3"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div>
                  <h3 className="font-semibold text-sm">{ob.obligacion}</h3>
                  <span className="text-xs text-[var(--ui-texto-suave)]">{ob.articulo_fuente}</span>
                </div>
                <span
                  data-testid={`mtge-estado-${idx}`}
                  className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${cfg.clase}`}
                >
                  <Icono className="w-3.5 h-3.5" aria-hidden="true" />
                  {cfg.texto}
                </span>
              </div>

              <p className="text-xs text-[var(--ui-texto-suave)] leading-relaxed">{ob.descripcion}</p>

              <div className="pt-2 border-t border-[var(--ui-borde)] flex flex-col sm:flex-row sm:items-center justify-between text-xs gap-1">
                <span className="text-[var(--ui-texto-suave)]">
                  <strong>Acción siguiente:</strong> {ob.accion_siguiente}
                </span>
                {ob.fecha_limite && (
                  <span className="text-[var(--ui-texto-suave)]">
                    Límite: <strong>{ob.fecha_limite}</strong>
                    {typeof ob.dias_restantes === "number" && (
                      <span className="ml-1">({ob.dias_restantes} días)</span>
                    )}
                  </span>
                )}
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}
