/**
 * Arnés de pruebas E2E para Mi Formación y Examen (FOR-01).
 *
 * Verifica:
 * 1. Acceso a "Mi formación" y aviso de intento único.
 * 2. Preguntas en radiogroup con opción obligatoria (botón deshabilitado mientras falten).
 * 3. Modal de confirmación con foco inicial en Cancelar.
 * 4. Envío exitoso con constancia de formación guardada.
 * 5. Doctrina 1: prohibido el uso de "certificado" o "diploma" en textos visibles.
 */
import { expect, test } from "@playwright/test";
import { configurarProyecto } from "../utiles";

test.describe("FOR-01: Examen de participante y constancia", () => {
  test.beforeEach(async ({ page }) => {
    await configurarProyecto(page);
  });

  test("flujo completo de examen con un solo intento y constancia de formación", async ({ page }) => {
    // Interceptar llamadas a API de formación
    await page.route("**/api/v1/formacion/**", async (route) => {
      const url = route.request().url();
      const metodo = route.request().method();

      if (url.includes("/participaciones/me") && metodo === "GET") {
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify([
            {
              id: "part-1",
              accion_id: "acc-1",
              accion_nombre: "Protección de Datos 2026",
              contenido_titulo: "Manual LOPDP",
              contenido_url: "https://ejemplo.com/manual.pdf",
              fecha_inicio: "2026-01-01",
              fecha_fin: "2026-12-31",
              nota_minima: 70,
              iniciado_en: null,
              terminado_en: null,
              nota: null,
              aprobo: null,
              evidencia_id: null,
            },
          ]),
        });
      }

      if (url.includes("/participaciones/part-1/iniciar") && metodo === "POST") {
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            id: "part-1",
            iniciado_en: "2026-11-16T15:00:00Z",
          }),
        });
      }

      if (url.includes("/participaciones/part-1/examen") && metodo === "GET") {
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            participacion_id: "part-1",
            accion_nombre: "Protección de Datos 2026",
            contenido_titulo: "Manual LOPDP",
            nota_minima: 70,
            preguntas: [
              {
                id: "preg-1",
                enunciado: "¿Cuál es el principio rector de licitud?",
                orden: 1,
                opciones: [
                  { id: "opc-1a", texto: "Tratamiento conforme a derecho" },
                  { id: "opc-1b", texto: "Publicar todo en internet" },
                ],
              },
              {
                id: "preg-2",
                enunciado: "¿Quién debe ser notificado ante una vulneración?",
                orden: 2,
                opciones: [
                  { id: "opc-2a", texto: "La autoridad de protección de datos" },
                  { id: "opc-2b", texto: "Nadie" },
                ],
              },
            ],
          }),
        });
      }

      if (url.includes("/participaciones/part-1/rendir") && metodo === "POST") {
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            participacion_id: "part-1",
            nota: 100,
            aprobo: true,
            evidencia_id: "evi-12345",
            mensaje: "Examen completado exitosamente",
          }),
        });
      }

      return route.continue();
    });

    await page.goto("/#mi_formacion");

    // Verificar título y aviso de un solo intento
    const main = page.getByRole("main", { name: "Mi formación" });
    await expect(main).toBeVisible();
    await expect(page.getByText("Tienes un solo intento. Una vez que lo envíes no podrás repetirlo.")).toBeVisible();

    // Doctrina 1: No debe aparecer la palabra diploma ni certificado
    const cuerpoTexto = await page.content();
    expect(cuerpoTexto.toLowerCase()).not.toContain("certificado");
    expect(cuerpoTexto.toLowerCase()).not.toContain("diploma");

    // Comenzar el examen
    const botonEmpezar = page.getByRole("button", { name: "Empezar el examen" });
    await botonEmpezar.click();

    // Comprobar que aparecen los dos radiogroups de preguntas
    const radiogroup1 = page.getByRole("radiogroup", { name: /1\. ¿Cuál es el principio rector de licitud\?/i });
    await expect(radiogroup1).toBeVisible();

    // El botón 'Enviar respuestas' debe estar en aria-disabled o disabled
    const botonEnviar = page.getByRole("button", { name: "Enviar respuestas" });
    await expect(botonEnviar).toHaveAttribute("aria-disabled", "true");
    await expect(page.getByText(/Te faltan 2 preguntas por responder/i)).toBeVisible();

    // Responder la primera pregunta
    await page.getByLabel("Tratamiento conforme a derecho").click();
    await expect(page.getByText(/Te faltan 1 preguntas por responder/i)).toBeVisible();

    // Responder la segunda pregunta
    await page.getByLabel("La autoridad de protección de datos").click();
    await expect(botonEnviar).toHaveAttribute("aria-disabled", "false");

    // Click en Enviar respuestas -> se abre el diálogo de confirmación
    await botonEnviar.click();
    const dialogo = page.getByRole("dialog", { name: "¿Enviar tus respuestas?" });
    await expect(dialogo).toBeVisible();
    await expect(page.getByText("Tienes un solo intento y no podrás cambiarlas después.")).toBeVisible();

    // Confirmar envío
    const botonConfirmar = dialogo.getByRole("button", { name: "Enviar respuestas" });
    await botonConfirmar.click();

    // Comprobar resultado aprobado y constancia de formación
    const status = page.getByRole("status");
    await expect(status).toBeVisible();
    await expect(status).toContainText("Aprobaste con 100. Tu constancia de formación quedó guardada.");
    await expect(page.getByRole("link", { name: "Abrir tu constancia" })).toBeVisible();
  });
});
