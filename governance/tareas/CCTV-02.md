+++
id = "CCTV-02"
titulo = "Congelamiento Forense (Hold Legal) de clips de videovigilancia por incidente o derecho ARCOP y actas quincenales de destrucción SHA-256"
ola = "D"
estado = "pendiente"
sala = "videovigilancia"
depende_de = ["CCTV-01", "BOV-02", "CON-01"]
propiedad = ["features/videovigilancia/services/__init__.py", "features/videovigilancia/services/cctv_legal_hold_engine.py", "features/videovigilancia/videovigilancia_service.py#CCTV-02", "features/videovigilancia/domain/errores.py#CCTV-02", "features/videovigilancia/routes/cctv_hold_routes.py", "app_core/pasillo/videovigilancia.py#CCTV-02", "app_core/pasillo/incidentes.py#CCTV-02", "app_core/pasillo/derechos_arco.py#CCTV-02", "frontend/src/components/layout/pantallas/CCTV-02.tsx", "frontend/src/components/layout/pantallas/index.tsx#CCTV-02", "tests/test_cctv02_legal_hold_y_acta_purga.py"]
arbitro = "pytest tests/test_cctv02_legal_hold_y_acta_purga.py + suite completa + vigilantes"
rastros = ["¤videovigilancia-cctv", "¤incidentes", "¤derechos", "¤conservacion"]
+++
# CCTV-02 · Congelamiento Forense (Hold Legal) de clips de videovigilancia por incidente o derecho ARCOP y actas quincenales de destrucción SHA-256

## Entrega
- Motor `features/videovigilancia/services/cctv_legal_hold_engine.py` que permite congelar un clip de videovigilancia (`aplicar_hold_legal`) vinculándolo a un expediente de vulneración (`app_core/pasillo/incidentes.py#CCTV-02`) o a una solicitud ARCOP (`app_core/pasillo/derechos_arco.py#CCTV-02`), promoviéndolo del bucket `short-ttl` de 15 días al bucket WORM `long-retention`.
- Ejecutor de purga quincenal que destruye todos los clips con antigüedad `>= 15` días que no tengan `hold_legal_activo = True` y emite el **Certificado Quincenal de Destrucción de Videovigilancia (`SHA-256`)**.
- Pantalla `frontend/src/components/layout/pantallas/CCTV-02.tsx` con línea de tiempo de clips de 15 días, botón de *Hold Legal* en 1 clic e historial de actas quincenales de purga.

## Pruebas
- `pytest tests/test_cctv02_legal_hold_y_acta_purga.py` verifica que al ejecutar la purga del día 15, los clips ordinarios se eliminan y quedan en el acta `SHA-256`, mientras que cualquier clip con *Hold Legal* activo permanece intacto en el bucket WORM (`INV_LOPDP_CCTV_LEGAL_HOLD_OVERRIDE`).
