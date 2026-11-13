# RET-07 · Cierre del retiro: listas reducidas a la historia
`¤sdd` `¤arbitro`

## 1. Datos

Sin tablas. Estado final de las listas y dependencias:

- `tests/sin_plataformas_pmv/permitidos.txt` contiene solo historia.
- `tests/sin_plataformas_pmv/pendientes/` queda vacío.
- `tests/sin_neon/` y `tests/test_sin_neon.py` se retiran: los reemplaza el árbitro de RET-00.
- `requirements.txt` y `frontend/package.json` sin `boto3`, `python-dotenv`, `openai` ni ningún paquete de Neon, Vercel, Upstash o Cloudflare.
- `governance/operaciones/BRIEF_PROPIETARIO_NEON.md` pasa a `governance/historico/pmv/`.

## 2. API

No aplica.

## 3. Reglas

- **R1 · Solo cierra.** Esta ficha no retira código de producto: si queda una mención fuera de la historia, pertenece a su ficha dueña y RET-07 espera.
- **R2 · Precondición.** RET-01, RET-02, RET-03, RET-05, RET-06, IA-04, IA-06 e IA-08 están `hecha` y sus pendientes, vacíos.
- **R3 · La historia se conserva.** No se edita ninguna migración, ficha `hecha`, aporte ni informe fechado para quitar una mención.
- **R4 · El árbitro queda como guardia permanente.** Tras el cierre, cualquier mención nueva fuera de la historia da rojo.
- **R5 · Nada fuera del repositorio.** No se crea ni se borra nada en las cuentas de Neon, Vercel, Upstash ni Cloudflare: eso lo decide el propietario.
- **R-ADPA · Ortogonalidad ZERAG (`RET-07`).** Toda invocación a otra sala va por `app_core/pasillo/<otra_sala>.py` (`ImportsCruzados = ∅`, ADR 0001). `verificar_adpa` queda sin importaciones huérfanas.

## 4. Interfaz

No aplica.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** el árbol final, **entonces** `pendientes/` está vacío y `permitidos.txt` solo tiene entradas de historia. Mutación: añadir a permitidos un archivo de producto hace fallar la prueba. | `test_permitidos_solo_historia` |
| **Dado** `requirements.txt` y `frontend/package.json`, **entonces** no declaran ninguna dependencia de las plataformas retiradas. | `test_sin_dependencias_de_plataformas` |
| **Dado** el árbol final, **entonces** no existen `tests/sin_neon/` ni `tests/test_sin_neon.py` y el árbitro nuevo sigue verde. | `test_sin_menciones_fuera_de_las_listas` |

## 6. Trazabilidad

- Ficha: `governance/tareas/RET-07.md`.
- Programa: `governance/apoyo/RETIRO_PLATAFORMAS_PMV.md` (PR #763), decisión del propietario del 2026-11-13.
- Especificación de referencia: `governance/especificaciones/README.md`.
- No se toca la rama `produccion` ni la historia (`alembic/versions/`, `governance/historico/pmv/`, fichas `hecha`, aportes, bibliografía). `.github/workflows/` y `verificadores/` son del propietario: si hacen falta, va un brief.
- Última del programa: después de RET-06 y de IA-06 e IA-08.
