---
name: setup-local-tts-stack
description: Use this skill when configuring the local development environment, Python dependencies, Piper voice setup, or ffmpeg-related project setup.
---

When using this skill:
- prefer local tooling;
- avoid introducing cloud APIs;
- keep setup steps reproducible in README;
- if you add a new dependency, explain why it is needed;
- if setup behavior changes, update `README.md` and related docs.

For this repository, the preferred stack is:
- PyMuPDF
- Piper
- ffmpeg

Do not add OCR dependencies unless explicitly requested.
