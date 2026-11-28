// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
// ¤boveda-cloud ¤videovigilancia-cctv ¤dpo-cockpit ¤conservacion
/**
 * Pantalla de BOV-04: Centro de Mando de las 10 Dimensiones LOPDP y Bóveda Cloud.
 * Presenta las 10 dimensiones por separado (sin porcentaje único global), la telemetría de nube,
 * las cámaras y clips bajo Hold Legal, las actas de purga SHA-256, escaneos DLP y caché normativo.
 */
"use client";

import React, { useCallback, useEffect, useState } from "react";
import { fetchAutenticado, leerOrganizacionActiva } from "@/lib/auth";
import { obtenerContextoRolesCapa } from "@/lib/capa";
import type { RegistroPantallas } from "./base";

const API = "/api/v1/boveda-cloud/orquestador-10d";
const ROLES = ["admin_organizacion", "dpo", "coordinador"];

export interface EstadoDimensionCloud {
  codigo: string;
  nombre: string;
  nivel_asignado: number;
  nivel_evidencia: number;
  controles_conformes: number;
  controles_totales: number;
  evidencias_custodiadas: number;
  estado_operativo: string;
  automatizacion_activa: boolean;
  modulo_asociado: string;
}

export interface ActaDestruccionCertificada {
  acta_id: string;
  origen: string;
  fecha_emision: string;
  sha256: string;
  elementos_purgados: number;
  elementos_hold_legal: number;
  verificada_dpo: boolean;
}

export interface ResumenOrquestadorDiezDimensiones {
  tenant_id: string;
  dimensiones: EstadoDimensionCloud[];
  uso_boveda_gb: number;
  uso_egress_gb: number;
  cuota_boveda_gb: number;
  cuota_egress_gb: number;
  camaras_activas: number;
  clips_en_hold_legal: number;
  actas_destruccion_emitidas: number;
  escaneos_dlp_completados: number;
  estado_cache_normativo: string;
  actas_sha256: ActaDestruccionCertificada[];
  modo_lectura: boolean;
  paquete_codigo: string;
  estado_suscripcion: string;
}

const FORMATO_GB = new Intl.NumberFormat("es-EC", {
  minimumFractionDigits: 1,
  maximumFractionDigits: 2,
});

function formatearGb(valor: number): string {
  return `${FORMATO_GB.format(valor)} GB`;
}

function claseEstado(estado: string): string {
  if (estado === "CONFORME" || estado === "ACTIVA" || estado === "ACTIVO") return "badge-render-success";
  if (estado === "ATENCION_REQUERIDA" || estado === "CUOTA_EXCEDIDA" || estado === "SUSPENDIDA") {
    return "badge-render-danger";
  }
  return "badge-render-warning";
}

function etiquetaCache(estado: string): string {
  switch (estado) {
    case "ACTIVO":
      return "Activo";
    case "DISPONIBLE_EN_ESPERA":
      return "Corpus listo en espera";
    case "SIN_CORPUS":
      return "Sin corpus";
    default:
      return "No disponible";
  }
}

function etiquetaEstadoOperativo(estado: string): string {
  switch (estado) {
    case "CONFORME":
      return "Conforme";
    case "PARCIAL":
      return "En progreso";
    case "ATENCION_REQUERIDA":
      return "Atención requerida";
    default:
      return "Pendiente";
  }
}

type EstadoVista =
  | { tipo: "cargando" }
  | { tipo: "prohibido" }
  | { tipo: "error" }
  | { tipo: "listo"; datos: ResumenOrquestadorDiezDimensiones };

export function OrquestadorDiezDimensiones() {
  const [estado, setEstado] = useState<EstadoVista>({ tipo: "cargando" });
  const [rol, setRol] = useState<string | null | undefined>(undefined);

  const resolverRol = useCallback(async () => {
    try {
      const ctx = await obtenerContextoRolesCapa();
      const encontrado = ROLES.find((r) => ctx.roles.includes(r)) ?? null;
      setRol(encontrado);
      if (!encontrado) {
        setEstado({ tipo: "prohibido" });
      }
      return encontrado;
    } catch {
      const locales = leerOrganizacionActiva()?.roles ?? [];
      const local = ROLES.find((r) => locales.includes(r)) ?? null;
      if (local) {
        setRol(local);
        return local;
      }
      setRol(undefined);
      setEstado({ tipo: "error" });
      return null;
    }
  }, []);

  const cargarResumen = useCallback(async (rolActivo?: string | null) => {
    const rolConsulta = rolActivo ?? rol;
    if (!rolConsulta) return;
    setEstado({ tipo: "cargando" });
    try {
      const res = await fetchAutenticado(API, {
        headers: { "X-Role": rolConsulta },
      });
      if (res.ok) {
        const datos = (await res.json()) as ResumenOrquestadorDiezDimensiones;
        setEstado({ tipo: "listo", datos });
        return;
      }
      if (res.status === 403) {
        setEstado({ tipo: "prohibido" });
        return;
      }
      setEstado({ tipo: "error" });
    } catch {
      setEstado({ tipo: "error" });
    }
  }, [rol]);

  useEffect(() => {
    let activo = true;
    resolverRol().then((encontrado) => {
      if (activo && encontrado) {
        void cargarResumen(encontrado);
      }
    });
    return () => {
      activo = false;
    };
  }, [resolverRol, cargarResumen]);

  const reintentar = async () => {
    const encontrado = rol ?? (await resolverRol());
    if (encontrado) {
      await cargarResumen(encontrado);
    }
  };

  return (
    <main
      aria-label="Orquestador de las 10 Dimensiones y Bóveda Cloud"
      className="mx-auto w-full max-w-6xl space-y-6 p-4 md:p-6"
    >
      <header
        className="flex flex-col gap-3 rounded-xl p-5 md:flex-row md:items-center md:justify-between"
        style={{ background: "var(--ui-superficie)", border: "1px solid var(--ui-borde)" }}
      >
        <div className="space-y-1">
          <h1 className="text-xl font-bold">Orquestador de las 10 Dimensiones y Bóveda Cloud</h1>
          <p className="text-sm" style={{ color: "var(--ui-texto-suave)" }}>
            Seguimiento separado de cada dimensión LOPDP, cuotas de almacenamiento, videovigilancia y actas de destrucción.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {estado.tipo === "listo" && estado.datos.modo_lectura && (
            <span className="badge-render-warning rounded px-2.5 py-1 text-xs font-semibold">
              Solo lectura
            </span>
          )}
          {estado.tipo === "listo" && (
            <span className={`${claseEstado(estado.datos.estado_suscripcion)} rounded px-2.5 py-1 text-xs font-semibold`}>
              Plan {estado.datos.paquete_codigo} · {estado.datos.estado_suscripcion}
            </span>
          )}
          <button
            type="button"
            onClick={() => void reintentar()}
            className="rounded-lg px-3 py-1.5 text-xs font-semibold cursor-pointer"
            style={{ background: "var(--ui-boton)", border: "1px solid var(--ui-borde-control)" }}
          >
            Actualizar
          </button>
        </div>
      </header>

      {estado.tipo === "cargando" && (
        <section
          className="rounded-xl p-5"
          style={{ background: "var(--ui-superficie)", border: "1px solid var(--ui-borde)" }}
        >
          <p role="status" className="text-sm">
            Cargando telemetría de Bóveda Cloud y las 10 dimensiones…
          </p>
        </section>
      )}

      {estado.tipo === "prohibido" && (
        <section
          className="rounded-xl p-5"
          style={{ background: "var(--ui-superficie)", border: "1px solid var(--ui-borde)" }}
        >
          <p role="status" className="text-sm">
            Esta vista está disponible únicamente para Administración, DPO y Coordinación.
          </p>
        </section>
      )}

      {estado.tipo === "error" && (
        <section
          className="flex flex-col items-start gap-3 rounded-xl p-5"
          style={{ background: "var(--ui-superficie)", border: "1px solid var(--ui-borde)" }}
        >
          <p role="alert" className="text-sm">
            No pudimos cargar el resumen del orquestador. Inténtalo de nuevo.
          </p>
          <button
            type="button"
            onClick={() => void reintentar()}
            className="rounded-lg px-3 py-1.5 text-xs font-semibold cursor-pointer"
            style={{ background: "var(--ui-boton)", border: "1px solid var(--ui-borde-control)" }}
          >
            Volver a cargar
          </button>
        </section>
      )}

      {estado.tipo === "listo" && <ContenidoOrquestador datos={estado.datos} />}
    </main>
  );
}

function ContenidoOrquestador({ datos }: { datos: ResumenOrquestadorDiezDimensiones }) {
  return (
    <div className="space-y-6">
      <section aria-label="Telemetría de Bóveda Cloud y automatizaciones" className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <TarjetaMetrica
          titulo="Almacenamiento en Bóveda"
          valor={formatearGb(datos.uso_boveda_gb)}
          detalle={datos.cuota_boveda_gb > 0 ? `Cuota contratada: ${formatearGb(datos.cuota_boveda_gb)}` : "Sin cuota asignada"}
        />
        <TarjetaMetrica
          titulo="Descargas y transferencia"
          valor={formatearGb(datos.uso_egress_gb)}
          detalle={datos.cuota_egress_gb > 0 ? `Límite mensual: ${formatearGb(datos.cuota_egress_gb)}` : "Sin cuota asignada"}
        />
        <TarjetaMetrica
          titulo="Cámaras de videovigilancia"
          valor={String(datos.camaras_activas)}
          detalle="Cámaras activas conformes"
        />
        <TarjetaMetrica
          titulo="Clips en Hold Legal"
          valor={String(datos.clips_en_hold_legal)}
          detalle="Protegidos contra purga ordinaria"
        />
        <TarjetaMetrica
          titulo="Escaneos DLP muestreados"
          valor={String(datos.escaneos_dlp_completados)}
          detalle={`Actas emitidas: ${datos.actas_destruccion_emitidas}`}
        />
        <TarjetaMetrica
          titulo="Caché normativo"
          valor={etiquetaCache(datos.estado_cache_normativo)}
          detalle="Corpus oficial LOPDP y SPDP"
        />
      </section>

      <section
        aria-label="Matriz de las 10 Dimensiones LOPDP"
        className="space-y-4 rounded-xl p-5"
        style={{ background: "var(--ui-superficie)", border: "1px solid var(--ui-borde)" }}
      >
        <div className="flex flex-col gap-1 md:flex-row md:items-center md:justify-between">
          <h2 className="text-base font-semibold">Las 10 Dimensiones LOPDP</h2>
          <p className="text-xs" style={{ color: "var(--ui-texto-suave)" }}>
            Cada dimensión se evalúa por separado en escala de 1 a 5 y evidencia de 0 a 4, sin cifra única global.
          </p>
        </div>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {datos.dimensiones.map((dim) => (
            <article
              key={dim.codigo}
              className="flex flex-col justify-between gap-3 rounded-lg p-4"
              style={{ background: "var(--ui-superficie-2)", border: "1px solid var(--ui-borde)" }}
            >
              <div className="flex items-start justify-between gap-2">
                <div>
                  <span className="font-mono text-xs font-semibold" style={{ color: "var(--ui-primario)" }}>
                    {dim.codigo}
                  </span>
                  <h3 className="text-sm font-semibold">{dim.nombre}</h3>
                  {dim.modulo_asociado && (
                    <p className="text-xs" style={{ color: "var(--ui-texto-suave)" }}>
                      {dim.modulo_asociado}
                    </p>
                  )}
                </div>
                <span className={`${claseEstado(dim.estado_operativo)} shrink-0 rounded px-2 py-0.5 text-xs font-medium`}>
                  {etiquetaEstadoOperativo(dim.estado_operativo)}
                </span>
              </div>

              <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
                <div className="flex flex-wrap gap-3">
                  <span>
                    Nivel: <strong>{dim.nivel_asignado} / 5</strong>
                  </span>
                  <span>
                    Evidencia: <strong>{dim.nivel_evidencia} / 4</strong>
                  </span>
                  <span>
                    Controles: <strong>{dim.controles_conformes} / {dim.controles_totales}</strong>
                  </span>
                </div>
                <span style={{ color: "var(--ui-texto-suave)" }}>
                  {dim.evidencias_custodiadas} evidencias · {dim.automatizacion_activa ? "Automatizada" : "Manual"}
                </span>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section
        aria-label="Purgas y actas criptográficas SHA-256"
        className="space-y-4 rounded-xl p-5"
        style={{ background: "var(--ui-superficie)", border: "1px solid var(--ui-borde)" }}
      >
        <div>
          <h2 className="text-base font-semibold">Purgas ejecutadas y Actas SHA-256</h2>
          <p className="text-xs" style={{ color: "var(--ui-texto-suave)" }}>
            Certificados criptográficos verificables por el DPO para acreditar destrucción segura y preservación legal.
          </p>
        </div>

        {datos.actas_sha256.length === 0 ? (
          <p className="text-sm" style={{ color: "var(--ui-texto-suave)" }}>
            Aún no se han emitido actas criptográficas de destrucción.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-left text-xs">
              <thead>
                <tr className="border-b" style={{ borderColor: "var(--ui-borde)", color: "var(--ui-texto-suave)" }}>
                  <th scope="col" className="py-2 pr-3">Acta</th>
                  <th scope="col" className="py-2 pr-3">Origen</th>
                  <th scope="col" className="py-2 pr-3">Fecha</th>
                  <th scope="col" className="py-2 pr-3">Purgados</th>
                  <th scope="col" className="py-2 pr-3">En Hold Legal</th>
                  <th scope="col" className="py-2 pr-3">Certificado SHA-256</th>
                  <th scope="col" className="py-2">Verificación</th>
                </tr>
              </thead>
              <tbody>
                {datos.actas_sha256.map((acta) => (
                  <tr key={acta.acta_id} className="border-b" style={{ borderColor: "var(--ui-borde)" }}>
                    <td className="py-2 pr-3 font-mono font-semibold">{acta.acta_id}</td>
                    <td className="py-2 pr-3">{acta.origen}</td>
                    <td className="py-2 pr-3">{acta.fecha_emision}</td>
                    <td className="py-2 pr-3 tabular-nums">{acta.elementos_purgados}</td>
                    <td className="py-2 pr-3 tabular-nums">{acta.elementos_hold_legal}</td>
                    <td className="py-2 pr-3 font-mono break-all">{acta.sha256}</td>
                    <td className="py-2">
                      <span className={acta.verificada_dpo ? "badge-render-success rounded px-2 py-0.5" : "badge-render-warning rounded px-2 py-0.5"}>
                        {acta.verificada_dpo ? "Verificada por DPO" : "Pendiente"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}

function TarjetaMetrica({ titulo, valor, detalle }: { titulo: string; valor: string; detalle: string }) {
  return (
    <div
      className="flex flex-col gap-1 rounded-xl p-4"
      style={{ background: "var(--ui-superficie)", border: "1px solid var(--ui-borde)" }}
    >
      <span className="text-xs font-medium" style={{ color: "var(--ui-texto-suave)" }}>
        {titulo}
      </span>
      <span className="text-xl font-bold tabular-nums">{valor}</span>
      <span className="text-xs" style={{ color: "var(--ui-texto-suave)" }}>
        {detalle}
      </span>
    </div>
  );
}

export const PANTALLAS_BOV_04: RegistroPantallas = {
  bov04_orquestador: () => <OrquestadorDiezDimensiones />,
};
