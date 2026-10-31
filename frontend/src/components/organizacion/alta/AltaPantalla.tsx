"use client";
// ¤asistente ¤frontend-ide ¤alta-organizacion
// Pantalla del alta (ORG-16) en el menú Configuración: resuelve el rol con /organizacion/me/roles y monta
// el asistente. Sin sesión no hay servidor del que leer el alta, y lo dice.
import React, { useEffect, useState } from "react";
import { useSesion } from "@/lib/auth";
import { organizacionApi } from "@/lib/roadmap/cliente";
import { puedeEscribirAlta } from "@/lib/organizacion/alta";
import type { OrganizacionRole } from "@/types/roadmap";
import AltaOrganizacion from "./AltaOrganizacion";

type Rol = { fase: "cargando" } | { fase: "sin_servidor" } | { fase: "lista"; rol: OrganizacionRole | null } | { fase: "error"; mensaje: string };

export default function AltaPantalla() {
  const { listo, requiereSesion, sesion } = useSesion();
  const [rol, setRol] = useState<Rol>({ fase: "cargando" });

  useEffect(() => {
    if (!listo) return;
    if (!requiereSesion || !sesion) {
      setRol({ fase: "sin_servidor" });
      return;
    }
    let cancelado = false;
    organizacionApi
      .getMyRoles()
      .then((roles) => {
        if (cancelado) return;
        const preferido = roles.find((r) => r.role === "admin_organizacion") ?? roles.find((r) => r.role === "implementador") ?? roles[0];
        setRol({ fase: "lista", rol: preferido?.role ?? null });
      })
      .catch((err: unknown) => {
        if (!cancelado) setRol({ fase: "error", mensaje: err instanceof Error ? err.message : "No se pudieron consultar tus roles." });
      });
    return () => {
      cancelado = true;
    };
  }, [listo, requiereSesion, sesion]);

  return (
    <div className="mx-auto max-w-4xl space-y-4 pb-10">
      {rol.fase === "cargando" && <p role="status" className="text-sm">Cargando…</p>}
      {rol.fase === "sin_servidor" && (
        <p className="text-sm">Inicia sesión para completar el alta: se guarda en el servidor de tu organización.</p>
      )}
      {rol.fase === "error" && <p role="alert" className="badge-render-danger rounded-md px-3 py-2 text-sm">{rol.mensaje}</p>}
      {rol.fase === "lista" && rol.rol === null && <p className="text-sm">No tienes un rol activo en esta organización.</p>}
      {rol.fase === "lista" && rol.rol !== null && <AltaOrganizacion rol={rol.rol} puedeEditar={puedeEscribirAlta(rol.rol)} />}
    </div>
  );
}
