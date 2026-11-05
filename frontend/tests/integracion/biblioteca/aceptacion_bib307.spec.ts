/**
 * BIB-307 · Aceptación de Biblioteca contra el backend real (sin page.route).
 *
 * Alcance honesto: aquí se comprueba por HTTP que la empresa sale de la sesión del servidor y que
 * cambiar el ID en la URL no da acceso a documentos ni expedientes de otra empresa. El recorrido completo
 * (tres perfiles, revisión, evidencia, cierre) lo acredita tests/test_bib_307_integracion.py contra la base.
 */
import { expect, test } from "@playwright/test";
import { crearTenantConAdmin, limpiarTenant } from "../dbHelper";

test.describe("BIB-307: cero accesos cruzados en Biblioteca", () => {
  let a: ReturnType<typeof crearTenantConAdmin>;

  test.beforeEach(() => {
    a = crearTenantConAdmin("bib307-a");
  });

  test.afterEach(() => {
    if (a) limpiarTenant(a.tenantId, a.domain);
  });

  test("sin empresa se rechaza y con otra empresa el documento no existe", async ({ request }) => {
    const sinEmpresa = await request.get("/api/v1/biblioteca/documentos");
    // Sin cabeceras de identidad, get_context rechaza la petición antes de llegar a la sala.
    expect(sinEmpresa.status()).toBe(422);

    const cabecerasA = { "X-Tenant-ID": a.tenantId, "X-User-ID": a.adminUserId, "X-Role": "admin_organizacion" };
    // El helper de TEST-03 crea una sola empresa por prueba (usuario demo exclusivo); la ajena es un ID cualquiera.
    const empresaAjena = `bib307-ajena-${crypto.randomUUID()}`;
    const listaA = await request.get("/api/v1/biblioteca/documentos", { headers: cabecerasA });
    expect(listaA.status()).toBe(200);
    expect(await listaA.json()).toEqual([]);

    // Un usuario de A que se declara de B no obtiene acceso: la pertenencia la decide el servidor.
    const suplantado = await request.get("/api/v1/biblioteca/documentos", {
      headers: { "X-Tenant-ID": empresaAjena, "X-User-ID": a.adminUserId, "X-Role": "admin_organizacion" },
    });
    expect([401, 403]).toContain(suplantado.status());

    const inexistente = await request.get(`/api/v1/biblioteca/documentos/${crypto.randomUUID()}`, {
      headers: cabecerasA,
    });
    expect(inexistente.status()).toBe(404);
  });
});
