/** API simulada del centro de conocimiento (REG-02): el contrato vive en governance/especificaciones/REG-02.md. */
import type { Page } from "@playwright/test";

const VERSION = "lopdp-rg-2026-09-20.1";
const ARTICULOS = [
  { fuente: "LOPDP", articulo: "Art. 7", titulo: "Tratamiento legítimo", texto: "Cada tratamiento debe apoyarse en una condición de licitud aplicable.", version: VERSION },
  { fuente: "LOPDP", articulo: "Art. 13", titulo: "Derecho de acceso", texto: "El titular puede conocer y obtener gratuitamente sus datos: derechos del titular.", version: VERSION },
  { fuente: "Reglamento General a la LOPDP", articulo: "Art. 15", titulo: "Registro de solicitudes", texto: "Deben registrarse todas las solicitudes de ejercicio de derechos.", version: VERSION },
];

export async function instalarApiConocimiento(page: Page): Promise<void> {
  await page.route("**/api/v1/**", async (route) => {
    const url = new URL(route.request().url());
    const ruta = url.pathname.replace(/^\/api\/v1/, "");
    const responder = (status: number, cuerpo: unknown) =>
      route.fulfill({ status, contentType: "application/json", body: JSON.stringify(cuerpo) });

    if (ruta === "/organizacion/me/roles") {
      return responder(200, { user_id: "u-reg-02", tenant_id: "tenant-reg-02", roles: [{ role: "implementador", area_id: null, area_nombre: null, valid_to: null }] });
    }
    if (ruta === "/conocimiento/normativa") {
      const fuente = (url.searchParams.get("fuente") ?? "").toLowerCase();
      const q = (url.searchParams.get("q") ?? "").toLowerCase();
      const lista = ARTICULOS.filter((a) => (!fuente || a.fuente.toLowerCase().startsWith(fuente)) && (!q || `${a.titulo} ${a.texto}`.toLowerCase().includes(q)));
      return responder(200, { articulos: lista });
    }
    if (ruta === "/conocimiento/ayuda") {
      const control = url.searchParams.get("control_ref");
      if (control === "P12") {
        const a = ARTICULOS[0];
        return responder(200, { texto: a.texto, cita: { fuente: a.fuente, articulo: a.articulo, version: a.version } });
      }
      return responder(404, { detail: "Sin fuente en el corpus.", code: "SIN_FUENTE", action_required: null });
    }
    return responder(200, {});
  });
}
