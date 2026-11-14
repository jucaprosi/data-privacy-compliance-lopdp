"use client";
// ¤incidentes
// Operación › Asistente de vulneración (INC-02): lista de vulneraciones con su avance y el asistente de
// ocho pasos. Los roles se leen de /organizacion/me/roles; el servidor los vuelve a comprobar.
import React, { useCallback, useEffect, useState } from "react";
import { fetchAutenticado } from "@/lib/auth";
import { ROLES_LECTURA, TOTAL_PASOS, resumenAsistentes, type ResumenAsistente } from "@/lib/incidentes/asistente";
import { cabecerasComo, rolEntre, rolesDelUsuario } from "@/lib/incidentes/roles";
import AsistenteIncidente from "./AsistenteIncidente";

interface Fila {
  id: string;
  titulo: string;
  fecha_deteccion: string;
  estado?: string;
}

const ESTADOS: Record<string, string> = { abierto: "Abierta", cerrado: "Cerrada" };

function fecha(valor: string): string {
  const d = new Date(valor);
  return Number.isNaN(d.getTime()) ? "" : d.toLocaleDateString("es-EC", { dateStyle: "medium" });
}

/** El implementador primero: es quien completa más pasos; luego dpo, coordinador y administración. */
const PREFERENCIA = ["implementador", "dpo", "coordinador", "admin_organizacion"] as const;

export default function AsistenteVulneraciones() {
  const [rol, setRol] = useState<string | null | undefined>(undefined);
  const [filas, setFilas] = useState<Fila[] | null>(null);
  const [resumen, setResumen] = useState<Record<string, ResumenAsistente>>({});
  const [error, setError] = useState(false);
  const [abierto, setAbierto] = useState<Fila | null>(null);

  const cargar = useCallback(async (rolActual: string) => {
    setError(false);
    try {
      const [bitacora, avance] = await Promise.all([
        fetchAutenticado("/api/v1/incidentes", { method: "GET" }, cabecerasComo(rolActual)).then(async (r) => {
          if (!r.ok) throw new Error(String(r.status));
          return (await r.json()) as { incidentes: Fila[] };
        }),
        resumenAsistentes(rolActual),
      ]);
      setFilas(bitacora.incidentes);
      setResumen(avance);
    } catch {
      setError(true);
    }
  }, []);

  useEffect(() => {
    let vivo = true;
    void rolesDelUsuario().then((roles) => {
      if (!vivo) return;
      const elegido = rolEntre(roles, PREFERENCIA.filter((r) => (ROLES_LECTURA as readonly string[]).includes(r)));
      setRol(elegido);
      if (elegido) void cargar(elegido);
    });
    return () => {
      vivo = false;
    };
  }, [cargar]);

  return (
    <main aria-label="Asistente de vulneración" className="flex min-w-0 flex-col gap-4 p-4">
      <h1 className="text-xl font-semibold">Asistente de vulneración</h1>
      {rol === null ? <p>No tienes permiso para esta acción.</p> : null}
      {rol && error ? (
        <div className="flex flex-col gap-2">
          <p role="alert" className="badge-render-danger rounded-md px-3 py-2 text-sm">
            No pudimos cargar el asistente. Inténtalo de nuevo.
          </p>
          <button
            type="button"
            className="self-start rounded-md border border-[var(--ui-borde)] bg-[var(--ui-boton)] px-3 py-1.5 text-sm"
            onClick={() => void cargar(rol)}
          >
            Volver a cargar
          </button>
        </div>
      ) : null}
      {rol && !error && filas === null ? <p role="status">Cargando el asistente…</p> : null}
      {rol && abierto ? (
        <AsistenteIncidente
          incidenteId={abierto.id}
          titulo={abierto.titulo}
          rol={rol}
          alVolver={() => {
            setAbierto(null);
            void cargar(rol);
          }}
        />
      ) : null}
      {rol && !abierto && filas !== null ? (
        filas.length === 0 ? (
          <p>Aún no hay vulneraciones registradas.</p>
        ) : (
          <ul aria-label="Vulneraciones" className="flex flex-col gap-2">
            {filas.map((f) => {
              const actual = resumen[f.id]?.seccion_actual ?? 1;
              return (
                <li
                  key={f.id}
                  className="flex flex-col gap-2 rounded-md border border-[var(--ui-borde)] bg-[var(--ui-superficie)] p-3 sm:flex-row sm:items-center sm:justify-between"
                >
                  <div className="flex min-w-0 flex-col gap-1">
                    <p className="break-words font-medium">{f.titulo}</p>
                    <p className="text-sm text-[var(--ui-texto-suave)]">
                      {fecha(f.fecha_deteccion)}
                      {f.estado ? ` · ${ESTADOS[f.estado] ?? f.estado}` : ""}
                    </p>
                    <p className="text-sm">
                      Sección {actual} de {TOTAL_PASOS}
                    </p>
                    <div
                      role="progressbar"
                      aria-label="Avance del asistente"
                      aria-valuemin={0}
                      aria-valuemax={TOTAL_PASOS}
                      aria-valuenow={actual - 1}
                      className="h-2 w-40 max-w-full overflow-hidden rounded bg-[var(--ui-borde)]"
                    >
                      <div className="h-full bg-[var(--ui-primario)]" style={{ width: `${((actual - 1) / TOTAL_PASOS) * 100}%` }} />
                    </div>
                  </div>
                  <button
                    type="button"
                    aria-label={`Continuar el asistente de ${f.titulo}`}
                    onClick={() => setAbierto(f)}
                    className="self-start rounded-md bg-[var(--ui-primario)] px-3 py-1.5 text-sm text-[var(--ui-primario-texto)] hover:bg-[var(--ui-primario-hover)]"
                  >
                    Continuar
                  </button>
                </li>
              );
            })}
          </ul>
        )
      ) : null}
    </main>
  );
}
