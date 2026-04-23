from __future__ import annotations

import sys


def main() -> None:
    """Launch the desktop application."""

    try:
        from PySide6.QtWidgets import QApplication
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "Desktop UI requires PySide6. Install it with "
            "'python -m pip install -e .[desktop]' before running pdf-tts-ru-gui."
        ) from exc

    from pdf_tts_ru.gui.window import MainWindow

    app = QApplication(sys.argv)
    app.setApplicationName("sayit")
    window = MainWindow()
    window.show()
    raise SystemExit(app.exec())


if __name__ == "__main__":
    main()
