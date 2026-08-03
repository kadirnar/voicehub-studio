#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
backend="auto"
with_training=0
with_desktop=0

for argument in "$@"; do
  case "$argument" in
    --cpu) backend="cpu" ;;
    --cuda) backend="cuda" ;;
    --training) with_training=1 ;;
    --desktop) with_desktop=1 ;;
    -h|--help)
      echo "Usage: $0 [--cpu|--cuda] [--training] [--desktop]"
      exit 0
      ;;
    *) echo "Unknown option: $argument" >&2; exit 2 ;;
  esac
done

if [[ "$backend" == "auto" ]]; then
  if command -v nvidia-smi >/dev/null 2>&1; then backend="cuda"; else backend="cpu"; fi
fi

uv_bin="$(command -v uv || true)"
if [[ -z "$uv_bin" ]]; then
  tools_dir="$project_dir/.tools"
  mkdir -p "$tools_dir"
  echo "Installing uv into $tools_dir"
  curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR="$tools_dir" sh
  uv_bin="$tools_dir/uv"
fi

echo "Creating the Python 3.12 environment"
"$uv_bin" venv --python 3.12 "$project_dir/.venv"

if [[ "$backend" == "cuda" ]]; then
  echo "Installing the PyTorch 2.8 CUDA 12.8 runtime"
  "$uv_bin" pip install --python "$project_dir/.venv/bin/python" "torch>=2.8,<2.9" \
    --index-url https://download.pytorch.org/whl/cu128
else
  echo "Installing the PyTorch 2.8 CPU runtime"
  "$uv_bin" pip install --python "$project_dir/.venv/bin/python" "torch>=2.8,<2.9" \
    --index-url https://download.pytorch.org/whl/cpu
fi

extras="test"
if [[ "$with_training" == 1 ]]; then extras="$extras,training"; fi
if [[ "$with_desktop" == 1 ]]; then extras="$extras,desktop"; fi

echo "Installing VoiceHub Studio with extras: $extras"
"$uv_bin" pip install --python "$project_dir/.venv/bin/python" -e "$project_dir[$extras]"

echo
"$project_dir/.venv/bin/python" - <<'PY'
import torch
import voicehub

print("VoiceHub:", voicehub.__version__)
print("PyTorch:", torch.__version__)
print("CUDA available:", torch.cuda.is_available())
if torch.cuda.is_available():
    print("GPU:", torch.cuda.get_device_name(0))
PY
echo "Ready. Start with: $project_dir/scripts/run.sh"
