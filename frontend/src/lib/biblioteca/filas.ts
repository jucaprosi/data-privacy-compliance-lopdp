// ¤adpa ¤rbac-tenant
/**
 * Cliente de las tablas de captura (BIB-203). El servidor decide: IDs, catálogos, fechas reales,
 * referencias del mismo tenant y atomicidad. Aquí solo se parte lo pegado en filas y se muestra.
 */
import { fetchAutenticado } from "@/lib/auth";
import { cabecerasDeMiembro } from "@/lib/auth/cabeceras";
import { mensajeDelServidor, ROLES_EDITORES } from "@/lib/biblioteca/http";

export type TablaCaptura = "INV" | "RAT" | "LEG";

export interface ColumnaCaptura {
  clave: string;
  etiqueta: string;
  tipo: "texto" | "fecha" | "catalogo" | "tratamiento";
  obligatoria: boolean;
  catalogo: string[];
}

export interface FilaEntrada {
  codigo: string;
  datos: Record<string, string>;
}

export interface FilaCaptura extends FilaEntrada {
  id: string;
  borrador_id: string;
  tabla: TablaCaptura;
  tratamiento_id: string | null;
  revision: number;
  actualizado_en: string;
}

export interface ResultadoFila {
  indice: number;
  codigo: string;
  errores: string[];
}

export interface Previa {
  tabla: TablaCaptura;
  valida: boolean;
  filas: ResultadoFila[];
}

export interface FilaPlan {
  id: string;
  titulo: string;
  control_ref: string;
  fecha_inicio: string | null;
  fecha_fin: string | null;
  estado: "En plazo" | "Vencida" | "Completada" | "Sin fecha válida";
  editable: false;
}

export const MAX_FILAS = 100;
const RUTA = "/api/v1/biblioteca/filas";
const enc = encodeURIComponent;

async function json<T>(respuesta: Response, mensaje: string): Promise<T> {
  const cuerpo = await respuesta.json().catch(() => null);
  if (!respuesta.ok) {
    const detalle = mensajeDelServidor(cuerpo, mensaje);
    throw new Error(detalle ?? mensaje);
  }
  return cuerpo as T;
}

function enviar(metodo: string, cuerpo: unknown): RequestInit {
  return { method: metodo, headers: { "Content-Type": "application/json" }, body: JSON.stringify(cuerpo) };
}

export async function obtenerEsquemas(): Promise<Record<TablaCaptura, ColumnaCaptura[]>> {
  return json(await fetchAutenticado(`${RUTA}/esquemas`, { cache: "no-store" }, cabecerasDeMiembro(ROLES_EDITORES)),
    "No se pudieron cargar las columnas.");
}

export async function listarFilas(borradorId: string, tabla: TablaCaptura): Promise<FilaCaptura[]> {
  return json(await fetchAutenticado(`${RUTA}/${enc(borradorId)}/${tabla}`, { cache: "no-store" },
    cabecerasDeMiembro(ROLES_EDITORES)), "No se pudieron cargar las filas.");
}

export async function validarFilas(borradorId: string, tabla: TablaCaptura, filas: FilaEntrada[]): Promise<Previa> {
  return json(await fetchAutenticado(`${RUTA}/${enc(borradorId)}/validar`, enviar("POST", { tabla, filas }),
    cabecerasDeMiembro(ROLES_EDITORES)), "No se pudo validar lo pegado.");
}

export async function confirmarFilas(borradorId: string, tabla: TablaCaptura, filas: FilaEntrada[]): Promise<FilaCaptura[]> {
  return json(await fetchAutenticado(`${RUTA}/${enc(borradorId)}`, enviar("POST", { tabla, filas }),
    cabecerasDeMiembro(ROLES_EDITORES)), "No se guardó ninguna fila.");
}

export async function editarFila(filaId: string, datos: Record<string, string>, revision: number): Promise<FilaCaptura> {
  return json(await fetchAutenticado(`${RUTA}/fila/${enc(filaId)}`, enviar("PUT", { datos, revision }),
    cabecerasDeMiembro(ROLES_EDITORES)), "No se guardó la fila.");
}

export async function leerPlan(roadmapId: string): Promise<FilaPlan[]> {
  return json(await fetchAutenticado(`${RUTA}/plan/${enc(roadmapId)}`, { cache: "no-store" }, cabecerasDeMiembro(ROLES_EDITORES)),
    "No se pudo leer el plan.");
}

/**
 * Parte texto pegado de una hoja de cálculo (tabulado, una fila por línea). La primera columna es el
 * código; las demás siguen el orden de `columnas`. Una línea con encabezado «codigo» se ignora.
 */
export function partirPegado(texto: string, columnas: ColumnaCaptura[]): FilaEntrada[] {
  return texto.split(/\r?\n/).filter((l) => l.trim() !== "")
    .map((linea) => linea.split("\t").map((c) => c.trim()))
    .filter((celdas) => celdas[0].toLowerCase() !== "codigo")
    .map(([codigo, ...resto]) => ({
      codigo,
      datos: Object.fromEntries(columnas.map((c, i) => [c.clave, resto[i] ?? ""]).filter(([, v]) => v !== "")),
    }));
}
