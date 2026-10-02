/**
 * Perfil de operación de la organización.
 *
 * Complementa la poda por tamaño: el número de empleados no dice qué hace la
 * organización con los datos. Diez selectores Sí/No definen qué controles se
 * descartan (por no existir el hecho que presuponen) y cuáles se incorporan
 * aunque el tamaño no los pida (por exposición a datos sensibles o a gran escala).
 *
 * Fundamento normativo:
 *  - LOPDP Art. 4 y 25: datos sensibles y categorías especiales (salud, datos de
 *    niñas, niños y adolescentes, discapacidad, biometría, genéticos, etc.).
 *  - LOPDP Art. 42 y 48: EIPD y Delegado de Protección de Datos para categorías
 *    especiales a gran escala. El Art. 48 obliga a designar Delegado cuando el
 *    tratamiento lo hace el sector público, cuando la actividad exige un control
 *    permanente y sistematizado, o cuando se tratan categorías especiales a gran escala.
 *  - Reglamento Arts. 38 y 39: el tamaño por sí solo no decide el RAT; basta riesgo,
 *    tratamiento no ocasional o categorías especiales.
 *  - Resolución SPDP-SPD-2026-0005-R: Modelo Técnico de Gran Escala (más de 10.000
 *    titulares puntúa en la variable «titulares») y supuestos de calificación
 *    directa (salud, biometría, menores, geolocalización, perfilamiento
 *    automatizado, transferencias sistemáticas, videovigilancia en espacios públicos).
 */

export type RespuestaPerfil = "si" | "no" | null;

export type ClavePerfil =
  | "internet"
  | "publicidad"
  | "camaras"
  | "terceros"
  | "nube"
  | "exterior"
  | "sistemas"
  | "decisionesAutomaticas"
  | "datosDelicados"
  | "granCantidad"
  | "obligadaDpd";

export type PerfilOperacion = Record<ClavePerfil, RespuestaPerfil>;

export const PERFIL_VACIO: PerfilOperacion = {
  internet: null,
  publicidad: null,
  camaras: null,
  terceros: null,
  nube: null,
  exterior: null,
  sistemas: null,
  decisionesAutomaticas: null,
  datosDelicados: null,
  granCantidad: null,
  obligadaDpd: null,
};

export interface SelectorPerfil {
  clave: ClavePerfil;
  pregunta: string;
  ayuda: string;
  /** Qué hace una respuesta, en lenguaje claro, para el resumen de alcance. */
  efectoNo?: string;
  efectoSi?: string;
}

export const SELECTORES_PERFIL: readonly SelectorPerfil[] = [
  {
    clave: "internet",
    pregunta: "¿Recibe datos de personas por internet?",
    ayuda: "Incluye página web, formularios en línea, redes sociales, aplicación y tienda en línea.",
    efectoNo: "no recibe datos por internet",
  },
  {
    clave: "publicidad",
    pregunta:
      "¿Usa datos de personas para enviarles publicidad, promociones o encuestas, u otros fines que requieran su permiso?",
    ayuda: "Por ejemplo, correos de ofertas, mensajes de promociones o uso de fotos de clientes o empleados.",
    efectoNo: "no usa datos para publicidad ni para fines que requieran permiso",
  },
  {
    clave: "camaras",
    pregunta: "¿Tiene cámaras de seguridad?",
    ayuda: "En locales, oficinas, bodegas o plantas.",
    efectoNo: "no tiene cámaras de seguridad",
  },
  {
    clave: "terceros",
    pregunta: "¿Trabaja con terceros que ven, reciben o guardan datos de personas?",
    ayuda:
      "Por ejemplo: contador, servicio de nómina, mensajería, soporte técnico o servicios en internet.",
    efectoNo: "no trabaja con terceros que accedan a datos de personas",
  },
  {
    clave: "nube",
    pregunta: "¿Guarda información o usa programas contratados por internet (la «nube»)?",
    ayuda: "Por ejemplo: Google Drive, OneDrive o sistemas contratados en línea.",
    efectoNo: "no usa servicios en la nube",
  },
  {
    clave: "exterior",
    pregunta: "¿Envía o guarda datos de personas fuera del país?",
    ayuda:
      "Incluye servicios cuyos servidores están en el exterior. Consulte al área de sistemas si no está seguro.",
    efectoNo: "no envía ni guarda datos fuera del país",
  },
  {
    clave: "sistemas",
    pregunta:
      "¿Desarrolla o prueba sistemas propios, o hace estadísticas o análisis con datos de personas?",
    ayuda:
      "Por ejemplo, programas hechos a la medida, informes de ventas o análisis de clientes o empleados.",
    efectoNo: "no desarrolla sistemas ni hace análisis con datos de personas",
  },
  {
    clave: "decisionesAutomaticas",
    pregunta: "¿Toma decisiones sobre personas con programas automáticos?",
    ayuda:
      "Por ejemplo: aprobar créditos, calificar clientes o seleccionar personal sin revisión humana.",
    efectoNo: "no toma decisiones automáticas sobre personas",
  },
  {
    clave: "datosDelicados",
    pregunta: "¿Maneja datos sensibles?",
    ayuda:
      "Salud, discapacidad, huellas digitales o biometría, datos genéticos, religión, origen étnico, orientación sexual, antecedentes penales, condición migratoria o datos de niñas, niños y adolescentes.",
    efectoSi: "maneja datos sensibles",
  },
  {
    clave: "granCantidad",
    pregunta: "¿Maneja datos de una gran cantidad de personas?",
    ayuda:
      "Responda Sí si en los últimos 12 meses trató datos de más de 10.000 personas (clientes, socios, usuarios, empleados), o si ubica o sigue a personas por geolocalización.",
    efectoSi: "maneja datos de una gran cantidad de personas",
  },
  {
    clave: "obligadaDpd",
    pregunta: "¿Está obligada a tener un Delegado de Protección de Datos (DPO)?",
    ayuda:
      "Responda Sí si es una entidad pública, si vigila de forma constante a las personas (por ejemplo, seguimiento continuo de clientes) o si maneja datos sensibles de muchas personas. Si no está seguro, consulte con el área legal.",
    efectoNo: "no está obligada a designar un Delegado de Protección de Datos",
    efectoSi: "está obligada a designar un Delegado de Protección de Datos",
  },
] as const;

/** Preguntas que se descartan cuando el selector se responde «No». */
const DESCARTA_SI_NO: Partial<Record<ClavePerfil, readonly number[]>> = {
  internet: [18, 35],
  publicidad: [21, 22, 36],
  camaras: [38],
  terceros: [41, 42, 43, 44, 47, 48],
  nube: [45],
  exterior: [46],
  sistemas: [40, 55],
  decisionesAutomaticas: [72],
  obligadaDpd: [4],
};

/** Controles estructurales: nunca se descartan (Reglamento Arts. 38 y 39). */
const ESTRUCTURALES: readonly number[] = [9, 10, 13, 28];

/** Paquete reforzado por datos sensibles (LOPDP Arts. 25, 26, 42 y 48). */
const PAQUETE_DELICADOS: readonly number[] = [3, 4, 40, 52, 59, 61, 63, 64, 65, 71];
/** Se agrega al paquete anterior solo si la organización trabaja con terceros. */
const PAQUETE_DELICADOS_CON_TERCEROS: readonly number[] = [42, 47, 48];
/** Paquete reforzado por gran escala (Resolución SPDP-SPD-2026-0005-R). */
const PAQUETE_GRAN_ESCALA: readonly number[] = [3, 4, 5, 6, 8, 16, 34, 65, 76];
/** Controles cuya criticidad sube al máximo con datos sensibles. */
const CRITICIDAD_MAXIMA_POR_DELICADOS: readonly number[] = [49, 50, 51, 53, 57, 58];

export interface AjustePerfil {
  /** Preguntas que el perfil descarta, con el selector que lo motivó. */
  descartadas: Map<number, ClavePerfil>;
  /** Preguntas que el perfil incorpora aunque el tamaño no las pida. */
  incluidas: Set<number>;
  /** Preguntas cuya criticidad sube al máximo. */
  criticidadMaxima: Set<number>;
}

export function perfilCompleto(perfil: PerfilOperacion | undefined): boolean {
  if (!perfil) return false;
  return (Object.keys(PERFIL_VACIO) as ClavePerfil[]).every((c) => perfil[c] === "si" || perfil[c] === "no");
}

export function respuestasPendientes(perfil: PerfilOperacion | undefined): number {
  const p = perfil ?? PERFIL_VACIO;
  return (Object.keys(PERFIL_VACIO) as ClavePerfil[]).filter((c) => p[c] === null || p[c] === undefined).length;
}

/**
 * Calcula el ajuste del perfil. Una respuesta sin contestar no descarta ni
 * incorpora nada: ante la duda se pregunta. Lo que se incorpora gana sobre lo
 * que se descarta, y los controles estructurales nunca se descartan.
 */
export function ajustePorPerfil(perfil: PerfilOperacion | undefined): AjustePerfil {
  const p = perfil ?? PERFIL_VACIO;
  const descartadas = new Map<number, ClavePerfil>();
  const incluidas = new Set<number>();
  const criticidadMaxima = new Set<number>();

  (Object.keys(DESCARTA_SI_NO) as ClavePerfil[]).forEach((clave) => {
    if (p[clave] !== "no") return;
    (DESCARTA_SI_NO[clave] ?? []).forEach((id) => descartadas.set(id, clave));
  });

  // La evaluación de impacto realizada solo se descarta si no hay ningún factor
  // de alto riesgo: datos sensibles, gran escala o decisiones automáticas.
  if (p.datosDelicados === "no" && p.granCantidad === "no" && p.decisionesAutomaticas === "no") {
    descartadas.set(67, "datosDelicados");
  }

  if (p.datosDelicados === "si") {
    PAQUETE_DELICADOS.forEach((id) => incluidas.add(id));
    if (p.terceros === "si") PAQUETE_DELICADOS_CON_TERCEROS.forEach((id) => incluidas.add(id));
    CRITICIDAD_MAXIMA_POR_DELICADOS.forEach((id) => criticidadMaxima.add(id));
  }
  if (p.granCantidad === "si") {
    PAQUETE_GRAN_ESCALA.forEach((id) => incluidas.add(id));
  }
  // Obligada a designar Delegado: se evalúa la designación (3) y su independencia (4).
  if (p.obligadaDpd === "si") {
    incluidas.add(3);
    incluidas.add(4);
  }

  ESTRUCTURALES.forEach((id) => descartadas.delete(id));
  incluidas.forEach((id) => descartadas.delete(id));

  return { descartadas, incluidas, criticidadMaxima };
}

/** Texto breve del motivo de descarte, para el resumen de alcance. */
export function motivoDescarte(clave: ClavePerfil): string {
  if (clave === "datosDelicados") {
    return "no maneja datos sensibles, ni gran cantidad de datos, ni decisiones automáticas";
  }
  return SELECTORES_PERFIL.find((s) => s.clave === clave)?.efectoNo ?? "no aplica según su perfil";
}

/**
 * Aviso no bloqueante cuando la respuesta sobre el Delegado parece contradecir
 * otras respuestas de la ficha (LOPDP Art. 48: sector público, control permanente
 * y sistematizado, o categorías especiales a gran escala).
 */
export function avisoCoherenciaDpd(perfil: PerfilOperacion | undefined, sector: string | undefined): string | null {
  if (!perfil || perfil.obligadaDpd !== "no") return null;
  if (sector === "Sector Público") {
    return "El tratamiento que realiza el sector público obliga a designar un Delegado de Protección de Datos (LOPDP Art. 48). Revise su respuesta.";
  }
  if (perfil.datosDelicados === "si" && perfil.granCantidad === "si") {
    return "Tratar datos sensibles de una gran cantidad de personas obliga a designar un Delegado de Protección de Datos (LOPDP Art. 48). Revise su respuesta.";
  }
  return null;
}
