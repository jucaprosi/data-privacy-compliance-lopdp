// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
/**
 * SEC-23 · Pruebas de comportamiento del proxy y cliente del copiloto.
 *
 * Ejecutan las funciones y handlers reales (`proxyCopiloto`, `identidadDe`,
 * `POST` consulta, `GET` estado, `consultarCopiloto`, `estadoCopiloto`) con
 * `NextRequest`, `window.sessionStorage` y `fetch` simulados.
 */
import { expect, test } from "@playwright/test";
import { NextRequest } from "next/server";

import { POST as postConsulta } from "../../src/app/api/ai-copilot/consulta/route";
import { GET as getEstado } from "../../src/app/api/ai-copilot/estado/route";
import { guardarOrganizacionActiva, olvidarOrganizaciones } from "../../src/lib/auth/organizacion";
import { guardarSesion, leerSesion } from "../../src/lib/auth/sesion";
import { consultarCopiloto, estadoCopiloto } from "../../src/lib/copilotClient";
import { identidadDe, proxyCopiloto } from "../../src/lib/copilotProxy";
import type { ConsultaCopiloto, EstadoCopiloto, RespuestaCopiloto } from "../../src/types/copilot";

type LlamadaFetch = { url: string; cabeceras: Headers; metodo: string; cuerpo?: string };

function tokenJwtPrueba(expiraEnSegundos = 3600): string {
  const b64 = (obj: unknown) => Buffer.from(JSON.stringify(obj)).toString("base64url");
  const exp = Math.floor(Date.now() / 1000) + expiraEnSegundos;
  return [
    b64({ alg: "RS256", typ: "JWT" }),
    b64({ email: "dpo@empresa.test", name: "DPO Prueba", exp }),
    "firma-prueba",
  ].join(".");
}

function respuestaCopilotoValida(): RespuestaCopiloto {
  return {
    pregunta: "Estado LOPDP",
    respuesta: "Orientación conforme al Art. 47 LOPDP.",
    modo: "local",
    fundamentos: [
      {
        articulo: "Art. 47",
        titulo: "LOPDP Ecuador",
        url: "https://datosprotegidos.gob.ec/lopdp",
        version: "2021",
        resumen: "Obligación de designar DPD.",
      },
    ],
    planes: [],
    advertencias: [],
    corpus_version: "v1",
    dlp_aplicado: true,
  };
}

function estadoCopilotoValido(): EstadoCopiloto {
  return {
    proveedor_configurado: true,
    proveedor: "vertex",
    modo: "local",
    corpus_version: "v1",
    dlp_activo: true,
  };
}

function consultaBase(pregunta = "Consulta sobre tratamiento de datos"): ConsultaCopiloto {
  return { pregunta, brechas: [], historial: [], estado: "Por iniciar" };
}

async function conFetchSimulado(
  respuestaFactory: (llamada: LlamadaFetch) => Response,
  fn: (llamadas: LlamadaFetch[]) => Promise<void>,
): Promise<void> {
  const globalObj = globalThis as unknown as Record<string, unknown>;
  const fetchPrevio = globalObj.fetch;
  const llamadas: LlamadaFetch[] = [];
  globalObj.fetch = async (input: RequestInfo | URL, init: RequestInit = {}) => {
    const llamada: LlamadaFetch = {
      url: String(input),
      cabeceras: new Headers(init.headers),
      metodo: init.method ?? "GET",
      cuerpo: typeof init.body === "string" ? init.body : undefined,
    };
    llamadas.push(llamada);
    return respuestaFactory(llamada);
  };
  try {
    await fn(llamadas);
  } finally {
    globalObj.fetch = fetchPrevio;
  }
}

async function conEntornoProxy(
  vars: Record<string, string | undefined>,
  fn: () => Promise<void>,
): Promise<void> {
  const previos: Record<string, string | undefined> = {};
  for (const [clave, valor] of Object.entries(vars)) {
    previos[clave] = process.env[clave];
    if (valor === undefined) delete process.env[clave];
    else process.env[clave] = valor;
  }
  try {
    await fn();
  } finally {
    for (const [clave, valor] of Object.entries(previos)) {
      if (valor === undefined) delete process.env[clave];
      else process.env[clave] = valor;
    }
  }
}

async function conNavegadorOidcSimulado(fn: () => Promise<void>): Promise<void> {
  const almacen = new Map<string, string>();
  const sessionStorage = {
    getItem: (k: string) => almacen.get(k) ?? null,
    setItem: (k: string, v: string) => void almacen.set(k, v),
    removeItem: (k: string) => void almacen.delete(k),
  };
  const globalObj = globalThis as unknown as Record<string, unknown>;
  const windowPrevio = globalObj.window;
  const modoPrevio = process.env.NEXT_PUBLIC_AUTH_MODE;
  process.env.NEXT_PUBLIC_AUTH_MODE = "oidc";
  globalObj.window = {
    sessionStorage,
    location: { pathname: "/dashboard", search: "", assign: () => undefined },
  };
  try {
    await fn();
  } finally {
    olvidarOrganizaciones();
    globalObj.window = windowPrevio;
    if (modoPrevio === undefined) delete process.env.NEXT_PUBLIC_AUTH_MODE;
    else process.env.NEXT_PUBLIC_AUTH_MODE = modoPrevio;
  }
}

test.describe("SEC-23 · Proxy y cliente del copiloto", () => {
  test("proxyCopiloto y POST consulta no fijan organización por defecto cuando falta X-Tenant-ID", async () => {
    await conEntornoProxy(
      { BACKEND_URL: "http://backend.interno.invalid:8080", COPILOT_API_URL: undefined, K_SERVICE: "evydentia-web" },
      async () => {
        await conFetchSimulado(
          () => new Response(JSON.stringify(respuestaCopilotoValida()), { status: 200 }),
          async (llamadas) => {
            const req = new NextRequest("http://localhost:3000/api/ai-copilot/consulta", {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
                Authorization: "Bearer token-oidc-usuario",
              },
              body: JSON.stringify(consultaBase()),
            });

            const res = await postConsulta(req);
            expect(res.status).toBe(200);
            expect(res.headers.get("Cache-Control")).toBe("no-store");
            expect(llamadas).toHaveLength(1);
            expect(llamadas[0].url).toBe("http://backend.interno.invalid:8080/api/v1/ai_copilot/consulta");
            expect(llamadas[0].cabeceras.get("authorization")).toBe("Bearer token-oidc-usuario");
            expect(llamadas[0].cabeceras.get("x-tenant-id")).toBeNull();
          },
        );
      },
    );
  });

  test("POST consulta y GET estado reenvían Authorization, X-Tenant-ID y X-Role, y bloquean cabeceras ajenas", async () => {
    await conEntornoProxy(
      { BACKEND_URL: "http://backend.interno.invalid:8080", COPILOT_API_URL: undefined, K_SERVICE: "evydentia-web" },
      async () => {
        await conFetchSimulado(
          (llamada) => {
            const payload = llamada.url.endsWith("/estado") ? estadoCopilotoValido() : respuestaCopilotoValida();
            return new Response(JSON.stringify(payload), { status: 200 });
          },
          async (llamadas) => {
            const reqPost = new NextRequest("http://localhost:3000/api/ai-copilot/consulta", {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
                Authorization: "Bearer token-real",
                "X-Tenant-ID": "org-real-77",
                "X-Role": "dpo",
                Cookie: "sesion=secreta",
                "X-Otro-Encabezado": "no-debe-pasar",
              },
              body: JSON.stringify(consultaBase("Revisar correo ana@empresa.test")),
            });
            const resPost = await postConsulta(reqPost);
            expect(resPost.status).toBe(200);

            const reqGet = new NextRequest("http://localhost:3000/api/ai-copilot/estado", {
              method: "GET",
              headers: {
                Authorization: "Bearer token-real",
                "X-Tenant-ID": "org-real-77",
                "X-Role": "coordinador",
              },
            });
            const resGet = await getEstado(reqGet);
            expect(resGet.status).toBe(200);

            expect(llamadas).toHaveLength(2);
            const [postCall, getCall] = llamadas;
            expect(postCall.cabeceras.get("authorization")).toBe("Bearer token-real");
            expect(postCall.cabeceras.get("x-tenant-id")).toBe("org-real-77");
            expect(postCall.cabeceras.get("x-role")).toBe("dpo");
            expect(postCall.cabeceras.get("cookie")).toBeNull();
            expect(postCall.cabeceras.get("x-otro-encabezado")).toBeNull();
            expect(postCall.cuerpo).not.toContain("ana@empresa.test");

            expect(getCall.url).toBe("http://backend.interno.invalid:8080/api/v1/ai_copilot/estado");
            expect(getCall.cabeceras.get("authorization")).toBe("Bearer token-real");
            expect(getCall.cabeceras.get("x-tenant-id")).toBe("org-real-77");
            expect(getCall.cabeceras.get("x-role")).toBe("coordinador");
          },
        );
      },
    );
  });

  test("en la nube (K_SERVICE) el proxy descarta X-User-ID; fuera de la nube lo conserva", async () => {
    const construirReq = () =>
      new NextRequest("http://localhost:3000/api/ai-copilot/estado", {
        method: "GET",
        headers: {
          Authorization: "Bearer token-real",
          "X-Tenant-ID": "org-real-77",
          "X-User-ID": "usuario-suplantado",
        },
      });

    await conEntornoProxy({ BACKEND_URL: "http://backend.interno.invalid:8080", K_SERVICE: "evydentia-web" }, async () => {
      expect(identidadDe(construirReq())).toEqual({
        authorization: "Bearer token-real",
        "x-tenant-id": "org-real-77",
      });
      await conFetchSimulado(
        () => new Response(JSON.stringify(estadoCopilotoValido()), { status: 200 }),
        async (llamadas) => {
          const res = await proxyCopiloto(construirReq(), "estado");
          expect(res.status).toBe(200);
          expect(llamadas[0].cabeceras.get("x-user-id")).toBeNull();
        },
      );
    });

    await conEntornoProxy({ BACKEND_URL: "http://backend.interno.invalid:8080", K_SERVICE: undefined }, async () => {
      expect(identidadDe(construirReq())["x-user-id"]).toBe("usuario-suplantado");
      await conFetchSimulado(
        () => new Response(JSON.stringify(estadoCopilotoValido()), { status: 200 }),
        async (llamadas) => {
          const res = await proxyCopiloto(construirReq(), "estado");
          expect(res.status).toBe(200);
          expect(llamadas[0].cabeceras.get("x-user-id")).toBe("usuario-suplantado");
        },
      );
    });
  });

  test("consultarCopiloto y estadoCopiloto usan fetchAutenticado y limpian la sesión ante 401", async () => {
    await conNavegadorOidcSimulado(async () => {
      const token = tokenJwtPrueba();
      expect(guardarSesion(token, { avisar: false })).toBe(true);
      guardarOrganizacionActiva({ tenant_id: "org-cliente-88", nombre_comercial: "Org 88", roles: ["dpo"] });

      await conFetchSimulado(
        (llamada) => {
          const payload = llamada.url.endsWith("/estado") ? estadoCopilotoValido() : respuestaCopilotoValida();
          return new Response(JSON.stringify(payload), { status: 200 });
        },
        async (llamadas) => {
          const resp = await consultarCopiloto(consultaBase());
          expect(resp.dlp_aplicado).toBe(true);
          const estado = await estadoCopiloto();
          expect(estado.dlp_activo).toBe(true);

          expect(llamadas).toHaveLength(2);
          for (const llamada of llamadas) {
            expect(llamada.cabeceras.get("authorization")).toBe(`Bearer ${token}`);
            expect(llamada.cabeceras.get("x-tenant-id")).toBe("org-cliente-88");
            expect(llamada.cabeceras.get("x-user-id")).toBeNull();
          }
          expect(llamadas[0].url).toBe("/api/ai-copilot/consulta");
          expect(llamadas[1].url).toBe("/api/ai-copilot/estado");
        },
      );

      // Sin organización activa en oidc no se inventa X-Tenant-ID; un 401 descarta la sesión (fetchAutenticado).
      olvidarOrganizaciones();
      expect(guardarSesion(token, { avisar: false })).toBe(true);
      await conFetchSimulado(
        () => new Response(JSON.stringify({ detail: "Expirado" }), { status: 401 }),
        async (llamadas) => {
          await expect(estadoCopiloto()).rejects.toThrow("Servicio no disponible");
          expect(llamadas[0].cabeceras.get("x-tenant-id")).toBeNull();
          expect(leerSesion()).toBeNull();
        },
      );
    });
  });
});
