/**
 * Humo 1 y 3, sin navegador por ser lo más rápido: la API real acepta el token correcto, rechaza cada
 * falsificación y no deja cruzar a otra organización.
 */
import { generateKeyPairSync } from "crypto";

import { expect, test } from "@playwright/test";

import { bearer, firmarToken, leerEscenario } from "./escenario";

const RUTA = "/api/v1/organizacion/mis-organizaciones";

test.describe("Identidad y aislamiento contra la API real", () => {
  test("la API responde a través del proxy de Next, con todos sus routers", async ({ request }) => {
    const respuesta = await request.get("/api/v1/health");
    expect(respuesta.status()).toBe(200);
    expect((await respuesta.json()).routers.fallidos).toEqual([]);
  });

  test("el token válido devuelve solo las organizaciones de la persona", async ({ request }) => {
    const { a } = leerEscenario();
    const respuesta = await request.get(RUTA, { headers: bearer(firmarToken(a)) });
    expect(respuesta.status()).toBe(200);
    const { organizaciones } = await respuesta.json();
    expect(organizaciones.map((o: { tenant_id: string }) => o.tenant_id)).toEqual([a.tenantId]);
  });

  test("sin token o con uno falsificado, 401", async ({ request }) => {
    const { a } = leerEscenario();
    const { privateKey } = generateKeyPairSync("rsa", {
      modulusLength: 2048,
      privateKeyEncoding: { type: "pkcs8", format: "pem" },
      publicKeyEncoding: { type: "spki", format: "pem" },
    });
    expect((await request.get(RUTA)).status()).toBe(401);
    for (const token of [
      firmarToken(a, { clavePrivada: privateKey }),
      firmarToken(a, { aud: "otra-aplicacion" }),
      firmarToken(a, { iss: "https://emisor-ajeno.test" }),
      firmarToken(a, { expEnSegundos: -60 }),
    ]) {
      expect((await request.get(RUTA, { headers: bearer(token) })).status()).toBe(401);
    }
  });

  test("con token válido, pedir otra organización responde 403", async ({ request }) => {
    const { a, b } = leerEscenario();
    const respuesta = await request.get("/api/v1/rat/actividades", {
      headers: { ...bearer(firmarToken(a)), "X-Tenant-ID": b.tenantId, "X-Role": "coordinador" },
    });
    expect(respuesta.status()).toBe(403);
  });
});
