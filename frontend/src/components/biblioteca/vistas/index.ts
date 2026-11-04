// ¤adpa ¤frontend-ide
// ¤¤frontend-architect
/**
 * Registro de vistas de Biblioteca (BIB-111): un archivo por tarea.
 *
 * Cada tarea pendiente tiene abajo su sección reservada, vacía, entre las marcas
 * `// === <ID> ===` y `// === fin <ID> ===`. Escribe ahí solo su `import` de la vista y su
 * `registrarVista(<ranura>, <Vista>)`; esa sección es lo único que posee de este archivo.
 * `BibliotecaWorkspace.tsx` importa este archivo y no vuelve a editarse.
 */
import "@/lib/biblioteca/registro";

// === BIB-102 ===
import VistaCatalogo from "@/components/biblioteca/catalogo/VistaCatalogo";
import { registrarVista as registrarVistaBib102 } from "@/lib/biblioteca/registro";

registrarVistaBib102("pestana:plantillas", VistaCatalogo);
// === fin BIB-102 ===

// === BIB-103 ===
import FichaPlantilla from "@/components/biblioteca/fichas/FichaPlantilla";
import "@/components/biblioteca/fichas/anfitrionPruebas";
import { registrarVista } from "@/lib/biblioteca/registro";
registrarVista("plantilla:ficha", FichaPlantilla);
// === fin BIB-103 ===

// === BIB-104 ===
import BotonDescargaPlantilla from "@/components/biblioteca/descargas/BotonDescargaPlantilla";
import "@/components/biblioteca/descargas/anfitrionPruebas";
import { registrarVista as registrarVistaBib104 } from "@/lib/biblioteca/registro";
registrarVistaBib104("plantilla:acciones", BotonDescargaPlantilla);
// === fin BIB-104 ===

// === BIB-106 ===
// === fin BIB-106 ===

// === BIB-113 ===
import VistaDocumentos from "@/components/biblioteca/documentos/VistaDocumentos";
import DetalleDocumento from "@/components/biblioteca/documentos/DetalleDocumento";
import { registrarVista as registrarVistaBib113 } from "@/lib/biblioteca/registro";

registrarVistaBib113("pestana:documentos", VistaDocumentos);
registrarVistaBib113("documento:detalle", DetalleDocumento);
// === fin BIB-113 ===

// === BIB-114 ===
import BotonUsarPlantilla from '@/components/biblioteca/editor/BotonUsarPlantilla';
import EditorBorrador from '@/components/biblioteca/editor/EditorBorrador';
import '@/components/biblioteca/editor/anfitrionPruebas';
import { registrarVista as registrarVistaBib114 } from '@/lib/biblioteca/registro';

registrarVistaBib114('plantilla:acciones', BotonUsarPlantilla);
registrarVistaBib114('documento:editor', EditorBorrador);
// === fin BIB-114 ===

// === BIB-202 ===
import PanelProcedencia from "@/components/biblioteca/procedencia/PanelProcedencia";
import { registrarVista as registrarVistaBib202 } from "@/lib/biblioteca/registro";

registrarVistaBib202("documento:acciones", PanelProcedencia);
// === fin BIB-202 ===

// === BIB-203 ===
import TablasCaptura from "@/components/biblioteca/tablas/TablasCaptura";
import { registrarVista as registrarVistaBib203 } from "@/lib/biblioteca/registro";

registrarVistaBib203("documento:editor", TablasCaptura);
// === fin BIB-203 ===

// === BIB-204 ===
import VistaRecomendados from '@/components/biblioteca/recomendados/VistaRecomendados';
import { registrarVista as registrarVistaBib204 } from '@/lib/biblioteca/registro';

registrarVistaBib204('pestana:plantillas', VistaRecomendados);
// === fin BIB-204 ===

// === BIB-205 ===
// === fin BIB-205 ===

// === BIB-206 ===
// === fin BIB-206 ===

// === BIB-207 ===
// === fin BIB-207 ===

// === BIB-208 ===
// === fin BIB-208 ===

// === BIB-301 ===
import FlujoRevision from "@/components/biblioteca/expediente/FlujoRevision";
import { registrarVista as registrarVistaBib301 } from "@/lib/biblioteca/registro";
registrarVistaBib301("documento:acciones", FlujoRevision);
// === fin BIB-301 ===

// === BIB-302 ===
import EnlacesAcciones from '@/components/biblioteca/enlaces/EnlacesAcciones';
import { registrarVista as registrarVistaBib302 } from '@/lib/biblioteca/registro';

registrarVistaBib302('documento:detalle', EnlacesAcciones);
// === fin BIB-302 ===

// === BIB-303 ===
// === fin BIB-303 ===

// === BIB-304 ===
import VistaImpactos from '@/components/biblioteca/impacto/VistaImpactos';
import { registrarVista as registrarVistaBib304 } from '@/lib/biblioteca/registro';
registrarVistaBib304('pestana:documentos', VistaImpactos);
// === fin BIB-304 ===

// === BIB-305 ===
// === fin BIB-305 ===

// === BIB-306 ===
import HistorialDocumento from "@/components/biblioteca/historial/HistorialDocumento";
import { registrarVista as registrarVistaBib306 } from "@/lib/biblioteca/registro";

registrarVistaBib306("documento:acciones", HistorialDocumento);
// === fin BIB-306 ===

// === BIB-401 ===
// === fin BIB-401 ===

// === BIB-402 ===
import VinculosDocumento from "@/components/biblioteca/vinculos/VinculosDocumento";
import { registrarVista as registrarVistaBib402 } from "@/lib/biblioteca/registro";

registrarVistaBib402("documento:detalle", VinculosDocumento);
// === fin BIB-402 ===
