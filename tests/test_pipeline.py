from __future__ import annotations

import wave
from pathlib import Path

import fitz
import pytest

from pdf_tts_ru.models import (
    OutputFormat,
    PiperSynthesisSettings,
    SileroSynthesisSettings,
    SplitMode,
    SynthesisRequest,
    TableStrategy,
    TtsEngineKind,
)
from pdf_tts_ru.pipeline import PdfTtsPipeline


class FakeEngine:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def synthesize_to_wav(self, text: str, output_wav: Path) -> None:
        self.calls.append(text)
        output_wav.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(output_wav), "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(16000)
            wav_file.writeframes(b"\x00\x00" * 1600)


def test_pipeline_per_page_creates_page_and_table_outputs(tmp_path: Path) -> None:
    pdf_path = create_table_pdf(tmp_path / "sample.pdf")
    request = SynthesisRequest(
        input_path=pdf_path,
        output_dir=tmp_path / "out",
        pages=[2],
        split_mode=SplitMode.PER_PAGE,
        output_format=OutputFormat.WAV,
        engine=TtsEngineKind.PIPER,
        voice_model=Path("unused.onnx"),
        table_strategy=TableStrategy.SEPARATE,
        tts_settings=PiperSynthesisSettings(),
    )

    outputs = PdfTtsPipeline(engine=FakeEngine()).run(request)

    assert outputs == [
        tmp_path / "out" / "sample_page_0002.wav",
        tmp_path / "out" / "sample_page_0002_table_01.wav",
    ]
    assert all(path.exists() for path in outputs)


def test_pipeline_merged_inserts_pause_between_pages(tmp_path: Path) -> None:
    pdf_path = create_prose_pdf(tmp_path / "sample.pdf")
    request = SynthesisRequest(
        input_path=pdf_path,
        output_dir=tmp_path / "out",
        pages=[1, 2],
        split_mode=SplitMode.MERGED,
        output_format=OutputFormat.WAV,
        engine=TtsEngineKind.PIPER,
        voice_model=Path("unused.onnx"),
        table_strategy=TableStrategy.SKIP,
        pause_between_pages_ms=200,
        tts_settings=PiperSynthesisSettings(),
    )

    outputs = PdfTtsPipeline(engine=FakeEngine()).run(request)

    assert outputs == [tmp_path / "out" / "sample_merged_pages_0001-0002.wav"]
    with wave.open(str(outputs[0]), "rb") as wav_file:
        assert wav_file.getframerate() == 16000
        assert wav_file.getnframes() == 6400


def test_pipeline_uses_factory_for_silero_requests(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    pdf_path = create_prose_pdf(tmp_path / "sample.pdf")
    request = SynthesisRequest(
        input_path=pdf_path,
        output_dir=tmp_path / "out",
        pages=[1],
        split_mode=SplitMode.PER_PAGE,
        output_format=OutputFormat.WAV,
        engine=TtsEngineKind.SILERO,
        table_strategy=TableStrategy.SKIP,
        silero_settings=SileroSynthesisSettings(),
    )
    created_for: list[TtsEngineKind] = []

    def fake_create_tts_engine(resolved_request: SynthesisRequest) -> FakeEngine:
        created_for.append(resolved_request.engine)
        return FakeEngine()

    monkeypatch.setattr("pdf_tts_ru.pipeline.create_tts_engine", fake_create_tts_engine)

    outputs = PdfTtsPipeline().run(request)

    assert created_for == [TtsEngineKind.SILERO]
    assert outputs == [tmp_path / "out" / "sample_page_0001.wav"]


def test_pipeline_normalizes_text_before_tts(tmp_path: Path) -> None:
    pdf_path = create_prose_pdf_with_whitespace(tmp_path / "sample.pdf")
    engine = FakeEngine()
    request = SynthesisRequest(
        input_path=pdf_path,
        output_dir=tmp_path / "out",
        pages=[1],
        split_mode=SplitMode.PER_PAGE,
        output_format=OutputFormat.WAV,
        engine=TtsEngineKind.PIPER,
        voice_model=Path("unused.onnx"),
        table_strategy=TableStrategy.SKIP,
        announce_page_numbers=True,
        tts_settings=PiperSynthesisSettings(),
    )

    PdfTtsPipeline(engine=engine).run(request)

    assert engine.calls == ["Страница 1.\n\nHello world\nThis is test"]


def test_pipeline_supports_text_input(tmp_path: Path) -> None:
    text_path = tmp_path / "sample.txt"
    text_path.write_text("Первая строка.\n\nВторая строка.", encoding="utf-8")
    request = SynthesisRequest(
        input_path=text_path,
        output_dir=tmp_path / "out",
        pages=[1],
        split_mode=SplitMode.PER_PAGE,
        output_format=OutputFormat.WAV,
        engine=TtsEngineKind.PIPER,
        voice_model=Path("unused.onnx"),
        table_strategy=TableStrategy.SKIP,
        tts_settings=PiperSynthesisSettings(),
    )

    outputs = PdfTtsPipeline(engine=FakeEngine()).run(request)

    assert outputs == [tmp_path / "out" / "sample_page_0001.wav"]


def test_pipeline_uses_silero_as_default_engine(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    pdf_path = create_prose_pdf(tmp_path / "sample.pdf")
    request = SynthesisRequest(
        input_path=pdf_path,
        output_dir=tmp_path / "out",
        pages=[1],
        split_mode=SplitMode.PER_PAGE,
        output_format=OutputFormat.WAV,
        table_strategy=TableStrategy.SKIP,
        silero_settings=SileroSynthesisSettings(),
    )
    created_for: list[TtsEngineKind] = []

    def fake_create_tts_engine(resolved_request: SynthesisRequest) -> FakeEngine:
        created_for.append(resolved_request.engine)
        return FakeEngine()

    monkeypatch.setattr("pdf_tts_ru.pipeline.create_tts_engine", fake_create_tts_engine)

    PdfTtsPipeline().run(request)

    assert created_for == [TtsEngineKind.SILERO]


def create_prose_pdf(path: Path) -> Path:
    document = fitz.open()
    first = document.new_page(width=300, height=300)
    first.insert_text((72, 72), "Hello page one.")
    second = document.new_page(width=300, height=300)
    second.insert_text((72, 72), "Hello page two.")
    document.save(path)
    document.close()
    return path


def create_prose_pdf_with_whitespace(path: Path) -> Path:
    document = fitz.open()
    page = document.new_page(width=300, height=300)
    page.insert_text((72, 72), "  Hello   world")
    page.insert_text((72, 100), " ")
    page.insert_text((72, 128), "This   is   test")
    document.save(path)
    document.close()
    return path


def create_table_pdf(path: Path) -> Path:
    document = fitz.open()
    first = document.new_page(width=400, height=400)
    first.insert_text((72, 72), "First page.")
    second = document.new_page(width=400, height=400)
    second.insert_text((72, 50), "Intro before table.")

    shape = second.new_shape()
    for y in (90, 130, 170):
        shape.draw_line((72, y), (272, y))
    for x in (72, 172, 272):
        shape.draw_line((x, 90), (x, 170))
    shape.finish(width=1)
    shape.commit()

    second.insert_text((84, 115), "Name")
    second.insert_text((184, 115), "Score")
    second.insert_text((84, 155), "Alice")
    second.insert_text((184, 155), "5")

    document.save(path)
    document.close()
    return path
