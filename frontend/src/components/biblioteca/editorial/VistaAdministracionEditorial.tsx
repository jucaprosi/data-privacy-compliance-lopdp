// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
// ¤adpa
// ¤¤frontend-architect
/** BIB-118 · Contenedor de la vista `biblioteca_editorial` en el panel: el alto y el desplazamiento son suyos. */
import { AdministracionEditorial } from "./AdministracionEditorial";

export default function VistaAdministracionEditorial() {
  return (
    <div className="h-full overflow-y-auto">
      <AdministracionEditorial />
    </div>
  );
}
