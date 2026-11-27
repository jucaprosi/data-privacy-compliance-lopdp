// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
// ¤adpa
// ¤¤frontend-architect
/**
 * BIB-118 · Contenedor de la vista `biblioteca_editorial` en el panel: el alto y el desplazamiento son suyos.
 * BIB-412: con `contexto` (Plataforma) añade la cabecera «Administración editorial · Plataforma».
 */
import { AdministracionEditorial } from "./AdministracionEditorial";

export default function VistaAdministracionEditorial({ contexto }: { contexto?: string } = {}) {
  return (
    <div className="h-full overflow-y-auto">
      {contexto && <p className="mx-auto max-w-6xl px-6 pt-4 text-sm text-[var(--ui-texto-suave)]">Administración editorial · {contexto}</p>}
      <AdministracionEditorial />
    </div>
  );
}
