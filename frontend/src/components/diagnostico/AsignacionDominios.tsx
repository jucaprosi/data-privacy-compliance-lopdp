"use client";
/**
 * DIAG-04: el administrador asigna cada dominio del assessment (D01 a D10) a un encargado del diagnóstico.
 * Los demás roles consultan. Quién responde lo cambia DIAG-07, no esta pantalla.
 */
import { useCallback, useEffect, useState } from "react";
import { ClipboardList } from "lucide-react";

import { rolesDelUsuario } from "@/lib/diagnostico/roles";
import {
  asignarDominio,
  cargarAsignaciones,
  cargarHistorial,
  cargarPersonasEncargables,
  puedeAsignar,
  rolParaAsignaciones,
  rolParaHistorial,
  type AsignacionDominio,
  type MovimientoAsignacion,
  type PersonaEncargable,
} from "@/lib/diagnostico/asignaciones";

function mensajeDe(error: unknown, porDefecto: string): string {
  return error instanceof Error && error.message ? error.message : porDefecto;
}

export default function AsignacionDominios() {
  const [filas, setFilas] = useState<AsignacionDominio[]>([]);
  const [personas, setPersonas] = useState<PersonaEncargable[]>([]);
  const [administra, setAdministra] = useState(false);
  const [rolHistorial, setRolHistorial] = useState<string | null>(null);
  const [historial, setHistorial] = useState<MovimientoAsignacion[] | null>(null);
  const [cargando, setCargando] = useState(true);
  const [ocupado, setOcupado] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const cargar = useCallback(async () => {
    setCargando(true);
    setError(null);
    try {
      const roles = await rolesDelUsuario();
      const rol = rolParaAsignaciones(roles);
      if (!rol) {
        setFilas([]);
        setError("Tu rol no consulta la asignación de dominios.");
        return;
      }
      setAdministra(puedeAsignar(roles));
      setRolHistorial(rolParaHistorial(roles));
      setFilas(await cargarAsignaciones(rol));
      if (puedeAsignar(roles)) setPersonas(await cargarPersonasEncargables());
    } catch (e: unknown) {
      setError(mensajeDe(e, "No se pudo cargar la asignación de dominios."));
    } finally {
      setCargando(false);
    }
  }, []);

  useEffect(() => {
    void cargar();
  }, [cargar]);

  const asignar = async (dimension: string, valor: string) => {
    setOcupado(dimension);
    setError(null);
    try {
      await asignarDominio(dimension, valor || null);
      await cargar();
      setHistorial(null);
    } catch (e: unknown) {
      setError(mensajeDe(e, "No se pudo guardar la asignación."));
    } finally {
      setOcupado(null);
    }
  };

  const verHistorial = async () => {
    if (!rolHistorial) return;
    try {
      setHistorial(await cargarHistorial(rolHistorial));
    } catch (e: unknown) {
      setError(mensajeDe(e, "No se pudo cargar el historial."));
    }
  };

  const nombreDe = (id: string | null): string => {
    if (!id) return "Sin asignar";
    return personas.find((p) => p.id === id)?.nombre ?? "Persona asignada";
  };

  return (
    <div data-testid="asignacion-dominios" className="space-y-6 text-[var(--ui-texto)]">
      <div className="pb-4 border-b border-[var(--ui-borde)]">
        <h2 className="text-xl font-bold flex items-center gap-2">
          <ClipboardList className="w-5 h-5 text-[var(--ui-acento)]" />
          Asignación de dominios
        </h2>
        <p className="text-xs text-[var(--ui-texto-suave)] mt-1">
          Cada dominio del assessment tiene un encargado del diagnóstico: cualquier persona con rol vigente en la
          organización, salvo el DPO, que revisa y sella.
        </p>
      </div>

      {error && (
        <div
          role="alert"
          className="rounded-lg border border-[var(--ui-peligro-borde)] bg-[var(--ui-peligro-fondo)] p-3 text-xs text-[var(--ui-peligro)]"
        >
          {error}
        </div>
      )}

      {cargando ? (
        <p className="text-xs text-[var(--ui-texto-suave)]">Cargando asignaciones…</p>
      ) : (
        <table className="w-full text-xs bg-[var(--ui-superficie)] border border-[var(--ui-borde)] rounded-xl">
          <thead>
            <tr className="text-left text-[var(--ui-texto-suave)]">
              <th className="p-3 font-medium">Dominio</th>
              <th className="p-3 font-medium">Encargado</th>
            </tr>
          </thead>
          <tbody>
            {filas.map((fila) => (
              <tr key={fila.dimension} data-testid={`asignacion-${fila.dimension}`} className="border-t border-[var(--ui-borde)]">
                <td className="p-3">
                  <span className="font-semibold">{fila.dimension}</span> · {fila.nombre_dimension}
                </td>
                <td className="p-3">
                  {administra ? (
                    <select
                      aria-label={`Encargado de ${fila.dimension}`}
                      value={fila.responsable_user_id ?? ""}
                      disabled={ocupado === fila.dimension}
                      onChange={(e) => void asignar(fila.dimension, e.target.value)}
                      className="w-full rounded-lg border border-[var(--ui-borde)] bg-[var(--ui-fondo)] p-2"
                    >
                      <option value="">Sin asignar</option>
                      {personas.map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.nombre}
                        </option>
                      ))}
                    </select>
                  ) : (
                    <span>{nombreDe(fila.responsable_user_id)}</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {rolHistorial && (
        <div className="space-y-2">
          <button
            type="button"
            onClick={() => void verHistorial()}
            className="text-xs font-medium text-[var(--ui-acento)] underline"
          >
            Ver historial de asignaciones
          </button>
          {historial && (
            <ul data-testid="historial-asignaciones" className="text-xs space-y-1">
              {historial.length === 0 && <li className="text-[var(--ui-texto-suave)]">Todavía no hay asignaciones.</li>}
              {historial.map((m, i) => (
                <li key={`${m.dimension}-${m.asignado_en}-${i}`}>
                  {m.dimension} · {m.responsable_user_id ? "asignado" : "desasignado"} ·{" "}
                  {new Date(m.asignado_en).toLocaleString("es-EC")}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
