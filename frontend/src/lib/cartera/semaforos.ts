/**
 * Semáforos por dimensión de una fila de la cartera (ORG-15). ¤cartera ¤tablero-dimensiones
 *
 * Misma doctrina que el tablero de la organización (FE-24, `lib/tableros/resumen.ts`): cuatro dimensiones
 * por separado y el número de brechas; este módulo no calcula ni devuelve un porcentaje, promedio o
 * puntaje global. Solo presenta lo que el servidor ya calculó.
 */
import { DIMENSIONES_SGPDP } from "@/lib/dimensionesSGPDP";
import type { TarjetaDimension } from "@/lib/tableros/resumen";
import type { DiagnosticoCartera, FilaCartera } from "./cliente";


/** Umbrales cualitativos del respaldo documental; la cifra no se muestra. */
const RESPALDO_ALTO = 75;
const RESPALDO_PARCIAL = 40;

function madurez(d: DiagnosticoCartera): TarjetaDimension {
  if (d.escala === "anterior") {
    return {
      id: "madurez", titulo: "Madurez", valor: "Escala anterior",
      detalle: "Este diagnóstico se hizo con una escala anterior; repítelo para ver la madurez actual.", semaforo: "warning",
    };
  }
  const evaluadas = d.niveles_por_dimension.filter((n) => n.nivel >= 1);
  if (evaluadas.length === 0) {
    return {
      id: "madurez", titulo: "Madurez", valor: "Sin evaluación suficiente",
      detalle: "Ninguna dimensión tiene respuestas para asignar un nivel.", semaforo: "danger",
    };
  }
  const menor = evaluadas.reduce((m, n) => (n.nivel < m.nivel ? n : m));
  const nombre = DIMENSIONES_SGPDP.find((x) => x.id === menor.dimension)?.nombre ?? menor.dimension;
  return {
    id: "madurez", titulo: "Madurez", valor: `Nivel más bajo: ${menor.nivel} de 5 · ${nombre}`,
    detalle: "Es el nivel de la dimensión que está más atrás.",
    semaforo: menor.nivel >= 4 ? "success" : menor.nivel === 3 ? "warning" : "danger",
  };
}

function textoRiesgo(criticas: number, altas: number): string {
  if (criticas === 0 && altas === 0) return "Sin riesgos críticos ni altos";
  const c = criticas === 1 ? "1 riesgo crítico" : `${criticas} riesgos críticos`;
  const a = altas === 1 ? "1 alto" : `${altas} altos`;
  return `${c} y ${a}`;
}

/** Cuatro tarjetas en el mismo orden que el tablero de la organización; `null` si no hay diagnóstico sellado. */
export function tarjetasDeFila(fila: FilaCartera): TarjetaDimension[] | null {
  const d = fila.diagnostico;
  if (!d) return null;
  const respaldo =
    d.respaldo_documental >= RESPALDO_ALTO ? "success" : d.respaldo_documental >= RESPALDO_PARCIAL ? "warning" : "danger";
  return [
    madurez(d),
    {
      id: "conformidad", titulo: "Conformidad", valor: d.brechas_criticas > 0 ? "Con incumplimientos críticos abiertos" : "Sin incumplimientos críticos abiertos",
      detalle: d.brechas_criticas > 0 ? "Hay controles críticos sin cumplir." : "No hay controles críticos sin cumplir.",
      semaforo: d.cumplimiento ? "success" : d.brechas_criticas > 0 ? "danger" : "warning",
    },
    {
      id: "evidencia", titulo: "Evidencia",
      valor: `Respaldo con documentos: ${respaldo === "success" ? "alto" : respaldo === "warning" ? "parcial" : "bajo"}`,
      detalle: "Según los documentos registrados.", semaforo: respaldo,
    },
    {
      id: "riesgo", titulo: "Riesgo", valor: textoRiesgo(d.brechas_criticas, d.brechas_altas),
      detalle: "Brechas abiertas al sellar; el riesgo no se resume en una cifra única.",
      semaforo: d.brechas_criticas > 0 ? "danger" : d.brechas_altas > 0 ? "warning" : "success",
    },
  ];
}
