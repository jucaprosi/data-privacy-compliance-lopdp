/**
 * Módulo DLP (Data Loss Prevention) Pre-Inferencia - Doctrina 7 del PRD
 * Detección y enmascaramiento de datos personales ecuatorianos (PII) antes de inferencia en LLMs.
 */

// Regex para correos electrónicos
export const REGEX_EMAIL = /[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+/g;

// Regex para capturar nombres personales en contextos contractuales o laborales comunes
// Utiliza negative lookahead para detenerse antes de preposiciones como 'con', 'cuyo', 'para', etc.
export const REGEX_NOMBRE_CONTEXTUAL =
  /(?<=\b(?:contrato\s+de|empleado(?:a)?|trabajador(?:a)?|titular|señor(?:a)?|sr\.(?:a)?|don|doña)\s+)([A-ZÁÉÍÓÚÑa-záéíóúñ]+(?:\s+(?!con\b|cuyo\b|cuya\b|para\b|de\b|en\b|que\b|cédula\b|ci\b)[A-ZÁÉÍÓÚÑa-záéíóúñ]+)*)/i;

// Regex para cédulas precedidas explícitamente por términos identificadores
export const REGEX_CEDULA_EXPLICITA =
  /(?<=\b(?:cédula|ci|identificación|cc|id)\s*(?:no\.?|número|:)?\s*)(\b\d{10}\b)/gi;

// Regex para candidatos generales a cédula ecuatoriana (10 dígitos con código de provincia 01-24 o 30)
export const REGEX_CEDULA_CANDIDATE = /\b(?:0[1-9]|1\d|2[0-4]|30)\d{8}\b/g;

// Regex para teléfonos móviles y fijos de Ecuador (+593 o prefijos locales)
export const REGEX_PHONE =
  /(?:\+?593[\s.-]?|0)(?:9(?:[\s.-]?\d){8}|[2-7](?:[\s.-]?\d){7})(?!\d)/g;

/**
 * Valida si una cadena de 10 dígitos cumple con el algoritmo Módulo 10 de la cédula ecuatoriana.
 */
export function validarCedulaEcuatoriana(cedula: string): boolean {
  if (cedula.length !== 10 || !/^\d{10}$/.test(cedula)) {
    return false;
  }

  const provincia = parseInt(cedula.substring(0, 2), 10);
  if (!((provincia >= 1 && provincia <= 24) || provincia === 30)) {
    return false;
  }

  const tercerDigito = parseInt(cedula[2], 10);
  if (tercerDigito >= 6) {
    return false;
  }

  const coeficientes = [2, 1, 2, 1, 2, 1, 2, 1, 2];
  let suma = 0;

  for (let i = 0; i < 9; i++) {
    let valor = parseInt(cedula[i], 10) * coeficientes[i];
    if (valor >= 10) {
      valor -= 9;
    }
    suma += valor;
  }

  const digitoVerificador = (10 - (suma % 10)) % 10;
  return digitoVerificador === parseInt(cedula[9], 10);
}

export interface ResultadoDLP {
  textoOriginal: string;
  textoSanitizado: string;
  conteoPII: number;
  detalles: {
    cedulasDetectadas: string[];
    emailsDetectados: string[];
    telefonosDetectados: string[];
    nombresDetectados: string[];
  };
}

/**
 * Sanitiza un texto aplicando las reglas DLP antes de enviarlo al modelo de lenguaje.
 */
export function sanitizarTextoDLP(texto: string): ResultadoDLP {
  let textoLimpio = texto;
  let conteo = 0;

  const cedulas: string[] = [];
  const emails: string[] = [];
  const telefonos: string[] = [];
  const nombres: string[] = [];

  // 1. Enmascarar correos electrónicos
  textoLimpio = textoLimpio.replace(REGEX_EMAIL, (match) => {
    emails.push(match);
    conteo++;
    return "[CORREO_OCULTO]";
  });

  // 2. Enmascarar nombres propios en contextos contractuales o laborales (ej: "contrato de Juan" -> "contrato de [NOMBRE_OCULTO]")
  textoLimpio = textoLimpio.replace(REGEX_NOMBRE_CONTEXTUAL, (match) => {
    if (match.trim().length > 0) {
      nombres.push(match.trim());
      conteo++;
      return "[NOMBRE_OCULTO]";
    }
    return match;
  });

  // 3. Enmascarar cédulas precedidas explícitamente por términos de identificación
  textoLimpio = textoLimpio.replace(REGEX_CEDULA_EXPLICITA, (match) => {
    cedulas.push(match);
    conteo++;
    return "[CÉDULA_OCULTA]";
  });

  // 4. Enmascarar cédulas de 10 dígitos que cumplan la regla provincial ecuatoriana
  textoLimpio = textoLimpio.replace(REGEX_CEDULA_CANDIDATE, (match) => {
    // Si ya está enmascarada o precedida por corchetes, no tocar
    if (match.includes("[") || match.includes("]")) return match;
    cedulas.push(match);
    conteo++;
    return "[CÉDULA_OCULTA]";
  });

  // 5. Enmascarar números telefónicos restantes
  textoLimpio = textoLimpio.replace(REGEX_PHONE, (match) => {
    telefonos.push(match);
    conteo++;
    return "[TELÉFONO_OCULTO]";
  });

  return {
    textoOriginal: texto,
    textoSanitizado: textoLimpio,
    conteoPII: conteo,
    detalles: {
      cedulasDetectadas: cedulas,
      emailsDetectados: emails,
      telefonosDetectados: telefonos,
      nombresDetectados: nombres,
    },
  };
}
