# AGENTS.md

## Project purpose

This repository builds a **local Russian PDF-to-audio pipeline** for clean text PDFs.
The user will use Codex to implement the project incrementally.

## Non-negotiable product constraints

1. Primary input is a **clean born-digital PDF**, not a scan.
2. Primary output is local audio: `wav`, `mp3`, `m4a`.
3. Primary language is **Russian**.
4. Default TTS engine is **Silero**.
5. Default PDF extraction is **PyMuPDF**.
6. Audio export / concatenation is done with **ffmpeg**.
7. Do not introduce OCR in the main happy path.
8. Do not convert PDF to Word as the main extraction path.
9. Keep the TTS layer abstract so the engine can be swapped later.
10. User-facing page numbers are **1-based**.

## How to work in this repo

For non-trivial tasks:
1. Read `README.md` and relevant docs under `docs/`.
2. Produce a short implementation plan.
3. Implement in small, reviewable steps.
4. Add or update tests.
5. Run verification commands.
6. Update docs if behavior changed.
7. If the change is green and nothing is broken, split the work into logical commits, use clear commit messages, and push them to `origin`.

## Architecture expectations

Keep the code split into layers:
- `cli.py` for command-line parsing only;
- `pdf_extract.py` for PDF reading and segmentation;
- `normalize.py` for text cleanup;
- `tts/` for engine abstraction and Piper adapter;
- `audio.py` for ffmpeg conversion / concatenation;
- `pipeline.py` for orchestration.

Avoid putting everything in one file.

## Table handling expectations

Tables are not normal prose.
Do not just flatten them blindly if it makes speech unreadable.
Start with configurable strategies:
- `skip`
- `inline`
- `separate`

For `inline`, convert tables into explicit spoken structure such as:
- table title if available;
- columns;
- row-by-row reading.

## Text extraction expectations

Default extraction path:
- use PyMuPDF directly;
- start with natural reading order / sorted text;
- fall back to blocks / words only when necessary;
- keep region-based extraction extensible for future work.

## CLI expectations

Provide these subcommands at minimum:
- `inspect`
- `synth`

Expected page selection syntax:
- `all`
- `1`
- `1,2,3`
- `1-5`
- `1,3-5,8`

Expected split modes:
- `per-page`
- `per-range`
- `merged`

Expected formats:
- `wav`
- `mp3`
- `m4a`

## Testing expectations

At minimum add tests for:
- page range parsing;
- text normalization;
- output filename planning;
- config parsing;
- error handling for invalid page ranges.

If you add logic, add tests for it.

## Verification commands

Use these commands unless the task explicitly changes the toolchain:

```bash
python -m pytest -q
python -m compileall src
python -m pdf_tts_ru.cli --help
bash tools/verify.sh
```

## Implementation style

- Prefer straightforward Python over clever abstractions.
- Use dataclasses or small typed models for config.
- Keep functions short and composable.
- Add docstrings for public functions.
- Raise actionable errors.
- Do not silently swallow failures from ffmpeg or voice loading.
- Keep logs human-readable.

## Done means

A task is not done until:
1. code is implemented;
2. tests relevant to the change exist and pass;
3. docs are updated if behavior changed;
4. the result matches the CLI / README contract;
5. successful changes are committed in logical chunks and pushed.

## Git workflow expectations

- After each completed change, if verification is green, create one or more logical commits instead of one large dump commit.
- Commit messages should describe the actual change clearly and concretely.
- Push successful commits to `origin` in the same task unless the user explicitly asks not to.
- Do not commit or push broken work.

## Skills

Before large changes, inspect `.agents/skills/` and use the matching skill.
If a repeated workflow emerges, create or update a skill.
