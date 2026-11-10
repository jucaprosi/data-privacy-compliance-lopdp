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

const MENSAJES_POR_CODIGO: Record<string, string> = {
  ENCARGADO_SIN_ROL:
    "La persona elegida no tiene un rol vigente en la organización. Elige a otra persona o asígnale un rol primero.",
  ENCARGADO_ES_DPO: "El DPO revisa y sella el diagnóstico, pero no lo responde. Elige a otra persona.",
};

/** El texto sale del código del error, no del servidor; un código desconocido usa el mensaje genérico. */
function mensajeDe(error: unknown, porDefecto: string): string {
  const codigo = (error as { code?: string } | null)?.code;
  return (codigo && MENSAJES_POR_CODIGO[codigo]) || porDefecto;
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
  const [guardado, setGuardado] = useState(false);

  const cargar = useCallback(async () => {
    setCargando(true);
    setError(null);
    try {
      const roles = await rolesDelUsuario();
      const rol = rolParaAsignaciones(roles);
      if (!rol) {
        setFilas([]);
        setError("No tienes permiso para ver la asignación de dominios.");
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
    setGuardado(false);
    try {
      await asignarDominio(dimension, valor || null);
      await cargar();
      setHistorial(null);
      setGuardado(true);
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

  const nombreDe = (fila: AsignacionDominio): string => {
    if (!fila.responsable_user_id) return "Sin asignar";
    return fila.responsable_nombre ?? "Asignado";
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
          <caption className="sr-only">Encargado del diagnóstico por dominio</caption>
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
                      aria-busy={ocupado === fila.dimension}
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
                    <span>{nombreDe(fila)}</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {guardado && (
        <p role="status" className="text-xs text-[var(--ui-texto-suave)]">
          Asignación guardada.
        </p>
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
                  {m.dimension} · {m.responsable_user_id ? "asignado" : "sin encargado"} ·{" "}
                  {new Date(m.asignado_en).toLocaleString("es-EC", { dateStyle: "short", timeStyle: "short" })}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
