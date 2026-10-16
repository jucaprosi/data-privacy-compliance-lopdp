"use client";

import React, { useId, useMemo, useState } from "react";

import { organizacionApi } from "@/lib/roadmap/cliente";
import type { AreaItem, OrganizacionRole, RoleGrantItem, UserItem } from "@/types/roadmap";
import { aplanar, construirArbol } from "./arbolAreas";
import { describirError, type ErrorDescrito } from "./errores";
import { BOTON, BOTON_PRIMARIO, BloqueError, CAMPO, ETIQUETA } from "./ui";

export const ETIQUETA_ROL: Readonly<Record<OrganizacionRole, string>> = {
  responsable_area: "Responsable de área",
  encargado: "Encargado",
  dpo: "Delegado de protección de datos",
  implementador: "Implementador",
  admin_organizacion: "Administrador de la organización",
};

export interface RolesTabProps {
  usuarios: UserItem[];
  areas: AreaItem[];
  asignaciones: RoleGrantItem[];
  alCambiar: () => Promise<void>;
  alIrAConfiguracion: () => void;
}

export function RolesTab({ usuarios, areas, asignaciones, alCambiar, alIrAConfiguracion }: RolesTabProps) {
  const id = useId();
  const [usuarioId, setUsuarioId] = useState("");
  const [rol, setRol] = useState<OrganizacionRole>("encargado");
  const [areaId, setAreaId] = useState("");
  const [vigenteHasta, setVigenteHasta] = useState("");
  const [aviso, setAviso] = useState<string | null>(null);
  const [error, setError] = useState<ErrorDescrito | null>(null);
  const [ocupado, setOcupado] = useState(false);
  const [aRevocar, setARevocar] = useState<string | null>(null);

  const nombreUsuario = useMemo(() => new Map(usuarios.map((u) => [u.id, u.nombre])), [usuarios]);
  const nombreArea = useMemo(() => new Map(areas.map((a) => [a.id, a.nombre])), [areas]);
  const opcionesArea = useMemo(() => aplanar(construirArbol(areas)), [areas]);

  // Solo el responsable de área se acota a un área; los demás roles son de toda la organización.
  const admiteArea = rol === "responsable_area";

  async function ejecutar(accion: () => Promise<unknown>): Promise<boolean> {
    setError(null);
    setOcupado(true);
    try {
      await accion();
      await alCambiar();
      return true;
    } catch (err: unknown) {
      setError(describirError(err));
      return false;
    } finally {
      setOcupado(false);
    }
  }

  async function asignar(evento: React.FormEvent) {
    evento.preventDefault();
    if (usuarioId === "") {
      setAviso("Elige a qué persona se le asigna el rol.");
      return;
    }
    setAviso(null);
    const ok = await ejecutar(() =>
      organizacionApi.grantRole({
        user_id: usuarioId,
        role: rol,
        area_id: admiteArea && areaId ? areaId : null,
        valid_to: vigenteHasta ? new Date(`${vigenteHasta}T23:59:59Z`).toISOString() : null,
      }),
    );
    if (ok) {
      setUsuarioId("");
      setAreaId("");
      setVigenteHasta("");
    }
  }

  async function revocar(asignacionId: string) {
    const ok = await ejecutar(() => organizacionApi.revokeRole(asignacionId));
    if (ok) setARevocar(null);
  }

  return (
    <div className="space-y-5">
      <form onSubmit={asignar} noValidate aria-label="Asignar rol" className="grid grid-cols-1 sm:grid-cols-4 gap-3 items-start">
        <div>
          <label htmlFor={`${id}-usuario`} className={ETIQUETA}>
            Persona
          </label>
          <select id={`${id}-usuario`} className={CAMPO} value={usuarioId} onChange={(e) => setUsuarioId(e.target.value)}>
            <option value="">Elige una persona</option>
            {usuarios.map((u) => (
              <option key={u.id} value={u.id}>
                {u.nombre}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor={`${id}-rol`} className={ETIQUETA}>
            Rol
          </label>
          <select
            id={`${id}-rol`}
            className={CAMPO}
            value={rol}
            onChange={(e) => {
              setRol(e.target.value as OrganizacionRole);
              setAreaId("");
            }}
          >
            {(Object.keys(ETIQUETA_ROL) as OrganizacionRole[]).map((r) => (
              <option key={r} value={r}>
                {ETIQUETA_ROL[r]}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor={`${id}-area`} className={ETIQUETA}>
            Área
          </label>
          <select
            id={`${id}-area`}
            className={CAMPO}
            value={areaId}
            disabled={!admiteArea}
            onChange={(e) => setAreaId(e.target.value)}
            aria-describedby={`${id}-area-ayuda`}
          >
            <option value="">Toda la organización</option>
            {opcionesArea.map((n) => (
              <option key={n.area.id} value={n.area.id}>
                {`${"— ".repeat(n.nivel)}${n.area.nombre}`}
              </option>
            ))}
          </select>
          <p id={`${id}-area-ayuda`} className="text-[11px] text-zinc-500 mt-1">
            {admiteArea ? "Opcional: sin área, el rol vale para toda la organización." : "Este rol vale para toda la organización."}
          </p>
        </div>
        <div>
          <label htmlFor={`${id}-vigencia`} className={ETIQUETA}>
            Vigente hasta (opcional)
          </label>
          <input id={`${id}-vigencia`} type="date" className={CAMPO} value={vigenteHasta} onChange={(e) => setVigenteHasta(e.target.value)} />
        </div>
        <div className="sm:col-span-4 flex items-center gap-3">
          <button type="submit" className={BOTON_PRIMARIO} disabled={ocupado}>
            {ocupado ? "Asignando…" : "Asignar rol"}
          </button>
          {aviso && (
            <p role="alert" className="text-[11px] text-[#ff6b86]">
              {aviso}
            </p>
          )}
        </div>
      </form>

      {error && <BloqueError error={error} testId="error-roles" onIrAConfiguracion={alIrAConfiguracion} />}

      {asignaciones.length === 0 ? (
        <p role="status" className="text-xs text-zinc-400">
          Todavía no hay roles asignados.
        </p>
      ) : (
        <table className="w-full text-left text-xs">
          <caption className="sr-only">Roles asignados</caption>
          <thead>
            <tr className="text-zinc-500 border-b border-[#26262b]">
              <th scope="col" className="py-2 pr-3 font-semibold">
                Persona
              </th>
              <th scope="col" className="py-2 pr-3 font-semibold">
                Rol
              </th>
              <th scope="col" className="py-2 pr-3 font-semibold">
                Área
              </th>
              <th scope="col" className="py-2 pr-3 font-semibold">
                Vigencia
              </th>
              <th scope="col" className="py-2 font-semibold">
                Acciones
              </th>
            </tr>
          </thead>
          <tbody>
            {asignaciones.map((a) => {
              const persona = nombreUsuario.get(a.user_id) ?? a.user_id;
              return (
                <tr key={a.id} data-testid={`rol-${a.id}`} className="border-b border-[#26262b]/60 align-top">
                  <td className="py-2 pr-3 text-zinc-100">{persona}</td>
                  <td className="py-2 pr-3 text-zinc-200">{ETIQUETA_ROL[a.role]}</td>
                  <td className="py-2 pr-3 text-zinc-300">{a.area_id ? nombreArea.get(a.area_id) ?? a.area_id : "Toda la organización"}</td>
                  <td className="py-2 pr-3 text-zinc-300">
                    {a.valid_to ? `Hasta ${new Date(a.valid_to).toLocaleDateString("es-EC")}` : "Sin vencimiento"}
                  </td>
                  <td className="py-2">
                    {aRevocar === a.id ? (
                      <div role="group" aria-label={`Confirmar la revocación del rol de ${persona}`} className="space-y-1.5">
                        <p className="text-[11px] text-zinc-300">
                          ¿Revocar el rol de {ETIQUETA_ROL[a.role].toLowerCase()} a {persona}?
                        </p>
                        <div className="flex gap-2">
                          <button type="button" className={BOTON} disabled={ocupado} onClick={() => void revocar(a.id)}>
                            Confirmar revocación
                          </button>
                          <button type="button" className={BOTON} disabled={ocupado} onClick={() => setARevocar(null)}>
                            Cancelar
                          </button>
                        </div>
                      </div>
                    ) : (
                      <button
                        type="button"
                        className={BOTON}
                        onClick={() => {
                          setError(null);
                          setARevocar(a.id);
                        }}
                        aria-label={`Revocar el rol de ${ETIQUETA_ROL[a.role].toLowerCase()} a ${persona}`}
                      >
                        Revocar
                      </button>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </div>
  );
}
