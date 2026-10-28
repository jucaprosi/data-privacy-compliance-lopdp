"use client";

// ¤frontend-ide ¤rbac-tenant
/**
 * Organización activa en el encabezado (FE-21). «Cambiar organización» aparece solo para quien
 * pertenece a dos o más. En modo "headers" (desarrollo) no se muestra: hay una sola organización.
 */
import * as React from "react";
import Link from "next/link";
import { Building2 } from "lucide-react";
import {
  leerMisOrganizaciones,
  leerOrganizacionActiva,
  modoAutenticacion,
  RUTA_ORGANIZACIONES,
  type Organizacion,
} from "@/lib/auth";

export default function SelectorOrganizacion() {
  const [activa, setActiva] = React.useState<Organizacion | null>(null);
  const [cuantas, setCuantas] = React.useState(0);

  // El almacenamiento de la sesión solo existe en el navegador: se lee ya montado.
  React.useEffect(() => {
    if (modoAutenticacion() !== "oidc") return;
    setActiva(leerOrganizacionActiva());
    setCuantas(leerMisOrganizaciones().length);
  }, []);

  if (!activa) return null;
  return (
    <div className="flex items-center space-x-1.5" data-testid="organizacion-activa">
      <Building2 className="w-3.5 h-3.5 text-[var(--ui-texto-suave)]" aria-hidden="true" />
      <span className="max-w-[160px] truncate font-semibold" title={activa.nombre_comercial}>
        {activa.nombre_comercial}
      </span>
      {cuantas >= 2 && (
        <Link
          href={RUTA_ORGANIZACIONES}
          className="h-7 px-2 rounded-md bg-[var(--ui-campo)] hover:bg-[var(--ui-boton)] border border-[var(--ui-borde)] text-[var(--ui-texto-suave)] flex items-center transition"
        >
          Cambiar organización
        </Link>
      )}
    </div>
  );
}
