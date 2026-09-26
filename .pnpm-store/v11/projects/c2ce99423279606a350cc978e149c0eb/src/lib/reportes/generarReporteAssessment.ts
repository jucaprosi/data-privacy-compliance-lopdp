/**
 * Generador del Reporte de Assessment de Madurez SGPDP.
 * Produce un documento HTML autocontenido, descargable e imprimible a PDF
 * desde el propio navegador (Ctrl+P → Guardar como PDF).
 */
import type { CompanyData, ResultadoAssessment } from "@/store/useAuditStore";

function escapeHtml(texto: string): string {
  return texto
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function filaDimension(dim: ResultadoAssessment["dimensiones"][number]): string {
  return `
    <tr>
      <td>${escapeHtml(dim.id)}</td>
      <td>${escapeHtml(dim.nombre)}</td>
      <td class="num">${dim.peso.toFixed(2)}</td>
      <td class="num">${dim.itemsEvaluados}/${dim.itemsAplicables}</td>
      <td class="num">${dim.itemsEvaluados > 0 ? `${dim.score.toFixed(1)}%` : "—"}</td>
      <td class="num">${dim.itemsEvaluados > 0 ? `N${dim.nivel} · ${dim.nivelEtiqueta}` : "No evaluada"}</td>
      <td class="num">${dim.brechasCriticas}</td>
      <td class="num">${dim.brechasAltas}</td>
      <td>${escapeHtml(dim.observacion || "—")}</td>
    </tr>`;
}

function filaBrecha(brecha: ResultadoAssessment["brechas"][number]): string {
  return `
    <tr class="${brecha.severidad === "Crítico" ? "critico" : brecha.severidad === "Alto" ? "alto" : ""}">
      <td>P${brecha.preguntaId}</td>
      <td>${escapeHtml(brecha.control)}</td>
      <td>${escapeHtml(brecha.dimensionId)} · ${escapeHtml(brecha.dimensionNombre)}</td>
      <td class="num">${brecha.nivelEfectivo}</td>
      <td class="num">${brecha.riesgo}</td>
      <td class="num">${escapeHtml(brecha.severidad)}</td>
      <td class="num">${brecha.esEstructural ? "Sí" : "No"}</td>
    </tr>`;
}

export function generarHtmlReporteAssessment(
  resultado: ResultadoAssessment,
  verificado: ResultadoAssessment,
  companyData: CompanyData
): string {
  const fecha = new Date().toLocaleString("es-EC", {
    dateStyle: "long",
    timeStyle: "short",
  });

  return `<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8" />
<title>Reporte de Assessment SGPDP · ${escapeHtml(companyData.razonSocial)}</title>
<style>
  * { box-sizing: border-box; }
  body { font-family: "Segoe UI", Arial, sans-serif; color: #1a1a1a; margin: 32px; font-size: 13px; }
  h1 { font-size: 20px; margin-bottom: 2px; color: #4a1a7a; }
  h2 { font-size: 14px; margin-top: 28px; margin-bottom: 8px; color: #4a1a7a; border-bottom: 2px solid #9a3bf1; padding-bottom: 4px; }
  .subtitulo { color: #555; margin-bottom: 18px; font-size: 12px; }
  .meta { display: flex; gap: 24px; flex-wrap: wrap; margin: 12px 0 20px; }
  .meta div { background: #f5f0fa; border: 1px solid #e0d0f5; border-radius: 8px; padding: 10px 14px; min-width: 150px; }
  .meta span.label { display: block; font-size: 10px; text-transform: uppercase; color: #7a4ab5; font-weight: 700; letter-spacing: .04em; }
  .meta span.valor { display: block; font-size: 18px; font-weight: 800; margin-top: 2px; }
  table { width: 100%; border-collapse: collapse; margin-top: 6px; }
  th, td { border: 1px solid #ddd; padding: 6px 8px; font-size: 11px; text-align: left; vertical-align: top; }
  th { background: #f5f0fa; text-transform: uppercase; font-size: 9px; letter-spacing: .03em; color: #555; }
  td.num { text-align: right; white-space: nowrap; }
  tr.critico { background: #ffecec; }
  tr.alto { background: #fff6e5; }
  footer { margin-top: 32px; font-size: 10px; color: #888; border-top: 1px solid #ddd; padding-top: 8px; }
  @media print { body { margin: 12mm; } h2 { break-after: avoid; } tr { break-inside: avoid; } }
</style>
</head>
<body>
  <h1>Reporte de Assessment de Madurez SGPDP</h1>
  <p class="subtitulo">${escapeHtml(companyData.razonSocial)} · ${escapeHtml(companyData.sector)} · Generado el ${fecha}</p>

  <div class="meta">
    <div><span class="label">Score Ponderado</span><span class="valor">${resultado.scorePonderado.toFixed(1)}%</span></div>
    <div><span class="label">Nivel Ajustado</span><span class="valor">N${resultado.nivelAjustado} · ${escapeHtml(resultado.nivelAjustadoEtiqueta)}</span></div>
    <div><span class="label">Cobertura</span><span class="valor">${resultado.coberturaPorcentaje.toFixed(1)}%</span></div>
    <div><span class="label">Verificado con Evidencia</span><span class="valor">${verificado.scorePonderado.toFixed(1)}%</span></div>
    <div><span class="label">Brechas Críticas</span><span class="valor">${resultado.brechasCriticas}</span></div>
    <div><span class="label">Brechas Altas</span><span class="valor">${resultado.brechasAltas}</span></div>
  </div>

  <h2>Resultados por Dimensión</h2>
  <table>
    <thead>
      <tr>
        <th>ID</th><th>Dimensión</th><th>Peso</th><th>Evaluados</th><th>Score</th>
        <th>Nivel</th><th>Crít.</th><th>Alto</th><th>Observación</th>
      </tr>
    </thead>
    <tbody>${resultado.dimensiones.map(filaDimension).join("")}</tbody>
  </table>

  <h2>Registro de Brechas (${resultado.brechas.length})</h2>
  <table>
    <thead>
      <tr>
        <th>Control</th><th>Descripción</th><th>Dimensión</th><th>Nivel Ef.</th>
        <th>Riesgo</th><th>Severidad</th><th>Estructural</th>
      </tr>
    </thead>
    <tbody>
      ${
        resultado.brechas.length > 0
          ? resultado.brechas.map(filaBrecha).join("")
          : `<tr><td colspan="7">Sin brechas registradas sobre los controles evaluados.</td></tr>`
      }
    </tbody>
  </table>

  <footer>JUBYS · Plataforma LOPDP 360 — Reporte de Assessment de Madurez SGPDP. Documento de trabajo interno, generado automáticamente a partir del estado del diagnóstico.</footer>
</body>
</html>`;
}

export function descargarReporteAssessment(
  resultado: ResultadoAssessment,
  verificado: ResultadoAssessment,
  companyData: CompanyData
): void {
  const html = generarHtmlReporteAssessment(resultado, verificado, companyData);
  const blob = new Blob([html], { type: "text/html;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const marcaTiempo = new Date().toISOString().slice(0, 10);
  const a = document.createElement("a");
  a.href = url;
  a.download = `reporte-assessment-sgpdp-${marcaTiempo}.html`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
