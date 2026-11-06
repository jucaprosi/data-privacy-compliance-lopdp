// ¤adpa ¤rbac-tenant
// ¤¤frontend-architect
/**
 * Catálogo de plantillas (BIB-102): `GET /biblioteca/plantillas?fuente=&tipo=&ola=`
 * (contrato de `docs/biblioteca-pmv.md`). La organización viaja solo en las cabeceras de identidad;
 * el servidor la autoriza. Cada fallo tiene su propio estado para que la pantalla no confunda «no hay
 * nada» con «no se pudo preguntar» ni con «no tienes permiso», y nunca se rellena con ejemplos.
 */
import { fetchAutenticado } from "@/lib/auth";
import { cabecerasDeMiembro } from "@/lib/auth/cabeceras";
import { falloDeRol, rechazoDeIdentidad } from "@/lib/biblioteca/http";

export const RUTA_CATALOGO = "/api/v1/biblioteca/plantillas";

export type FuentePlantilla = "smartcidi" | "organizacion";

export interface PlantillaCatalogo {
  id: string;
  codigo: string;
  nombre: string | null;
  tipo: string | null;
  fuente: FuentePlantilla;
  version: string;
  formato: string;
  validacion_legal: string | null;
  ola: number | null;
  estado: string;
  descargable: boolean;
}

export interface FiltrosCatalogo {
  fuente: FuentePlantilla | "";
  tipo: string;
  ola: string;
}

export const SIN_FILTROS: FiltrosCatalogo = { fuente: "", tipo: "", ola: "" };

export const FUENTES: ReadonlyArray<{ id: FuentePlantilla; nombre: string }> = [
  { id: "smartcidi", nombre: "SMARTCIDI" },
  { id: "organizacion", nombre: "Mi plantilla" },
];

/** Tipos del contrato de plantillas Markdown (`docs/biblioteca-pmv.md` §b). */
export const TIPOS: ReadonlyArray<{ id: string; nombre: string }> = [
  { id: "politica", nombre: "Política" },
  { id: "aviso", nombre: "Aviso" },
  { id: "formulario", nombre: "Formulario" },
  { id: "acuerdo", nombre: "Acuerdo" },
  { id: "contrato", nombre: "Contrato" },
  { id: "registro", nombre: "Registro" },
  { id: "procedimiento", nombre: "Procedimiento" },
  { id: "protocolo", nombre: "Protocolo" },
  { id: "modelo", nombre: "Modelo" },
];

export const OLAS = [1, 2, 3] as const;

/**
 * `desconectado`: la petición no llegó al servidor. `denegado`: el servidor rechazó a la persona.
 * `error`: el servidor respondió con un fallo o con algo que no es el catálogo.
 */
export type ResultadoCatalogo =
  | { estado: "listo"; plantillas: PlantillaCatalogo[] }
  | { estado: "desconectado"; mensaje: string }
  | { estado: "denegado"; mensaje: string }
  | { estado: "error"; mensaje: string };

export function hayFiltros(filtros: FiltrosCatalogo): boolean {
  return filtros.fuente !== "" || filtros.tipo !== "" || filtros.ola !== "";
}

function esPlantilla(valor: unknown): valor is PlantillaCatalogo {
  const p = valor as Partial<PlantillaCatalogo> | null;
  return Boolean(p) && typeof p?.id === "string" && typeof p.codigo === "string"
    && typeof p.version === "string" && typeof p.estado === "string" && typeof p.descargable === "boolean";
}

export function consultaDe(filtros: FiltrosCatalogo): string {
  const parametros = new URLSearchParams();
  if (filtros.fuente) parametros.set("fuente", filtros.fuente);
  if (filtros.tipo) parametros.set("tipo", filtros.tipo);
  if (filtros.ola) parametros.set("ola", filtros.ola);
  const texto = parametros.toString();
  return texto ? `?${texto}` : "";
}

export async function consultarCatalogo(filtros: FiltrosCatalogo): Promise<ResultadoCatalogo> {
  let respuesta: Response;
  try {
    respuesta = await fetchAutenticado(`${RUTA_CATALOGO}${consultaDe(filtros)}`, { cache: "no-store" }, cabecerasDeMiembro());
  } catch (error) {
    const sinRol = falloDeRol(error);
    if (sinRol) return { estado: "denegado", mensaje: sinRol };
    return { estado: "desconectado", mensaje: "No hay conexión con el servidor." };
  }
  const cuerpo = await respuesta.json().catch(() => null);
  const rechazo = rechazoDeIdentidad(respuesta.status, cuerpo, "No tienes acceso a la Biblioteca de esta organización.");
  if (rechazo) return { estado: "denegado", mensaje: rechazo };
  if (!respuesta.ok || !Array.isArray(cuerpo) || !cuerpo.every(esPlantilla)) {
    return { estado: "error", mensaje: "El servidor no pudo entregar el catálogo de plantillas." };
  }
  return { estado: "listo", plantillas: cuerpo };
}
