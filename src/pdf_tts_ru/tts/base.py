from __future__ import annotations

from pathlib import Path
from typing import Protocol


class TtsEngine(Protocol):
    def synthesize_to_wav(self, text: str, output_wav: Path) -> None:
        """Synthesize text to a WAV file."""
        ...
