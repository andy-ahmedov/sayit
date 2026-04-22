from __future__ import annotations

import wave
from dataclasses import dataclass, field
from pathlib import Path

from piper.config import SynthesisConfig as PiperConfig
from piper.voice import PiperVoice

from pdf_tts_ru.models import PiperSynthesisSettings


@dataclass(slots=True)
class PiperEngine:
    voice_model: Path
    tts_settings: PiperSynthesisSettings = field(default_factory=PiperSynthesisSettings)
    _voice: PiperVoice | None = field(default=None, init=False, repr=False)

    def synthesize_to_wav(self, text: str, output_wav: Path) -> None:
        """Synthesize Russian text using Piper."""

        if not text.strip():
            raise ValueError("cannot synthesize empty text")

        voice = self._load_voice()
        output_wav.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(output_wav), "wb") as wav_file:
            voice.synthesize_wav(
                text,
                wav_file,
                syn_config=self._build_config(),
            )

    def _load_voice(self) -> PiperVoice:
        if self._voice is not None:
            return self._voice

        if not self.voice_model.exists():
            raise FileNotFoundError(f"Piper voice model not found: {self.voice_model}")

        config_path = Path(f"{self.voice_model}.json")
        if not config_path.exists():
            raise FileNotFoundError(f"Piper voice config not found: {config_path}")

        try:
            self._voice = PiperVoice.load(self.voice_model, config_path=config_path)
        except Exception as exc:
            raise RuntimeError(f"failed to load Piper voice {self.voice_model}: {exc}") from exc

        return self._voice

    def _build_config(self) -> PiperConfig | None:
        if (
            self.tts_settings.length_scale is None
            and self.tts_settings.noise_scale is None
            and self.tts_settings.noise_w_scale is None
        ):
            return None

        return PiperConfig(
            length_scale=self.tts_settings.length_scale,
            noise_scale=self.tts_settings.noise_scale,
            noise_w_scale=self.tts_settings.noise_w_scale,
        )
