"""Configuración raíz de pytest para TutorIA.

Los tests viven en ``backend/tests`` e importan tanto ``app.*`` como ``tests.*``,
que solo son resolubles con ``backend/`` en ``sys.path``. Al insertarlo aquí, la
suite se ejecuta desde la raíz del repositorio, que es además el directorio de
trabajo que esperan las verificaciones sobre ``documentacion/``.
"""

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
