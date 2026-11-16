"use client";
// ¤frontend-ide ¤inventario
// Resuelve el rol con el que se consulta (ORG-18): /organizacion/me/roles; sin sesión no hay servidor.
import { useEffect, useState } from "react";
import { useSesion } from "@/lib/auth";
import { organizacionApi } from "@/lib/roadmap/cliente";
import type { OrganizacionRole } from "@/types/roadmap";

export type RolSedes =
  | { fase: "cargando" }
  | { fase: "sin_servidor" }
  | { fase: "sin_rol" }
  | { fase: "error"; mensaje: string }
  | { fase: "lista"; rol: OrganizacionRole };

export function useRolSedes(): RolSedes {
  const { listo, requiereSesion, sesion } = useSesion();
  const [estado, setEstado] = useState<RolSedes>({ fase: "cargando" });

  useEffect(() => {
    if (!listo) return;
    if (!requiereSesion || !sesion) {
      setEstado({ fase: "sin_servidor" });
      return;
    }
    let cancelado = false;
    organizacionApi
      .getMyRoles()
      .then((roles) => {
        if (cancelado) return;
        const orden: OrganizacionRole[] = ["admin_organizacion", "implementador", "coordinador", "dpo"];
        const rol = orden.find((r) => roles.some((x) => x.role === r));
        setEstado(rol ? { fase: "lista", rol } : { fase: "sin_rol" });
      })
      .catch(() => {
        if (!cancelado) setEstado({ fase: "error", mensaje: "No pudimos comprobar tus permisos. Inténtalo de nuevo." });
      });
    return () => {
      cancelado = true;
    };
  }, [listo, requiereSesion, sesion]);

  return estado;
}
