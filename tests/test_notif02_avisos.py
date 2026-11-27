# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤notificaciones ¤arbitro
"""NOTIF-02: avisos y recordatorios de versiones por revisar. Textos (R2, R3) y calendario sin base de datos.

Cada prueba documenta su mutación: el cambio en el código que la pondría en rojo.
"""
from datetime import date, datetime, timezone

import pytest

from features.notificaciones.domain import avisos as av

PROHIBIDAS = ["undefined", "null", "None", "{", "}", ", ,", "  ", "conforme", "cumple", "garantiza", "certificado", "legal"]


def _limpio(texto: str) -> None:
    for p in PROHIBIDAS:
        assert p not in texto, (p, texto)


def test_fecha_larga_en_espanol_sin_cero():
    assert av.fecha_larga(date(2026, 12, 5)) == "5 de diciembre de 2026"
    assert av.fecha_larga(date(2027, 1, 31)) == "31 de enero de 2027"


def test_hoy_se_calcula_en_hora_de_ecuador():
    # 03:00 UTC del 6 es todavía el 5 a las 22:00 en Ecuador (UTC-5).
    assert av.hoy_ecuador(datetime(2026, 12, 6, 3, 0, tzinfo=timezone.utc)) == date(2026, 12, 5)


def test_titulo():
    assert av.titulo("Política de privacidad") == "Versión por revisar: Política de privacidad"
    assert av.ENLACE_TEXTO == "Revisar la versión"


HOY = date(2026, 11, 25)


@pytest.mark.parametrize("vigencia,esperado", [
    (date(2026, 12, 5), "Motivo del cambio: Resolución 1, artículo 4, que entra en vigencia el 5 de diciembre de 2026."),
    (HOY, "Motivo del cambio: Resolución 1, artículo 4, que entra en vigencia hoy."),
    (date(2026, 11, 1), "Motivo del cambio: Resolución 1, artículo 4, que entró en vigencia el 1 de noviembre de 2026."),
    (None, "Motivo del cambio: Resolución 1, artículo 4. La norma no indica fecha de vigencia."),
])
def test_motivo_por_resolucion(vigencia, esperado):
    t = av.motivo(origen="resolucion", norma="Resolución 1", articulo="artículo 4", vigencia=vigencia, hoy=HOY)
    assert t == esperado
    _limpio(t)


def test_sin_articulo_se_quita_la_coma_entera():
    """Mutación m5: dejar «, ,» al faltar el artículo da rojo."""
    for articulo in (None, "", "  "):
        t = av.motivo(origen="resolucion", norma="Resolución 1", articulo=articulo, vigencia=date(2026, 12, 5), hoy=HOY)
        assert t == "Motivo del cambio: Resolución 1, que entra en vigencia el 5 de diciembre de 2026."
        _limpio(t)
    t = av.motivo(origen="resolucion", norma="Resolución 1", articulo=None, vigencia=None, hoy=HOY)
    assert t == "Motivo del cambio: Resolución 1. La norma no indica fecha de vigencia."


def test_peticion_con_y_sin_texto():
    assert av.motivo(origen="peticion", nombre="Ana", texto="Actualizar el plazo", hoy=HOY) == \
        "Motivo del cambio: petición de Ana: «Actualizar el plazo»."
    for vacio in (None, "", "   "):
        assert av.motivo(origen="peticion", nombre="Ana", texto=vacio, hoy=HOY) == "Motivo del cambio: petición de Ana."


def test_peticion_larga_se_corta_a_200_y_va_como_texto_plano():
    """Mutación m7: una petición de 300 caracteres sin cortar da rojo."""
    t = av.motivo(origen="peticion", nombre="Ana", texto="x" * 300, hoy=HOY)
    assert t == "Motivo del cambio: petición de Ana: «" + "x" * 200 + "…»."
    justo = av.motivo(origen="peticion", nombre="Ana", texto="y" * 200, hoy=HOY)
    assert "…" not in justo


def test_peticion_texto_plano_sin_formato_ni_enlaces():
    t = av.motivo(origen="peticion", nombre="Ana", texto="**negrita** [x](http://a.b)\n# t", hoy=HOY)
    assert "**" not in t and "](" not in t and "\n" not in t and "  " not in t


# ------------------------------------------------------------ R3
def test_recordatorios_con_fecha_futura():
    assert av.programa(date(2026, 11, 25), date(2026, 12, 5)) == [date(2026, 11, 28), date(2026, 12, 4)]
    assert av.programa(date(2026, 11, 25), date(2026, 11, 30)) == [date(2026, 11, 29)]


def test_recordatorios_sin_fecha_pasada_o_peticion_a_5_y_10_dias():
    """Mutación m2: un tercer recordatorio sin fecha da rojo."""
    esperado = [date(2026, 11, 30), date(2026, 12, 5)]
    assert av.programa(date(2026, 11, 25), None) == esperado
    assert av.programa(date(2026, 11, 25), date(2026, 11, 1)) == esperado
    assert len(av.programa(date(2026, 11, 25), None)) == 2


@pytest.mark.parametrize("hoy,esperado", [
    (date(2026, 11, 25), "La norma que motiva el cambio entra en vigencia el 2 de diciembre de 2026 (faltan 7 días)."),
    (date(2026, 12, 1), "La norma que motiva el cambio entra en vigencia el 2 de diciembre de 2026 (falta 1 día)."),
])
def test_texto_recordatorio_por_vigencia(hoy, esperado):
    """Mutación m6: «faltan 1 días» da rojo."""
    t = av.recordatorio(vigencia=date(2026, 12, 2), hoy=hoy)
    assert t == esperado
    _limpio(t)


def test_texto_recordatorio_el_dia_de_la_vigencia():
    assert av.recordatorio(vigencia=HOY, hoy=HOY) == "La norma que motiva el cambio entra en vigencia hoy."


@pytest.mark.parametrize("n,esperado", [
    (5, "Sigue sin revisión técnica desde hace 5 días."), (1, "Sigue sin revisión técnica desde hace 1 día."),
])
def test_texto_recordatorio_sin_vigencia(n, esperado):
    assert av.recordatorio(vigencia=None, hoy=date(2026, 11, 25), creado=date(2026, 11, 25 - n)) == esperado


def test_fin_del_aviso():
    assert av.TEXTO_FIN == "Ya no está pendiente"


def test_las_palabras_prohibidas_no_estan_en_los_textos_fijos():
    for t in (av.ENLACE_TEXTO, av.TEXTO_FIN, av.titulo("Plantilla")):
        _limpio(t)


def test_peticion_sin_nombre_no_deja_huecos():
    t = av.motivo(origen="peticion", nombre=None, texto=None, hoy=HOY)
    assert t == "Motivo del cambio: petición."
    _limpio(t)
