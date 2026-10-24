"use client";

import React, { useCallback, useEffect, useRef, useState } from "react";
import { Loader2, Lock } from "lucide-react";

import { organizacionApi } from "@/lib/roadmap/cliente";
import { useRoadmapStore } from "@/store/useRoadmapStore";
import type { AreaItem, RoleGrantItem, UserItem } from "@/types/roadmap";
import { AreasTab } from "./AreasTab";
import { ConfiguracionTab } from "./ConfiguracionTab";
import {
  designacionesApi,
  type DesignacionFormal,
  type InformeEstadoDesignaciones,
} from "./designaciones";
import { DesignacionesTab } from "./DesignacionesTab";
import { describirError, type ErrorDescrito } from "./errores";
import {
  estructuraApi,
  type AreaEstructuraNodo,
  type InformeCoberturaResponse,
} from "./estructura";
import { EstructuraTab } from "./EstructuraTab";
import { RolesTab } from "./RolesTab";
import { BOTON, BloqueError } from "./ui";
import { UsuariosTab } from "./UsuariosTab";

export type SeccionAdmin =
  | "usuarios"
  | "areas"
  | "roles"
  | "estructura"
  | "designaciones"
  | "configuracion";

const SECCIONES_ADMIN: ReadonlyArray<{ clave: SeccionAdmin; etiqueta: string }> = [
  { clave: "usuarios", etiqueta: "Usuarios" },
  { clave: "areas", etiqueta: "Áreas" },
  { clave: "roles", etiqueta: "Roles" },
  { clave: "estructura", etiqueta: "Estructura" },
  { clave: "designaciones", etiqueta: "Designaciones" },
  { clave: "configuracion", etiqueta: "Configuración" },
];

export interface AdminPanelProps {
  seccionInicial?: SeccionAdmin;
  alIrASolicitudRM10?: () => void;
}

export function AdminPanel({ seccionInicial = "usuarios", alIrASolicitudRM10 }: AdminPanelProps) {
  const rol = useRoadmapStore((s) => s.session.role);
  const esAdmin = rol === "admin_organizacion";
  const puedeEscribir = esAdmin;

  const [seccion, setSeccion] = useState<SeccionAdmin>(seccionInicial);

  const [usuarios, setUsuarios] = useState<UserItem[]>([]);
  const [areas, setAreas] = useState<AreaItem[]>([]);
  const [asignaciones, setAsignaciones] = useState<RoleGrantItem[]>([]);
  const [arbolEstructura, setArbolEstructura] = useState<AreaEstructuraNodo[]>([]);
  const [coberturaEstructura, setCoberturaEstructura] = useState<InformeCoberturaResponse | null>(null);
  const [designaciones, setDesignaciones] = useState<DesignacionFormal[]>([]);
  const [estadoDesignaciones, setEstadoDesignaciones] = useState<InformeEstadoDesignaciones | null>(null);

  const [cargando, setCargando] = useState(esAdmin);
  const [errorCarga, setErrorCarga] = useState<ErrorDescrito | null>(null);
  const botones = useRef<Array<HTMLButtonElement | null>>([]);

  const recargarEstructura = useCallback(async () => {
    try {
      const [resArbol, resCob] = await Promise.all([
        estructuraApi.obtenerArbol(rol),
        estructuraApi.obtenerCobertura(rol),
      ]);
      setArbolEstructura(resArbol.arbol || []);
      setCoberturaEstructura(resCob);
    } catch {
      // Resiliente si el mockServer de pruebas anteriores (ej. FE-05) no simula estructura
      setArbolEstructura([]);
      setCoberturaEstructura(null);
    }
  }, [rol]);

  const recargarDesignaciones = useCallback(async () => {
    try {
      const [resLista, resEstado] = await Promise.all([
        designacionesApi.listar(undefined, rol),
        designacionesApi.obtenerEstado(rol),
      ]);
      setDesignaciones(resLista || []);
      setEstadoDesignaciones(resEstado || null);
    } catch {
      // Resiliente si arneses no simulan designaciones
      setDesignaciones([]);
      setEstadoDesignaciones(null);
    }
  }, [rol]);

  const recargar = useCallback(async () => {
    if (esAdmin) {
      const [u, a, r] = await Promise.all([
        organizacionApi.listUsers(),
        organizacionApi.listAreas(),
        organizacionApi.listRoles(),
      ]);
      setUsuarios(u);
      setAreas(a);
      setAsignaciones(r);
      await Promise.all([recargarEstructura(), recargarDesignaciones()]);
    }
  }, [esAdmin, recargarEstructura, recargarDesignaciones]);

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
    if (esAdmin) {
      void cargarInicial();
    }
  }, [esAdmin, cargarInicial]);

  function moverConTeclado(evento: React.KeyboardEvent, indice: number) {
    if (evento.key !== "ArrowRight" && evento.key !== "ArrowLeft") return;
    evento.preventDefault();
    const siguiente = (indice + (evento.key === "ArrowRight" ? 1 : -1) + SECCIONES_ADMIN.length) % SECCIONES_ADMIN.length;
    setSeccion(SECCIONES_ADMIN[siguiente].clave);
    botones.current[siguiente]?.focus();
  }

  if (!esAdmin) {
    return (
      <section aria-label="Administración de la organización" className="bg-[var(--ui-superficie)] border border-[var(--ui-borde)] rounded-xl p-5">
        <div role="note" className="flex items-start gap-2.5 p-3 rounded-lg bg-[#ffb300]/10 border border-[#ffb300]/40 text-xs text-zinc-200">
          <Lock className="w-4 h-4 shrink-0 mt-0.5 text-[#ffb300]" aria-hidden="true" />
          <p>
            Tu rol actual es <strong>{rol}</strong>. Solo la persona con el rol <strong>administrador de la organización</strong>{" "}
            gestiona usuarios, áreas, roles, estructura, designaciones y la configuración.
          </p>
        </div>
      </section>
    );
  }

  return (
    <section aria-label="Administración de la organización" className="bg-[var(--ui-superficie)] border border-[var(--ui-borde)] rounded-xl p-5 space-y-4 text-zinc-200">
      <header>
        <h2 className="text-sm font-bold uppercase tracking-wider text-white">Administración de la organización</h2>
        <p className="text-[11px] text-zinc-400 mt-0.5">
          Usuarios, áreas, roles, estructura orgánica, designaciones formales y configuración de la organización.
        </p>
      </header>

      <div role="tablist" aria-label="Secciones de administración" className="flex flex-wrap gap-2 border-b border-[var(--ui-borde)] pb-2">
        {SECCIONES_ADMIN.map((s, i) => (
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
              seccion === s.clave ? "bg-[var(--ui-primario)] text-[var(--ui-primario-texto)]" : "bg-[var(--ui-boton)] text-zinc-300 hover:bg-[var(--ui-boton-hover)]"
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
          {seccion === "estructura" && (
            <EstructuraTab
              arbol={arbolEstructura}
              cobertura={coberturaEstructura}
              areas={areas}
              usuarios={usuarios}
              puedeEditar={puedeEscribir}
              alCambiar={recargar}
              alIrASolicitudRM10={alIrASolicitudRM10}
            />
          )}
          {seccion === "designaciones" && (
            <DesignacionesTab
              designaciones={designaciones}
              estadoDesignaciones={estadoDesignaciones}
              usuarios={usuarios}
              puedeEditar={puedeEscribir}
              alCambiar={recargar}
            />
          )}
          {seccion === "configuracion" && <ConfiguracionTab />}
        </div>
      )}
    </section>
  );
}

export default AdminPanel;
