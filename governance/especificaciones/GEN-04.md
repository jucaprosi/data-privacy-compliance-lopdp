# GEN-04 · Marca en la interfaz: título EVYDENTIA · LOPDP 360, texto alternativo y logotipos sin la marca del operador
`¤sdd` `¤frontend-ide` `¤arbitro`

## 1. Datos

Sin backend. Programa: GEN-01 §0.

| Archivo | Estado final |
| :--- | :--- |
| `frontend/src/app/page.tsx:5` | `title: "EVYDENTIA · LOPDP 360"` |
| `frontend/src/components/layout/DashboardHeader.tsx:38` | `alt="EVYDENTIA"` |
| `frontend/public/brand/evydentia-principal.png`, `evydentia-negativo.png` | los archivos del propietario, sin la marca del operador dibujada |
| `frontend/tests/layout/marca-generica.spec.ts` (nuevo) | casos de §5 |

Hecho medido en `origin/main` ea6d26bf: los dos logotipos llevan dibujada la leyenda de la marca del operador. Un cambio de texto no los corrige.

## 2. API

Sin rutas.

## 3. Reglas

- **R1 · Nombre único.** La interfaz se llama «EVYDENTIA · LOPDP 360» en el título y «EVYDENTIA» en el texto alternativo del logotipo, igual que el nombre del producto de MARCA-01.
- **R2 · Logotipos del propietario.**
  - El propietario entrega los dos PNG nuevos en `C:\Users\Juan Carlos\compartido\evydentia\marca\`, con los mismos nombres, proporciones y fondo (claro y negativo).
  - **Sin ellos, la ficha no se lanza.** La ficha no dibuja ni edita logotipos.
- **R3 · Sin prohibiciones.** La prueba comprueba el título y el texto alternativo esperados, no la ausencia de una palabra (GEN-01 R3).
- **R-ADPA · Ortogonalidad ZERAG (`GEN-04`).** Solo la propiedad.

## 4. Interfaz

Pasa por UX/UI: revisa que los logotipos nuevos se vean en los dos temas y en la cabecera, sin cambios de tamaño.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** la portada, **entonces** `document.title` es «EVYDENTIA · LOPDP 360». Mutación m1: otro título da rojo. | `marca-generica.spec.ts` |
| **Dado** la cabecera, **entonces** el logotipo tiene `alt="EVYDENTIA"` y carga sin error con los dos temas. | `marca-generica.spec.ts` |
| **Dado** los PNG, **entonces** son los del propietario (lo confirma UX/UI en el PR). | revisión de UX/UI |

## 6. Trazabilidad

- Programa GEN-01 §0. Condición §5.3 del brief del CTO.
- Depende de las fichas hechas que comparten estos archivos: FE-19 (logotipos) y FE-28 (cabecera).
