# ¤¤qa-engineer
# ¤ci-cd
"""Lector YAML de las pruebas (CI-21), sin dependencias: PyYAML no está en requirements.txt.

Cubre solo el subconjunto de los manifiestos de `governance/operaciones/`: mapas por sangría, listas con
`-`, escalares (cadenas con y sin comillas, enteros, `true`/`false`, `null`), listas en línea planas
`[a, b]`, comentarios `#`, bloques `|` y varios documentos separados por `---`.
Lo demás (anclas `&`, alias `*`, etiquetas `!`, flujo `{}`, flujo anidado, bloques `>`) lanza un
`ValueError` con el número de línea: nunca devuelve algo aproximado.

`leer_yaml(texto)` devuelve el documento (`dict` o `list`), o la lista de documentos si hay más de uno.
"""
from __future__ import annotations

import re

_ENTERO = re.compile(r"-?\d+")


class _Linea:
    __slots__ = ("sangria", "texto", "numero")

    def __init__(self, sangria: int, texto: str, numero: int):
        self.sangria, self.texto, self.numero = sangria, texto, numero


def _error(numero: int, motivo: str) -> ValueError:
    return ValueError(f"línea {numero}: {motivo} no está soportado por tests/_lector_yaml.py")


def _sin_comentario(texto: str) -> str:
    comilla = None
    for i, c in enumerate(texto):
        if comilla:
            if c == comilla:
                comilla = None
        elif c in "\"'":
            comilla = c
        elif c == "#" and (i == 0 or texto[i - 1] in " \t"):
            return texto[:i].rstrip()
    return texto.rstrip()


def _partir_lista_en_linea(interior: str, numero: int) -> list[str]:
    partes, actual, comilla = [], "", None
    for c in interior:
        if comilla:
            actual += c
            if c == comilla:
                comilla = None
        elif c in "\"'":
            comilla = c
            actual += c
        elif c in "[]{}":
            raise _error(numero, "un flujo anidado")
        elif c == ",":
            partes.append(actual.strip())
            actual = ""
        else:
            actual += c
    if actual.strip():
        partes.append(actual.strip())
    return partes


def _escalar(valor: str, numero: int):
    if not valor:
        return None
    inicial = valor[0]
    if inicial == "&":
        raise _error(numero, "un ancla")
    if inicial == "*":
        raise _error(numero, "un alias")
    if inicial == "!":
        raise _error(numero, "una etiqueta")
    if inicial == "{":
        raise _error(numero, "un flujo {}")
    if inicial == ">":
        raise _error(numero, "un bloque >")
    if inicial == "[":
        if not valor.endswith("]"):
            raise _error(numero, "una lista en línea sin cerrar")
        return [_escalar(p, numero) for p in _partir_lista_en_linea(valor[1:-1], numero)]
    if inicial in "\"'":
        if len(valor) < 2 or valor[-1] != inicial:
            raise _error(numero, "una cadena sin cerrar")
        return valor[1:-1]
    if valor in ("true", "false"):
        return valor == "true"
    if valor in ("null", "~"):
        return None
    if _ENTERO.fullmatch(valor):
        return int(valor)
    return valor


def _partir_clave(texto: str, numero: int) -> tuple[str, str] | None:
    """`clave: valor` → (clave, valor); None si la línea no es una clave."""
    comilla = None
    for i, c in enumerate(texto):
        if comilla:
            if c == comilla:
                comilla = None
        elif c in "\"'" and i == 0:
            comilla = c
        elif c == ":" and (i + 1 == len(texto) or texto[i + 1] == " "):
            clave = texto[:i].strip()
            if clave[:1] in "&*!?{[":
                raise _error(numero, "una clave compleja, ancla o etiqueta")
            return _escalar(clave, numero) if clave[:1] in "\"'" else clave, texto[i + 1:].strip()
    return None


class _Lector:
    def __init__(self, lineas_crudas: list[tuple[int, str]]):
        self.crudas = lineas_crudas  # (número, texto) sin quitar comentarios, para los bloques |
        self.lineas: list[_Linea] = []
        for numero, cruda in lineas_crudas:
            limpia = _sin_comentario(cruda)
            if limpia.strip():
                self.lineas.append(_Linea(len(limpia) - len(limpia.lstrip(" ")), limpia.strip(), numero))
        self.i = 0

    def _actual(self) -> _Linea | None:
        return self.lineas[self.i] if self.i < len(self.lineas) else None

    def documento(self):
        if not self.lineas:
            return None
        valor = self._bloque(self.lineas[0].sangria)
        if self._actual() is not None:
            raise _error(self._actual().numero, "una sangría inesperada")
        return valor

    def _bloque(self, sangria: int):
        linea = self._actual()
        if linea.texto == "-" or linea.texto.startswith("- "):
            return self._lista(sangria)
        return self._mapa(sangria)

    def _lista(self, sangria: int) -> list:
        lista = []
        while (linea := self._actual()) and linea.sangria == sangria and (linea.texto == "-" or linea.texto.startswith("- ")):
            resto = linea.texto[1:].lstrip()
            if not resto:
                self.i += 1
                siguiente = self._actual()
                lista.append(self._bloque(siguiente.sangria) if siguiente and siguiente.sangria > sangria else None)
            elif _partir_clave(resto, linea.numero) is not None:
                # «- clave: valor»: el mapa del elemento empieza en la columna del contenido.
                self.lineas[self.i] = _Linea(sangria + len(linea.texto) - len(resto), resto, linea.numero)
                lista.append(self._mapa(self.lineas[self.i].sangria))
            else:
                lista.append(_escalar(resto, linea.numero))
                self.i += 1
        return lista

    def _mapa(self, sangria: int) -> dict:
        mapa: dict = {}
        while (linea := self._actual()) and linea.sangria == sangria:
            if linea.texto == "-" or linea.texto.startswith("- "):
                raise _error(linea.numero, "un elemento de lista dentro de un mapa")
            partes = _partir_clave(linea.texto, linea.numero)
            if partes is None:
                raise _error(linea.numero, f"la línea «{linea.texto}» (no es «clave: valor»)")
            clave, valor = partes
            if clave in mapa:
                raise _error(linea.numero, f"la clave repetida «{clave}»")
            self.i += 1
            if valor in ("|", "|-"):
                mapa[clave] = self._bloque_literal(linea, valor == "|-")
            elif valor:
                mapa[clave] = _escalar(valor, linea.numero)
            else:
                siguiente = self._actual()
                if siguiente and (siguiente.sangria > sangria or (
                        siguiente.sangria == sangria and (siguiente.texto == "-" or siguiente.texto.startswith("- ")))):
                    mapa[clave] = self._bloque(siguiente.sangria)
                else:
                    mapa[clave] = None
        linea = self._actual()
        if linea and linea.sangria > sangria:
            raise _error(linea.numero, "una sangría inesperada")
        return mapa

    def _bloque_literal(self, cabecera: _Linea, sin_salto_final: bool) -> str:
        """Las líneas crudas más sangradas que la clave, tal cual (los # son texto)."""
        posicion = next(k for k, (n, _) in enumerate(self.crudas) if n == cabecera.numero) + 1
        cuerpo: list[str] = []
        sangria_bloque = None
        while posicion < len(self.crudas):
            numero, cruda = self.crudas[posicion]
            if cruda.strip():
                sangria = len(cruda) - len(cruda.lstrip(" "))
                if sangria <= cabecera.sangria:
                    break
                sangria_bloque = sangria if sangria_bloque is None else sangria_bloque
                cuerpo.append(cruda[sangria_bloque:])
            else:
                cuerpo.append("")
            posicion += 1
        while cuerpo and not cuerpo[-1]:
            cuerpo.pop()
        ultimo = self.crudas[posicion - 1][0] if posicion > 0 else cabecera.numero
        while self._actual() and self._actual().numero <= ultimo:
            self.i += 1
        texto = "\n".join(cuerpo)
        return texto if sin_salto_final else texto + "\n"


def leer_yaml(texto: str):
    """El documento del texto (`dict` o `list`); con varios documentos `---`, la lista de documentos."""
    documentos: list[list[tuple[int, str]]] = [[]]
    for numero, linea in enumerate(texto.splitlines(), start=1):
        if "\t" in linea[: len(linea) - len(linea.lstrip())]:
            raise _error(numero, "una sangría con tabulador")
        if linea.rstrip() == "---":
            documentos.append([])
        elif linea.rstrip() == "...":
            raise _error(numero, "el fin de documento «...»")
        else:
            documentos[-1].append((numero, linea))
    leidos = [_Lector(d).documento() for d in documentos]
    if documentos[0] and not any(_sin_comentario(c).strip() for _, c in documentos[0]):
        leidos = leidos[1:]  # solo comentarios antes del primer ---
    leidos = [d for d in leidos if d is not None] or [None]
    return leidos[0] if len(leidos) == 1 else leidos
