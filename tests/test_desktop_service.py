from __future__ import annotations

from pathlib import Path

import pytest

from pdf_tts_ru.gui.models import DesktopFormState
from pdf_tts_ru.gui.runtime import resolve_bundled_ffmpeg_path
from pdf_tts_ru.gui.service import DesktopAppService
from pdf_tts_ru.models import ProgressEvent, ProgressStage, TtsEngineKind


class FakePipeline:
    def __init__(self, progress_callback=None) -> None:
        self.progress_callback = progress_callback
        self.requests = []

    def run(self, request):
        self.requests.append(request)
        if self.progress_callback is not None:
            self.progress_callback(
                ProgressEvent(
                    stage=ProgressStage.SYNTHESIZING,
                    message="Synthesizing page 1",
                    page_number=1,
                )
            )
        output = request.output_dir / "result.mp3"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"audio")
        return [output]


def test_make_default_form_uses_runtime_ffmpeg(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "pdf_tts_ru.gui.service.resolve_bundled_ffmpeg_path",
        lambda: "C:/sayit/ffmpeg.exe",
    )

    form = DesktopAppService().make_default_form()

    assert form.ffmpeg_bin == "C:/sayit/ffmpeg.exe"


def test_save_and_load_form_config_round_trip(tmp_path: Path) -> None:
    service = DesktopAppService()
    original = service.make_default_form(input_path=Path("book.pdf"))
    original.pages_spec = "1-3"
    original.silero_model_id = "v5_4_ru"
    original.output_dir = tmp_path / "audio"

    config_path = tmp_path / "gui.toml"
    service.save_form_to_config(original, config_path)
    restored = service.load_form_from_config(
        config_path,
        input_path=original.input_path,
        pages_spec=original.pages_spec,
    )

    assert restored == original


def test_run_synthesis_validates_pages_and_emits_progress(tmp_path: Path) -> None:
    text_path = tmp_path / "sample.txt"
    text_path.write_text("Привет, мир.", encoding="utf-8")
    created_pipelines: list[FakePipeline] = []
    events: list[ProgressEvent] = []

    def pipeline_factory(progress_callback):
        pipeline = FakePipeline(progress_callback)
        created_pipelines.append(pipeline)
        return pipeline

    service = DesktopAppService(pipeline_factory=pipeline_factory)
    form = service.make_default_form(input_path=text_path)
    form.output_dir = tmp_path / "out"

    outputs = service.run_synthesis(form, progress_callback=events.append)

    assert outputs == [tmp_path / "out" / "result.mp3"]
    assert [event.stage for event in events] == [
        ProgressStage.INSPECTING,
        ProgressStage.SYNTHESIZING,
    ]
    assert created_pipelines[0].requests[0].pages == [1]


def test_run_synthesis_rejects_out_of_bounds_pages(tmp_path: Path) -> None:
    text_path = tmp_path / "sample.txt"
    text_path.write_text("Привет, мир.", encoding="utf-8")
    form = DesktopAppService().make_default_form(input_path=text_path)
    form.pages_spec = "2"

    with pytest.raises(ValueError, match="out of bounds"):
        DesktopAppService().run_synthesis(form)


def test_run_synthesis_requires_piper_voice_model(tmp_path: Path) -> None:
    text_path = tmp_path / "sample.txt"
    text_path.write_text("Привет, мир.", encoding="utf-8")
    form = DesktopAppService().make_default_form(input_path=text_path)
    form.engine = TtsEngineKind.PIPER
    form.voice_model = None

    with pytest.raises(ValueError, match="voice model is required for Piper"):
        DesktopAppService().run_synthesis(form)


def test_resolve_bundled_ffmpeg_path_prefers_bundle_root(tmp_path: Path) -> None:
    ffmpeg_path = tmp_path / "ffmpeg.exe"
    ffmpeg_path.write_text("", encoding="utf-8")

    resolved = resolve_bundled_ffmpeg_path(bundle_root=tmp_path)

    assert resolved == str(ffmpeg_path)
