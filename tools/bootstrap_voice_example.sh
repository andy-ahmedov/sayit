#!/usr/bin/env bash
set -euo pipefail

VOICE_NAME="${1:-ru_RU-dmitri-medium}"

echo "Example only. Adjust the voice name if needed."
echo "python -m piper.download_voices ${VOICE_NAME}"
