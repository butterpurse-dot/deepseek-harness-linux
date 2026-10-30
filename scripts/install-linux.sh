#!/usr/bin/env bash
# Install DeepSeek Harness for Linux from GitHub Releases.
#
#   curl -fsSL https://raw.githubusercontent.com/butterpurse-dot/deepseek-harness-linux/master/scripts/install-linux.sh | bash
#
# Options:
#   --version <tag>   install a specific release tag (default: newest release)
#   --prefix <dir>    install prefix (default: ~/.local)
set -euo pipefail

REPO="butterpurse-dot/deepseek-harness-linux"
PREFIX="${PREFIX:-$HOME/.local}"
VERSION=""

while [ $# -gt 0 ]; do
  case "$1" in
    --version) VERSION="${2:?--version requires a tag}"; shift 2 ;;
    --prefix) PREFIX="${2:?--prefix requires a directory}"; shift 2 ;;
    -h|--help) sed -n '2,10p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "install: unknown argument $1" >&2; exit 2 ;;
  esac
done

case "$(uname -m)" in
  x86_64|amd64) ARCH=x64 ;;
  *) echo "install: only x64 builds are published right now (detected $(uname -m))" >&2; exit 1 ;;
esac

command -v curl >/dev/null || { echo "install: curl is required" >&2; exit 1; }
command -v python3 >/dev/null || { echo "install: python3 is required" >&2; exit 1; }

api="https://api.github.com/repos/$REPO/releases"
if [ -n "$VERSION" ]; then
  release_json="$(curl -fsSL "$api/tags/$VERSION")"
else
  release_json="$(curl -fsSL "$api?per_page=1" | python3 -c 'import json,sys; print(json.dumps(json.load(sys.stdin)[0]))')"
fi

tag="$(printf '%s' "$release_json" | python3 -c 'import json,sys; print(json.load(sys.stdin)["tag_name"])')"
assets="$(printf '%s' "$release_json" | python3 -c '
import json,sys
for asset in json.load(sys.stdin)["assets"]:
    print(asset["name"] + "\t" + asset["browser_download_url"])
')"

appimage_line="$(printf '%s\n' "$assets" | grep -E '\.AppImage$' | head -1 || true)"
sums_line="$(printf '%s\n' "$assets" | grep -E '(^|/)SHA256SUMS\.txt$' | head -1 || true)"
[ -n "$appimage_line" ] || { echo "install: release $tag has no AppImage" >&2; exit 1; }
[ -n "$sums_line" ] || { echo "install: release $tag has no SHA256SUMS.txt" >&2; exit 1; }

appimage_name="${appimage_line%%$'\t'*}"
appimage_url="${appimage_line#*$'\t'}"
sums_url="${sums_line#*$'\t'}"

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

echo "install: downloading $tag ($appimage_name)"
curl -fsSL -o "$tmp/$appimage_name" "$appimage_url"
curl -fsSL -o "$tmp/SHA256SUMS.txt" "$sums_url"

( cd "$tmp" && sha256sum -c SHA256SUMS.txt --ignore-missing )

mkdir -p "$PREFIX/bin" "$PREFIX/share/applications" "$PREFIX/share/icons/hicolor/512x512/apps"
install -m 0755 "$tmp/$appimage_name" "$PREFIX/bin/deepseek-harness"

curl -fsSL -o "$PREFIX/share/icons/hicolor/512x512/apps/deepseek-harness.png" \
  "https://raw.githubusercontent.com/$REPO/$tag/apps/desktop/resources/icon.png" || true

desktop_exec="$PREFIX/bin/deepseek-harness"
cat > "$PREFIX/share/applications/deepseek-harness.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=DeepSeek Harness
Comment=DeepSeek Harness desktop client
Exec=$desktop_exec %U
Icon=deepseek-harness
Terminal=false
Categories=Development;
StartupNotify=true
StartupWMClass=dsh-desktop
MimeType=x-scheme-handler/dsh;
EOF

command -v update-desktop-database >/dev/null && update-desktop-database "$PREFIX/share/applications" >/dev/null 2>&1 || true
command -v gtk-update-icon-cache >/dev/null && gtk-update-icon-cache -f -t "$PREFIX/share/icons/hicolor" >/dev/null 2>&1 || true

echo "install: installed $tag to $PREFIX/bin/deepseek-harness"
echo "install: run 'deepseek-harness' or open DeepSeek Harness from your application menu"
case ":$PATH:" in
  *":$PREFIX/bin:"*) ;;
  *) echo "install: add $PREFIX/bin to PATH to run it from a terminal" ;;
esac
