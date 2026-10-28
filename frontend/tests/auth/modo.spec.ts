/**
 * Reglas puras de la identidad del frontend (FE-07): modo por defecto, tenant y lectura de la
 * credencial. No abren navegador: ejecutan el código real de lib/auth en Node.
 *
 * Importa lo mismo que usa la aplicación; el modo por defecto de un build de producción no se puede
 * observar desde el servidor de desarrollo (allí NODE_ENV es "development"), por eso se ejercita aquí.
 */
import { expect, test } from "@playwright/test";

import { modoAutenticacion, tenantConfigurado } from "../../src/lib/auth/modo";
import { haCaducado, leerCredencial } from "../../src/lib/auth/sesion";

const VARIABLES = ["NODE_ENV", "NEXT_PUBLIC_AUTH_MODE", "NEXT_PUBLIC_TENANT_ID"] as const;
const env = process.env as Record<string, string | undefined>;

test.describe("Modo de autenticación por defecto", () => {
  const guardado: Record<string, string | undefined> = {};
  test.beforeEach(() => {
    for (const v of VARIABLES) guardado[v] = env[v];
    delete env.NEXT_PUBLIC_AUTH_MODE;
    delete env.NEXT_PUBLIC_TENANT_ID;
  });
  test.afterEach(() => {
    for (const v of VARIABLES) {
      if (guardado[v] === undefined) delete env[v];
      else env[v] = guardado[v];
    }
  });

  test("un build de producción arranca en oidc salvo que se pida otra cosa", () => {
    env.NODE_ENV = "production";
    expect(modoAutenticacion()).toBe("oidc");
  });

  test("el servidor de desarrollo arranca en headers", () => {
    env.NODE_ENV = "development";
    expect(modoAutenticacion()).toBe("headers");
  });

  test("NEXT_PUBLIC_AUTH_MODE fuerza el modo, también en producción", () => {
    env.NODE_ENV = "production";
    env.NEXT_PUBLIC_AUTH_MODE = "headers";
    expect(modoAutenticacion()).toBe("headers");
    env.NODE_ENV = "development";
    env.NEXT_PUBLIC_AUTH_MODE = "oidc";
    expect(modoAutenticacion()).toBe("oidc");
  });

  test("un valor desconocido cae en oidc, nunca en headers", () => {
    for (const valor of ["cabeceras", "true", "0", "header", "none"]) {
      env.NODE_ENV = "development";
      env.NEXT_PUBLIC_AUTH_MODE = valor;
      expect(modoAutenticacion(), valor).toBe("oidc");
    }
  });

  test("en oidc el tenant es el de la organización elegida, nunca el del despliegue (FE-21)", () => {
    env.NODE_ENV = "production";
    expect(tenantConfigurado()).toBe("");
    env.NEXT_PUBLIC_TENANT_ID = "  organizacion-del-despliegue ";
    expect(tenantConfigurado()).toBe("");
  });

  test("en headers se conserva el tenant de demostración de desarrollo", () => {
    env.NODE_ENV = "development";
    expect(tenantConfigurado()).toBe("tenant-corp-demo");
  });
});

test.describe("Lectura de la credencial de Google", () => {
  const b64 = (o: unknown) => Buffer.from(JSON.stringify(o)).toString("base64url");
  const jwt = (carga: unknown) => `${b64({ alg: "RS256" })}.${b64(carga)}.firma`;

  test("lee correo, nombre y caducidad sin verificar la firma", () => {
    expect(leerCredencial(jwt({ email: "a@b.test", name: "Ana", exp: 2000000000 }))).toEqual({
      email: "a@b.test",
      nombre: "Ana",
      exp: 2000000000,
    });
  });

  test("sin nombre usa el correo; con caracteres no ASCII los lee bien", () => {
    expect(leerCredencial(jwt({ email: "a@b.test", exp: 1 }))?.nombre).toBe("a@b.test");
    expect(leerCredencial(jwt({ email: "a@b.test", name: "Ñandú Pérez", exp: 1 }))?.nombre).toBe("Ñandú Pérez");
  });

  test("lo que no es un JWT con caducidad no es utilizable", () => {
    for (const malo of ["", "abc", "a.b", "a.b.c.d", jwt({ email: "a@b.test" }), jwt({ exp: "mañana" }), `${b64({})}.@@@.firma`]) {
      expect(leerCredencial(malo), malo).toBeNull();
    }
  });

  test("caduca 30 segundos antes del instante real, para no enviar un token a punto de vencer", () => {
    const ahoraMs = 1_000_000_000_000;
    const exp = ahoraMs / 1000 + 100;
    expect(haCaducado(exp, ahoraMs)).toBe(false);
    expect(haCaducado(exp - 69, ahoraMs)).toBe(false); // faltan 31 s: aún vale
    expect(haCaducado(exp - 70, ahoraMs)).toBe(true); // faltan 30 s: ya no
    expect(haCaducado(exp - 200, ahoraMs)).toBe(true);
  });
});
