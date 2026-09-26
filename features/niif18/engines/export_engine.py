"""
Reportes NIIF 18: paquete Excel de cierre e informe de diagnóstico.
[¤niif18-reportes]
"""
import io

import pandas as pd
from fpdf import FPDF

from features.niif18.engines.financials_engine import estructurar_estado_resultados

_ETIQUETA_MPM = {
    "nombre": "Métrica", "subtotal_base": "Anclaje NIIF 18", "valor_base": "Base NIIF 18",
    "ajuste": "Ajuste", "efecto_fiscal": "Efecto fiscal", "total_mpm": "Total MPM",
    "justificacion": "Justificación",
}


def _hojas_analiticas(diagnostico: dict | None, recomendaciones: dict | None) -> dict[str, pd.DataFrame]:
    hojas: dict[str, pd.DataFrame] = {}
    if diagnostico:
        hojas["Diagnostico"] = pd.DataFrame([
            {"Código": h["codigo"], "Severidad": h["severidad"], "Hallazgo": h["titulo"],
             "Detalle": h["detalle"], "Cuentas": ", ".join(h["cuentas"]), "Referencia": h["referencia"]}
            for h in diagnostico["hallazgos"]
        ], columns=["Código", "Severidad", "Hallazgo", "Detalle", "Cuentas", "Referencia"])
    if recomendaciones:
        hojas["Recomendaciones"] = pd.DataFrame([
            {"Prioridad": a["prioridad"], "Tipo": a["tipo"], "Acción": a["accion"], "Fundamento": a["fundamento"]}
            for a in recomendaciones["acciones"]
        ], columns=["Prioridad", "Tipo", "Acción", "Fundamento"])
        hojas["Hoja_de_ruta"] = pd.DataFrame([
            {"Fase": r["fase"], "Descripción": r["descripcion"], "Referencia": r["referencia"]}
            for r in recomendaciones["hoja_de_ruta"]
        ])
    return hojas


def generar_excel_estado_resultados(df: pd.DataFrame, mpm_registros: list[dict] | None = None,
                                    diagnostico: dict | None = None,
                                    recomendaciones: dict | None = None) -> bytes:
    """Paquete Excel en memoria: estado de resultados, trazabilidad, MPM, diagnóstico y hoja de ruta."""
    salida = io.BytesIO()
    estado = pd.DataFrame(estructurar_estado_resultados(df)).rename(
        columns={"concepto": "Concepto", "monto": "Monto", "tipo": "Tipo"})
    with pd.ExcelWriter(salida, engine='openpyxl') as writer:
        estado.to_excel(writer, index=False, sheet_name='Estado_Resultados_NIIF18')
        df.to_excel(writer, index=False, sheet_name='Trazabilidad_Mapeo')
        if mpm_registros:
            pd.DataFrame(mpm_registros).rename(columns=_ETIQUETA_MPM).to_excel(
                writer, index=False, sheet_name='Nota_MPM')
        for nombre, hoja in _hojas_analiticas(diagnostico, recomendaciones).items():
            hoja.to_excel(writer, index=False, sheet_name=nombre)
        for ws in writer.book.worksheets:
            for col in ws.columns:
                ancho = max(len(str(c.value)) if c.value is not None else 0 for c in col)
                ws.column_dimensions[col[0].column_letter].width = min(max(ancho + 2, 12), 70)
    return salida.getvalue()


def _pct(valor: float | None) -> str:
    return "n/d" if valor is None else f"{valor:.1%}"


def generar_informe_markdown(estado: list[dict], diagnostico: dict, recomendaciones: dict,
                             indicadores: dict, mpm_registros: list[dict] | None = None,
                             empresa: str = "") -> str:
    """Informe de implementación NIIF 18 legible para la gerencia y la firma auditora."""
    sufijo = f" · {empresa}" if empresa else ""
    cuadre = diagnostico["cuadre"]
    estado_cuadre = "correcto" if cuadre["cuadra"] else f"DESCUADRADA por {cuadre['diferencia']:,.2f}"
    L = [f"# Informe de diagnóstico NIIF 18{sufijo}", "",
         f"**Estado:** {diagnostico['estado'].replace('_', ' ').title()} · **Puntaje:** {diagnostico['puntaje']}/100 · "
         f"**Cuentas analizadas:** {diagnostico['total_cuentas']}", "",
         "## Estado de resultados estructurado", "", "| Concepto | Monto |", "|---|---:|"]
    for f in estado:
        if f["tipo"] == "subtotal":
            L.append(f"| **{f['concepto']}** | {f['monto']:,.2f} |")
        elif f["tipo"] == "categoria":
            L.append(f"| {f['concepto']} | {f['monto']:,.2f} |")
    L += ["", "## Indicadores", "",
          f"- Margen operativo: {_pct(indicadores.get('margen_operativo'))}",
          f"- Margen neto: {_pct(indicadores.get('margen_neto'))}",
          f"- Tasa efectiva de impuestos: {_pct(indicadores.get('tasa_efectiva_impuestos'))}",
          f"- EBITDA referencial: {indicadores.get('ebitda_referencial', 0):,.2f}", "",
          "## Diagnóstico", "", f"Cuadre de la balanza: {estado_cuadre}.", ""]
    for h in diagnostico["hallazgos"]:
        cuentas = f" (cuentas: {', '.join(h['cuentas'])})" if h["cuentas"] else ""
        L.append(f"- **[{h['severidad']}] {h['codigo']} · {h['titulo']}:** {h['detalle']}{cuentas}")
    if not diagnostico["hallazgos"]:
        L.append("- Sin hallazgos.")
    if mpm_registros:
        L += ["", "## Nota de MPM", "",
              "| Métrica | Anclaje | Base | Ajuste | Efecto fiscal | Total |", "|---|---|---:|---:|---:|---:|"]
        for m in mpm_registros:
            L.append(f"| {m['nombre']} | {m['subtotal_base']} | {m['valor_base']:,.2f} | {m['ajuste']:,.2f} | "
                     f"{m['efecto_fiscal']:,.2f} | {m['total_mpm']:,.2f} |")
    L += ["", "## Recomendaciones priorizadas", ""]
    for a in recomendaciones["acciones"]:
        L.append(f"- **{a['prioridad']} · {a['tipo']}:** {a['accion']} _({a['fundamento']})_")
    L += ["", "## Hoja de ruta de implementación", ""]
    for r in recomendaciones["hoja_de_ruta"]:
        L.append(f"1. **{r['fase']}** — {r['descripcion']} _({r['referencia']})_")
    return "\n".join(L) + "\n"


def _latin1(texto: str) -> str:
    """Las fuentes base del PDF solo admiten latin-1; se sustituye lo demás."""
    for origen, destino in (("—", "-"), ("–", "-"), ("“", '"'), ("”", '"'), ("’", "'")):
        texto = texto.replace(origen, destino)
    return texto.encode("latin-1", "replace").decode("latin-1")


def generar_informe_pdf(estado: list[dict], diagnostico: dict, recomendaciones: dict,
                        indicadores: dict, mpm_registros: list[dict] | None = None,
                        empresa: str = "") -> bytes:
    """Informe de diagnóstico y plan de implementación NIIF 18 en PDF."""
    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    ancho = pdf.w - pdf.l_margin - pdf.r_margin

    def titulo(texto: str, tam: int = 13) -> None:
        pdf.ln(3)
        pdf.set_font("Helvetica", "B", tam)
        pdf.multi_cell(ancho, 7, _latin1(texto), new_x="LMARGIN", new_y="NEXT")

    def parrafo(texto: str, negrita: bool = False) -> None:
        pdf.set_font("Helvetica", "B" if negrita else "", 9)
        pdf.multi_cell(ancho, 5, _latin1(texto), new_x="LMARGIN", new_y="NEXT")

    titulo(f"Informe de diagnostico NIIF 18{' - ' + empresa if empresa else ''}", 16)
    cuadre = diagnostico["cuadre"]
    estado_cuadre = "cuadrada" if cuadre["cuadra"] else f"descuadrada por {cuadre['diferencia']:,.2f}"
    parrafo(f"Estado: {diagnostico['estado'].replace('_', ' ').title()} | Puntaje: {diagnostico['puntaje']}/100 | "
            f"Cuentas: {diagnostico['total_cuentas']} | Balanza: {estado_cuadre}")

    titulo("Estado de resultados estructurado")
    for f in estado:
        if f["tipo"] == "cuenta":
            continue
        pdf.set_font("Helvetica", "B" if f["tipo"] == "subtotal" else "", 9)
        pdf.cell(ancho * 0.72, 5.5, _latin1(f["concepto"])[:70])
        pdf.cell(ancho * 0.28, 5.5, f"{f['monto']:,.2f}", align="R", new_x="LMARGIN", new_y="NEXT")

    titulo("Indicadores")
    parrafo(f"Margen operativo: {_pct(indicadores.get('margen_operativo'))} | Margen neto: {_pct(indicadores.get('margen_neto'))} | "
            f"Tasa efectiva: {_pct(indicadores.get('tasa_efectiva_impuestos'))} | "
            f"EBITDA referencial: {indicadores.get('ebitda_referencial', 0):,.2f}")

    titulo("Hallazgos")
    for h in diagnostico["hallazgos"]:
        parrafo(f"[{h['severidad']}] {h['codigo']} - {h['titulo']}", negrita=True)
        parrafo(h["detalle"] + (f" Cuentas: {', '.join(h['cuentas'])}." if h["cuentas"] else ""))
    if not diagnostico["hallazgos"]:
        parrafo("Sin hallazgos.")

    if mpm_registros:
        titulo("Nota de MPM")
        for m in mpm_registros:
            parrafo(f"{m['nombre']} ({m['subtotal_base']}): base {m['valor_base']:,.2f}, ajuste {m['ajuste']:,.2f}, "
                    f"efecto fiscal {m['efecto_fiscal']:,.2f}, total {m['total_mpm']:,.2f}. {m['justificacion']}")

    titulo("Recomendaciones priorizadas")
    for a in recomendaciones["acciones"]:
        parrafo(f"{a['prioridad']} - {a['tipo']}: {a['accion']} ({a['fundamento']})")
    titulo("Hoja de ruta de implementacion")
    for r in recomendaciones["hoja_de_ruta"]:
        parrafo(r["fase"], negrita=True)
        parrafo(f"{r['descripcion']} ({r['referencia']})")
    return bytes(pdf.output())
