#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
python_bin="$project_dir/.venv/bin/python"

if [[ ! -x "$python_bin" ]]; then
  echo "VoiceHub Studio is not bootstrapped. Run: $project_dir/scripts/bootstrap.sh --cuda" >&2
  exit 1
fi

exec "$python_bin" -m voicehub_studio "$@"
