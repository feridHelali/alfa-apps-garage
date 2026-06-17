import sys

from PyQt6.QtWidgets import QApplication

from garage_app.bootstrap import bootstrap
from garage_app.gui.app import GarageApplication
from garage_app.gui.auth.login_window import LoginWindow
from garage_app.gui.splash_screen import SplashScreen


def main() -> None:
    app = GarageApplication(sys.argv)

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
    window.show()


if __name__ == "__main__":
    main()
