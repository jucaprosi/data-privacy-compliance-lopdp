/**
 * Resumen del tablero de la organización (FE-24) a partir del último resultado sellado del
 * diagnóstico (DIAG-03). Doctrina 4 e INV_LOPDP_MULTIDIMENSIONAL_METRICS: cuatro dimensiones
 * por separado y el número de brechas críticas; este módulo no calcula ni devuelve ningún
 * porcentaje, promedio o puntaje global. No recalcula las dimensiones: solo las presenta.
 */
import type { ResultadoSellado } from "@/lib/diagnostico/clienteResultados";
import { AVISO_ESCALA_ANTERIOR } from "@/lib/diagnostico/indicadores";

export type Semaforo = "success" | "warning" | "danger";
export type IdDimension = "madurez" | "conformidad" | "evidencia" | "riesgo";

export interface TarjetaDimension {
  id: IdDimension;
  titulo: string;
  /** Texto cualitativo o conteo; nunca un porcentaje ni una cifra única. */
  valor: string;
  detalle: string;
  semaforo: Semaforo;
}

export interface ResumenTablero {
  dimensiones: TarjetaDimension[];
  brechasCriticasAbiertas: number;
  selladoEn: string;
  secuencia: number;
}

export function resumirResultado(resultado: ResultadoSellado): ResumenTablero {
  const ind = resultado.indicadores;
  const total = resultado.respuestas.length;
  const conDocumento = resultado.respuestas.filter((r) => r.con_documento).length;

  const evaluadas = (ind.por_dimension ?? []).filter((d) => d.nivel >= 1);
  const masBaja = evaluadas.reduce<(typeof evaluadas)[number] | null>(
    (menor, d) => (menor === null || d.nivel < menor.nivel ? d : menor), null);
  const madurez: TarjetaDimension = ind.escala === "anterior"
    ? { id: "madurez", titulo: "Madurez", valor: "Escala anterior", detalle: AVISO_ESCALA_ANTERIOR, semaforo: "warning" }
    : masBaja === null
      ? { id: "madurez", titulo: "Madurez", valor: "Sin evaluación suficiente",
          detalle: "Ninguna dimensión tiene cobertura para asignar un nivel.", semaforo: "danger" }
      : { id: "madurez", titulo: "Madurez", valor: `Nivel ${masBaja.nivel} de 5 en ${masBaja.nombre}`,
          detalle: evaluadas.map((d) => `${d.nombre}: nivel ${d.nivel}`).join(" · "),
          semaforo: masBaja.nivel >= 4 ? "success" : masBaja.nivel === 3 ? "warning" : "danger" };

  const conformidad: TarjetaDimension = {
    id: "conformidad",
    titulo: "Conformidad",
    valor: ind.cumplimiento ? "Conforme" : "No conforme",
    detalle: `${ind.preguntas_evaluadas} de ${ind.preguntas_aplicables} controles aplicables evaluados.`,
    semaforo: ind.cumplimiento ? "success" : ind.brechas_criticas > 0 ? "danger" : "warning",
  };

  const evidencia: TarjetaDimension = {
    id: "evidencia",
    titulo: "Evidencia",
    valor: `${conDocumento} de ${total} con documento`,
    detalle: "Respuestas selladas respaldadas por un documento vinculado.",
    semaforo: total === 0 || conDocumento === 0 ? "danger" : conDocumento < total ? "warning" : "success",
  };

  const altas = ind.brechas_altas;
  const riesgo: TarjetaDimension = {
    id: "riesgo",
    titulo: "Riesgo",
    valor: altas === undefined ? `${ind.brechas_criticas} brechas críticas` : `${ind.brechas_criticas} críticas y ${altas} altas`,
    detalle: "Brechas abiertas al sellar; el riesgo no se resume en una cifra única.",
    semaforo: ind.brechas_criticas > 0 ? "danger" : altas ? "warning" : "success",
  };

  return {
    dimensiones: [madurez, conformidad, evidencia, riesgo],
    brechasCriticasAbiertas: ind.brechas_criticas,
    selladoEn: resultado.sellado_en,
    secuencia: resultado.secuencia,
  };
}
