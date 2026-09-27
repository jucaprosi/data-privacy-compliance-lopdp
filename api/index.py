import sys
import os

# Asegurar que la raíz del proyecto esté en el sys.path para importar app_core y features
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# Proveer valores por defecto en os.environ si las variables no están configuradas en Vercel
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
os.environ.setdefault("CORS_ORIGINS", "*")
os.environ.setdefault("JWT_SECRET", "super_secret_jwt_key_for_lopdp_360_prod_fallback")

from main import app

handler = app
