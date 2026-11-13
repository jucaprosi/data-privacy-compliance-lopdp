import { cabecerasDePlataforma } from "@/lib/auth/cabeceras";
import { fetchAutenticado } from "@/lib/auth/fetchAutenticado";

const BASE = "/api/v1/plataforma/paquetes";

export type EstadoPaquete = "borrador" | "publicado" | "retirado";
export type UnidadPlazo = "habiles" | "calendario";
export type TerminoLegal = "plazo" | "termino";

export interface Paquete {
  id: string;
  codigo: string;
  nombre: string;
  version: string;
  estado: EstadoPaquete;
  creado_por: string;
  creado_en: string;
  publicado_por: string | null;
  publicado_en: string | null;
  retirado_en: string | null;
  sin_verificar: number;
}

export interface Parametro {
  clave: string;
  valor: string;
  unidad: UnidadPlazo | null;
  termino_legal: TerminoLegal | null;
  articulo: string;
  fuente_url: string;
  verificado: boolean;
  verificado_por: string | null;
  verificado_por_nombre: string | null;
  verificado_en: string | null;
  actualizado_por: string;
  actualizado_en: string;
}

export interface ParametroEntrada {
  valor: string;
  unidad: UnidadPlazo | null;
  termino_legal: TerminoLegal | null;
  articulo: string;
  fuente_url: string;
  verificado: boolean;
}

export interface Impacto {
  plantillas: string[];
  plantillas_pendiente: boolean;
  organizaciones: number | null;
  organizaciones_pendiente: boolean;
}

export interface DetallePaquete {
  paquete: Paquete;
  parametros: Parametro[];
}

/** Mensajes fijos por código: nunca se muestra el texto del servidor. */
const MENSAJES: Record<string, string> = {
  NO_ES_OPERADOR: "Esta sección está reservada para operadores de la plataforma.",
  PARAMETRO_NO_VERIFICADO: "Hay parámetros sin verificar. Verifícalos antes de publicar.",
  PAQUETE_NO_BORRADOR: "Esta versión ya no es un borrador: crea una versión nueva para cambiarla.",
  UNIDAD_REQUERIDA: "Todo plazo necesita su unidad: días hábiles o días calendario.",
  PAQUETE_NO_ENCONTRADO: "No se encontró el paquete normativo.",
  VERSION_DUPLICADA: "Esa versión del paquete ya existe.",
  VERSION_REQUERIDA: "Indica la versión.",
};

const MENSAJE_GENERICO = "La operación no pudo completarse. Inténtalo de nuevo.";

export class ErrorPaquetes extends Error {
  constructor(
    readonly status: number,
    readonly codigo?: string,
  ) {
    super((codigo && MENSAJES[codigo]) || (status === 403 ? MENSAJES.NO_ES_OPERADOR : MENSAJE_GENERICO));
    this.name = "ErrorPaquetes";
  }
}

async function solicitar<T>(ruta: string, init: RequestInit = {}): Promise<T> {
  const respuesta = await fetchAutenticado(
    `${BASE}${ruta}`,
    { ...init, headers: { "Content-Type": "application/json", ...(init.headers ?? {}) } },
    cabecerasDePlataforma(),
  );
  if (!respuesta.ok) {
    let codigo: string | undefined;
    try {
      codigo = ((await respuesta.json()) as { code?: string }).code;
    } catch {
      // Sin JSON: queda el mensaje genérico por estado.
    }
    throw new ErrorPaquetes(respuesta.status, codigo);
  }
  return (await respuesta.json()) as T;
}

export const paquetesApi = {
  listar: async () => (await solicitar<{ paquetes: Paquete[] }>("")).paquetes,
  detalle: (id: string) => solicitar<DetallePaquete>(`/${encodeURIComponent(id)}`),
  fijarParametro: (id: string, clave: string, datos: ParametroEntrada) =>
    solicitar<Parametro>(`/${encodeURIComponent(id)}/parametros/${encodeURIComponent(clave)}`, {
      method: "PUT",
      body: JSON.stringify(datos),
    }),
  crearVersion: (codigo: string, version: string) =>
    solicitar<Paquete>(`/${encodeURIComponent(codigo)}/versiones`, {
      method: "POST",
      body: JSON.stringify({ version }),
    }),
  publicar: (id: string) =>
    solicitar<{ paquete: Paquete; impacto: Impacto }>(`/${encodeURIComponent(id)}/publicar`, { method: "POST" }),
};

export const ETIQUETA_ESTADO: Record<EstadoPaquete, string> = {
  borrador: "Borrador",
  publicado: "Publicado",
  retirado: "Retirado",
};

export const ETIQUETA_UNIDAD: Record<UnidadPlazo, string> = {
  habiles: "Días hábiles",
  calendario: "Días calendario",
};

export const ETIQUETA_TERMINO: Record<TerminoLegal, string> = {
  plazo: "Plazo",
  termino: "Término",
};

/** Nombre legible de cada parámetro; una clave desconocida se muestra sin guiones bajos. */
const NOMBRES: Record<string, string> = {
  plazo_derechos_dias: "Plazo para atender los derechos",
  plazo_vulneracion_encargado_dias: "Aviso del encargado al responsable",
  plazo_vulneracion_autoridad_dias: "Notificación a la Autoridad",
  plazo_vulneracion_titulares_dias: "Comunicación a los titulares",
  autoridad: "Autoridad de control",
  canal_notificacion: "Canal de notificación",
};

export const nombreParametro = (clave: string) => NOMBRES[clave] ?? clave.replace(/_/g, " ");

export const esPlazo = (clave: string) => clave.startsWith("plazo_");

export function formatearFecha(iso: string | null): string {
  if (!iso) return "";
  return new Intl.DateTimeFormat("es-EC", { dateStyle: "medium" }).format(new Date(iso));
}
