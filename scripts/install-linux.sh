#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
backend="auto"
with_training=0
install_system_deps=0
launch_after=0

usage() {
  cat <<'EOF'
Usage: ./scripts/install-linux.sh [options]

Install VoiceHub Studio as a current-user Linux desktop application.

Options:
  --cpu                 Install the CPU-only PyTorch runtime
  --cuda                Install the NVIDIA CUDA 12.8 PyTorch runtime
  --training            Include model fine-tuning dependencies
  --system-deps         Install FFmpeg and native Qt/XCB runtime packages with sudo
  --launch              Open VoiceHub Studio after installation
  -h, --help            Show this help
EOF
}

for argument in "$@"; do
  case "$argument" in
    --cpu) backend="cpu" ;;
    --cuda) backend="cuda" ;;
    --training) with_training=1 ;;
    --system-deps) install_system_deps=1 ;;
    --launch) launch_after=1 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $argument" >&2; usage >&2; exit 2 ;;
  esac
done

if [[ "$(uname -s)" != "Linux" ]]; then
  echo "VoiceHub Studio's desktop installer currently supports Linux only." >&2
  exit 1
fi

install_native_dependencies() {
  if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update
    sudo apt-get install -y curl ffmpeg git python3-venv build-essential libegl1 libgl1 libxkbcommon-x11-0 libxcb-cursor0
  elif command -v dnf >/dev/null 2>&1; then
    sudo dnf install -y curl ffmpeg git python3-devel gcc gcc-c++ libxkbcommon-x11 xcb-util-cursor mesa-libEGL
  elif command -v pacman >/dev/null 2>&1; then
    sudo pacman -S --needed curl ffmpeg git python libxkbcommon-x11 xcb-util-cursor
  else
    echo "Unsupported package manager. Install FFmpeg and the Qt/XCB desktop runtime libraries manually." >&2
    exit 1
  fi
}

if [[ "$install_system_deps" == 1 ]]; then
  install_native_dependencies
fi

missing=()
command -v curl >/dev/null 2>&1 || missing+=(curl)
command -v ffmpeg >/dev/null 2>&1 || missing+=(ffmpeg)
command -v ffprobe >/dev/null 2>&1 || missing+=(ffprobe)
command -v git >/dev/null 2>&1 || missing+=(git)
if (( ${#missing[@]} )); then
  echo "Missing system tools: ${missing[*]}" >&2
  echo "Re-run with --system-deps or install them with your distribution package manager." >&2
  exit 1
fi

bootstrap=("$project_dir/scripts/bootstrap.sh")
if [[ "$backend" == "cpu" ]]; then
  bootstrap+=(--cpu)
elif [[ "$backend" == "cuda" ]]; then
  bootstrap+=(--cuda)
fi
bootstrap+=(--desktop)
if [[ "$with_training" == 1 ]]; then bootstrap+=(--training); fi

"${bootstrap[@]}"
"$project_dir/scripts/install-desktop.sh"
"$project_dir/.venv/bin/python" -m voicehub_studio --help >/dev/null

echo
echo "VoiceHub Studio 0.2.0 is installed."
echo "Open it from the application menu or run: voicehub-studio --window"

if [[ "$launch_after" == 1 ]]; then
  launcher_dir="${XDG_BIN_HOME:-$HOME/.local/bin}"
  exec "$launcher_dir/voicehub-studio" --window
fi
