"""Pytest configuration — add backend/ to sys.path."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from utils.storage import LocalStorage  # noqa: E402


@pytest.fixture
def storage(tmp_path):
    """LocalStorage backed by a temp directory."""
    return LocalStorage(tmp_path / "rankings")
