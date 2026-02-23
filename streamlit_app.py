"""
Launcher – run from project root:
    streamlit run streamlit_app.py
"""
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

runpy.run_path(str(ROOT / "app" / "app.py"), run_name="__main__")
