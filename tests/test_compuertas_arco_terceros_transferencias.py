"""Pruebas de verificación de compuertas ADPA: Derechos ARCO, Terceros y Transferencias.
`¤adpa` `¤derechos` `¤transferencias`

Verifica:
1. Existencia e integridad de las tres compuertas:
   - features/derechos_arco/derechos_arco_service.py
   - features/terceros/terceros_service.py
   - features/transferencias/transferencias_service.py
2. Encapsulamiento ADPA estricto: los routers (arco_router.py y terceros_router.py)
   importan únicamente la compuerta de su sala (<sala>_service) y ningún submódulo interno.
3. Exposición de la superficie pública mínima requerida en cada compuerta.
4. Funcionalidad de servicios y compatibilidad con tipos y contratos de sala.
"""
import ast
import os
import pytest

from features.derechos_arco import derechos_arco_service
from features.terceros import terceros_service
from features.transferencias import transferencias_service

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_existencia_compuertas_adpa():
    """Cada una de las 3 salas debe contar con su compuerta publica <sala>_service.py."""
    compuertas = [
        os.path.join(RAIZ, "features", "derechos_arco", "derechos_arco_service.py"),
        os.path.join(RAIZ, "features", "terceros", "terceros_service.py"),
        os.path.join(RAIZ, "features", "transferencias", "transferencias_service.py"),
    ]
    for c in compuertas:
        assert os.path.isfile(c), f"No existe la compuerta requerida: {c}"


def test_superficie_publica_compuertas():
    """Cada compuerta debe exponer los simbolos esperados en __all__."""
    # derechos_arco
    for simbolo in ["SolicitudARCO", "TipoSolicitud", "EstadoSolicitud", "listar_solicitudes_arco", "crear_solicitud_arco"]:
        assert hasattr(derechos_arco_service, simbolo), f"derechos_arco_service no expone {simbolo}"
        assert simbolo in derechos_arco_service.__all__

    # terceros
    for simbolo in ["Tercero", "listar_terceros_encargados"]:
        assert hasattr(terceros_service, simbolo), f"terceros_service no expone {simbolo}"
        assert simbolo in terceros_service.__all__

    # transferencias
    for simbolo in ["TerceroEncargado", "RolTercero", "NivelProteccion", "listar_transferencias"]:
        assert hasattr(transferencias_service, simbolo), f"transferencias_service no expone {simbolo}"
        assert simbolo in transferencias_service.__all__


def _analizar_imports_de_archivo(ruta_relativa: str) -> list[tuple[str, str | None]]:
    """Devuelve tuplas (modulo_importado, nombre_especifico) para cada import."""
    ruta_completa = os.path.join(RAIZ, ruta_relativa)
    with open(ruta_completa, "r", encoding="utf-8") as f:
        arbol = ast.parse(f.read(), filename=ruta_completa)
    
    imports = []
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            for alias in nodo.names:
                imports.append((alias.name, None))
        elif isinstance(nodo, ast.ImportFrom) and nodo.module:
            for alias in nodo.names:
                imports.append((nodo.module, alias.name))
    return imports


def test_arco_router_importa_solamente_compuerta():
    """arco_router.py no debe importar ningun archivo interno de features/derechos_arco, solo derechos_arco_service."""
    imports = _analizar_imports_de_archivo("api/routers/arco_router.py")
    
    for modulo, nombre in imports:
        if modulo.startswith("features.derechos_arco"):
            assert modulo == "features.derechos_arco" or modulo == "features.derechos_arco.derechos_arco_service", (
                f"arco_router viola ADPA: importa '{modulo}.{nombre}', debe usar unicamente derechos_arco_service"
            )
            if modulo == "features.derechos_arco":
                assert nombre == "derechos_arco_service", (
                    f"arco_router viola ADPA: importa '{nombre}' desde features.derechos_arco en vez de derechos_arco_service"
                )


def test_terceros_router_importa_solamente_compuerta():
    """terceros_router.py no debe importar ningun archivo interno de features/terceros, solo terceros_service."""
    imports = _analizar_imports_de_archivo("api/routers/terceros_router.py")
    
    for modulo, nombre in imports:
        if modulo.startswith("features.terceros"):
            assert modulo == "features.terceros" or modulo == "features.terceros.terceros_service", (
                f"terceros_router viola ADPA: importa '{modulo}.{nombre}', debe usar unicamente terceros_service"
            )
            if modulo == "features.terceros":
                assert nombre == "terceros_service", (
                    f"terceros_router viola ADPA: importa '{nombre}' desde features.terceros en vez de terceros_service"
                )


def test_transferencias_router_o_servicios_cumplen_adpa():
    """Ningun archivo fuera de features/transferencias importa ficheros internos de transferencias."""
    for base, _, files in os.walk(os.path.join(RAIZ, "api")):
        for file in files:
            if not file.endswith(".py"):
                continue
            rel = os.path.relpath(os.path.join(base, file), RAIZ)
            imports = _analizar_imports_de_archivo(rel)
            for modulo, nombre in imports:
                if modulo.startswith("features.transferencias"):
                    assert modulo in {"features.transferencias", "features.transferencias.transferencias_service"}, (
                        f"{rel} viola ADPA al importar modulo interno '{modulo}.{nombre}'"
                    )


@pytest.mark.asyncio
async def test_compuerta_transferencias_legalidad():
    """Verifica la logica Poka-Yoke de transferencia legal expuesta en la compuerta."""
    t_adecuada = transferencias_service.TerceroEncargado(
        nombre="Cloud Provider Adecuado",
        rol=transferencias_service.RolTercero.ENCARGADO,
        pais_destino="Espana",
        nivel_proteccion=transferencias_service.NivelProteccion.ADECUADO,
        clausulas_firmadas=False,
    )
    assert t_adecuada.es_transferencia_legal() is True

    t_estandar_sin_firmar = transferencias_service.TerceroEncargado(
        nombre="Proveedor Sin Clausulas",
        rol=transferencias_service.RolTercero.SUBENCARGADO,
        pais_destino="EEUU",
        nivel_proteccion=transferencias_service.NivelProteccion.ESTANDAR,
        clausulas_firmadas=False,
    )
    assert t_estandar_sin_firmar.es_transferencia_legal() is False

    t_estandar_firmada = transferencias_service.TerceroEncargado(
        nombre="Proveedor Con SCC",
        rol=transferencias_service.RolTercero.SUBENCARGADO,
        pais_destino="EEUU",
        nivel_proteccion=transferencias_service.NivelProteccion.ESTANDAR,
        clausulas_firmadas=True,
    )
    assert t_estandar_firmada.es_transferencia_legal() is True
