import sys
import os

# Asegurar que la raíz del proyecto esté en el sys.path para importar app_core y features
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from main import app
