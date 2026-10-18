/**
 * Mapeo del tamaño de la organización (FE-08): una sola fuente para la ficha, el banco de preguntas y
 * el panel de administración. Pruebas sin navegador sobre el código real.
 */
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { expect, test } from "@playwright/test";

import { TAMANOS } from "../../src/components/modules/roadmap/admin/configuracion";
import {
  ORDEN_TAMANO,
  TAMANOS_EMPRESA,
  etiquetaFichaDeTamano,
  etiquetaTamanoPorPersonas,
  normalizarTamano,
  rangoDeTamano,
} from "../../src/lib/bancoPreguntas/tipos";
import {
  CLAVES_DE_TAMANO,
  TAMANOS_ORGANIZACION,
  claveDeEtiqueta,
  esClaveDeTamano,
  etiquetaDeFicha,
  tamanoPorPersonas,
} from "../../src/lib/tamanoOrganizacion";

test.describe("Las claves son las del servidor", () => {
  test("coinciden, en el mismo orden, con features/organizacion/domain/tamanos.py", () => {
    const fuente = readFileSync(resolve(process.cwd(), "..", "features", "organizacion", "domain", "tamanos.py"), "utf-8");
    const delServidor = [...fuente.matchAll(/^\s+\w+\s*=\s*"(\w+)"\s*$/gm)].map((m) => m[1]);
    expect(delServidor.length, "se esperaban las claves de la enumeración").toBeGreaterThanOrEqual(4);
    expect([...CLAVES_DE_TAMANO]).toEqual(delServidor);
  });

  test("el panel de administración, el banco de preguntas y la ficha parten de la misma lista", () => {
    expect(TAMANOS.map((t) => t.clave)).toEqual([...CLAVES_DE_TAMANO]);
    expect(TAMANOS.map((t) => t.etiqueta)).toEqual(TAMANOS_ORGANIZACION.map((t) => t.etiqueta));
    expect(TAMANOS_EMPRESA.map((t) => t.id)).toEqual([...CLAVES_DE_TAMANO]);
    expect(TAMANOS_EMPRESA.map((t) => t.etiqueta)).toEqual(TAMANOS_ORGANIZACION.map((t) => t.etiqueta));
    expect([...ORDEN_TAMANO]).toEqual([...CLAVES_DE_TAMANO]);
    expect(CLAVES_DE_TAMANO.map(rangoDeTamano)).toEqual([0, 1, 2, 3]);
  });

  test("solo las cuatro claves cuentan como claves", () => {
    for (const clave of CLAVES_DE_TAMANO) expect(esClaveDeTamano(clave), clave).toBe(true);
    for (const otra of ["", "Micro", "grande", "mediana ", null, undefined, 3]) expect(esClaveDeTamano(otra), String(otra)).toBe(false);
  });
});

test.describe("Del total de personas a la talla", () => {
  const casos: Array<[number, string]> = [
    [0, "micro"], [1, "micro"], [9, "micro"],
    [10, "pequena"], [49, "pequena"],
    [50, "mediana"], [199, "mediana"],
    [200, "corporativo"], [201, "corporativo"], [5000, "corporativo"],
  ];
  for (const [personas, talla] of casos) {
    test(`${personas} personas es ${talla}`, () => {
      expect(tamanoPorPersonas(personas)).toBe(talla);
      expect(normalizarTamano(etiquetaTamanoPorPersonas(personas))).toBe(talla);
    });
  }

  test("200 personas ya es corporativo y su etiqueta no dice «> 200», que lo excluiría", () => {
    expect(etiquetaTamanoPorPersonas(200)).toBe("Corporativo (200 o más)");
    expect(etiquetaTamanoPorPersonas(200)).not.toContain(">");
  });
});

test.describe("De la etiqueta guardada a la talla", () => {
  const etiquetasActuales: Array<[string, string]> = [
    ["Microempresa (1-9)", "micro"],
    ["Pequeña empresa (10-49)", "pequena"],
    ["Mediana empresa (50-199)", "mediana"],
    ["Corporativo (200 o más)", "corporativo"],
  ];
  const etiquetasAnteriores: Array<[string, string]> = [
    ["Organización micro (1-9)", "micro"],
    ["Organización pequeña (10-49)", "pequena"],
    ["Organización mediana (50-199)", "mediana"],
    ["Corporativo (> 200)", "corporativo"],
    ["Mediana Empresa (50-199)", "mediana"],
    ["Pequeña Empresa (10-49)", "pequena"],
    ["Gran empresa", "corporativo"],
  ];

  for (const [etiqueta, talla] of [...etiquetasActuales, ...etiquetasAnteriores]) {
    test(`«${etiqueta}» es ${talla}`, () => {
      expect(normalizarTamano(etiqueta)).toBe(talla);
      expect(claveDeEtiqueta(etiqueta)).toBe(talla);
    });
  }

  test("la clave del servidor también se reconoce", () => {
    for (const clave of CLAVES_DE_TAMANO) expect(claveDeEtiqueta(clave), clave).toBe(clave);
  });

  test("lo desconocido es la talla más exigente, nunca una menos exigente", () => {
    for (const raro of [undefined, "", "   ", "no sé", "xl"]) expect(normalizarTamano(raro), String(raro)).toBe("corporativo");
  });

  test("una ficha guardada con la etiqueta anterior se muestra con la actual sin cambiar su talla", () => {
    for (const [anterior, talla] of etiquetasAnteriores) {
      const actual = etiquetaFichaDeTamano(anterior);
      expect(normalizarTamano(actual), anterior).toBe(talla);
      expect(actual, anterior).toBe(etiquetaDeFicha(talla as (typeof CLAVES_DE_TAMANO)[number]));
    }
    expect(etiquetaFichaDeTamano(undefined)).toBe("");
  });

  test("las etiquetas actuales hacen el viaje de ida y vuelta", () => {
    for (const clave of CLAVES_DE_TAMANO) expect(claveDeEtiqueta(etiquetaDeFicha(clave))).toBe(clave);
    expect(etiquetasActuales.map(([e]) => e)).toEqual(CLAVES_DE_TAMANO.map(etiquetaDeFicha));
  });
});
