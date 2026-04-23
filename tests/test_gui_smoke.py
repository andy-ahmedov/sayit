from __future__ import annotations

import os

import pytest

pytest.importorskip("PySide6")

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from pdf_tts_ru.gui.window import MainWindow
from pdf_tts_ru.models import TtsEngineKind


@pytest.fixture(scope="module")
def app():
    instance = QApplication.instance()
    if instance is not None:
        return instance
    return QApplication([])


def test_main_window_builds(app) -> None:
    window = MainWindow()
    window.show()
    app.processEvents()

    assert window.windowTitle() == "sayit"
    assert window.run_button.text() == "Озвучить"


def test_main_window_switches_engine_fields(app) -> None:
    window = MainWindow()
    window.show()
    app.processEvents()
    window._set_combo_value(window.engine_combo, TtsEngineKind.PIPER)
    window._update_engine_fields()
    app.processEvents()

    assert window.piper_group.isVisible()
    assert not window.silero_group.isVisible()
