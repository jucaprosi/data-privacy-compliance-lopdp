"use client";
/**
 * DIAG-14: junto a cada control de nivel y de evidencia, explica a un rol que no es DPO por qué no
 * puede asignarlo. En la demo ofrece pasar a la persona DPO (lib/demo solo se lee).
 */
import { useEffect, useState } from "react";
import { Lock } from "lucide-react";

import { cambiarPersona } from "@/lib/demo/cliente";
import { leerPersonaActiva } from "@/lib/demo/estado";
import { useDemo } from "@/lib/demo/store";
import { rolParaConsultar } from "@/lib/diagnostico/roles";

const ETIQUETA_DE_ROL: Record<string, string> = {
  admin_organizacion: "Administrador de la organización",
  coordinador: "Coordinador",
  implementador: "Implementador",
  responsable_area: "Responsable de área",
  auditor: "Auditor",
};

export function etiquetaDeRol(rol: string | null | undefined): string {
  if (!rol) return "un rol que solo puede consultar";
  // Nunca el identificador interno de un rol desconocido.
  return ETIQUETA_DE_ROL[rol] ?? "otro rol";
}

/** Qué no puede hacer quien no es DPO, en el control junto al que aparece la nota. */
export type AccionSoloDpo = "asignar el nivel" | "registrar la evidencia";

export default function NotaSoloDpo({
  roles,
  accion,
  testId,
}: {
  roles: readonly string[];
  accion: AccionSoloDpo;
  testId: string;
}) {
  const rol = rolParaConsultar(roles) ?? roles[0];
  const estado = useDemo((s) => s.estado);
  const refrescar = useDemo((s) => s.refrescar);
  const adoptar = useDemo((s) => s.adoptar);
  const [cambiando, setCambiando] = useState(false);

  // Solo una sesión que ya entró en la demo (persona guardada por el servidor) consulta su estado,
  // con el cliente autenticado. Fuera de la demo no se pide nada: ni /entorno ni /demo/estado.
  useEffect(() => {
    if (!estado && leerPersonaActiva()) void refrescar();
  }, [estado, refrescar]);

  const dpo = estado?.demo ? estado.personas.find((p) => p.rol === "dpo") : undefined;

  const verComoDpo = async () => {
    if (!dpo) return;
    setCambiando(true);
    const r = await cambiarPersona(dpo.usuario_id);
    setCambiando(false);
    if (r.ok) {
      adoptar(r.valor);
      window.location.reload();
    }
  };

  return (
    <p
      data-testid={testId}
      className="flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-[var(--ui-texto-suave)] leading-relaxed"
    >
      <Lock aria-hidden="true" className="w-3 h-3 shrink-0" />
      <span>
        Solo el DPO puede {accion}. Estás viendo como {etiquetaDeRol(rol)}.
      </span>
      {dpo && (
        // Enlace y no botón: la nota vive dentro del <fieldset disabled> de los controles.
        <a
          href="#"
          data-testid={`${testId}-ver-dpo`}
          aria-busy={cambiando}
          onClick={(e) => {
            e.preventDefault();
            if (!cambiando) void verComoDpo();
          }}
          className="inline-block py-1 underline underline-offset-2 text-[var(--ui-primario)] hover:text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--ui-primario)]"
        >
          {cambiando ? "Cambiando a DPO…" : "Ver como DPO"}
        </a>
      )}
    </p>
  );
}
