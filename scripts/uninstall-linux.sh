#!/usr/bin/env bash
set -euo pipefail

purge_data=0
if [[ "${1:-}" == "--purge-data" ]]; then purge_data=1; fi
if [[ $# -gt 1 || ( $# -eq 1 && "${1:-}" != "--purge-data" ) ]]; then
  echo "Usage: ./scripts/uninstall-linux.sh [--purge-data]" >&2
  exit 2
fi

data_root="${XDG_DATA_HOME:-$HOME/.local/share}"
config_root="${XDG_CONFIG_HOME:-$HOME/.config}"
cache_root="${XDG_CACHE_HOME:-$HOME/.cache}"
bin_root="${XDG_BIN_HOME:-$HOME/.local/bin}"

rm -f -- \
  "$data_root/applications/io.github.kadirnar.VoiceHubStudio.desktop" \
  "$data_root/icons/hicolor/scalable/apps/io.github.kadirnar.VoiceHubStudio.svg" \
  "$data_root/metainfo/io.github.kadirnar.VoiceHubStudio.metainfo.xml" \
  "$bin_root/voicehub-studio"

command -v update-desktop-database >/dev/null 2>&1 \
  && update-desktop-database "$data_root/applications" || true

if [[ "$purge_data" == 1 ]]; then
  for target in \
    "$data_root/voicehub-studio" \
    "$config_root/voicehub-studio" \
    "$cache_root/voicehub-studio"; do
    if [[ -d "$target" && "$target" != "/" ]]; then rm -rf -- "$target"; fi
  done
  echo "VoiceHub Studio and its local data were removed. This cannot be undone."
else
  echo "VoiceHub Studio launcher removed. Local voices, models, and settings were preserved."
fi
