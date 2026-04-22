from __future__ import annotations

import importlib
import re
import wave
from array import array
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pdf_tts_ru.models import SileroSynthesisSettings
from pdf_tts_ru.tts.silero_text import prepare_text_for_silero

_SUPPORTED_SAMPLE_RATES = {8000, 24000, 48000}
_MAX_CHARS_PER_CHUNK = 900
_CHUNK_PAUSE_MS = 120


@dataclass(slots=True)
class SileroEngine:
    """Synthesize Russian text with Silero TTS."""

    settings: SileroSynthesisSettings = field(default_factory=SileroSynthesisSettings)
    _model: Any | None = field(default=None, init=False, repr=False)

    def synthesize_to_wav(self, text: str, output_wav: Path) -> None:
        """Synthesize Russian text to a WAV file using Silero."""

        prepared_text = prepare_text_for_silero(text, self.settings)
        if not prepared_text.strip():
            raise ValueError("cannot synthesize empty text")

        if self.settings.sample_rate not in _SUPPORTED_SAMPLE_RATES:
            allowed = ", ".join(str(rate) for rate in sorted(_SUPPORTED_SAMPLE_RATES))
            raise ValueError(
                f"unsupported Silero sample rate {self.settings.sample_rate}; "
                f"expected one of: {allowed}"
            )

        model = self._load_model()
        chunks = _split_text_into_chunks(prepared_text, max_chars=_MAX_CHARS_PER_CHUNK)
        pcm_frames = b""
        for index, chunk in enumerate(chunks):
            if index > 0:
                pcm_frames += self._chunk_pause()
            pcm_frames += self._synthesize_text(model, chunk)

        output_wav.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(output_wav), "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(self.settings.sample_rate)
            wav_file.writeframes(pcm_frames)

    def _load_model(self) -> Any:
        if self._model is not None:
            return self._model

        try:
            torch = importlib.import_module("torch")
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "Silero requires the 'torch' package; install the optional dependency set "
                "or run 'python -m pip install --index-url https://download.pytorch.org/whl/cpu torch'"
            ) from exc

        try:
            silero_module = importlib.import_module("silero")
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "Silero requires the 'silero' package; install it with "
                "'python -m pip install silero'"
            ) from exc

        try:
            device = torch.device(self.settings.device)
        except Exception as exc:
            raise ValueError(f"invalid Silero device {self.settings.device!r}: {exc}") from exc

        try:
            self._model, _example_text = silero_module.silero_tts(
                language="ru",
                speaker=self.settings.model_id,
            )
            self._model.to(device)
        except Exception as exc:
            raise RuntimeError(
                "failed to load Silero model "
                f"{self.settings.model_id!r}; verify the model id, network access for the "
                f"first download, and installed runtime dependencies: {exc}"
            ) from exc

        return self._model

    def _synthesize_chunk(self, model: Any, text: str) -> bytes:
        try:
            audio = model.apply_tts(
                text=text,
                speaker=self.settings.speaker,
                sample_rate=self.settings.sample_rate,
            )
        except Exception as exc:
            raise RuntimeError(
                "failed to synthesize with Silero "
                f"(model_id={self.settings.model_id}, speaker={self.settings.speaker}): {exc}"
            ) from exc

        return _to_pcm16_bytes(audio)

    def _synthesize_text(self, model: Any, text: str) -> bytes:
        try:
            return self._synthesize_chunk(model, text)
        except RuntimeError as exc:
            if not _is_silero_too_long_error(exc):
                raise

        retry_chunks = _split_retry_chunk(text)
        if len(retry_chunks) <= 1:
            raise RuntimeError(
                "failed to synthesize with Silero "
                f"(model_id={self.settings.model_id}, speaker={self.settings.speaker}): "
                "text is still too long after retry splitting"
            )

        pcm_frames = b""
        for index, chunk in enumerate(retry_chunks):
            if index > 0:
                pcm_frames += self._chunk_pause()
            pcm_frames += self._synthesize_text(model, chunk)
        return pcm_frames

    def _chunk_pause(self) -> bytes:
        return _build_silence(
            sample_rate=self.settings.sample_rate,
            duration_ms=_CHUNK_PAUSE_MS,
        )


def _to_pcm16_bytes(audio: Any) -> bytes:
    normalized = audio
    if hasattr(normalized, "detach"):
        normalized = normalized.detach()
    if hasattr(normalized, "cpu"):
        normalized = normalized.cpu()
    if hasattr(normalized, "numpy"):
        normalized = normalized.numpy()
    if hasattr(normalized, "tolist"):
        normalized = normalized.tolist()

    if not isinstance(normalized, list):
        normalized = list(normalized)
    if normalized and isinstance(normalized[0], list):
        normalized = normalized[0]

    pcm = array("h")
    for sample in normalized:
        value = float(sample)
        clamped = max(-1.0, min(1.0, value))
        pcm.append(int(clamped * 32767))
    return pcm.tobytes()


def _split_text_into_chunks(text: str, *, max_chars: int) -> list[str]:
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    if not paragraphs:
        return [text.strip()]

    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        if len(paragraph) > max_chars:
            if current:
                chunks.append(current)
                current = ""
            chunks.extend(_split_long_part(paragraph, max_chars=max_chars))
            continue

        candidate = f"{current}\n\n{paragraph}" if current else paragraph
        if len(candidate) <= max_chars:
            current = candidate
            continue

        if current:
            chunks.append(current)
        current = paragraph

    if current:
        chunks.append(current)
    return chunks


def _split_long_part(text: str, *, max_chars: int) -> list[str]:
    sentences = [part.strip() for part in re.split(r"(?<=[.!?…])\s+", text) if part.strip()]
    if not sentences:
        sentences = [text.strip()]

    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        if len(sentence) > max_chars:
            if current:
                chunks.append(current)
                current = ""
            chunks.extend(_split_long_sentence(sentence, max_chars=max_chars))
            continue

        candidate = f"{current} {sentence}".strip() if current else sentence
        if len(candidate) <= max_chars:
            current = candidate
            continue

        if current:
            chunks.append(current)
        current = sentence

    if current:
        chunks.append(current)
    return chunks


def _split_long_sentence(text: str, *, max_chars: int) -> list[str]:
    words = text.split()
    if not words:
        return [text.strip()]

    chunks: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip() if current else word
        if len(candidate) <= max_chars:
            current = candidate
            continue

        if current:
            chunks.append(current)
            current = word
            continue

        while len(word) > max_chars:
            chunks.append(word[:max_chars])
            word = word[max_chars:]
        current = word

    if current:
        chunks.append(current)
    return chunks


def _build_silence(*, sample_rate: int, duration_ms: int) -> bytes:
    frame_count = round(sample_rate * (duration_ms / 1000))
    return b"\x00\x00" * frame_count
def _is_silero_too_long_error(exc: RuntimeError) -> bool:
    message = str(exc).lower()
    return "too long" in message or "size of tensor a" in message


def _split_retry_chunk(text: str) -> list[str]:
    for splitter in (_split_retry_by_lines, _split_retry_by_sentences, _split_retry_by_words):
        chunks = splitter(text)
        if len(chunks) > 1:
            return chunks
    return _split_retry_by_midpoint(text)


def _split_retry_by_lines(text: str) -> list[str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(lines) < 2:
        return [text]
    midpoint = len(lines) // 2
    return ["\n".join(lines[:midpoint]), "\n".join(lines[midpoint:])]


def _split_retry_by_sentences(text: str) -> list[str]:
    sentences = [part.strip() for part in re.split(r"(?<=[.!?…])\s+", text) if part.strip()]
    if len(sentences) < 2:
        return [text]
    midpoint = len(sentences) // 2
    return [" ".join(sentences[:midpoint]), " ".join(sentences[midpoint:])]


def _split_retry_by_words(text: str) -> list[str]:
    words = text.split()
    if len(words) < 2:
        return [text]
    midpoint = len(words) // 2
    return [" ".join(words[:midpoint]), " ".join(words[midpoint:])]


def _split_retry_by_midpoint(text: str) -> list[str]:
    stripped = text.strip()
    if len(stripped) < 2:
        return [stripped]

    midpoint = len(stripped) // 2
    split_at = stripped.rfind(" ", 0, midpoint)
    if split_at == -1:
        split_at = stripped.find(" ", midpoint)
    if split_at == -1:
        split_at = midpoint

    left = stripped[:split_at].strip()
    right = stripped[split_at:].strip()
    return [part for part in (left, right) if part]
