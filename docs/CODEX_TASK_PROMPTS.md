# Ready prompts for Codex

## 1. Plan first

```text
Read README.md, AGENTS.md, docs/ARCHITECTURE.md and the skills in .agents/skills.
Do not code yet.
Build a concrete implementation plan for v1 of this repository.
Break it into small steps with risks, dependencies, and verification commands.
If the implementation is completed successfully, split it into logical commits with clear messages and push to origin.
```

## 2. Implement page range parsing and CLI skeleton

```text
Implement the initial CLI and page range parsing for this repo.
Requirements:
- support inspect and synth subcommands
- support page specs: all, 1, 1-5, 1,3-5,8
- add tests
- do not implement OCR
- update docs if behavior changes
Run verification commands after changes.
If everything is green, make logical commits and push them.
```

## 3. Implement PDF extraction layer

```text
Implement the PyMuPDF extraction layer for clean PDFs.
Requirements:
- direct PDF reading only
- expose page-wise extraction
- add a table strategy abstraction: skip / inline / separate
- do not yet optimize for scans
- add tests where possible
Run verification commands after changes.
If everything is green, make logical commits and push them.
```

## 4. Implement Piper adapter

```text
Implement a pluggable TTS interface and a Piper engine adapter.
Requirements:
- engine interface must be swappable later
- Piper is the default implementation
- write WAV first
- make voice path configurable
- add clear errors for missing voice model
- add tests/mocks where possible
Run verification commands after changes.
If everything is green, make logical commits and push them.
```

## 5. Implement ffmpeg export

```text
Implement ffmpeg-based export and concatenation.
Requirements:
- convert wav to mp3 and m4a
- support merged output from multiple wav files
- fail loudly on ffmpeg errors
- keep filenames deterministic
- add tests for command construction if real ffmpeg is not used in tests
Run verification commands after changes.
If everything is green, make logical commits and push them.
```

## 6. End-to-end verification

```text
Review the whole repository against README.md and AGENTS.md.
Find missing pieces for a real v1.
Then implement the smallest set of changes needed to make the repo coherent.
Add/update tests and docs.
Run verification commands.
If everything is green, make logical commits and push them.
```
