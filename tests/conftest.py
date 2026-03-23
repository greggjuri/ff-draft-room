"""Pytest configuration — add app/ to sys.path to match Streamlit's import behavior."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "app"))
