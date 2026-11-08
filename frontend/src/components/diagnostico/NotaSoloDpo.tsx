"use client";
/**
 * DIAG-14: junto a cada control de nivel y de evidencia, explica a un rol que no es DPO por qué no
 * puede asignarlo. En la demo ofrece pasar a la persona DPO (lib/demo solo se lee).
 */
import { useEffect, useState } from "react";
import { Lock } from "lucide-react";

import { cambiarPersona } from "@/lib/demo/cliente";
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
  if (!rol) return "un rol sin permiso de escritura";
  return ETIQUETA_DE_ROL[rol] ?? rol;
}

export default function NotaSoloDpo({ roles, testId }: { roles: readonly string[]; testId: string }) {
  const rol = rolParaConsultar(roles) ?? roles[0];
  const estado = useDemo((s) => s.estado);
  const iniciar = useDemo((s) => s.iniciar);
  const adoptar = useDemo((s) => s.adoptar);
  const [cambiando, setCambiando] = useState(false);

  useEffect(() => {
    void iniciar();
  }, [iniciar]);

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
      className="flex flex-wrap items-center gap-x-2 gap-y-1 text-[11px] text-[var(--ui-texto-suave)] leading-relaxed"
    >
      <Lock aria-hidden="true" className="w-3 h-3 shrink-0" />
      <span>
        Solo el DPO puede asignar el nivel. Estás viendo como {etiquetaDeRol(rol)}.
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
          className="underline underline-offset-2 text-[var(--ui-primario)] hover:text-white"
        >
          Ver como {dpo.rol_etiqueta}
        </a>
      )}
    </p>
  );
}
