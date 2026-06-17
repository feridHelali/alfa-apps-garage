import sys

from PyQt6.QtWidgets import QApplication

from garage_app.bootstrap import bootstrap
from garage_app.gui.app import GarageApplication
from garage_app.gui.auth.login_window import LoginWindow


def main() -> None:
    app = GarageApplication(sys.argv)
    ctx = bootstrap()
    login = LoginWindow(ctx.auth_service)
    login.logged_in.connect(lambda session: _on_logged_in(app, ctx, session))
    login.exec()
    if not ctx.auth_service.current_session:
        sys.exit(0)
    sys.exit(app.exec())


def _on_logged_in(app: QApplication, ctx, session) -> None:  # type: ignore[type-arg]
    from garage_app.gui.main_window import MainWindow
    window = MainWindow(ctx, session)
    app.main_window = window  # type: ignore[attr-defined]
    window.show()


if __name__ == "__main__":
    main()
