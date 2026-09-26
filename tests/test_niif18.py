import pytest
from fastapi.testclient import TestClient
from main import app
import io
import pandas as pd

client = TestClient(app)

def test_procesar_balance_niif18():
    # Crear un DataFrame dummy que simule el balance de prueba
    df = pd.DataFrame({
        "Codigo": ["1000", "4000", "5000", "6000", "5500"],
        "Nombre": ["Caja", "Ingresos por Ventas", "Gastos Operativos", "Gastos Financieros", "Impuestos"],
        "Saldo": [1000.0, -5000.0, 2000.0, 500.0, 300.0]
    })
    
    excel_io = io.BytesIO()
    df.to_excel(excel_io, index=False)
    excel_io.seek(0)
    
    files = {'file': ('balance.xlsx', excel_io, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
    
    response = client.post("/api/v1/niif18/procesar-balance", files=files)
    
    assert response.status_code == 200
    data = response.json()
    
    # Validar campos de respuesta
    assert "inferencia_columnas" in data
    assert "subtotales" in data
    assert "cuentas" in data
    
    # Validar clasificación NIIF 18
    subtotales = data["subtotales"]
    # Ventas = 5000, Gastos Op = -2000 -> Operativo = 3000
    # Financiero = -500
    # Impuestos = -300
    
    # Tolerancia por errores de float
    assert abs(subtotales["1_resultado_operativo"] - 3000.0) < 0.1
    assert abs(subtotales["2_resultado_antes_fin_imp"] - 3000.0) < 0.1
    assert abs(subtotales["3_resultado_periodo"] - 2200.0) < 0.1


BALANZA_DEMO = (
    "Cuenta,Descripcion,Saldo\n"
    "100000,Efectivo y equivalentes al efectivo,250000.00\n"
    "130000,Propiedades planta y equipo,1500000.00\n"
    "300000,Capital social,-1000000.00\n"
    "410000,Ingresos ordinarios por ventas,-850000.00\n"
    "420000,Ingresos por dividendos (Inversiones),-45000.00\n"
    "510000,Costo de ventas,350000.00\n"
    "520000,Gastos de administración,120000.00\n"
    "530000,Gastos de distribución,85000.00\n"
    "540000,Gastos por intereses financieros,35000.00\n"
    "550000,Gasto por impuesto a las ganancias,25000.00\n"
)


def _procesar_demo():
    files = {'file': ('demo.csv', BALANZA_DEMO.encode('utf-8'), 'text/csv')}
    resp = client.post("/api/v1/niif18/procesar-balance", files=files)
    assert resp.status_code == 200
    return resp.json()


def test_costos_e_impuestos_restan_del_resultado():
    sub = _procesar_demo()["subtotales"]
    assert abs(sub["1_resultado_operativo"] - 295000.0) < 0.01
    assert abs(sub["2_resultado_antes_fin_imp"] - 340000.0) < 0.01
    assert abs(sub["3_resultado_periodo"] - 280000.0) < 0.01


def test_recalcular_acepta_formato_api_y_devuelve_formato_api():
    cuentas = _procesar_demo()["cuentas"]
    cuentas[8]["categoria"] = "1. Operación (Ingresos / Gastos Operativos)"  # costos financieros a operación
    resp = client.post("/api/v1/niif18/recalcular-subtotales", json=cuentas)
    assert resp.status_code == 200
    data = resp.json()
    assert abs(data["subtotales"]["1_resultado_operativo"] - 260000.0) < 0.01
    assert {"cuenta", "categoria", "pl_neto"} <= set(data["cuentas"][0])


def test_diagnostico_detecta_balanza_descuadrada_y_recomienda():
    data = _procesar_demo()
    diag = data["diagnostico"]
    assert diag["cuadre"]["cuadra"] is False
    assert diag["estado"] == "REQUIERE_CORRECCION"
    assert any(h["codigo"] == "D01" for h in diag["hallazgos"])
    informe = client.post("/api/v1/niif18/informe", json=data["cuentas"]).json()
    assert informe["recomendaciones"]["acciones"][0]["prioridad"] == "P1"
    assert len(informe["recomendaciones"]["hoja_de_ruta"]) == 6
    assert informe["estado_resultados"][-1]["concepto"] == "RESULTADO DEL PERIODO"


def test_mpm_concilia_con_efecto_fiscal_y_exige_justificacion():
    ok = client.post("/api/v1/niif18/mpm", json={
        "nombre": "EBITDA Ajustado", "subtotal_base": "1. Resultado Operativo",
        "valor_base": 295000.0, "ajuste": 50000.0, "justificacion": "Costos no recurrentes"})
    assert ok.status_code == 200
    body = ok.json()
    assert body["total_mpm"] == 345000.0 and body["efecto_fiscal"] == -12500.0
    sin_justificacion = client.post("/api/v1/niif18/mpm", json={
        "nombre": "X", "subtotal_base": "1. Resultado Operativo", "valor_base": 1, "ajuste": 1, "justificacion": ""})
    assert sin_justificacion.status_code == 422


def test_exportaciones_excel_e_informe():
    import openpyxl
    data = _procesar_demo()
    payload = {"cuentas": data["cuentas"], "empresa": "Demo SA", "mpm": [{
        "nombre": "EBITDA", "subtotal_base": "1. Resultado Operativo", "valor_base": 1.0,
        "ajuste": 2.0, "efecto_fiscal": -0.5, "total_mpm": 3.0, "justificacion": "j"}]}
    xlsx = client.post("/api/v1/niif18/exportar/excel", json=payload)
    assert xlsx.status_code == 200
    hojas = openpyxl.load_workbook(io.BytesIO(xlsx.content)).sheetnames
    assert {"Estado_Resultados_NIIF18", "Trazabilidad_Mapeo", "Nota_MPM", "Diagnostico", "Recomendaciones", "Hoja_de_ruta"} <= set(hojas)
    md = client.post("/api/v1/niif18/exportar/informe", json=payload)
    assert md.status_code == 200 and "Demo SA" in md.text and "Hoja de ruta" in md.text


def test_balanza_demo_cuadra_y_exporta_pdf():
    from pathlib import Path
    demo = Path(__file__).resolve().parent.parent / "data" / "balanza_ejemplo_niif18.csv"
    resp = client.post("/api/v1/niif18/procesar-balance", files={"file": ("demo.csv", demo.read_bytes(), "text/csv")})
    data = resp.json()
    assert data["diagnostico"]["cuadre"]["cuadra"] is True
    assert abs(data["subtotales"]["3_resultado_periodo"] - 280000.0) < 0.01
    pdf = client.post("/api/v1/niif18/exportar/pdf", json={"cuentas": data["cuentas"], "empresa": "Demo SA"})
    assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF")
