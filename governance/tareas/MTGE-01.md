+++
id = "MTGE-01"
titulo = "Cálculo de gran escala conforme al texto vinculante de la Res. SPDP-SPD-2026-0005-R"
ola = "D"
estado = "bloqueada"
sala = "riesgos_mtge"
depende_de = []
propiedad = ["features/riesgos_mtge/services/mtge_calculator.py", "features/riesgos_mtge/domain/models.py", "tests/test_mtge_resolucion_0005.py"]
arbitro = "pytest tests/test_mtge_resolucion_0005.py (un caso por supuesto directo y por ejemplo de la norma) + suite completa; prueba de mutación documentada"
rastros = ["¤mtge-granescala"]
+++

# MTGE-01 · Gran escala según la norma

**Bloqueada:** falta el texto oficial de la Res. SPDP-SPD-2026-0005-R (Norma General sobre el Tratamiento de Datos Personales a Gran Escala). Se desbloquea cuando el propietario lo deje en `data/`.

**Hallazgo (2026-10-23).** `mtge_calculator.py` usa una escala propia de 100 puntos, cuatro variables con pesos sin fuente y dos supuestos directos citando un «art. 12». La matriz MTGE del equipo consultor (SALUDATA) y varias reseñas jurídicas describen seis variables con puntajes de 0,5 a 4, umbral de **6 puntos o más** y supuestos de calificación directa en el **art. 14** (14.1 salud e historias clínicas a 14.7 courier). Las reseñas no coinciden entre sí: **nada de esto se implementa sin leer el texto vinculante.**

## Entrega (al desbloquearse)
- Variables, puntajes, umbral y supuestos directos exactamente como la resolución, cada constante con su artículo en un comentario.
- El resultado indica el camino (calificación directa con su numeral, o puntaje) y sus efectos (DPO, EIPD, RAT, medidas reforzadas) según la norma.
- Pruebas: un caso por supuesto directo y por ejemplo de la norma; bordes del umbral.
- **Prueba de mutación documentada:** cambiar el umbral y comprobar que una prueba de borde falla.

## Hecho cuando
- Su árbitro pasa, la suite completa pasa y los checks del PR están en verde. No modificó ningún archivo fuera de su propiedad.
