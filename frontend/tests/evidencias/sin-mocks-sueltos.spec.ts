/**
 * EVI-01b: guardia. Ningún spec mockea por su cuenta las rutas nuevas de evidencias ni el almacén: solo
 * `simularSubidaFirmada` de `tests/utiles.ts`. Un `page.route` suelto deja a los demás specs probando un
 * servidor distinto del que prueba la guardia.
 *
 * Mutación documentada (EVI-01b): añadir un `page.route` sobre la ruta de subidas de evidencias a un spec ->
 * esta guardia falla nombrando el archivo.
 */
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join, relative, sep } from "node:path";

import { expect, test } from "@playwright/test";

const RAIZ = join(__dirname, "..");
const PROHIBIDO = /evidencias\/subidas|almacen\.invalid/;
const PERMITIDOS = new Set(["utiles.ts", join("evidencias", "sin-mocks-sueltos.spec.ts")]);

function especificaciones(carpeta: string): string[] {
  return readdirSync(carpeta).flatMap((nombre) => {
    const ruta = join(carpeta, nombre);
    if (statSync(ruta).isDirectory()) return nombre === "node_modules" ? [] : especificaciones(ruta);
    return ruta.endsWith(".ts") ? [ruta] : [];
  });
}

test("solo utiles.ts mockea la subida firmada", () => {
  const archivos = especificaciones(RAIZ);
  expect(archivos.some((a) => relative(RAIZ, a) === "utiles.ts")).toBe(true);
  const sueltos = archivos
    .filter((a) => !PERMITIDOS.has(relative(RAIZ, a)))
    .filter((a) => PROHIBIDO.test(readFileSync(a, "utf-8")))
    .map((a) => relative(RAIZ, a).split(sep).join("/"));
  expect(sueltos).toEqual([]);
});
