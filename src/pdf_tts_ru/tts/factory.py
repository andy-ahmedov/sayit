from __future__ import annotations

from pdf_tts_ru.models import SynthesisRequest, TtsEngineKind
from pdf_tts_ru.tts.base import TtsEngine
from pdf_tts_ru.tts.piper_engine import PiperEngine
from pdf_tts_ru.tts.silero_engine import SileroEngine


def create_tts_engine(request: SynthesisRequest) -> TtsEngine:
    """Build a concrete TTS engine for the resolved synthesis request."""

    if request.engine == TtsEngineKind.PIPER:
        if request.voice_model is None:
            raise ValueError("voice model is required for Piper synthesis")
        return PiperEngine(request.voice_model, request.tts_settings)

    if request.engine == TtsEngineKind.SILERO:
        return SileroEngine(request.silero_settings)

    raise ValueError(f"unsupported TTS engine: {request.engine}")
