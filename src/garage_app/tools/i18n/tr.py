from __future__ import annotations

from PyQt6.QtCore import QCoreApplication


def tr(context: str, key: str) -> str:
    """Wrapper around Qt translation so strings are extractable by pylupdate6."""
    return QCoreApplication.translate(context, key)
