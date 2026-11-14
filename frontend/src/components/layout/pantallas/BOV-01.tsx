// ¤boveda-cloud
/**
 * Pantalla de BOV-01: espacio y descargas del plan de almacenamiento de la organización, en solo lectura.
 * Solo BOV-01 edita este archivo. Los errores se muestran con textos fijos: nunca el texto del servidor.
 */
"use client";

import React, { useCallback, useEffect, useState } from "react";
import { fetchAutenticado } from "@/lib/auth";
import { obtenerContextoRolesCapa } from "@/lib/capa";
import type { RegistroPantallas } from "./base";

const API = "/api/v1/boveda-cloud/suscripcion";

/** Confirmado por el CTO (2026-11-13): solo estos roles ven la vista. */
const ROLES = ["admin_organizacion", "dpo", "coordinador"];

/** Textos fijos para quien consuma los 409 de cuota (subidas y descargas). */
export const MENSAJES_CUOTA: Record<string, string> = {
  BOVEDA_CUOTA_ALMACENAMIENTO_EXCEDIDA: "No hay espacio suficiente en tu plan para subir este archivo.",
  BOVEDA_CUOTA_EGRESS_EXCEDIDA: "Alcanzaste el límite de descargas de tu plan.",
};

const NOTA_CERTIFICACIONES =
  "Son certificaciones de la infraestructura del proveedor. No certifican a tu organización ni sustituyen tu propio cumplimiento.";

const ESTADOS: Record<string, { etiqueta: string; linea?: string; clase: string }> = {
  ACTIVA: { etiqueta: "Activa", clase: "badge-render-success" },
  CUOTA_EXCEDIDA: {
    etiqueta: "Límite excedido",
    clase: "badge-render-danger",
    linea:
      "Alcanzaste el límite de tu plan. Mientras no lo amplíes, no podrás subir ni descargar más archivos de este tipo. Escribe al equipo de EVYDENTIA para ampliarlo.",
  },
  SUSPENDIDA: {
    etiqueta: "Suspendida",
    clase: "badge-render-danger",
    linea: "Tu servicio de almacenamiento está suspendido. Escribe al equipo de EVYDENTIA para reactivarlo.",
  },
};

export interface Suscripcion {
  paquete_codigo: string;
  paquete_nombre: string | null;
  cuota_almacenamiento_bytes: number;
  uso_almacenamiento_bytes: number;
  cuota_egress_mensual_bytes: number;
  uso_egress_mensual_bytes: number;
  certificaciones_heredadas: string[];
  estado: string;
}

// Base binaria (1 GB = 1024^3 bytes): la misma con que la migración bov01 siembra las cuotas del plan vendido.
// VERIFICADO: es la unidad de la factura de Cloud Storage (1 GB = 2^30 bytes, https://cloud.google.com/storage/pricing); CTO, 2026-11-13.
const GB = 1024 ** 3;
const MB = 1024 ** 2;
const FORMATO_GB = new Intl.NumberFormat("es-EC", { minimumFractionDigits: 1, maximumFractionDigits: 1 });
const FORMATO_ENTERO = new Intl.NumberFormat("es-EC", { maximumFractionDigits: 0 });

/** GB con un decimal; por debajo de 1 GB, MB sin decimales. Nunca bytes. */
export function formatearTamano(bytes: number): string {
  if (bytes >= GB) return `${FORMATO_GB.format(bytes / GB)} GB`;
  return `${FORMATO_ENTERO.format(Math.round(bytes / MB))} MB`;
}

export function porcentaje(uso: number, cuota: number): number {
  return cuota > 0 ? Math.floor((uso / cuota) * 100) : 0;
}

/** Hasta 79 % neutro; de 80 a 99 % «Cerca del límite»; 100 % o más «Límite alcanzado». */
export function nivel(pct: number): { texto: string; clase: string; icono: string } | null {
  if (pct >= 100) return { texto: "Límite alcanzado", clase: "badge-render-danger", icono: "⛔" };
  if (pct >= 80) return { texto: "Cerca del límite", clase: "badge-render-warning", icono: "⚠" };
  return null;
}

function Medidor({ etiqueta, uso, cuota, ayuda }: { etiqueta: string; uso: number; cuota: number; ayuda?: string }) {
  const pct = porcentaje(uso, cuota);
  const aviso = nivel(pct);
  const texto = `${formatearTamano(uso)} de ${formatearTamano(cuota)}`;
  return (
    <div className="flex min-w-0 flex-col gap-2">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <span className="font-medium">{etiqueta}</span>
        <span className="text-sm">
          {texto} · {pct} %
        </span>
      </div>
      <div
        role="meter"
        aria-label={etiqueta}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={Math.min(pct, 100)}
        aria-valuetext={`${texto}, ${pct} %`}
        className="h-2 w-full overflow-hidden rounded-full"
        style={{ background: "var(--ui-superficie-2)", border: "1px solid var(--ui-borde)" }}
      >
        <div className="h-full" style={{ width: `${Math.min(pct, 100)}%`, background: "var(--ui-primario)" }} />
      </div>
      {aviso && (
        <p className={`${aviso.clase} w-fit rounded px-2 py-0.5 text-sm`}>
          <span aria-hidden="true">{aviso.icono} </span>
          {aviso.texto}
        </p>
      )}
      {ayuda && (
        <p className="text-sm" style={{ color: "var(--ui-texto-suave)" }}>
          {ayuda}
        </p>
      )}
    </div>
  );
}

type Carga =
  | { tipo: "cargando" }
  | { tipo: "sin_plan" }
  | { tipo: "error" }
  | { tipo: "prohibido" }
  | { tipo: "listo"; datos: Suscripcion };

export function AlmacenamientoDescargas() {
  const [carga, setCarga] = useState<Carga>({ tipo: "cargando" });
  const [rol, setRol] = useState<string | null | undefined>(undefined);

  useEffect(() => {
    obtenerContextoRolesCapa()
      .then((c) => setRol(ROLES.find((r) => c.roles.includes(r)) ?? null))
      .catch(() => setRol(null));
  }, []);

  const cargar = useCallback(async () => {
    if (!rol) return;
    setCarga({ tipo: "cargando" });
    try {
      const res = await fetchAutenticado(API, { headers: { "X-Role": rol } });
      if (res.ok) {
        setCarga({ tipo: "listo", datos: (await res.json()) as Suscripcion });
        return;
      }
      if (res.status === 403) return setCarga({ tipo: "prohibido" });
      const cuerpo = await res.json().catch(() => null);
      if (res.status === 404 && cuerpo?.code === "BOVEDA_SUSCRIPCION_NO_ENCONTRADA") return setCarga({ tipo: "sin_plan" });
      setCarga({ tipo: "error" });
    } catch {
      setCarga({ tipo: "error" });
    }
  }, [rol]);

  useEffect(() => {
    if (rol === null) setCarga({ tipo: "prohibido" });
    else if (rol) void cargar();
  }, [rol, cargar]);

  if (carga.tipo === "prohibido") return null;

  return (
    <main
      aria-label="Almacenamiento y descargas"
      className="mx-auto w-full max-w-4xl p-4"
      style={{ color: "inherit" }}
    >
      <section
        className="flex flex-col gap-4 rounded-lg p-4"
        style={{ background: "var(--ui-superficie)", border: "1px solid var(--ui-borde)" }}
      >
        {carga.tipo === "cargando" && <p role="status">Cargando tu plan de almacenamiento…</p>}
        {carga.tipo === "sin_plan" && (
          <p role="status">
            Tu organización aún no tiene un plan de almacenamiento activo. Escribe al equipo de EVYDENTIA.
          </p>
        )}
        {carga.tipo === "error" && (
          <div className="flex flex-col items-start gap-2">
            <p role="alert">No pudimos cargar tu plan de almacenamiento. Inténtalo de nuevo.</p>
            <button
              type="button"
              onClick={() => void cargar()}
              className="rounded px-3 py-1.5 text-sm"
              style={{ background: "var(--ui-boton)", border: "1px solid var(--ui-borde)" }}
            >
              Volver a cargar
            </button>
          </div>
        )}
        {carga.tipo === "listo" && <Contenido datos={carga.datos} />}
      </section>
    </main>
  );
}

function Contenido({ datos }: { datos: Suscripcion }) {
  const estado = ESTADOS[datos.estado] ?? ESTADOS.ACTIVA;
  const nombre = datos.paquete_nombre?.trim();
  return (
    <>
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-xl font-semibold">Almacenamiento y descargas</h1>
        <span role="status" className={`${estado.clase} rounded px-2 py-0.5 text-sm`}>
          {estado.etiqueta}
        </span>
      </div>
      {estado.linea && <p className="text-sm">{estado.linea}</p>}
      <p>{nombre ? `Tu plan: ${nombre}` : "Tu plan"}</p>
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        <Medidor etiqueta="Espacio usado" uso={datos.uso_almacenamiento_bytes} cuota={datos.cuota_almacenamiento_bytes} />
        <Medidor
          etiqueta="Descargas"
          uso={datos.uso_egress_mensual_bytes}
          cuota={datos.cuota_egress_mensual_bytes}
          ayuda="Se cuentan los archivos que descargas de la plataforma."
        />
      </div>
      {datos.certificaciones_heredadas.length > 0 && (
        <div className="flex flex-col gap-2">
          <h2 className="font-medium">Certificaciones del proveedor de nube</h2>
          <ul aria-label="Certificaciones del proveedor de nube" className="flex flex-wrap gap-2">
            {datos.certificaciones_heredadas.map((c) => (
              <li key={c} className="rounded px-2 py-0.5 text-sm" style={{ border: "1px solid var(--ui-borde)" }}>
                {c}
              </li>
            ))}
          </ul>
          <p className="text-sm" style={{ color: "var(--ui-texto-suave)" }}>
            {NOTA_CERTIFICACIONES}
          </p>
        </div>
      )}
    </>
  );
}

export const PANTALLAS_BOV_01: RegistroPantallas = {
  bov01_suscripcion: () => <AlmacenamientoDescargas />,
};
