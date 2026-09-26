from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO
import datetime

def exportar_pdf_diagnostico(tenant_id: str, id_diagnostico: str, normativa: str = "PI") -> bytes:
    """Genera un PDF inmutable (WORM) para un informe de diagnóstico."""
    buffer = BytesIO()
    
    # Crear el objeto PDF, usando BytesIO como el 'archivo'.
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    es_niif = (normativa == "NIIF")
    titulo_informe = "Informe de Auditoría NIIF 18" if es_niif else "Informe de Diagnóstico LOPDP"
    dictamen_texto = "Este documento representa un dictamen inmutable de cumplimiento financiero (IFRS 18)." if es_niif else "Este documento representa un dictamen inmutable de cumplimiento LOPDP."
    snapshot_normativo = "IFRS-18-2027" if es_niif else "LOPDP-2026-v1.0"

    # Dibujar contenido principal
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, height - 80, f"{titulo_informe}: {id_diagnostico}")
    
    c.setFont("Helvetica", 12)
    c.drawString(100, height - 120, f"Tenant ID: {tenant_id}")
    c.drawString(100, height - 140, dictamen_texto)
    
    # Pie de página: metadato de versión normativa y fecha UTC
    fecha_utc = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    footer_text = f"Snapshot Normativo: {snapshot_normativo} | Fecha Certificación (UTC): {fecha_utc}"
    
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(100, 50, footer_text)

    # Cerrar el objeto PDF
    c.showPage()
    c.save()

    # Obtener el valor de BytesIO y retornar bytes
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes
