"""Shared icon helper — maps semantic action names to Qt standard icons.

Usage::

    from garage_app.gui.widgets.icon_helper import icon as _icon

    btn = QPushButton(_icon("delete"), "Supprimer")
    # or
    self._btn_save.setIcon(_icon("save"))

All icons use QStyle.StandardPixmap which works on Windows without any
external icon theme.
"""
from __future__ import annotations

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QStyle

_MAP: dict[str, QStyle.StandardPixmap] = {
    "new":       QStyle.StandardPixmap.SP_FileDialogNewFolder,
    "save":      QStyle.StandardPixmap.SP_DialogSaveButton,
    "open":      QStyle.StandardPixmap.SP_DialogOpenButton,
    "delete":    QStyle.StandardPixmap.SP_TrashIcon,
    "close":     QStyle.StandardPixmap.SP_DialogCloseButton,
    "apply":     QStyle.StandardPixmap.SP_DialogApplyButton,
    "refresh":   QStyle.StandardPixmap.SP_BrowserReload,
    "print":     QStyle.StandardPixmap.SP_FileDialogDetailedView,
    "info":      QStyle.StandardPixmap.SP_MessageBoxInformation,
    "warning":   QStyle.StandardPixmap.SP_MessageBoxWarning,
    "question":  QStyle.StandardPixmap.SP_MessageBoxQuestion,
    "drive":     QStyle.StandardPixmap.SP_DriveHDIcon,
    "ok":        QStyle.StandardPixmap.SP_DialogOkButton,
    "cancel":    QStyle.StandardPixmap.SP_DialogCancelButton,
    "up":        QStyle.StandardPixmap.SP_ArrowUp,
    "down":      QStyle.StandardPixmap.SP_ArrowDown,
    "forward":   QStyle.StandardPixmap.SP_ArrowRight,
    "back":      QStyle.StandardPixmap.SP_ArrowLeft,
    "edit":      QStyle.StandardPixmap.SP_FileDialogDetailedView,
    "search":    QStyle.StandardPixmap.SP_FileDialogContentsView,
    "snapshot":  QStyle.StandardPixmap.SP_DriveCDIcon,
    "restore":   QStyle.StandardPixmap.SP_DialogResetButton,
    "help":      QStyle.StandardPixmap.SP_TitleBarContextHelpButton,
    "check":     QStyle.StandardPixmap.SP_DialogYesButton,
    "user":      QStyle.StandardPixmap.SP_FileIcon,
    "logo":      QStyle.StandardPixmap.SP_DirOpenIcon,
    "password":  QStyle.StandardPixmap.SP_VistaShield,
}


def icon(name: str) -> QIcon:
    """Return a QIcon for the given semantic action name.

    Returns an empty QIcon if *name* is not recognised — this is safe to pass
    to QPushButton constructors and setIcon().
    """
    sp = _MAP.get(name)
    if sp is None:
        return QIcon()
    return QApplication.style().standardIcon(sp)
