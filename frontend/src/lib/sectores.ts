/**
 * Sectores de la organización para la ficha organizacional.
 *
 * Cada sector es una opción independiente: no se agrupan actividades distintas
 * (por ejemplo, educación y sector público) en una misma opción. El valor se
 * guarda como texto, por lo que las fichas y snapshots anteriores con los
 * sectores agrupados siguen mostrándose sin migración.
 */
export const SECTORES: readonly string[] = [
  "Agroindustria y Agricultura",
  "Alimentos y Bebidas",
  "Comercio Electrónico",
  "Comercio Minorista (Retail)",
  "Construcción e Inmobiliario",
  "Educación",
  "Energía, Petróleo y Minería",
  "Farmacéutica y Laboratorios",
  "Fintech",
  "Logística y Transporte",
  "Manufactura e Industria",
  "Marketing y Publicidad",
  "Medios de Comunicación y Entretenimiento",
  "Organizaciones sin Fines de Lucro",
  "Salud (Hospitales, Clínicas y Consultorios)",
  "Sector Público",
  "Seguros",
  "Servicios Financieros, Banca y Cooperativas",
  "Servicios Profesionales y Consultoría",
  "Tecnología y Software",
  "Telecomunicaciones",
  "Turismo, Hotelería y Restauración",
  "Otro",
] as const;

export const SECTOR_POR_DEFECTO = "Telecomunicaciones";
