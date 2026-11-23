// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
"use client";

/** `/cartera` abre el tablero de cartera dentro del panel (Inicio › Tablero de cartera). ¤cartera */
import * as React from "react";
import { useRouter } from "next/navigation";
import { useAuditStore, type ActiveView } from "@/store/useAuditStore";

export default function CarteraPage() {
  const router = useRouter();
  React.useEffect(() => {
    useAuditStore.getState().setActiveView("cartera" as unknown as ActiveView);
    router.replace("/dashboard");
  }, [router]);
  return null;
}
