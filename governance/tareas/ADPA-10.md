+++
id = "ADPA-10"
titulo = "La propiedad de cada ficha se comprueba contra el árbol: existe, la crea ella o la crea y siembra una ancestro"
ola = "indep"
estado = "en_curso"
sala = "gobernanza"
depende_de = ["GOB-02"]
propiedad = ["scripts/generar_indice_tareas.py", "tests/test_generar_indice_tareas_arbol.py", "governance/tareas/_exenciones_propiedad.txt", "governance/tareas/README.md#ADPA-10", "scripts/seleccionar_pruebas.py"]
crea = ["tests/test_generar_indice_tareas_arbol.py", "governance/tareas/_exenciones_propiedad.txt"]
arbitro = "pytest tests/test_generar_indice_tareas_arbol.py + python scripts/generar_indice_tareas.py --verificar"
rastros = ["¤arbitro"]
+++

# ADPA-10 · Regla R-PROP-EXISTE

El diseño completo está en `governance/apoyo/DISENO_PROPIEDAD_CONTRA_ARBOL.md` (Arquitecto de soluciones ADPA). El CTO lo aprobó el 2026-11-07.

## Por qué

El verificador compara las fichas entre sí, nunca contra el disco. Una entrada que no designa nada real no choca con nada y pasa sin error. Ese defecto apareció como sección inexistente (Aporte 118), como `carpeta/` (Aporte 129) y como ruta equivocada (#458).

## Entrega

1. **Campos nuevos.** `crea` y `siembra`, opcionales y vacíos por defecto, se leen en `cargar_tareas`.
2. **`validar_contra_arbol(tareas, arbol, leer)`.** Va dentro de `validar()` y aplica las reglas 1 a 4 del §2 del diseño. `arbol` sale de `git ls-tree -r --name-only HEAD`; `arbol` y `leer` se inyectan para las pruebas.
3. **Mensajes.** Siempre se imprime la base comparada: «Base: HEAD <sha>, N fichas no hechas, M entradas». Cada error sugiere la ruta real (§3).
4. **Fase 1 (estricta en lo seguro).** Falla en:
   - una sección `#ID` sin marca ni `siembra`;
   - una sección `#ID` sin creadora;
   - una ruta para la que se puede sugerir la real;
   - un `crea` o un `siembra` incoherente.

   La creación implícita y un comodín sin base solo dan aviso.

   La lista `governance/tareas/_exenciones_propiedad.txt` (`ficha|entrada|motivo`) se genera una sola vez con la medición y solo puede decrecer: falla si tiene una exención nueva y si conserva una ya resuelta.
5. **Fase 2 (al cerrar la Ola 2).** La creación implícita y el comodín sin base también fallan: toda ruta nueva va en `crea`. La fase 2 la lanza otra ficha.
6. **README.** En `governance/tareas/README.md`, solo dentro de la marca `ADPA-10`, se documentan `crea` y `siembra`.

## Pruebas (árbol sintético inyectado)

1. `x/y.py#A`, con `x/y.py` existente:
   - sin marca → rechaza;
   - con `=== A ===` → acepta;
   - con una ancestro que la declara en `siembra` → acepta;
   - con una ficha sin relación que la siembra → rechaza.
2. `nuevo/z.py#A`:
   - sin creadora → rechaza;
   - con una ancestro que tiene `crea` y `siembra` → acepta;
   - con una creadora sin relación → rechaza.
3. `a/pantallas/i.tsx` no existe y `a/layout/pantallas/i.tsx` sí → rechaza con «¿quiso decir a/layout/pantallas/i.tsx?».
4. Rechaza:
   - un `crea` de una ruta que ya existe;
   - dos creadoras de la misma ruta.
5. Rechaza:
   - una exención nueva en la lista;
   - una exención resuelta que sigue en la lista.
6. Con cero fichas, falla e informa la base.

## Mutaciones que el árbitro debe matar

- **M1.** La ficha sintética `MUT-01` declara `frontend/src/components/pantallas/index.tsx#MUT-01`, y el árbol solo tiene `frontend/src/components/layout/pantallas/index.tsx` con `=== MUT-01 ===`. Debe rechazarla y sugerir la ruta real. Si `validar_contra_arbol` devuelve siempre `[]` o ignora las entradas con `#`, la prueba falla.
- **M2.** Aceptar como creadora a una ficha que no es ancestro hace fallar la prueba 2.
- **M3.** Comparar la marca solo por nombre de archivo, sin la ruta, hace fallar la prueba 1.

## Prioridad

Va antes de lanzar ADPA-05 y ADPA-06. Las dos ya declaran `crea` y `siembra` (2026-11-07).

## Cierre pendiente (2026-11-07, CTO)

ADPA-10 no pasa a hecha hasta que el árbitro corra en todo PR:
- `tests/test_generar_indice_tareas_arbol.py` valida el árbol real y exige cero errores (#474).
- `ARBITRO_DE_REPOSITORIO` de `scripts/seleccionar_pruebas.py` reconoce `arbol_git(` y `cargar_tareas(`. Así esa prueba y `tests/test_indice_tareas.py` pasan a núcleo.
- Una prueba de selección, en el archivo propio de ADPA-10, comprueba que un cambio solo en `features/diagnostico/**` elige `tests/test_generar_indice_tareas_arbol.py`.
