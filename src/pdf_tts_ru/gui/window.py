from __future__ import annotations

from pathlib import Path

from pdf_tts_ru.gui.models import DesktopFormState, DesktopInspectionSummary
from pdf_tts_ru.gui.service import DesktopAppService
from pdf_tts_ru.models import (
    OutputFormat,
    ProgressEvent,
    SileroLineBreakMode,
    SileroRate,
    SplitMode,
    TableStrategy,
    TtsEngineKind,
)


def _import_qt():
    from PySide6 import QtCore, QtGui, QtWidgets

    return QtCore, QtGui, QtWidgets


QtCore, QtGui, QtWidgets = _import_qt()


class SynthesisWorker(QtCore.QObject):
    """Run synthesis off the UI thread."""

    progress = QtCore.Signal(object)
    finished = QtCore.Signal(object)
    failed = QtCore.Signal(str)

    def __init__(self, service: DesktopAppService, form: DesktopFormState) -> None:
        super().__init__()
        self._service = service
        self._form = form

    @QtCore.Slot()
    def run(self) -> None:
        try:
            outputs = self._service.run_synthesis(
                self._form,
                progress_callback=self.progress.emit,
            )
        except Exception as exc:
            self.failed.emit(str(exc))
            return
        self.finished.emit(outputs)


class MainWindow(QtWidgets.QMainWindow):
    """Desktop UI for the local Russian document-to-audio pipeline."""

    def __init__(self, service: DesktopAppService | None = None) -> None:
        super().__init__()
        self._service = service or DesktopAppService()
        self._thread: QtCore.QThread | None = None
        self._worker: SynthesisWorker | None = None
        self._last_output_dir: Path | None = None
        self._last_inspection: DesktopInspectionSummary | None = None

        self.setWindowTitle("sayit")
        self.resize(1120, 840)

        self._build_ui()
        self._apply_form_state(self._service.make_default_form())
        self._set_busy(False)
        self._update_engine_fields()

    def _build_ui(self) -> None:
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        container = QtWidgets.QWidget()
        scroll.setWidget(container)
        self.setCentralWidget(scroll)

        layout = QtWidgets.QVBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        layout.addWidget(self._build_config_group())
        layout.addWidget(self._build_input_group())
        layout.addWidget(self._build_engine_group())
        layout.addWidget(self._build_output_group())
        layout.addWidget(self._build_run_group())

    def _build_config_group(self) -> QtWidgets.QGroupBox:
        group = QtWidgets.QGroupBox("Конфиг")
        layout = QtWidgets.QHBoxLayout(group)

        self.load_config_button = QtWidgets.QPushButton("Загрузить TOML")
        self.save_config_button = QtWidgets.QPushButton("Сохранить TOML как...")

        layout.addWidget(self.load_config_button)
        layout.addWidget(self.save_config_button)
        layout.addStretch(1)

        self.load_config_button.clicked.connect(self._load_config)
        self.save_config_button.clicked.connect(self._save_config)
        return group

    def _build_input_group(self) -> QtWidgets.QGroupBox:
        group = QtWidgets.QGroupBox("Документ")
        layout = QtWidgets.QGridLayout(group)

        self.input_path_edit = QtWidgets.QLineEdit()
        self.browse_input_button = QtWidgets.QPushButton("Выбрать файл")
        self.inspect_button = QtWidgets.QPushButton("Inspect")
        self.pages_edit = QtWidgets.QLineEdit("all")
        self.summary_text = QtWidgets.QPlainTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setMinimumHeight(140)

        layout.addWidget(QtWidgets.QLabel("Файл"), 0, 0)
        layout.addWidget(self.input_path_edit, 0, 1)
        layout.addWidget(self.browse_input_button, 0, 2)
        layout.addWidget(self.inspect_button, 0, 3)
        layout.addWidget(QtWidgets.QLabel("Страницы"), 1, 0)
        layout.addWidget(self.pages_edit, 1, 1, 1, 3)
        layout.addWidget(QtWidgets.QLabel("Инспекция"), 2, 0)
        layout.addWidget(self.summary_text, 3, 0, 1, 4)

        self.browse_input_button.clicked.connect(self._browse_input)
        self.inspect_button.clicked.connect(self._inspect_input)
        return group

    def _build_engine_group(self) -> QtWidgets.QGroupBox:
        group = QtWidgets.QGroupBox("Движок")
        layout = QtWidgets.QVBoxLayout(group)

        top_row = QtWidgets.QHBoxLayout()
        self.engine_combo = QtWidgets.QComboBox()
        self.engine_combo.addItem("Silero", TtsEngineKind.SILERO)
        self.engine_combo.addItem("Piper", TtsEngineKind.PIPER)
        top_row.addWidget(QtWidgets.QLabel("Engine"))
        top_row.addWidget(self.engine_combo)
        top_row.addStretch(1)
        layout.addLayout(top_row)

        self.silero_group = QtWidgets.QGroupBox("Silero")
        silero_layout = QtWidgets.QFormLayout(self.silero_group)
        self.silero_model_edit = QtWidgets.QLineEdit()
        self.silero_speaker_edit = QtWidgets.QLineEdit()
        self.silero_sample_rate_spin = QtWidgets.QSpinBox()
        self.silero_sample_rate_spin.setRange(8000, 96000)
        self.silero_sample_rate_spin.setSingleStep(8000)
        self.silero_rate_combo = QtWidgets.QComboBox()
        self.silero_rate_combo.addItem("(default)", None)
        for rate in SileroRate:
            self.silero_rate_combo.addItem(rate.value, rate)
        self.silero_device_edit = QtWidgets.QLineEdit()
        self.silero_line_break_combo = QtWidgets.QComboBox()
        for mode in SileroLineBreakMode:
            self.silero_line_break_combo.addItem(mode.value, mode)
        self.silero_transliterate_checkbox = QtWidgets.QCheckBox("Транслитерировать Latin")
        self.silero_numbers_checkbox = QtWidgets.QCheckBox("Озвучивать числа словами")
        self.silero_abbrev_checkbox = QtWidgets.QCheckBox("Читать кириллические аббревиатуры по буквам")
        self.silero_units_checkbox = QtWidgets.QCheckBox("Разворачивать короткие единицы измерения")

        silero_layout.addRow("Model ID", self.silero_model_edit)
        silero_layout.addRow("Speaker", self.silero_speaker_edit)
        silero_layout.addRow("Sample rate", self.silero_sample_rate_spin)
        silero_layout.addRow("Speech rate", self.silero_rate_combo)
        silero_layout.addRow("Device", self.silero_device_edit)
        silero_layout.addRow("Line breaks", self.silero_line_break_combo)
        silero_layout.addRow("", self.silero_transliterate_checkbox)
        silero_layout.addRow("", self.silero_numbers_checkbox)
        silero_layout.addRow("", self.silero_abbrev_checkbox)
        silero_layout.addRow("", self.silero_units_checkbox)

        self.piper_group = QtWidgets.QGroupBox("Piper")
        piper_layout = QtWidgets.QFormLayout(self.piper_group)
        self.voice_model_edit = QtWidgets.QLineEdit()
        self.browse_voice_button = QtWidgets.QPushButton("Выбрать .onnx")
        voice_row = QtWidgets.QHBoxLayout()
        voice_row.setContentsMargins(0, 0, 0, 0)
        voice_row.addWidget(self.voice_model_edit)
        voice_row.addWidget(self.browse_voice_button)
        voice_container = QtWidgets.QWidget()
        voice_container.setLayout(voice_row)
        self.length_scale_edit = QtWidgets.QLineEdit()
        self.noise_scale_edit = QtWidgets.QLineEdit()
        self.noise_w_scale_edit = QtWidgets.QLineEdit()
        self.length_scale_edit.setPlaceholderText("default")
        self.noise_scale_edit.setPlaceholderText("default")
        self.noise_w_scale_edit.setPlaceholderText("default")
        piper_layout.addRow("Voice model", voice_container)
        piper_layout.addRow("length_scale", self.length_scale_edit)
        piper_layout.addRow("noise_scale", self.noise_scale_edit)
        piper_layout.addRow("noise_w_scale", self.noise_w_scale_edit)

        self.browse_voice_button.clicked.connect(self._browse_voice_model)
        self.engine_combo.currentIndexChanged.connect(self._update_engine_fields)

        layout.addWidget(self.silero_group)
        layout.addWidget(self.piper_group)
        return group

    def _build_output_group(self) -> QtWidgets.QGroupBox:
        group = QtWidgets.QGroupBox("Выход")
        layout = QtWidgets.QFormLayout(group)

        self.output_dir_edit = QtWidgets.QLineEdit()
        self.browse_output_button = QtWidgets.QPushButton("Папка...")
        output_row = QtWidgets.QHBoxLayout()
        output_row.setContentsMargins(0, 0, 0, 0)
        output_row.addWidget(self.output_dir_edit)
        output_row.addWidget(self.browse_output_button)
        output_container = QtWidgets.QWidget()
        output_container.setLayout(output_row)

        self.output_format_combo = QtWidgets.QComboBox()
        for fmt in OutputFormat:
            self.output_format_combo.addItem(fmt.value, fmt)
        self.split_mode_combo = QtWidgets.QComboBox()
        for mode in SplitMode:
            self.split_mode_combo.addItem(mode.value, mode)
        self.table_strategy_combo = QtWidgets.QComboBox()
        for strategy in TableStrategy:
            self.table_strategy_combo.addItem(strategy.value, strategy)
        self.announce_checkbox = QtWidgets.QCheckBox("Озвучивать номера страниц")
        self.pause_spin = QtWidgets.QSpinBox()
        self.pause_spin.setRange(0, 10000)
        self.pause_spin.setSuffix(" ms")
        self.ffmpeg_edit = QtWidgets.QLineEdit()

        layout.addRow("Папка результата", output_container)
        layout.addRow("Формат", self.output_format_combo)
        layout.addRow("Split mode", self.split_mode_combo)
        layout.addRow("Таблицы", self.table_strategy_combo)
        layout.addRow("", self.announce_checkbox)
        layout.addRow("Пауза между страницами", self.pause_spin)
        layout.addRow("ffmpeg", self.ffmpeg_edit)

        self.browse_output_button.clicked.connect(self._browse_output_dir)
        return group

    def _build_run_group(self) -> QtWidgets.QGroupBox:
        group = QtWidgets.QGroupBox("Запуск")
        layout = QtWidgets.QVBoxLayout(group)

        buttons_row = QtWidgets.QHBoxLayout()
        self.run_button = QtWidgets.QPushButton("Озвучить")
        self.open_output_button = QtWidgets.QPushButton("Открыть папку результата")
        buttons_row.addWidget(self.run_button)
        buttons_row.addWidget(self.open_output_button)
        buttons_row.addStretch(1)

        self.status_label = QtWidgets.QLabel("Готово")
        self.log_text = QtWidgets.QPlainTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(180)
        self.outputs_list = QtWidgets.QListWidget()
        self.outputs_list.setMinimumHeight(120)

        layout.addLayout(buttons_row)
        layout.addWidget(self.status_label)
        layout.addWidget(QtWidgets.QLabel("Лог"))
        layout.addWidget(self.log_text)
        layout.addWidget(QtWidgets.QLabel("Файлы результата"))
        layout.addWidget(self.outputs_list)

        self.run_button.clicked.connect(self._start_synthesis)
        self.open_output_button.clicked.connect(self._open_output_folder)
        return group

    def _browse_input(self) -> None:
        path, _selected = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Выберите документ",
            "",
            "Documents (*.pdf *.docx *.md *.txt *.doc);;All files (*)",
        )
        if not path:
            return
        self.input_path_edit.setText(path)
        self._inspect_input()

    def _browse_voice_model(self) -> None:
        path, _selected = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Выберите Piper voice model",
            "",
            "ONNX model (*.onnx);;All files (*)",
        )
        if path:
            self.voice_model_edit.setText(path)

    def _browse_output_dir(self) -> None:
        path = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "Выберите папку результата",
            self.output_dir_edit.text() or "",
        )
        if path:
            self.output_dir_edit.setText(path)

    def _inspect_input(self) -> None:
        try:
            input_path = self._current_input_path()
            summary = self._service.inspect_input(input_path)
        except Exception as exc:
            self._show_error(str(exc))
            return

        self._last_inspection = summary
        self.summary_text.setPlainText(summary.render_text())
        self.status_label.setText(f"Страниц: {summary.page_count}")
        self._append_log(f"[inspect] {input_path}")

    def _load_config(self) -> None:
        path, _selected = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Загрузить конфиг",
            "",
            "TOML (*.toml);;All files (*)",
        )
        if not path:
            return

        current = self._collect_form_state()
        try:
            form = self._service.load_form_from_config(
                Path(path),
                input_path=current.input_path,
                pages_spec=current.pages_spec,
            )
        except Exception as exc:
            self._show_error(str(exc))
            return

        self._apply_form_state(form)
        self._append_log(f"[config] loaded {path}")

    def _save_config(self) -> None:
        path, _selected = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Сохранить конфиг",
            "config.toml",
            "TOML (*.toml)",
        )
        if not path:
            return

        try:
            self._service.save_form_to_config(self._collect_form_state(), Path(path))
        except Exception as exc:
            self._show_error(str(exc))
            return

        self._append_log(f"[config] saved {path}")

    def _start_synthesis(self) -> None:
        try:
            form = self._collect_form_state()
            if form.input_path is None:
                raise ValueError("input file is required")
        except Exception as exc:
            self._show_error(str(exc))
            return

        self.outputs_list.clear()
        self.log_text.clear()
        self._append_log("[run] starting")
        self._set_busy(True)

        self._thread = QtCore.QThread(self)
        self._worker = SynthesisWorker(self._service, form)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self._handle_progress)
        self._worker.finished.connect(self._handle_finished)
        self._worker.failed.connect(self._handle_failed)
        self._worker.finished.connect(self._thread.quit)
        self._worker.failed.connect(self._thread.quit)
        self._thread.finished.connect(self._cleanup_worker)
        self._thread.start()

    def _handle_progress(self, event: ProgressEvent) -> None:
        self.status_label.setText(event.message)
        self._append_log(f"[{event.stage.value}] {event.message}")

    def _handle_finished(self, outputs: object) -> None:
        output_paths = [Path(item) for item in outputs]
        for path in output_paths:
            self.outputs_list.addItem(str(path))
        if output_paths:
            self._last_output_dir = output_paths[0].parent
        self.status_label.setText("Готово")
        self._append_log("[done] synthesis completed")
        self._set_busy(False)

    def _handle_failed(self, message: str) -> None:
        self.status_label.setText("Ошибка")
        self._append_log(f"[error] {message}")
        self._set_busy(False)
        self._show_error(message)

    def _cleanup_worker(self) -> None:
        if self._worker is not None:
            self._worker.deleteLater()
            self._worker = None
        if self._thread is not None:
            self._thread.deleteLater()
            self._thread = None

    def _open_output_folder(self) -> None:
        directory = self._resolve_output_directory()
        if directory is None:
            self._show_error("output directory is not available yet")
            return
        QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(str(directory)))

    def _resolve_output_directory(self) -> Path | None:
        candidates = []
        if self._last_output_dir is not None:
            candidates.append(self._last_output_dir)
        output_dir_text = self.output_dir_edit.text().strip()
        if output_dir_text:
            candidates.append(Path(output_dir_text))
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return None

    def _collect_form_state(self) -> DesktopFormState:
        return DesktopFormState(
            input_path=self._optional_path(self.input_path_edit.text()),
            pages_spec=self.pages_edit.text().strip() or "all",
            output_dir=self._required_path(self.output_dir_edit.text(), field_name="output_dir"),
            engine=self._current_combo_value(self.engine_combo),
            voice_model=self._optional_path(self.voice_model_edit.text()),
            ffmpeg_bin=self.ffmpeg_edit.text().strip() or "ffmpeg",
            output_format=self._current_combo_value(self.output_format_combo),
            split_mode=self._current_combo_value(self.split_mode_combo),
            table_strategy=self._current_combo_value(self.table_strategy_combo),
            announce_page_numbers=self.announce_checkbox.isChecked(),
            pause_between_pages_ms=self.pause_spin.value(),
            length_scale=self._optional_float(self.length_scale_edit.text(), "length_scale"),
            noise_scale=self._optional_float(self.noise_scale_edit.text(), "noise_scale"),
            noise_w_scale=self._optional_float(self.noise_w_scale_edit.text(), "noise_w_scale"),
            silero_model_id=self.silero_model_edit.text().strip() or "v5_5_ru",
            silero_speaker=self.silero_speaker_edit.text().strip() or "xenia",
            silero_sample_rate=self.silero_sample_rate_spin.value(),
            silero_rate=self._current_combo_value(self.silero_rate_combo),
            silero_device=self.silero_device_edit.text().strip() or "cpu",
            silero_line_break_mode=self._current_combo_value(self.silero_line_break_combo),
            silero_transliterate_latin=self.silero_transliterate_checkbox.isChecked(),
            silero_verbalize_numbers=self.silero_numbers_checkbox.isChecked(),
            silero_spell_cyrillic_abbreviations=self.silero_abbrev_checkbox.isChecked(),
            silero_expand_short_units=self.silero_units_checkbox.isChecked(),
        )

    def _apply_form_state(self, form: DesktopFormState) -> None:
        self.input_path_edit.setText(str(form.input_path) if form.input_path is not None else "")
        self.pages_edit.setText(form.pages_spec)
        self.output_dir_edit.setText(str(form.output_dir))
        self._set_combo_value(self.engine_combo, form.engine)
        self.voice_model_edit.setText(str(form.voice_model) if form.voice_model is not None else "")
        self.ffmpeg_edit.setText(form.ffmpeg_bin)
        self._set_combo_value(self.output_format_combo, form.output_format)
        self._set_combo_value(self.split_mode_combo, form.split_mode)
        self._set_combo_value(self.table_strategy_combo, form.table_strategy)
        self.announce_checkbox.setChecked(form.announce_page_numbers)
        self.pause_spin.setValue(form.pause_between_pages_ms)
        self.length_scale_edit.setText("" if form.length_scale is None else str(form.length_scale))
        self.noise_scale_edit.setText("" if form.noise_scale is None else str(form.noise_scale))
        self.noise_w_scale_edit.setText("" if form.noise_w_scale is None else str(form.noise_w_scale))
        self.silero_model_edit.setText(form.silero_model_id)
        self.silero_speaker_edit.setText(form.silero_speaker)
        self.silero_sample_rate_spin.setValue(form.silero_sample_rate)
        self._set_combo_value(self.silero_rate_combo, form.silero_rate)
        self.silero_device_edit.setText(form.silero_device)
        self._set_combo_value(self.silero_line_break_combo, form.silero_line_break_mode)
        self.silero_transliterate_checkbox.setChecked(form.silero_transliterate_latin)
        self.silero_numbers_checkbox.setChecked(form.silero_verbalize_numbers)
        self.silero_abbrev_checkbox.setChecked(form.silero_spell_cyrillic_abbreviations)
        self.silero_units_checkbox.setChecked(form.silero_expand_short_units)
        self._update_engine_fields()

    def _update_engine_fields(self) -> None:
        engine = self._current_combo_value(self.engine_combo)
        self.silero_group.setVisible(engine == TtsEngineKind.SILERO)
        self.piper_group.setVisible(engine == TtsEngineKind.PIPER)

    def _set_busy(self, busy: bool) -> None:
        self.run_button.setEnabled(not busy)
        self.inspect_button.setEnabled(not busy)
        self.load_config_button.setEnabled(not busy)
        self.save_config_button.setEnabled(not busy)
        self.open_output_button.setEnabled(not busy)

    def _append_log(self, message: str) -> None:
        self.log_text.appendPlainText(message)

    def _show_error(self, message: str) -> None:
        QtWidgets.QMessageBox.critical(self, "sayit", message)

    def _current_input_path(self) -> Path:
        return self._required_path(self.input_path_edit.text(), field_name="input")

    @staticmethod
    def _current_combo_value(combo: QtWidgets.QComboBox):
        return combo.currentData()

    @staticmethod
    def _set_combo_value(combo: QtWidgets.QComboBox, value: object) -> None:
        for index in range(combo.count()):
            if combo.itemData(index) == value:
                combo.setCurrentIndex(index)
                return
        combo.setCurrentIndex(0)

    @staticmethod
    def _optional_path(raw_value: str) -> Path | None:
        normalized = raw_value.strip()
        if not normalized:
            return None
        return Path(normalized)

    @staticmethod
    def _required_path(raw_value: str, *, field_name: str) -> Path:
        normalized = raw_value.strip()
        if not normalized:
            raise ValueError(f"{field_name} is required")
        return Path(normalized)

    @staticmethod
    def _optional_float(raw_value: str, field_name: str) -> float | None:
        normalized = raw_value.strip()
        if not normalized:
            return None
        try:
            return float(normalized)
        except ValueError as exc:
            raise ValueError(f"{field_name} must be a number") from exc
