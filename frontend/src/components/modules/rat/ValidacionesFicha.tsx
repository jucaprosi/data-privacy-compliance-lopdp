"use client";

import React, { useCallback, useEffect, useState } from "react";
import { CheckCircle2, Loader2, X, XCircle } from "lucide-react";

import { obtenerContextoRolesCapa } from "@/lib/capa";
import {
  CONDICIONES_HABILITANTES,
  guardarCondicion,
  leerVersion,
  listarVersiones,
  obtenerValidaciones,
  type ValidacionesFicha as Validaciones,
  type VersionFicha,
} from "@/lib/rat/validaciones";
import { useAuditStore, type ActiveView } from "@/store/useAuditStore";
import { useRoadmapStore } from "@/store/useRoadmapStore";

/**
 * Panel lateral «Validaciones» de una ficha del RAT (RAT-05).
 *
 * Reglas en verde o rojo con su mensaje, enlace al hallazgo vigente y pestaña «Versiones». La regla de datos
 * sensibles se corrige aquí declarando la condición habilitante; ese guardado es del coordinador.
 */

const ROLES_LECTURA = ["coordinador", "implementador", "dpo", "admin_organizacion", "responsable_area"];
const REGLA_CONDICION = "RAT-SENS";

const NOMBRES_REGLA: Record<string, string> = {
  "RAT-SENS": "Datos sensibles",
  "RAT-EIPD": "Evaluación de impacto",
  "RAT-BASE": "Base de legitimación",
  "RAT-PLAZO": "Plazo de conservación",
};

type Pestana = "validaciones" | "versiones";

function mensajeDe(error: unknown, porDefecto: string): string {
  return error instanceof Error ? error.message : porDefecto;
}

interface Props {
  ratId: string;
  nombre: string;
  onCerrar: () => void;
}

export default function ValidacionesFicha({ ratId, nombre, onCerrar }: Props) {
  const sesion = useRoadmapStore((s) => s.session);
  const setActiveView = useAuditStore((s) => s.setActiveView);

  const [roles, setRoles] = useState<string[]>(sesion.role ? [sesion.role] : []);
  const [uid, setUid] = useState(sesion.userId);
  const [pestana, setPestana] = useState<Pestana>("validaciones");
  const [validaciones, setValidaciones] = useState<Validaciones | null>(null);
  const [versiones, setVersiones] = useState<VersionFicha[]>([]);
  const [abierta, setAbierta] = useState<{ numero: number; contenido: Record<string, unknown> } | null>(null);
  const [condicion, setCondicion] = useState("");
  const [cargando, setCargando] = useState(true);
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const rolLectura = (rolesActuales: string[]) => ROLES_LECTURA.find((r) => rolesActuales.includes(r)) ?? sesion.role;

  const cargar = useCallback(async () => {
    setCargando(true);
    setError(null);
    let rolesActuales: string[] = sesion.role ? [sesion.role] : [];
    let usuario = sesion.userId;
    try {
      const contexto = await obtenerContextoRolesCapa();
      rolesActuales = contexto.roles;
      usuario = contexto.user_id || usuario;
      setRoles(rolesActuales);
      setUid(usuario);
    } catch {
      // Sin /organizacion/me/roles se conserva el rol de la sesión local.
    }
    const rol = ROLES_LECTURA.find((r) => rolesActuales.includes(r)) ?? sesion.role;
    try {
      const [estado, lista] = await Promise.all([
        obtenerValidaciones(ratId, rol, usuario),
        listarVersiones(ratId, rol, usuario),
      ]);
      setValidaciones(estado);
      setVersiones(lista);
    } catch (e) {
      setError(mensajeDe(e, "No se pudieron cargar las validaciones."));
    } finally {
      setCargando(false);
    }
  }, [ratId, sesion.role, sesion.userId]);

  useEffect(() => {
    void cargar();
  }, [cargar]);

  async function verVersion(numero: number) {
    setError(null);
    try {
      setAbierta({ numero, contenido: await leerVersion(ratId, numero, rolLectura(roles), uid) });
    } catch (e) {
      setError(mensajeDe(e, "No se pudo leer la versión."));
    }
  }

  async function declararCondicion() {
    setGuardando(true);
    setError(null);
    try {
      await guardarCondicion(ratId, condicion, "coordinador", uid);
      setCondicion("");
      await cargar();
    } catch (e) {
      setError(mensajeDe(e, "No se pudo guardar la condición habilitante."));
    } finally {
      setGuardando(false);
    }
  }

  const pestanaClase = (activa: boolean) =>
    `px-3 py-1.5 font-semibold border-b-2 ${
      activa ? "border-[var(--ui-primario)]" : "border-transparent text-[var(--ui-texto-suave)]"
    }`;

  return (
    <aside
      aria-label="Validaciones"
      className="fixed inset-y-0 right-0 z-40 w-full max-w-md overflow-y-auto border-l border-[var(--ui-borde)] bg-[var(--ui-superficie)] p-4 space-y-3 text-xs shadow-2xl"
    >
      <div className="flex items-start justify-between gap-2">
        <div>
          <h3 className="text-sm font-bold">Validaciones</h3>
          <p className="text-[var(--ui-texto-suave)]">{nombre}</p>
        </div>
        <button type="button" onClick={onCerrar} aria-label="Cerrar panel" className="p-1">
          <X className="w-4 h-4" aria-hidden="true" />
        </button>
      </div>

      <div role="tablist" className="flex border-b border-[var(--ui-borde)]">
        <button type="button" role="tab" aria-selected={pestana === "validaciones"} onClick={() => setPestana("validaciones")} className={pestanaClase(pestana === "validaciones")}>
          Reglas
        </button>
        <button type="button" role="tab" aria-selected={pestana === "versiones"} onClick={() => setPestana("versiones")} className={pestanaClase(pestana === "versiones")}>
          Versiones
        </button>
      </div>

      {error && (
        <p role="alert" className="rounded-lg border border-[var(--status-danger)] p-3 text-[var(--status-danger)]">
          {error}
        </p>
      )}
      {cargando && <Loader2 className="w-4 h-4 animate-spin" aria-label="Cargando" />}

      {pestana === "validaciones" && validaciones && (
        <div className="space-y-2">
          <ul className="space-y-2">
            {validaciones.reglas.map((regla) => (
              <li
                key={regla.codigo}
                data-cumple={regla.cumple}
                className={`flex items-start gap-2 ${regla.cumple ? "text-[var(--status-success)]" : "text-[var(--status-danger)]"}`}
              >
                {regla.cumple ? (
                  <CheckCircle2 className="w-4 h-4 shrink-0" aria-hidden="true" />
                ) : (
                  <XCircle className="w-4 h-4 shrink-0" aria-hidden="true" />
                )}
                <span>
                  <strong>{NOMBRES_REGLA[regla.codigo] ?? regla.codigo}.</strong>{" "}
                  {regla.cumple ? "Conforme." : regla.mensaje}
                </span>
              </li>
            ))}
          </ul>

          {validaciones.hallazgo_id && (
            <button
              type="button"
              onClick={() => setActiveView("roadmap" as ActiveView)}
              title={`Hallazgo ${validaciones.hallazgo_id}`}
              className="font-semibold text-[var(--status-danger)] underline"
            >
              Ver hallazgo
            </button>
          )}

          {roles.includes("coordinador") && validaciones.reglas.some((r) => r.codigo === REGLA_CONDICION && !r.cumple) && (
            <div className="space-y-2 pt-2 border-t border-[var(--ui-borde)]">
              <label className="block space-y-1">
                <span className="font-medium text-[var(--ui-texto-suave)]">Condición habilitante (art. 26 LOPDP)</span>
                <select
                  value={condicion}
                  onChange={(e) => setCondicion(e.target.value)}
                  className="w-full rounded-md border border-[var(--ui-borde)] bg-[var(--ui-campo)] p-2"
                >
                  <option value="">Seleccione una condición</option>
                  {CONDICIONES_HABILITANTES.map((c) => (
                    <option key={c.valor} value={c.valor}>
                      {c.etiqueta}
                    </option>
                  ))}
                </select>
              </label>
              <button
                type="button"
                onClick={declararCondicion}
                disabled={guardando || !condicion}
                className="rounded-md bg-[var(--ui-primario)] px-3 py-1.5 font-semibold text-[var(--ui-primario-texto)] hover:bg-[var(--ui-primario-hover)] disabled:opacity-50"
              >
                Guardar condición
              </button>
            </div>
          )}
        </div>
      )}

      {pestana === "versiones" && (
        <div className="space-y-2">
          {versiones.length === 0 && !cargando && <p className="text-[var(--ui-texto-suave)]">Esta ficha aún no tiene versiones.</p>}
          <ul className="space-y-1">
            {versiones.map((v) => (
              <li key={v.numero}>
                <button type="button" onClick={() => verVersion(v.numero)} className="underline">
                  Versión {v.numero}
                </button>
                <span className="text-[var(--ui-texto-suave)]">
                  {" "}· {new Date(v.creado_en).toLocaleString("es-EC")}
                  {v.creado_por ? ` · ${v.creado_por}` : ""}
                </span>
              </li>
            ))}
          </ul>
          {abierta && (
            <section aria-label={`Contenido de la versión ${abierta.numero}`} className="rounded-md border border-[var(--ui-borde)] p-2">
              <dl className="space-y-1">
                {Object.entries(abierta.contenido).map(([campo, valor]) => (
                  <div key={campo}>
                    <dt className="font-medium text-[var(--ui-texto-suave)]">{campo.replaceAll("_", " ")}</dt>
                    <dd className="break-words">{typeof valor === "string" ? valor || "—" : JSON.stringify(valor)}</dd>
                  </div>
                ))}
              </dl>
            </section>
          )}
        </div>
      )}
    </aside>
  );
}
