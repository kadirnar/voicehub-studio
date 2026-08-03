#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
applications_dir="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
icons_dir="${XDG_DATA_HOME:-$HOME/.local/share}/icons/hicolor/scalable/apps"
metadata_dir="${XDG_DATA_HOME:-$HOME/.local/share}/metainfo"
launcher_dir="${XDG_BIN_HOME:-$HOME/.local/bin}"

if [[ ! -x "$project_dir/.venv/bin/voicehub-studio" ]]; then
  echo "Bootstrap VoiceHub Studio before installing the desktop entry." >&2
  exit 1
fi

mkdir -p "$applications_dir" "$icons_dir" "$metadata_dir" "$launcher_dir"
cp "$project_dir/voicehub_studio/static/icon.svg" "$icons_dir/io.github.kadirnar.VoiceHubStudio.svg"
cp "$project_dir/packaging/io.github.kadirnar.VoiceHubStudio.metainfo.xml" "$metadata_dir/"

launcher="$launcher_dir/voicehub-studio"
desktop_file="$applications_dir/io.github.kadirnar.VoiceHubStudio.desktop"
sed "s|^Exec=.*|Exec=$launcher --window|" "$project_dir/packaging/io.github.kadirnar.VoiceHubStudio.desktop" > "$desktop_file"
printf '#!/usr/bin/env bash\nexec %q -m voicehub_studio "$@"\n' "$project_dir/.venv/bin/python" > "$launcher"
chmod +x "$launcher" "$desktop_file"

command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database "$applications_dir" || true
echo "Installed VoiceHub Studio in the current user's application menu."
