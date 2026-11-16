import { expect, test, type Page } from "@playwright/test";

// REG-01: pantallas del operador para el paquete normativo. La API se simula.

const PAQUETE = {
  id: "pqn-lopdp-1-0",
  codigo: "LOPDP",
  nombre: "Ley Orgánica de Protección de Datos Personales",
  version: "1.0",
  estado: "borrador",
  creado_por: "migracion-reg01",
  creado_en: "2026-11-13T10:00:00Z",
  publicado_por: null,
  publicado_en: null,
  retirado_en: null,
  sin_verificar: 2,
};

function parametro(clave: string, verificado: boolean, unidad: string | null = "calendario") {
  return {
    clave,
    valor: "15",
    unidad,
    termino_legal: "plazo",
    articulo: "LOPDP art. 13",
    fuente_url: "https://example.test/lopdp.pdf",
    verificado,
    verificado_por: verificado ? "op-1" : null,
    verificado_por_nombre: verificado ? "Ana Operadora" : null,
    verificado_en: verificado ? "2026-11-13T10:00:00Z" : null,
    actualizado_por: "op-1",
    actualizado_en: "2026-11-13T10:00:00Z",
  };
}

async function simular(page: Page, opciones: { sinVerificar: boolean; denegado?: boolean }) {
  const publicaciones: string[] = [];
  const parametros = opciones.sinVerificar
    ? [parametro("plazo_derechos_dias", false), parametro("autoridad", false, null)]
    : [parametro("plazo_derechos_dias", true), parametro("autoridad", true, null)];
  await page.route("**/api/v1/plataforma/paquetes**", async (route) => {
    const peticion = route.request();
    const ruta = new URL(peticion.url()).pathname.replace("/api/v1/plataforma/paquetes", "");
    const responder = (status: number, cuerpo: unknown) =>
      route.fulfill({ status, contentType: "application/json", body: JSON.stringify(cuerpo) });
    if (opciones.denegado) return responder(403, { code: "NO_ES_OPERADOR", detail: "texto del servidor" });
    if (ruta === "" && peticion.method() === "GET") {
      return responder(200, { paquetes: [{ ...PAQUETE, sin_verificar: opciones.sinVerificar ? 2 : 0 }] });
    }
    if (ruta === `/${PAQUETE.id}` && peticion.method() === "GET") {
      return responder(200, { paquete: PAQUETE, parametros });
    }
    if (ruta === `/${PAQUETE.id}/publicar` && peticion.method() === "POST") {
      publicaciones.push(ruta);
      return responder(200, {
        paquete: { ...PAQUETE, estado: "publicado" },
        impacto: { plantillas: [], plantillas_pendiente: true, organizaciones: null, organizaciones_pendiente: true },
      });
    }
    return responder(404, { code: "PAQUETE_NO_ENCONTRADO" });
  });
  return publicaciones;
}

test("la lista muestra estado y parámetros sin verificar, sin tokens de gobernanza", async ({ page }) => {
  await simular(page, { sinVerificar: true });
  await page.goto("/plataforma/paquetes");
  await expect(page.getByRole("heading", { name: "Paquetes normativos", exact: true })).toBeVisible();
  const fila = page.getByRole("row", { name: /Ley Orgánica/ });
  await expect(fila).toContainText("Borrador");
  await expect(fila).toContainText("2 sin verificar");
  const texto = await page.locator("main").innerText();
  expect(texto).not.toContain("¤");
  expect(texto).not.toContain("¦");
});

test("con dos parámetros sin verificar, Publicar está deshabilitado y los lista", async ({ page }) => {
  const publicaciones = await simular(page, { sinVerificar: true });
  await page.goto(`/plataforma/paquetes/${PAQUETE.id}`);
  const publicar = page.getByRole("button", { name: "Publicar", exact: true });
  await expect(publicar).toHaveAttribute("aria-disabled", "true");
  await expect(publicar).toHaveAccessibleDescription(
    "Faltan por verificar: Plazo para atender los derechos, Autoridad de control",
  );
  await expect(page.getByText("Pendiente de verificar")).toHaveCount(2);
  await publicar.click({ force: true });
  await expect(page.getByRole("dialog")).toHaveCount(0);
  expect(publicaciones).toHaveLength(0);
  await expect(page.getByLabel("Unidad")).toBeVisible();
});

test("con todo verificado, el diálogo pide confirmación con Cancelar enfocado", async ({ page }) => {
  const publicaciones = await simular(page, { sinVerificar: false });
  await page.goto(`/plataforma/paquetes/${PAQUETE.id}`);
  await expect(page.getByText("Verificado por Ana Operadora el").first()).toBeVisible();
  await page.getByRole("button", { name: "Publicar", exact: true }).click();
  const dialogo = page.getByRole("dialog", {
    name: "¿Publicar la versión 1.0 del paquete Ley Orgánica de Protección de Datos Personales?",
  });
  await expect(dialogo).toBeVisible();
  await expect(dialogo.getByRole("button", { name: "Cancelar" })).toBeFocused();
  await dialogo.getByRole("button", { name: "Publicar" }).click();
  await expect(page.getByRole("status")).toContainText("todavía no se puede medir");
  expect(publicaciones).toHaveLength(1);
});

test("un usuario que no es operador ve acceso denegado y nunca el texto del servidor", async ({ page }) => {
  await simular(page, { sinVerificar: true, denegado: true });
  await page.goto("/plataforma/paquetes");
  await expect(page.getByRole("heading", { name: "Acceso denegado" })).toBeVisible();
  await expect(page.getByText("texto del servidor")).toHaveCount(0);
});
