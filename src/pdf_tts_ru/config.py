from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TypeVar

from pdf_tts_ru.models import (
    normalize_silero_rate,
    OutputFormat,
    PiperSynthesisSettings,
    SileroLineBreakMode,
    SileroRate,
    SileroSynthesisSettings,
    SplitMode,
    SynthesisRequest,
    TableStrategy,
    TtsEngineKind,
)


TEnum = TypeVar(
    "TEnum",
    SplitMode,
    OutputFormat,
    TableStrategy,
    TtsEngineKind,
    SileroLineBreakMode,
)

_KNOWN_CONFIG_KEYS = {
    "engine",
    "voice_model",
    "ffmpeg_bin",
    "output_format",
    "split_mode",
    "table_strategy",
    "announce_page_numbers",
    "pause_between_pages_ms",
    "length_scale",
    "noise_scale",
    "noise_w_scale",
    "output_dir",
    "silero_model_id",
    "silero_speaker",
    "silero_sample_rate",
    "silero_rate",
    "silero_device",
    "silero_line_break_mode",
    "silero_transliterate_latin",
    "silero_verbalize_numbers",
    "silero_spell_cyrillic_abbreviations",
    "silero_expand_short_units",
}


@dataclass(slots=True)
class SynthesisConfig:
    """Optional TOML-backed defaults for the synth command."""

    engine: TtsEngineKind = TtsEngineKind.SILERO
    voice_model: Path | None = None
    ffmpeg_bin: str = "ffmpeg"
    output_format: OutputFormat = OutputFormat.MP3
    split_mode: SplitMode = SplitMode.PER_PAGE
    table_strategy: TableStrategy = TableStrategy.INLINE
    announce_page_numbers: bool = False
    pause_between_pages_ms: int = 0
    length_scale: float | None = None
    noise_scale: float | None = None
    noise_w_scale: float | None = None
    output_dir: Path = Path("output")
    silero_model_id: str = "v5_5_ru"
    silero_speaker: str = "xenia"
    silero_sample_rate: int = 48000
    silero_rate: SileroRate | None = None
    silero_device: str = "cpu"
    silero_line_break_mode: SileroLineBreakMode = SileroLineBreakMode.SMART
    silero_transliterate_latin: bool = True
    silero_verbalize_numbers: bool = True
    silero_spell_cyrillic_abbreviations: bool = True
    silero_expand_short_units: bool = True


def load_synthesis_config(path: Path) -> SynthesisConfig:
    """Load synthesis defaults from a TOML file."""

    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"config file not found: {path}") from exc
    except tomllib.TOMLDecodeError as exc:
        raise ValueError(f"invalid TOML in config file {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError(f"config file must contain a top-level table: {path}")

    unknown = sorted(set(data) - _KNOWN_CONFIG_KEYS)
    if unknown:
        raise ValueError(f"unknown config keys in {path}: {', '.join(unknown)}")

    return SynthesisConfig(
        engine=_get_enum(data, "engine", TtsEngineKind, TtsEngineKind.SILERO),
        voice_model=_get_path(data, "voice_model"),
        ffmpeg_bin=_get_string(data, "ffmpeg_bin", "ffmpeg"),
        output_format=_get_enum(data, "output_format", OutputFormat, OutputFormat.MP3),
        split_mode=_get_enum(data, "split_mode", SplitMode, SplitMode.PER_PAGE),
        table_strategy=_get_enum(data, "table_strategy", TableStrategy, TableStrategy.INLINE),
        announce_page_numbers=_get_bool(data, "announce_page_numbers", False),
        pause_between_pages_ms=_get_int(data, "pause_between_pages_ms", 0),
        length_scale=_get_float(data, "length_scale"),
        noise_scale=_get_float(data, "noise_scale"),
        noise_w_scale=_get_float(data, "noise_w_scale"),
        output_dir=_get_path(data, "output_dir") or Path("output"),
        silero_model_id=_get_string(data, "silero_model_id", "v5_5_ru"),
        silero_speaker=_get_string(data, "silero_speaker", "xenia"),
        silero_sample_rate=_get_int(data, "silero_sample_rate", 48000),
        silero_rate=normalize_silero_rate(_get_optional_string(data, "silero_rate")),
        silero_device=_get_string(data, "silero_device", "cpu"),
        silero_line_break_mode=_get_enum(
            data,
            "silero_line_break_mode",
            SileroLineBreakMode,
            SileroLineBreakMode.SMART,
        ),
        silero_transliterate_latin=_get_bool(data, "silero_transliterate_latin", True),
        silero_verbalize_numbers=_get_bool(data, "silero_verbalize_numbers", True),
        silero_spell_cyrillic_abbreviations=_get_bool(
            data,
            "silero_spell_cyrillic_abbreviations",
            True,
        ),
        silero_expand_short_units=_get_bool(data, "silero_expand_short_units", True),
    )


def render_synthesis_config(config: SynthesisConfig) -> str:
    """Render a synthesis config dataclass into a TOML document."""

    fields: list[tuple[str, Any]] = [
        ("engine", config.engine.value),
        ("voice_model", config.voice_model),
        ("ffmpeg_bin", config.ffmpeg_bin),
        ("output_format", config.output_format.value),
        ("split_mode", config.split_mode.value),
        ("table_strategy", config.table_strategy.value),
        ("announce_page_numbers", config.announce_page_numbers),
        ("pause_between_pages_ms", config.pause_between_pages_ms),
        ("length_scale", config.length_scale),
        ("noise_scale", config.noise_scale),
        ("noise_w_scale", config.noise_w_scale),
        ("output_dir", config.output_dir),
        ("silero_model_id", config.silero_model_id),
        ("silero_speaker", config.silero_speaker),
        ("silero_sample_rate", config.silero_sample_rate),
        ("silero_rate", config.silero_rate.value if config.silero_rate is not None else None),
        ("silero_device", config.silero_device),
        ("silero_line_break_mode", config.silero_line_break_mode.value),
        ("silero_transliterate_latin", config.silero_transliterate_latin),
        ("silero_verbalize_numbers", config.silero_verbalize_numbers),
        (
            "silero_spell_cyrillic_abbreviations",
            config.silero_spell_cyrillic_abbreviations,
        ),
        ("silero_expand_short_units", config.silero_expand_short_units),
    ]
    lines = [
        f"{key} = {_format_toml_value(value)}"
        for key, value in fields
        if value is not None
    ]
    return "\n".join(lines) + "\n"


def save_synthesis_config(path: Path, config: SynthesisConfig) -> None:
    """Write a synthesis config dataclass to a TOML file."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_synthesis_config(config), encoding="utf-8")


def resolve_synthesis_request(
    *,
    input_path: Path,
    pages: list[int],
    output_dir: Path | None = None,
    engine: TtsEngineKind | None = None,
    voice_model: Path | None = None,
    ffmpeg_bin: str | None = None,
    output_format: OutputFormat | None = None,
    split_mode: SplitMode | None = None,
    table_strategy: TableStrategy | None = None,
    announce_page_numbers: bool | None = None,
    pause_between_pages_ms: int | None = None,
    length_scale: float | None = None,
    noise_scale: float | None = None,
    noise_w_scale: float | None = None,
    silero_model_id: str | None = None,
    silero_speaker: str | None = None,
    silero_sample_rate: int | None = None,
    silero_rate: str | SileroRate | None = None,
    silero_device: str | None = None,
    silero_line_break_mode: SileroLineBreakMode | None = None,
    silero_transliterate_latin: bool | None = None,
    silero_verbalize_numbers: bool | None = None,
    silero_spell_cyrillic_abbreviations: bool | None = None,
    silero_expand_short_units: bool | None = None,
    config: SynthesisConfig | None = None,
) -> SynthesisRequest:
    """Merge CLI values with optional config and return a complete request."""

    defaults = config or SynthesisConfig()
    resolved_engine = engine or defaults.engine
    resolved_voice_model = voice_model or defaults.voice_model

    resolved_pause = (
        pause_between_pages_ms
        if pause_between_pages_ms is not None
        else defaults.pause_between_pages_ms
    )
    if resolved_pause < 0:
        raise ValueError("pause_between_pages_ms must be zero or positive")

    resolved_silero_sample_rate = (
        silero_sample_rate
        if silero_sample_rate is not None
        else defaults.silero_sample_rate
    )
    if resolved_silero_sample_rate <= 0:
        raise ValueError("silero_sample_rate must be positive")

    resolved_silero_rate = (
        normalize_silero_rate(silero_rate)
        if silero_rate is not None
        else defaults.silero_rate
    )

    if resolved_engine == TtsEngineKind.PIPER and resolved_voice_model is None:
        raise ValueError(
            "voice model is required for Piper; pass --voice or set voice_model in config.toml"
        )

    return SynthesisRequest(
        input_path=input_path,
        output_dir=output_dir or defaults.output_dir,
        pages=pages,
        split_mode=split_mode or defaults.split_mode,
        output_format=output_format or defaults.output_format,
        engine=resolved_engine,
        voice_model=resolved_voice_model,
        ffmpeg_bin=ffmpeg_bin or defaults.ffmpeg_bin,
        table_strategy=table_strategy or defaults.table_strategy,
        announce_page_numbers=(
            announce_page_numbers
            if announce_page_numbers is not None
            else defaults.announce_page_numbers
        ),
        pause_between_pages_ms=resolved_pause,
        tts_settings=PiperSynthesisSettings(
            length_scale=length_scale if length_scale is not None else defaults.length_scale,
            noise_scale=noise_scale if noise_scale is not None else defaults.noise_scale,
            noise_w_scale=noise_w_scale if noise_w_scale is not None else defaults.noise_w_scale,
        ),
        silero_settings=SileroSynthesisSettings(
            model_id=(silero_model_id if silero_model_id is not None else defaults.silero_model_id),
            speaker=(silero_speaker if silero_speaker is not None else defaults.silero_speaker),
            sample_rate=resolved_silero_sample_rate,
            rate=resolved_silero_rate,
            device=silero_device if silero_device is not None else defaults.silero_device,
            line_break_mode=(
                silero_line_break_mode
                if silero_line_break_mode is not None
                else defaults.silero_line_break_mode
            ),
            transliterate_latin=(
                silero_transliterate_latin
                if silero_transliterate_latin is not None
                else defaults.silero_transliterate_latin
            ),
            verbalize_numbers=(
                silero_verbalize_numbers
                if silero_verbalize_numbers is not None
                else defaults.silero_verbalize_numbers
            ),
            spell_cyrillic_abbreviations=(
                silero_spell_cyrillic_abbreviations
                if silero_spell_cyrillic_abbreviations is not None
                else defaults.silero_spell_cyrillic_abbreviations
            ),
            expand_short_units=(
                silero_expand_short_units
                if silero_expand_short_units is not None
                else defaults.silero_expand_short_units
            ),
        ),
    )


def _get_path(data: dict[str, Any], key: str) -> Path | None:
    value = data.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"config key {key!r} must be a non-empty string")
    return Path(value)


def _get_string(data: dict[str, Any], key: str, default: str) -> str:
    value = data.get(key, default)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"config key {key!r} must be a non-empty string")
    return value


def _get_optional_string(data: dict[str, Any], key: str) -> str | None:
    value = data.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"config key {key!r} must be a non-empty string")
    return value


def _get_bool(data: dict[str, Any], key: str, default: bool) -> bool:
    value = data.get(key, default)
    if not isinstance(value, bool):
        raise ValueError(f"config key {key!r} must be true or false")
    return value


def _get_int(data: dict[str, Any], key: str, default: int) -> int:
    value = data.get(key, default)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"config key {key!r} must be an integer")
    return value


def _get_float(data: dict[str, Any], key: str) -> float | None:
    value = data.get(key)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"config key {key!r} must be a number")
    return float(value)


def _get_enum(
    data: dict[str, Any], key: str, enum_cls: type[TEnum], default: TEnum
) -> TEnum:
    value = data.get(key)
    if value is None:
        return default
    if not isinstance(value, str):
        raise ValueError(f"config key {key!r} must be a string")
    try:
        return enum_cls(value)
    except ValueError as exc:
        allowed = ", ".join(item.value for item in enum_cls)
        raise ValueError(f"invalid {key!r}: {value!r}; expected one of: {allowed}") from exc


def _format_toml_value(value: Any) -> str:
    if isinstance(value, Path):
        return _quote_toml_string(str(value))
    if isinstance(value, str):
        return _quote_toml_string(value)
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int | float):
        return str(value)
    raise TypeError(f"unsupported TOML value type: {type(value)!r}")


def _quote_toml_string(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'
