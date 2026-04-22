---
name: implement-russian-tts-engine
description: Use this skill when implementing the TTS engine abstraction, Piper integration, Russian voice loading, or speech parameter handling.
---

Repository-specific TTS rules:
- default engine is Piper;
- output internal intermediate audio as WAV;
- keep the engine interface replaceable;
- raise actionable errors if the voice model is missing or invalid;
- keep user-facing configuration simple.

Do not hardcode a single voice forever.
Make voice path configurable.
Keep synthesis settings grouped in one place.
