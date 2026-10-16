"use client";

import React, { useCallback, useEffect, useRef, useState } from "react";
import { Loader2, Lock } from "lucide-react";

import { organizacionApi } from "@/lib/roadmap/cliente";
import { useRoadmapStore } from "@/store/useRoadmapStore";
import type { AreaItem, RoleGrantItem, UserItem } from "@/types/roadmap";
import { AreasTab } from "./AreasTab";
import { ConfiguracionTab } from "./ConfiguracionTab";
import { describirError, type ErrorDescrito } from "./errores";
import { RolesTab } from "./RolesTab";
import { BOTON, BloqueError } from "./ui";
import { UsuariosTab } from "./UsuariosTab";

export type SeccionAdmin = "usuarios" | "areas" | "roles" | "configuracion";

const SECCIONES: ReadonlyArray<{ clave: SeccionAdmin; etiqueta: string }> = [
  { clave: "usuarios", etiqueta: "Usuarios" },
  { clave: "areas", etiqueta: "Áreas" },
  { clave: "roles", etiqueta: "Roles" },
  { clave: "configuracion", etiqueta: "Configuración" },
];

export interface AdminPanelProps {
  seccionInicial?: SeccionAdmin;
}

export function AdminPanel({ seccionInicial = "usuarios" }: AdminPanelProps) {
  const rol = useRoadmapStore((s) => s.session.role);
  const esAdmin = rol === "admin_organizacion";

  const [seccion, setSeccion] = useState<SeccionAdmin>(seccionInicial);
  const [usuarios, setUsuarios] = useState<UserItem[]>([]);
  const [areas, setAreas] = useState<AreaItem[]>([]);
  const [asignaciones, setAsignaciones] = useState<RoleGrantItem[]>([]);
  const [cargando, setCargando] = useState(esAdmin);
  const [errorCarga, setErrorCarga] = useState<ErrorDescrito | null>(null);
  const botones = useRef<Array<HTMLButtonElement | null>>([]);

  const recargar = useCallback(async () => {
    const [u, a, r] = await Promise.all([
      organizacionApi.listUsers(),
      organizacionApi.listAreas(),
      organizacionApi.listRoles(),
    ]);
    setUsuarios(u);
    setAreas(a);
    setAsignaciones(r);
  }, []);

  const cargarInicial = useCallback(async () => {
    setCargando(true);
    setErrorCarga(null);
    try {
      await recargar();
    } catch (err: unknown) {
      setErrorCarga(describirError(err));
    } finally {
      setCargando(false);
    }
  }, [recargar]);

  useEffect(() => {
    // Solo el administrador gestiona la organización: al resto el servidor le responde 403
    // incluso al listar, así que ni se intenta.
    if (esAdmin) void cargarInicial();
  }, [esAdmin, cargarInicial]);

  function moverConTeclado(evento: React.KeyboardEvent, indice: number) {
    if (evento.key !== "ArrowRight" && evento.key !== "ArrowLeft") return;
    evento.preventDefault();
    const siguiente = (indice + (evento.key === "ArrowRight" ? 1 : -1) + SECCIONES.length) % SECCIONES.length;
    setSeccion(SECCIONES[siguiente].clave);
    botones.current[siguiente]?.focus();
  }

  if (!esAdmin) {
    return (
      <section aria-label="Administración de la organización" className="bg-[#141417] border border-[#26262b] rounded-xl p-5">
        <div role="note" className="flex items-start gap-2.5 p-3 rounded-lg bg-[#ffb300]/10 border border-[#ffb300]/40 text-xs text-zinc-200">
          <Lock className="w-4 h-4 shrink-0 mt-0.5 text-[#ffb300]" aria-hidden="true" />
          <p>
            Tu rol actual es <strong>{rol}</strong>. Solo la persona con el rol <strong>administrador de la organización</strong>{" "}
            gestiona usuarios, áreas, roles y la configuración.
          </p>
        </div>
      </section>
    );
  }

  return (
    <section aria-label="Administración de la organización" className="bg-[#141417] border border-[#26262b] rounded-xl p-5 space-y-4 text-zinc-200">
      <header>
        <h2 className="text-sm font-bold uppercase tracking-wider text-white">Administración de la organización</h2>
        <p className="text-[11px] text-zinc-400 mt-0.5">Usuarios, áreas, roles y configuración de la organización.</p>
      </header>

      <div role="tablist" aria-label="Secciones de administración" className="flex flex-wrap gap-2 border-b border-[#26262b] pb-2">
        {SECCIONES.map((s, i) => (
          <button
            key={s.clave}
            ref={(el) => {
              botones.current[i] = el;
            }}
            type="button"
            role="tab"
            id={`pestana-${s.clave}`}
            aria-selected={seccion === s.clave}
            aria-controls={`panel-${s.clave}`}
            tabIndex={seccion === s.clave ? 0 : -1}
            onClick={() => setSeccion(s.clave)}
            onKeyDown={(e) => moverConTeclado(e, i)}
            className={`rounded-md px-3 py-1.5 text-xs font-semibold focus:outline-none focus-visible:ring-2 focus-visible:ring-[#3892f3] ${
              seccion === s.clave ? "bg-[#3892f3] text-white" : "bg-[#1b1b20] text-zinc-300 hover:bg-[#23232a]"
            }`}
          >
            {s.etiqueta}
          </button>
        ))}
      </div>

      {cargando && (
        <p role="status" className="flex items-center gap-2 text-xs text-zinc-300">
          <Loader2 className="w-4 h-4 animate-spin text-[#3892f3]" aria-hidden="true" />
          Cargando la organización…
        </p>
      )}

      {errorCarga && (
        <div className="space-y-2">
          <BloqueError error={errorCarga} testId="error-carga" />
          <button type="button" className={BOTON} onClick={() => void cargarInicial()}>
            Reintentar la carga
          </button>
        </div>
      )}

      {!cargando && !errorCarga && (
        <div role="tabpanel" id={`panel-${seccion}`} aria-labelledby={`pestana-${seccion}`}>
          {seccion === "usuarios" && <UsuariosTab usuarios={usuarios} alCambiar={recargar} />}
          {seccion === "areas" && <AreasTab areas={areas} alCambiar={recargar} />}
          {seccion === "roles" && (
            <RolesTab
              usuarios={usuarios}
              areas={areas}
              asignaciones={asignaciones}
              alCambiar={recargar}
              alIrAConfiguracion={() => setSeccion("configuracion")}
            />
          )}
          {seccion === "configuracion" && <ConfiguracionTab />}
        </div>
      )}
    </section>
  );
}

export default AdminPanel;
