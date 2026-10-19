/**
 * Arnés de interfaz de FE-05: administración de la organización.
 *
 * Monta AdminPanel en /harness-roadmap/admin contra el servidor simulado de FE-01. Parámetros de
 * la ruta: rol, seccion, tamano y fallo (tamano | sod | duplicado | ultimo | carga | config).
 * Datos del simulado: 4 usuarios, 3 áreas (area-003 cuelga de area-001) y 4 asignaciones de rol.
 * La configuración la simula el propio harness: el backend (RM-15) aún no existe.
 */
import { expect, test, type Page } from "@playwright/test";

const RUTA = "/harness-roadmap/admin";

async function abrir(page: Page, consulta = ""): Promise<void> {
  await page.goto(`${RUTA}${consulta}`);
  await expect(page.getByRole("region", { name: "Administración de la organización" })).toBeVisible();
}

const pestana = (page: Page, nombre: string) => page.getByRole("tab", { name: nombre });

async function irA(page: Page, nombre: string): Promise<void> {
  await pestana(page, nombre).click();
  await expect(pestana(page, nombre)).toHaveAttribute("aria-selected", "true");
}

test.describe("Administración de la organización (FE-05)", () => {
  test("quien no es administrador no ve las pestañas y se le explica por qué", async ({ page }) => {
    await abrir(page, "?rol=coordinador");

    await expect(page.getByRole("note")).toContainText("Solo la persona con el rol administrador de la organización");
    await expect(page.getByRole("tablist")).toHaveCount(0);
    await expect(page.getByRole("form")).toHaveCount(0);
  });

  test("las pestañas se recorren con las flechas del teclado", async ({ page }) => {
    await abrir(page);
    await pestana(page, "Usuarios").focus();
    await page.keyboard.press("ArrowRight");
    await expect(pestana(page, "Áreas")).toHaveAttribute("aria-selected", "true");
    await expect(pestana(page, "Áreas")).toBeFocused();
    await page.keyboard.press("ArrowLeft");
    await page.keyboard.press("ArrowLeft");
    await expect(pestana(page, "Configuración")).toHaveAttribute("aria-selected", "true");
  });

  test.describe("usuarios", () => {
    test("lista a las personas de la organización", async ({ page }) => {
      await abrir(page);
      await expect(page.getByTestId("usuario-user-admin-01")).toContainText("Administrador de Organización");
      await expect(page.getByTestId("usuario-user-resp-01")).toContainText("responsable.ti@corp.ec");
      await expect(page.getByRole("table", { name: "Usuarios de la organización" }).getByRole("row")).toHaveCount(5);
    });

    test("valida el correo y el nombre antes de crear", async ({ page }) => {
      await abrir(page);
      await page.getByLabel("Correo electrónico").fill("no-es-un-correo");
      await page.getByRole("button", { name: "Crear usuario" }).click();

      await expect(page.getByText("Escribe un correo electrónico válido, por ejemplo nombre@empresa.ec.")).toBeVisible();
      await expect(page.getByText("Indica el nombre de la persona.")).toBeVisible();
      await expect(page.getByRole("table", { name: "Usuarios de la organización" }).getByRole("row")).toHaveCount(5);
    });

    test("crea un usuario y aparece en la lista", async ({ page }) => {
      await abrir(page);
      await page.getByLabel("Correo electrónico").fill("laura.mena@corp.ec");
      await page.getByLabel("Nombre", { exact: true }).fill("Laura Mena");
      await page.getByRole("button", { name: "Crear usuario" }).click();

      await expect(page.getByTestId("usuario-creado")).toContainText("Se creó el usuario Laura Mena");
      await expect(page.getByRole("table", { name: "Usuarios de la organización" })).toContainText("laura.mena@corp.ec");
      await expect(page.getByRole("table", { name: "Usuarios de la organización" }).getByRole("row")).toHaveCount(6);
    });
  });

  test.describe("áreas", () => {
    test("muestra la jerarquía: el área subordinada cuelga de su superior", async ({ page }) => {
      await abrir(page, "?seccion=areas");

      await expect(page.getByTestId("area-area-001")).toHaveAttribute("data-nivel", "0");
      await expect(page.getByTestId("area-area-003")).toHaveAttribute("data-nivel", "1");
      await expect(page.getByTestId("area-area-002")).toHaveAttribute("data-nivel", "0");
      // La subordinada está anidada dentro de su superior en la estructura de la lista.
      await expect(page.getByTestId("area-area-001").getByTestId("area-area-003")).toBeVisible();
    });

    test("exige el nombre y crea un área bajo la superior elegida", async ({ page }) => {
      await abrir(page, "?seccion=areas");
      await page.getByRole("button", { name: "Crear área" }).click();
      await expect(page.getByText("Indica el nombre del área.")).toBeVisible();

      await page.getByLabel("Nombre del área").first().fill("Recursos Humanos");
      await page.getByLabel("Área superior").selectOption({ label: "Asesoría Jurídica y Cumplimiento" });
      await page.getByRole("button", { name: "Crear área" }).click();

      const nueva = page.getByTestId("area-area-002").getByRole("listitem").filter({ hasText: "Recursos Humanos" });
      await expect(nueva).toBeVisible();
      await expect(nueva).toHaveAttribute("data-nivel", "1");
    });

    test("editar un área subordinada cambia esa y no la superior", async ({ page }) => {
      await abrir(page, "?seccion=areas");

      await page.getByRole("button", { name: "Editar Seguridad de la Información" }).click();
      const formulario = page.getByRole("form", { name: "Editar Seguridad de la Información" });
      await formulario.getByLabel("Nombre del área").fill("Seguridad y Privacidad");
      await formulario.getByRole("button", { name: "Guardar área" }).click();

      await expect(page.getByTestId("area-area-003")).toContainText("Seguridad y Privacidad");
      await expect(page.getByTestId("area-area-001")).toContainText("Dirección de Tecnología y Ciberseguridad");
      await expect(page.getByTestId("area-area-003")).toHaveAttribute("data-nivel", "1");
    });
  });

  test.describe("roles", () => {
    test("lista las asignaciones con su área y vigencia", async ({ page }) => {
      await abrir(page, "?seccion=roles");

      const tabla = page.getByRole("table", { name: "Roles asignados" });
      await expect(tabla.getByRole("row")).toHaveCount(5);
      await expect(page.getByTestId("rol-assign-004")).toContainText("Responsable de área");
      await expect(page.getByTestId("rol-assign-004")).toContainText("Dirección de Tecnología y Ciberseguridad");
      await expect(page.getByTestId("rol-assign-001")).toContainText("Toda la organización");
      await expect(page.getByTestId("rol-assign-001")).toContainText("Sin vencimiento");
    });

    test("el área solo se puede elegir para el responsable de área", async ({ page }) => {
      await abrir(page, "?seccion=roles");

      const selectRol = page.getByLabel("Rol", { exact: true });
      await expect(selectRol.locator('option[value="coordinador"]')).toHaveText("Coordinador");
      await expect(selectRol.locator('option[value="encargado"]')).toHaveCount(0);

      await selectRol.selectOption("coordinador");
      await expect(page.getByLabel("Área", { exact: true })).toBeDisabled();
      await expect(page.getByText("Este rol vale para toda la organización.")).toBeVisible();

      await selectRol.selectOption("responsable_area");
      await expect(page.getByLabel("Área", { exact: true })).toBeEnabled();
    });

    test("exige elegir a la persona y asigna el rol", async ({ page }) => {
      await abrir(page, "?seccion=roles");
      await page.getByRole("button", { name: "Asignar rol" }).click();
      await expect(page.getByText("Elige a qué persona se le asigna el rol.")).toBeVisible();

      await page.getByLabel("Persona").selectOption({ label: "Líder de Implementación" });
      await page.getByLabel("Rol", { exact: true }).selectOption("coordinador");
      await page.getByRole("button", { name: "Asignar rol" }).click();

      const nueva = page.getByRole("table", { name: "Roles asignados" }).getByRole("row").filter({ hasText: "Líder de Implementación" }).filter({ hasText: "Coordinador" });
      await expect(nueva).toBeVisible();
      await expect(page.getByRole("table", { name: "Roles asignados" }).getByRole("row")).toHaveCount(6);
    });

    test("revocar pide confirmación y cancelar no revoca nada", async ({ page }) => {
      await abrir(page, "?seccion=roles");
      const fila = page.getByTestId("rol-assign-002");

      await fila.getByRole("button", { name: /Revocar el rol de delegado de protección de datos/ }).click();
      await expect(fila.getByRole("group", { name: /Confirmar la revocación/ })).toBeVisible();
      await fila.getByRole("button", { name: "Cancelar" }).click();
      await expect(fila).toBeVisible();
      await expect(page.getByRole("table", { name: "Roles asignados" }).getByRole("row")).toHaveCount(5);

      await fila.getByRole("button", { name: /Revocar el rol de delegado de protección de datos/ }).click();
      await fila.getByRole("button", { name: "Confirmar revocación" }).click();
      await expect(page.getByTestId("rol-assign-002")).toHaveCount(0);
      await expect(page.getByRole("table", { name: "Roles asignados" }).getByRole("row")).toHaveCount(4);
    });
  });

  test.describe("errores de negocio", () => {
    async function asignarCoordinador(page: Page): Promise<void> {
      await page.getByLabel("Persona").selectOption({ label: "Líder de Implementación" });
      await page.getByLabel("Rol", { exact: true }).selectOption("coordinador");
      await page.getByRole("button", { name: "Asignar rol" }).click();
    }

    test("TENANT_SIZE_NOT_CONFIGURED explica el motivo y lleva a la configuración", async ({ page }) => {
      await abrir(page, "?seccion=roles&fallo=tamano");
      await asignarCoordinador(page);

      const error = page.getByTestId("error-roles");
      await expect(error).toContainText("Primero configura el tamaño de la organización.");
      await expect(error).toContainText("Código: TENANT_SIZE_NOT_CONFIGURED");
      await expect(error).toContainText("Acción requerida: configure_tenant_size");

      await error.getByRole("button", { name: "Ir a la configuración" }).click();
      await expect(pestana(page, "Configuración")).toHaveAttribute("aria-selected", "true");
      await expect(page.getByRole("form", { name: "Configuración de la organización" })).toBeVisible();
      await expect(page.getByTestId("aviso-tamano")).toBeVisible();
    });

    test("SOD_VIOLATION se muestra con una explicación y sin botón de configuración", async ({ page }) => {
      await abrir(page, "?seccion=roles&fallo=sod");
      await asignarCoordinador(page);

      const error = page.getByTestId("error-roles");
      await expect(error).toContainText("rompe la separación de funciones");
      await expect(error).toContainText("Código: SOD_VIOLATION");
      await expect(error.getByRole("button", { name: "Ir a la configuración" })).toHaveCount(0);
    });

    test("MEMBER_ALREADY_EXISTS se explica en lenguaje claro", async ({ page }) => {
      await abrir(page, "?seccion=roles&fallo=duplicado");
      await asignarCoordinador(page);

      await expect(page.getByTestId("error-roles")).toContainText("Esa persona ya tiene esta asignación en la organización.");
    });

    test("no se puede revocar al último administrador y se explica qué hacer", async ({ page }) => {
      await abrir(page, "?seccion=roles&fallo=ultimo");
      const fila = page.getByTestId("rol-assign-001");

      await fila.getByRole("button", { name: /Revocar el rol de administrador de la organización/ }).click();
      await fila.getByRole("button", { name: "Confirmar revocación" }).click();

      const error = page.getByTestId("error-roles");
      await expect(error).toContainText("No se puede revocar al último administrador");
      await expect(error).toContainText("Código: LAST_ADMIN_CANNOT_BE_REVOKED");
      await expect(page.getByTestId("rol-assign-001")).toBeVisible();
    });

    test("si falla la carga de la organización se muestra el error y se puede reintentar", async ({ page }) => {
      await abrir(page, "?fallo=carga");

      await expect(page.getByTestId("error-carga")).toContainText("Código: ORG_UNAVAILABLE");
      await page.getByRole("button", { name: "Reintentar la carga" }).click();
      await expect(page.getByTestId("usuario-user-admin-01")).toBeVisible();
      await expect(page.getByTestId("error-carga")).toHaveCount(0);
    });
  });

  test.describe("configuración", () => {
    test("sin tamaño configurado avisa de la consecuencia y exige elegirlo", async ({ page }) => {
      await abrir(page, "?seccion=configuracion");

      await expect(page.getByTestId("aviso-tamano")).toContainText("aún no está configurado");
      await page.getByRole("button", { name: "Guardar configuración" }).click();
      await expect(page.getByText("Elige el tamaño de la organización.")).toBeVisible();
      await expect(page.getByTestId("configuracion-guardada")).toHaveCount(0);
    });

    test("guarda el tamaño y el sector, y el aviso desaparece", async ({ page }) => {
      await abrir(page, "?seccion=configuracion");

      await page.getByLabel("Tamaño de la organización").selectOption("mediana");
      await page.getByLabel("Sector").fill("Salud");
      await page.getByRole("button", { name: "Guardar configuración" }).click();

      await expect(page.getByTestId("configuracion-guardada")).toBeVisible();
      await expect(page.getByTestId("aviso-tamano")).toHaveCount(0);
      await expect(page.getByLabel("Tamaño de la organización")).toHaveValue("mediana");
      await expect(page.getByLabel("Sector")).toHaveValue("Salud");
    });

    test("con el tamaño ya configurado lo muestra y no avisa", async ({ page }) => {
      await abrir(page, "?seccion=configuracion&tamano=pequena");

      await expect(page.getByLabel("Tamaño de la organización")).toHaveValue("pequena");
      await expect(page.getByTestId("aviso-tamano")).toHaveCount(0);
    });

    test("ofrece los cuatro tamaños del vocabulario cerrado", async ({ page }) => {
      await abrir(page, "?seccion=configuracion");
      const opciones = await page.getByLabel("Tamaño de la organización").locator("option").allTextContents();
      expect(opciones).toEqual(["Sin configurar", "Microempresa", "Pequeña empresa", "Mediana empresa", "Corporativo"]);
    });

    test("si falla la carga de la configuración muestra el error y permite reintentar", async ({ page }) => {
      await abrir(page, "?seccion=configuracion&fallo=config");

      await expect(page.getByTestId("error-configuracion")).toContainText("Código: CONFIG_UNAVAILABLE");
      await page.getByRole("button", { name: "Reintentar la carga" }).click();
      await expect(page.getByRole("form", { name: "Configuración de la organización" })).toBeVisible();
    });
  });

  test("ninguna pantalla muestra tokens de gobernanza", async ({ page }) => {
    await abrir(page);
    for (const nombre of ["Usuarios", "Áreas", "Roles", "Configuración"]) {
      await irA(page, nombre);
      const texto = await page.locator("body").innerText();
      expect(texto, nombre).not.toMatch(/[¤¦]/);
    }
  });
});
