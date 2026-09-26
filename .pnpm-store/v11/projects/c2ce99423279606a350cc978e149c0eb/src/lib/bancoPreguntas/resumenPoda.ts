import {
  BANCO_PREGUNTAS,
  TAMANOS_EMPRESA,
  aplicaATamano,
  type PreguntaAssessment,
  type TamanoDescriptor,
  type TamanoEmpresa,
} from "@/lib/bancoPreguntas";
import {
  CONTROLES_ESTRUCTURALES,
  DIMENSIONES_SGPDP,
  DIMENSION_POR_ID,
  type DimensionId,
} from "@/lib/dimensionesSGPDP";

export interface DesglosePodaDimension {
  id: DimensionId;
  nombre: string;
  aplicables: number;
  total: number;
}

export interface ControlEstructuralPoda {
  id: number;
  control: string;
  dimensionId: DimensionId;
  dimensionNombre: string;
  aplica: boolean;
}

export interface ControlOmitido {
  id: number;
  control: string;
  dimensionId: DimensionId;
  dimensionNombre: string;
  tamanoMinimo: TamanoDescriptor;
}

export interface ResumenPoda {
  tamano: TamanoDescriptor;
  totalBanco: number;
  aplicables: number;
  omitidos: number;
  porDimension: DesglosePodaDimension[];
  estructurales: ControlEstructuralPoda[];
  estructuralesSiempreAplican: boolean;
  controlesOmitidos: ControlOmitido[];
}

function descriptorDe(tamano: TamanoEmpresa): TamanoDescriptor {
  const descriptor = TAMANOS_EMPRESA.find((t) => t.id === tamano);
  if (!descriptor) throw new Error(`Talla desconocida: ${tamano}`);
  return descriptor;
}

function esEstructural(pregunta: PreguntaAssessment): boolean {
  return (
    pregunta.esEstructural === true ||
    CONTROLES_ESTRUCTURALES.some((c) => c.preguntaId === pregunta.id)
  );
}

export function resumenPoda(
  tamano: TamanoEmpresa,
  banco: readonly PreguntaAssessment[] = BANCO_PREGUNTAS
): ResumenPoda {
  const aplicables = banco.filter((p) => aplicaATamano(p, tamano));
  const omitidas = banco.filter((p) => !aplicaATamano(p, tamano));

  const porDimension = DIMENSIONES_SGPDP.map((d) => {
    const deLaDimension = banco.filter((p) => p.dimensionId === d.id);
    return {
      id: d.id,
      nombre: d.nombre,
      aplicables: deLaDimension.filter((p) => aplicaATamano(p, tamano)).length,
      total: deLaDimension.length,
    };
  });

  const estructurales = banco.filter(esEstructural).map((p) => ({
    id: p.id,
    control: p.control,
    dimensionId: p.dimensionId,
    dimensionNombre: DIMENSION_POR_ID[p.dimensionId].nombre,
    aplica: aplicaATamano(p, tamano),
  }));

  const controlesOmitidos = omitidas.map((p) => ({
    id: p.id,
    control: p.control,
    dimensionId: p.dimensionId,
    dimensionNombre: DIMENSION_POR_ID[p.dimensionId].nombre,
    tamanoMinimo: descriptorDe(p.tamanoMinimo),
  }));

  return {
    tamano: descriptorDe(tamano),
    totalBanco: banco.length,
    aplicables: aplicables.length,
    omitidos: omitidas.length,
    porDimension,
    estructurales,
    estructuralesSiempreAplican: banco
      .filter(esEstructural)
      .every((p) => p.tamanoMinimo === "micro"),
    controlesOmitidos,
  };
}
