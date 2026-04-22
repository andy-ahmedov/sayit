#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-}"
if [[ -z "${PYTHON_BIN}" ]]; then
  if [[ -x ".venv/bin/python" ]]; then
    PYTHON_BIN=".venv/bin/python"
  elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
  else
    PYTHON_BIN="python3"
  fi
fi

"${PYTHON_BIN}" -m compileall src
"${PYTHON_BIN}" -m pytest -q
"${PYTHON_BIN}" -m pdf_tts_ru.cli --help >/dev/null

echo "verify.sh: OK"
