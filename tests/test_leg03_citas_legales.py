# ¤regulation-code ¤seguridad ¤arbitro
"""LEG-03: el documento de citas legales cumple su estructura y su inventario coincide con el git grep."""
import importlib.util
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("verificar_citas_legales", RAIZ / "scripts" / "verificar_citas_legales.py")
vcl = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vcl)

URL = "https://www.spdp.gob.ec/ley.pdf"
TABLA = (
    "## Tabla de verificación\n\n| Dato | PRD | Artículo | Fuente | URL | Valor | Estado |\n|---|---|---|---|---|---|---|\n"
    "| Plazo | §5 | LOPDP art. 43 | LOPDP | {url} | 5 días | {estado} |\n\n"
)
INVENTARIO = "## Inventario de citas de la interfaz\n\n| Archivo | Cita | Norma | Correcta | Estado |\n|---|---|---|---|---|\n{filas}\n"


def _doc(filas: str, url: str = URL, estado: str = "verificado") -> str:
    return TABLA.format(url=url, estado=estado) + INVENTARIO.format(filas=filas)


def test_el_documento_real_cumple_y_coincide_con_el_git_grep():
    texto = vcl.DOCUMENTO.read_text(encoding="utf-8")
    esperados = vcl.pares_esperados()
    assert esperados, "el git grep de la ficha no encontró citas"
    assert vcl.errores(texto, esperados) == []


def test_normaliza_las_formas_de_citar():
    assert vcl.normalizar("Arts. 21") == vcl.normalizar("Artículo 21") == vcl.normalizar("Art.21") == "Art. 21"
    assert vcl.normalizar("SLA 72") == "SLA 72"


def test_una_cita_nueva_sin_fila_falla():
    esperados = {("a.ts", "Art. 7"), ("a.ts", "Art. 8")}
    fallos = vcl.errores(_doc("| `a.ts` | Art. 7 | LOPDP | LOPDP, art. 7 | verificado |"), esperados)
    assert any("falta la fila" in f and "Art. 8" in f for f in fallos)


def test_una_fila_que_el_grep_ya_no_encuentra_falla():
    fallos = vcl.errores(_doc("| `a.ts` | Art. 7 | LOPDP | LOPDP, art. 7 | verificado |"), set())
    assert any("sobra la fila" in f for f in fallos)


def test_url_no_oficial_y_estado_desconocido_fallan():
    fila = "| `a.ts` | Art. 7 | LOPDP | LOPDP, art. 7 | verificado |"
    assert any("URL no es oficial" in f for f in vcl.errores(_doc(fila, url="https://www.lexis.com.ec/x"), {("a.ts", "Art. 7")}))
    assert any("estado" in f for f in vcl.errores(_doc(fila, estado="dudoso"), {("a.ts", "Art. 7")}))


def test_inventario_sin_norma_o_estado_valido_falla():
    fallos = vcl.errores(_doc("| `a.ts` | Art. 7 |  | LOPDP, art. 7 | quizá |"), {("a.ts", "Art. 7")})
    assert any("falta la norma" in f for f in fallos)
    assert any("estado «quizá»" in f for f in fallos)
