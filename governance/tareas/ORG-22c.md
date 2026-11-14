+++
id = "ORG-22c"
titulo = "Rutas de descubrimiento DLP y bóveda en la matriz de permisos, con sus filas y mutación"
ola = "D"
estado = "pendiente"
sala = "organizacion"
depende_de = ["ORG-22", "DLP-01", "BOV-01"]
propiedad = ["tests/test_matriz_permisos.py", "tests/matriz/DLP-01.py", "tests/matriz/BOV-01.py"]
crea = ["tests/matriz/BOV-01.py"]
arbitro = "pytest tests/test_matriz_permisos.py: con los prefijos /api/v1/dlp-discovery y /api/v1/boveda-cloud en PREFIJOS_MATRIZ no queda ruta registrada sin fila; mutación documentada: quitar una fila de la matriz hace fallar la detección de rutas sin cubrir; revisión de Seguridad"
rastros = ["¤rbac-tenant"]
+++

# ORG-22c · Rutas de DLP y bóveda en la matriz de permisos

Sale de ORG-22 (que se cierra como hecha) por pedido del CTO (2026-11-13): la tarea corta que ORG-22 llevaba anotada pasa a una ficha libre, del dominio seguridad.

## Entrega
- Añadir `/api/v1/dlp-discovery` (DLP-01) y `/api/v1/boveda-cloud` (BOV-01) a `PREFIJOS_MATRIZ` en `tests/test_matriz_permisos.py`, para que la detección de rutas sin cubrir las vea.
- Filas de matriz de cada ruta nueva por rol: completar `tests/matriz/DLP-01.py` (existe) y crear `tests/matriz/BOV-01.py`, con el mismo formato de las demás. Lo que no deba cubrir la matriz va a `FUERA_DE_MATRIZ` con su motivo.
- El rol del auditor sigue sin poder ejecutar ni cerrar (INV_LOPDP_AUDITOR_SOLE_ROLE); no se cambian los permisos reales, solo se declaran.

## Pruebas
- Toda ruta registrada bajo los dos prefijos tiene fila o motivo en `FUERA_DE_MATRIZ`.
- Mutación documentada: quitar una fila y comprobar que la prueba de rutas sin cubrir falla.

## Límites
- Sin código de producción ni migración; si una ruta resulta mal protegida, se abre ficha aparte.
