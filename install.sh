#!/bin/sh
set -eu

case "$(uname -s)" in
  Darwin) destination="$HOME/Library/Application Support/Commander/plugins/embroidery-viewer" ;;
  Linux) destination="${XDG_DATA_HOME:-$HOME/.local/share}/commander/plugins/embroidery-viewer" ;;
  *) echo "On Windows, copy this folder to %APPDATA%\\Commander\\plugins\\embroidery-viewer" >&2; exit 1 ;;
esac

python3 -m pip install --user -r "$(dirname "$0")/requirements.txt"
mkdir -p "$destination"
cp "$(dirname "$0")/plugin.json" "$(dirname "$0")/embroidery_viewer.py" "$destination/"
echo "Installed embroidery-viewer in $destination"
