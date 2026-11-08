# Diseño: la propiedad de una ficha se comprueba contra el árbol

Arquitecto de soluciones ADPA · 2026-11-07 · Solo diseño; lo implementa la ficha que escriba Tech Lead.
Base medida: `origin/main` 46c2912 (ya incluye el #458), 270 fichas, 88 no hechas. Medición reproducible y de solo lectura: `medir_propiedad.py`, en este mismo scratchpad.
Referencias: `scripts/generar_indice_tareas.py` (`validar`, `propiedades_se_solapan`, rechazo de `carpeta/` del #454); ZERAG `governance/nucleo/COORDINACION.md` C.2 y `TICKETS_PENDIENTES.md` 270–275 (solo lectura).

## 1. Diagnóstico

El verificador compara las entradas de las fichas **entre sí**, nunca contra el disco. Las tres variantes del defecto tienen la misma causa:
- sección que no existe (Aporte 118);
- `carpeta/` (Aporte 129);
- ruta equivocada (#458).

Una entrada que no designa nada real no puede chocar con nada, así que el verificador la da por buena. La corrección no es un caso más, sino una regla de **existencia o creación declarada**.

Una convención implícita («sin `#ID` y no existe = la crea la ficha») no basta. El mismo error tipográfico del #458 sigue vivo en 8 fichas como «creación» de `frontend/src/components/pantallas/<ID>.tsx` (véase §4), y la convención lo acepta en silencio. Por eso la creación se declara.

## 2. Regla final (R-PROP-EXISTE)

Cabecera de ficha: dos campos nuevos, **opcionales** (vacíos por defecto, para no romper las 270 fichas):
- `crea = ["ruta", ...]`: archivos que la ficha crea. Cada uno figura también en su `propiedad`, **sin** `#ID`, porque quien crea es dueño del archivo entero.
- `siembra = ["ruta#ID", ...]`: marcas vacías `=== ID ===` / `=== fin ID ===` que la ficha deja en archivos suyos (creados o poseídos enteros) para fichas posteriores.

Sea `T` la base comparada (el árbol del commit verificado), `anc(t)` los ancestros transitivos de `t` por `depende_de`, y `marca(f, ID)` que el contenido de `f` en `T` contenga `=== ID ===` o la forma heredada `--- INICIO ID ---` (hoy conviven 220 y 6 casos).

Para toda ficha `t` con estado distinto de `hecha`, y toda entrada `e = f` o `e = f#ID` de su propiedad:

1. **Ruta concreta (sin comodín):**
   - **(a)** `f ∈ T`. Si `e` lleva `#ID`, se cumple `marca(f, ID)` o existe `u ∈ anc(t)` con `f#ID ∈ u.siembra`.
   - **(b)** `f ∉ T`. Entonces `f ∈ t.crea` y `e` no lleva `#ID`, o bien existe `u ∈ anc(t)` con `f ∈ u.crea`, y si `e` lleva `#ID`, además `f#ID ∈ u.siembra`.
2. **Comodín (`dir/**`, `dir/*.py`…):** el prefijo fijo `dir/` existe en `T`, o es prefijo de algún `crea` de `t` o de `anc(t)`.
3. **Coherencia de `crea`:** ninguna ruta de `crea` existe ya en `T`. Cada ruta de `crea` tiene una sola creadora entre las fichas no hechas, y figura en su `propiedad` sin `#ID`.
4. **Coherencia de `siembra`:** `f#ID ∈ u.siembra` exige que `u` posea `f` entero (lo crea o lo tiene sin `#ID`) y que la ficha `ID` dependa transitivamente de `u`. Una marca sembrada para quien no depende de ti no garantiza nada.

Cuando `u` se fusiona y pasa a `hecha`, el archivo ya existe con sus marcas, y las dependientes pasan por (1a). La regla se sostiene a sí misma.

## 3. Dónde vive el árbitro

- **En `validar()` de `scripts/generar_indice_tareas.py`**, como `validar_contra_arbol(tareas, arbol, leer)`. `arbol` es el conjunto de rutas versionadas (`git ls-tree -r --name-only HEAD`) y `leer(ruta)` devuelve su contenido. Se inyectan para probarlo sin disco.
- Corre con `--verificar`, que la CI ya ejecuta. No hay script ni workflow nuevo.
- La base comparada se imprime siempre, como pide el TICKET-270 punto 3: «Base: HEAD <sha>, N fichas no hechas, M entradas».
- **Mensaje con sugerencia.** Si `f ∉ T`, se busca el ancestro existente más cercano de `f`. Si dentro de él hay un directorio con el mismo nombre que el primer segmento que falta, se propone la ruta reconstruida. Si no, se usa `difflib.get_close_matches` restringido a archivos con el mismo nombre base. Ejemplo:
  `ADPA-07: «frontend/src/components/pantallas/index.tsx» no existe en HEAD 46c2912; ¿quiso decir «frontend/src/components/layout/pantallas/index.tsx»? Si la crea otra ficha, declárela en su «crea» y dependa de ella.`
- Con el conjunto vacío de fichas falla, igual que pide el 270.

## 4. Medición sobre `origin/main` 46c2912

Las violaciones bajo la regla, contando solo lo que hoy no se puede justificar sin tocar fichas:

| Clase | Entradas | Fichas | Qué es |
|---|---|---|---|
| **E. Sección en un archivo que no existe y que ninguna ficha crea** | 152 | 45 | 50 rutas: 80 entradas en 21 pasillos `app_core/pasillo/*.py`, 49 en `domain/errores.py` de salas nuevas y 23 en otras rutas. **Error real**, sobre todo de diseño (véase la causa raíz) |
| **A. Sección sin marca en un archivo que existe, y ningún ancestro lo toca** | 11 | 3 | ADPA-04 (`pasillo/rat.py`, `pasillo/diagnostico.py`, `roadmap/services/alcance_area_engine.py`), ADPA-05 (7 compuertas y `roadmap/domain/errores.py`) y DEMO-04 (`lib/auth/fetchAutenticado.ts`) |
| **Ruta equivocada que pasa como creación** | 8 | 8 | `frontend/src/components/pantallas/<ID>.tsx` en BOV-01, BOV-03, BOV-04, CCTV-01, CCTV-02, CON-01, DLP-01 y ORG-15; la ruta real es `components/layout/pantallas/`. **Es el mismo error del #458, que sigue vivo** |
| **Otras rutas sospechosas** (dentro de E) | 9 | 9 | `api/main.py` (BOV-01, CCTV-01, CON-01, DLP-01; real `main.py`); `features/ai_copilot/copilot_service.py` (NORM-03, VTX-01; real `ai_copilot_service.py`, y el PRD §5.2 usa `copilot_service.py`); `features/terceros/models.py` y `db/models/terceros.py` (ADPA-08; real `features/terceros/domain/models.py`); `features/roadmap/generador_service.py` y `recalculo_service.py` (ADPA-04) |
| B. Sección sin marca; un ancestro toca el archivo | 147 | 50 | Pasa si ese ancestro declara `siembra`. Hoy no se puede saber: es deuda de declaración, no necesariamente un error |
| D/F. Archivo que crea un ancestro | 6 | 5 | Pasa al declarar `crea` y, si hace falta, `siembra` en el ancestro |
| C. Comodín sobre una carpeta que no existe | 37 | 22 | Salas nuevas: pasa al declarar `crea` en la creadora. Hay 2 sospechosas: BIB-106 `components/biblioteca/cargas/**` y REG-01 `app/plataforma/paquetes/**` |
| G. Creación implícita (sin `#ID`, no existe, sin `crea`) | 381 | 79 | Legítima casi siempre; necesita `crea`. Es la clase que esconde el error de `pantallas/` |

**Causa raíz de E y A.** ADPA-05 (errores y compuertas) y ADPA-06 (pasillos) declaran `f#ADPA-0x`, es decir, «una sección mía», en archivos que no existen. Con la regla, deben ser **creadoras**: `crea = [f]`, `propiedad` con `f` sin `#ID` y `siembra = [f#ID por cada dependiente]`. Y las 45 fichas de E deben `depende_de` de ellas. Por ejemplo, `pasillo/biblioteca.py`, que Tech Lead asignó a ADPA-06, hoy no lo crea nadie según la cabecera.

**Discrepancia con el PRD (para el CTO):** el §5.2 nombra compuertas que no coinciden con el código (`copilot_service.py`, `mtge_service.py`, `auditoria_service.py`, `dpo_service.py`, frente a `ai_copilot_service.py`, `riesgos_mtge_service.py`, `auditoria_capa_service.py` y `dpo_cockpit_service.py`). Dos fichas ya copiaron el nombre del PRD. La regla lo detectará, pero el PRD es la fuente del error.

## 5. Migración sin bloquear las olas

| Fase | Qué falla en CI | Cuándo |
|---|---|---|
| 1 · Estricta en lo seguro | (1a) con `#ID` sin marca ni `siembra`; (1b) con `#ID` sin creador; rutas con **sugerencia** (error tipográfico de directorio); `crea` y `siembra` incoherentes (3 y 4). La creación implícita (G) y los comodines sin base (C) solo **avisan** | al fusionar la ficha |
| 2 · Total | también G y C: toda ruta nueva va en `crea` | cuando se cierre la Ola 2 |

Para no bloquear las olas en curso, la fase 1 se activa con **una lista de exenciones congelada** (`governance/tareas/_exenciones_propiedad.txt`, `ficha|entrada|motivo`), generada una sola vez con la medición. Un árbitro exige que la lista **solo decrezca**: una entrada nueva falla, y una exención resuelta que sigue en la lista también falla. Las fichas de la Ola 1 (ADPA-04, ADPA-07, SEC-18 y TEST-05) y de la Ola 2 (SEC-13, SEC-14, OPS-07 y BIB-106) siguen su curso. Tech Lead corrige sus cabeceras cuando las libere cada sub chat, sin editar la propiedad de una ficha en curso.

Lo que esas ocho fichas tienen hoy contra la regla, sin contar la creación implícita:
- ADPA-04: A ×3, E ×2 (`generador_service.py`, `recalculo_service.py`) y B ×4;
- ADPA-07: B ×5; su error del #458 ya está corregido;
- SEC-13: B ×2; OPS-07: B ×1;
- BIB-106: C ×1, sospechosa;
- SEC-18, SEC-14 y TEST-05: solo G.

Orden de corrección (gobernanza, un PR por tanda):
1. las 8 rutas `components/pantallas/<ID>.tsx` y las 9 sospechosas, que son errores ya;
2. ADPA-05 y ADPA-06 como creadoras con `crea` y `siembra`, más el `depende_de` de sus 45 dependientes;
3. `siembra` en los sembradores de B (ADPA-07, ADPA-09…);
4. `crea` mecánico para G, generado por un script desde la medición y revisado por Tech Lead.

## 6. Encaje con ZERAG (TICKET-270 a 275)

- **270** (contrato del generador): esta regla es una comprobación más del mismo generador, con base comparada y fallo con el conjunto vacío. Encaja sin cambios.
- **272** (secciones sembradas): es la mitad de esta regla, la de la sección. Propongo **ampliar el 272 a «toda entrada poseída existe o la crea una ancestro»**, con los mismos campos `crea` y `siembra`, para que el molde y EVYDENTIA usen la misma forma y no nazca una cuarta variante. Lo que dice ahora («o que `f` lo cree una tarea anterior») necesita un campo que lo diga. Sin `crea` no hay forma de saberlo, y la convención implícita deja pasar errores tipográficos.
- **273** (`carpeta/`): EVYDENTIA ya lo tiene (#454). Con esta regla, `carpeta/` también falla por (2).
- **271** (comodín que absorbe secciones ajenas) y **274** (tandas frente al mínimo): no cambian. La regla 2 reduce los falsos choques de 271, porque un comodín sin base deja de ser válido.
- **275** (doctrina y plantilla): la plantilla de tarea del molde lleva `crea` y `siembra` vacíos, y C.2 pasa a NORMA en los proyectos.

## 7. Texto propuesto para la ficha

```
+++
id = "ADPA-10"   # el número lo asigna Tech Lead
titulo = "La propiedad de cada ficha se comprueba contra el árbol: existe, la crea ella o la crea y siembra una ancestro"
ola = "indep"
estado = "pendiente"
sala = "gobernanza"
depende_de = []
propiedad = ["scripts/generar_indice_tareas.py", "tests/test_generar_indice_tareas_arbol.py", "governance/tareas/_exenciones_propiedad.txt", "governance/tareas/README.md#ADPA-10"]
crea = ["tests/test_generar_indice_tareas_arbol.py", "governance/tareas/_exenciones_propiedad.txt"]
arbitro = "pytest tests/test_generar_indice_tareas_arbol.py + python scripts/generar_indice_tareas.py --verificar"
+++
```
(Si `README.md` no tiene la marca `=== ADPA-10 ===`, la ficha posee el README entero o Tech Lead siembra la marca antes; la regla se aplica a sí misma.)

**Entrega.** Campos opcionales `crea` y `siembra`. `validar_contra_arbol` con las reglas 1 a 4 del §2, la fase 1 del §5 y la lista de exenciones que solo decrece. Mensaje con la ruta sugerida y la base comparada.

**Pruebas (árbol sintético inyectado):**
1. `x/y.py#A`, con `x/y.py` existente sin marca → rechazo; con `=== A ===` → acepta; con una ancestro que la declara en `siembra` → acepta; con una ficha sin relación que la siembra → rechazo.
2. `nuevo/z.py#A`, sin creadora → rechazo; con una ancestro que tiene `crea` y `siembra` → acepta; con una creadora sin relación → rechazo.
3. `a/pantallas/i.tsx`, inexistente, con `a/layout/pantallas/i.tsx` en el árbol → rechazo con «¿quiso decir a/layout/pantallas/i.tsx?».
4. `crea` de una ruta que ya existe → rechazo; dos creadoras de la misma ruta → rechazo.
5. Exención nueva en la lista → rechazo; exención ya resuelta que sigue en la lista → rechazo.
6. Cero fichas → falla e informa de la base.

**Mutaciones que el árbitro debe matar:**
- M1 (la principal): la ficha sintética **`MUT-01`** con `propiedad = ["frontend/src/components/pantallas/index.tsx#MUT-01"]` sobre un árbol que solo tiene `frontend/src/components/layout/pantallas/index.tsx` con `=== MUT-01 ===`. El árbitro debe rechazarla y sugerir la ruta real. Si una mutación hace que `validar_contra_arbol` devuelva siempre `[]` o ignore las entradas con `#`, la prueba falla.
- M2: aceptar como creadora a una ficha que no es ancestro: la prueba 2c debe fallar.
- M3: comparar la marca solo por el nombre del archivo, sin la ruta: la prueba 1a debe fallar.
