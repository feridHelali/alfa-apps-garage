import sys

from PyQt6.QtWidgets import QApplication, QMessageBox

from garage_app.bootstrap import bootstrap
from garage_app.gui.app import GarageApplication
from garage_app.gui.auth.login_window import LoginWindow
from garage_app.gui.licence_dialog import LicenceDialog, is_activated
from garage_app.gui.splash_screen import SplashScreen


def _check_licence(app: QApplication) -> bool:
    """Return True if a valid licence is present; prompt activation otherwise."""
    if is_activated():
        return True

    dlg = LicenceDialog()
    if dlg.exec() == LicenceDialog.DialogCode.Accepted:
        return True

    QMessageBox.critical(
        None,
        "Activation requise",
        "Le logiciel n'a pas pu être activé.\n"
        "Contactez Alfa Computers Apps pour obtenir une clé de licence.",
    )
    return False


def main() -> None:
    app = GarageApplication(sys.argv)

    if not _check_licence(app):
        sys.exit(1)

    splash = SplashScreen()
    splash.show()
    QApplication.processEvents()

    splash.update_message("Initialisation de la base de données…")
    ctx = bootstrap()

    splash.update_message("Chargement de l'interface…")
    app.apply_stylesheet("light")

    splash.update_message("Prêt.")

    login = LoginWindow(ctx.auth_service)
    login.logged_in.connect(lambda session: _on_logged_in(app, ctx, session, splash))
    splash.finish(login)
    login.exec()
    if not ctx.auth_service.current_session:
        sys.exit(0)
    sys.exit(app.exec())


def _on_logged_in(app: QApplication, ctx, session, splash=None) -> None:  # type: ignore[type-arg]
    from garage_app.gui.main_window import MainWindow
    window = MainWindow(ctx, session)
    app.main_window = window  # type: ignore[attr-defined]
    if splash:
        splash.finish(window)
    window.showMaximized()


if __name__ == "__main__":
    main()
