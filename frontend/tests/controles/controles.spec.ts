/**
 * Controles periódicos (CAPA-02, governance/especificaciones/CAPA-02.md §5).
 *
 * Con la API simulada: un control que vence en 3 días se ve en ámbar; uno vencido, en rojo con enlace a su
 * hallazgo; el `implementador` revisa vencimientos al abrir, crea y verifica; el `dpo` solo consulta.
 */
import { expect, test, type Page } from "@playwright/test";

import { hoyGuayaquil } from "../../src/lib/controles/api";
import { abrirAppLimpia, configurarProyecto, irASala } from "../utiles";

interface ControlSimulado {
  id: string;
  nombre: string;
  control_ref: string | null;
  frecuencia: string;
  responsable_user_id: string;
  proxima_verificacion: string;
  estado: string;
  hallazgo_vigente_id: string | null;
  ultima_verificacion_en: string | null;
}

function enDias(dias: number): string {
  return new Date(Date.parse(hoyGuayaquil()) + dias * 86_400_000).toISOString().slice(0, 10);
}

function control(id: string, dias: number, extra: Partial<ControlSimulado> = {}): ControlSimulado {
  return {
    id,
    nombre: `Control ${id}`,
    control_ref: null,
    frecuencia: "trimestral",
    responsable_user_id: "usuario-responsable",
    proxima_verificacion: enDias(dias),
    estado: "vigente",
    hallazgo_vigente_id: null,
    ultima_verificacion_en: null,
    ...extra,
  };
}

async function simularApi(page: Page, userId: string, roles: string[], controles: ControlSimulado[]) {
  const estado = { controles: [...controles], vencer: 0, verificados: [] as string[] };
  await page.route("**/api/v1/**", async (route) => {
    const peticion = route.request();
    const ruta = new URL(peticion.url()).pathname.replace(/^\/api\/v1/, "");
    const metodo = peticion.method();
    const responder = (status: number, cuerpo: unknown) =>
      route.fulfill({ status, contentType: "application/json", body: JSON.stringify(cuerpo) });

    if (ruta === "/organizacion/me/roles") {
      return responder(200, {
        user_id: userId,
        tenant_id: "tenant-controles-e2e",
        roles: roles.map((role) => ({ role, area_id: null, area_nombre: null, valid_to: null })),
      });
    }
    if (ruta === "/auditoria-capa/controles/vencer" && metodo === "POST") {
      estado.vencer += 1;
      return responder(200, { vencidos: 0, hallazgos_creados: 0 });
    }
    if (ruta === "/auditoria-capa/controles" && metodo === "GET") {
      return responder(200, { controles: estado.controles });
    }
    if (ruta === "/auditoria-capa/controles" && metodo === "POST") {
      const cuerpo = JSON.parse(peticion.postData() ?? "{}") as Partial<ControlSimulado>;
      const nuevo = control("nuevo", 30, cuerpo);
      estado.controles.push(nuevo);
      return responder(201, nuevo);
    }
    const verificacion = ruta.match(/^\/auditoria-capa\/controles\/([^/]+)\/verificaciones$/);
    if (verificacion && metodo === "POST") {
      const actual = estado.controles.find((c) => c.id === verificacion[1])!;
      Object.assign(actual, { estado: "vigente", hallazgo_vigente_id: null, proxima_verificacion: enDias(90) });
      estado.verificados.push(actual.id);
      return responder(201, { control: actual, verificacion: { id: "v1" } });
    }
    return responder(200, []);
  });
  return estado;
}

async function abrirControles(page: Page) {
  await abrirAppLimpia(page);
  await configurarProyecto(page);
  await irASala(page, /Controles periódicos/);
  await expect(page.getByTestId("controles-periodicos")).toBeVisible();
}

test("el semáforo muestra ámbar a 3 días y rojo con enlace al hallazgo", async ({ page }) => {
  const estado = await simularApi(page, "usuario-impl", ["implementador"], [
    control("lejano", 30),
    control("cercano", 3),
    control("vencido", -2, { estado: "vencido", hallazgo_vigente_id: "hallazgo-1" }),
  ]);
  await abrirControles(page);

  await expect(page.getByTestId("control-lejano").getByTestId("semaforo")).toHaveAttribute("data-semaforo", "vigente");
  const cercano = page.getByTestId("control-cercano").getByTestId("semaforo");
  await expect(cercano).toHaveAttribute("data-semaforo", "por_vencer");
  await expect(cercano).toHaveClass(/badge-render-warning/);

  const vencido = page.getByTestId("control-vencido");
  await expect(vencido.getByTestId("semaforo")).toHaveClass(/badge-render-danger/);
  await expect(vencido.getByRole("button", { name: "Ver hallazgo" })).toBeVisible();
  await expect(page.getByTestId("control-cercano").getByRole("button", { name: "Ver hallazgo" })).toHaveCount(0);
  expect(estado.vencer).toBeGreaterThan(0);
});

test("el implementador crea un control y registra su verificación", async ({ page }) => {
  const estado = await simularApi(page, "usuario-impl", ["implementador"], [
    control("vencido", -2, { estado: "vencido", hallazgo_vigente_id: "hallazgo-1" }),
  ]);
  await abrirControles(page);

  await page.getByLabel("Nombre").fill("Revisión de accesos");
  await page.getByLabel("Primera verificación").fill(enDias(30));
  await page.getByLabel("Responsable (usuario)").fill("usuario-responsable");
  await page.getByRole("button", { name: "Crear control" }).click();
  await expect(page.getByTestId("control-nuevo")).toContainText("Revisión de accesos");

  const fila = page.getByTestId("control-vencido");
  await fila.getByRole("button", { name: "Registrar verificación" }).click();
  await fila.getByRole("button", { name: "Guardar verificación" }).click();
  await expect(fila.getByTestId("semaforo")).toHaveAttribute("data-semaforo", "vigente");
  await expect(fila.getByRole("button", { name: "Ver hallazgo" })).toHaveCount(0);
  expect(estado.verificados).toEqual(["vencido"]);
});

test("el dpo consulta: no crea, no verifica ni revisa vencimientos", async ({ page }) => {
  const estado = await simularApi(page, "usuario-responsable", ["dpo"], [control("uno", 30)]);
  await abrirControles(page);

  await expect(page.getByTestId("control-uno")).toBeVisible();
  await expect(page.getByRole("form", { name: "Nuevo control" })).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Registrar verificación" })).toHaveCount(0);
  expect(estado.vencer).toBe(0);
});

test("el responsable verifica los suyos y no los ajenos", async ({ page }) => {
  await simularApi(page, "usuario-responsable", ["responsable_area"], [
    control("mio", 3),
    control("ajeno", 3, { responsable_user_id: "otra-persona" }),
  ]);
  await abrirControles(page);

  await expect(page.getByTestId("control-mio").getByRole("button", { name: "Registrar verificación" })).toBeVisible();
  await expect(page.getByTestId("control-ajeno").getByRole("button", { name: "Registrar verificación" })).toHaveCount(0);
  await expect(page.getByRole("form", { name: "Nuevo control" })).toHaveCount(0);
});
