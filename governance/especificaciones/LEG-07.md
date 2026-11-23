# LEG-07 · Finales de línea CRLF en los .bat para que cmd lea el aviso de autor
`¤sdd` `¤ip` `¤arbitro`

## 1. Datos

Sin tablas ni migraciones. Estado final:

| Archivo | Estado final |
| :--- | :--- |
| `.gitattributes` | añade `*.bat text eol=crlf` y `*.cmd text eol=crlf`; `data/biblioteca/** -text` queda igual |
| `ejecutar_arnes_tres_pilares.bat` | CRLF, mismo contenido |
| `ejecutar_arnes_verificacion.bat` | CRLF, mismo contenido |
| `iniciar_backend.bat` | CRLF, mismo contenido |
| `iniciar_frontend.bat` | CRLF, mismo contenido |
| `iniciar_todo.bat` | CRLF, mismo contenido |
| `scripts/entorno.bat` | CRLF, mismo contenido |
| `tests/test_leg06_aviso_de_autor.py` | el caso de §5 |

Hecho medido en `origin/main` 0342ab96:
- `git ls-files --eol` da `i/lf w/lf` en los seis `.bat`; no hay `.cmd` versionados.
- LEG-06 puso «REM © 2026 … Proaño …» después de `@echo off`. Con LF y caracteres multibyte, cmd lee mal esa línea y cada `.bat` imprime al arrancar «© no se reconoce como un comando interno o externo», con las páginas de códigos 850 y 65001. Con CRLF no pasa. El mismo desplazamiento puede cortar otras líneas.
- `poner_aviso_de_autor.py` respeta el final de línea del archivo, así que tras renormalizar escribe el aviso con CRLF.
- `.gitattributes` solo tiene `data/biblioteca/** -text`. Ahí no hay `.bat` (`git ls-files data/biblioteca` no da ninguno), así que la regla nueva no la toca.

## 2. API

No aplica.

## 3. Reglas

- **R1 · CRLF en Windows.** Todo `.bat` y `.cmd` versionado se guarda en el índice con CRLF, por `.gitattributes`. La renormalización se hace con `git add --renormalize` sobre los seis archivos y el diff solo cambia los finales de línea.
- **R2 · El aviso no cambia.** El texto y la posición de LEG-06 R2 siguen igual.
- **R3 · Alcance.** Solo los archivos de la propiedad. `data/biblioteca/**` conserva `-text`, porque su huella SHA-256 depende de los bytes.
- **R-ADPA · Ortogonalidad ZERAG (`LEG-07`).** Sin `import yaml`.

## 4. Interfaz

No aplica.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** `git ls-files` con extensión `.bat` o `.cmd`, **entonces** cada archivo del árbol usa `\r\n` en todas sus líneas y no tiene ningún `\n` suelto. Mutación m1: pasar un `.bat` a LF da rojo con su nombre. | `tests/test_leg06_aviso_de_autor.py::test_bat_y_cmd_en_crlf` |
| **Dado** `.gitattributes`, **entonces** declara `*.bat text eol=crlf` y `*.cmd text eol=crlf`, y conserva `data/biblioteca/** -text`. Mutación m2: quitar la línea de `.bat` da rojo. | `tests/test_leg06_aviso_de_autor.py::test_gitattributes_crlf_y_biblioteca` |
| **Dado** cada `.bat`, **entonces** al ejecutarlo en cmd no aparece «no se reconoce como un comando». Lo comprueba el ingeniero en Windows y anota la salida en el PR. | prueba en físico |

## 6. Trazabilidad

- Ficha: `governance/tareas/LEG-07.md`. Especificación de referencia: `governance/especificaciones/README.md`.
- Pedido del CTO (2026-11-23), por un defecto de LEG-06 (#959).
- Depende de las fichas que comparten archivos de la propiedad: ENT-01, LEG-06, MARCA-05 y QA-02.
