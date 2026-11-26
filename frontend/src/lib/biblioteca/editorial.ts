// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
// ¤adpa
// ¤¤developer-architect
import { httpBiblioteca } from "./http";

export type Capacidad = "editor" | "revisor_tecnico" | "revisor_juridico" | "publicador";
export interface Ficha {
  nombre: string; objetivo: string; fuentes: string; fecha_revision: string;
  instrucciones: string; dependencias: string; restricciones: string;
}
/** BIB-410: redacción y aprobación de una versión publicada; nula sin aprobación registrada. */
export interface Leyenda { redaccion: "ia" | "persona"; aprobada_por: string; aprobada_en: string; texto: string }
export interface CambioIa { seccion: string; antes: string; despues: string; cita: string }
export interface Version {
  id: string; codigo: string; version: string; formato: "DOCX" | "XLSX" | "MD";
  ficha: Ficha | null; responsable_id: string; autores: string[];
  estado: "en_revision" | "publicada" | "retirada" | "sustituida";
  generacion: number; sha256: string | null; nombre_archivo: string | null;
  sustituye_id: string | null; creada_en: string;
  // BIB-406: origen de la versión (persona o IA). Opcionales: las versiones anteriores no los traen.
  redactada_por?: "persona" | "ia"; modelo_ia?: string | null; origen_ia?: "resolucion" | "peticion" | null;
  id_resolucion?: string | null; motivo_ia?: string | null; cambios_ia?: CambioIa[] | null;
  nota_descarte?: string | null; descartada_por?: string | null; descartada_en?: string | null;
  solicitante_nombre?: string | null;
  leyenda?: Leyenda | null;
}
export interface Revision {
  version_id: string; generacion: number; tipo: "tecnica" | "juridica";
  aprobado: boolean; revisor_id: string; comentario: string; creada_en: string;
}
export interface CatalogoEditorial {
  actor_id: string; capacidades: Capacidad[]; versiones: Version[]; revisiones: Revision[];
}
export interface EventoEditorial {
  actor_id: string; alcance: string; accion: string; generacion: number; motivo: string | null; creada_en: string;
}
const base = "/biblioteca/editorial";
export const listarEditorial = () => httpBiblioteca<CatalogoEditorial>(base);
export const crearVersion = (codigo: string, version: string, formato: string, sustituye_id: string | null) =>
  httpBiblioteca<Version>(`${base}/versiones`, { method: "POST", body: JSON.stringify({ codigo, version, formato, sustituye_id }) });
export const guardarFicha = (v: Version, ficha: Ficha) => httpBiblioteca<Version>(`${base}/versiones/${v.id}/ficha`, {
  method: "PUT", body: JSON.stringify({ ficha, generacion: v.generacion }),
});
export const dictaminar = (v: Version, tipo: string, aprobado: boolean, comentario: string) =>
  httpBiblioteca<Version>(`${base}/versiones/${v.id}/revisiones`, {
    method: "POST", body: JSON.stringify({ tipo, aprobado, comentario, generacion: v.generacion }),
  });
export const cambiarEstado = (v: Version, accion: "publicar" | "retirar", motivo: string) =>
  httpBiblioteca<Version>(`${base}/versiones/${v.id}/${accion}`, {
    method: "POST", body: JSON.stringify({ motivo, generacion: v.generacion }),
  });
export const leerHistorial = (v: Version) => httpBiblioteca<EventoEditorial[]>(`${base}/versiones/${v.id}/historial`);
export async function cargarArchivo(v: Version, archivo: File): Promise<Version> {
  if (!archivo.size || archivo.size > 10 * 1024 * 1024) throw new Error("El archivo debe contener datos y no superar 10 MB.");
  const contenido = await new Promise<string>((resolve, reject) => {
    const lector = new FileReader();
    lector.onload = () => resolve(String(lector.result).split(",")[1]);
    lector.onerror = () => reject(new Error("No se pudo leer el archivo."));
    lector.readAsDataURL(archivo);
  });
  return httpBiblioteca<Version>(`${base}/versiones/${v.id}/archivo`, {
    method: "PUT", body: JSON.stringify({ nombre: archivo.name, contenido_base64: contenido, generacion: v.generacion }),
  });
}

// === BIB-408 · versiones Markdown, comparación y propuestas de la IA ===
export interface CitaCambio {
  clave: string; norma: string | null; articulo: string | null; url: string | null;
  verificada: boolean; fecha_vigencia: string | null;
}
export interface CambioSeccion { antes: string; despues: string; cita: CitaCambio | null }
export interface SeccionComparada { titulo: string; cambiada: boolean; cambios: CambioSeccion[]; texto?: string | null }
export interface Comparacion { primera_version: boolean; secciones: SeccionComparada[] }
export interface ResultadoPropuesta {
  resultado: "creada" | "sin_cambios" | "propuesta_en_revision"; versiones: Version[]; omitidas: string[];
}

export const compararVersion = (v: Version) => httpBiblioteca<Comparacion>(`${base}/versiones/${v.id}/comparacion`);
export const proponerCambio = (codigo: string, motivo: string) =>
  httpBiblioteca<ResultadoPropuesta>(`${base}/propuestas`, { method: "POST", body: JSON.stringify({ codigo, motivo }) });
export const descartarVersion = (v: Version, nota: string) =>
  httpBiblioteca<Version>(`${base}/versiones/${v.id}/descartar`, { method: "POST", body: JSON.stringify({ nota, generacion: v.generacion }) });
/** Devolver con observaciones es una revisión técnica no aprobada (BIB-406 R5). */
export const devolverVersion = (v: Version, observaciones: string) => dictaminar(v, "tecnica", false, observaciones);
/** R1: «Aprobar y publicar» registra la revisión técnica aprobada y después la publicación, con la misma persona. */
export async function aprobarYPublicar(v: Version, motivo: string): Promise<Version> {
  const revisada = await dictaminar(v, "tecnica", true, motivo);
  return cambiarEstado({ ...v, generacion: revisada.generacion ?? v.generacion }, "publicar", motivo);
}

export const TEXTO_ESTADO = {
  en_revision: "En revisión", devuelta: "Devuelta con observaciones", publicada: "Publicada", descartada: "Descartada",
  sustituida: "Sustituida", retirada: "Retirada",
} as const;
export type EstadoVisible = keyof typeof TEXTO_ESTADO;
export const FORMATO_TEXTO = { MD: "Markdown", DOCX: "DOCX", XLSX: "XLSX" } as const;

/** El estado que ve la persona: «devuelta» y «descartada» no son estados de la base, salen de la revisión y de la nota. */
export function estadoVisible(v: Version, revisiones: Revision[]): EstadoVisible {
  if (v.estado === "retirada" && v.nota_descarte) return "descartada";
  if (v.estado === "en_revision") {
    const tecnicas = revisiones.filter(r => r.version_id === v.id && r.generacion === v.generacion && r.tipo === "tecnica");
    if (tecnicas.length && !tecnicas[tecnicas.length - 1].aprobado) return "devuelta";
  }
  return v.estado;
}
export const esDeLaIa = (v: Version) => v.redactada_por === "ia";
export const autoria = (v: Version) => (esDeLaIa(v) ? "Redactada por la IA" : v.solicitante_nombre ?? v.responsable_id);

const MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"];
export const fechaLarga = (iso: string) => {
  const d = new Date(iso.length === 10 ? `${iso}T12:00:00` : iso);
  return `${d.getDate()} de ${MESES[d.getMonth()]} de ${d.getFullYear()}`;
};
/** Parte el texto de la leyenda alrededor de su fecha larga, para envolverla en `<time datetime>`. */
export function partirLeyenda(l: Leyenda): { antes: string; fecha: string; iso: string; despues: string } | null {
  const m = /(\d{1,2}) de ([a-záéíóú]+) de (\d{4})/.exec(l.texto);
  const mes = m ? MESES.indexOf(m[2]) : -1;
  if (!m || mes < 0) return null;
  const iso = `${m[3]}-${String(mes + 1).padStart(2, "0")}-${m[1].padStart(2, "0")}`;
  return { antes: l.texto.slice(0, m.index), fecha: m[0], iso, despues: l.texto.slice(m.index + m[0].length) };
}

export const MOTIVOS = {
  revisar: "No puedes revisar una versión de la que tienes la autoría.",
  publicar: "No puedes publicar una versión de la que tienes la autoría.",
  editor: "Necesitas el permiso de edición.", tecnico: "Necesitas el permiso de revisión técnica.",
  publicador: "Necesitas el permiso de publicación.",
} as const;
export const CITAS_SIN_VERIFICAR = "Hay citas sin verificar.";
export const CONFLICTO_PROPUESTA =
  "Ya hay una propuesta de la IA en revisión para esta plantilla. Apruébala, devuélvela o descártala antes de pedir otra.";

/** R4: «Publicación pendiente: falta {lista}.», solo con lo que falta. `null` si no falta nada. */
export function avisoPendiente(faltan: string[]): string | null {
  if (!faltan.length) return null;
  const lista = faltan.length === 1 ? faltan[0] : `${faltan.slice(0, -1).join(", ")} y ${faltan[faltan.length - 1]}`;
  return `Publicación pendiente: falta ${lista}.`;
}
