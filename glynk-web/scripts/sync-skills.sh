#!/usr/bin/env bash
# Copy ../skills/* + install-remote.sh into public/ so build produces a
# self-contained dist. Runs automatically as predev / prebuild via npm hooks.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
WEB_ROOT="$HERE/.."
REPO_ROOT="$WEB_ROOT/.."

PUBLIC_DIR="$WEB_ROOT/public"
PUBLIC_SKILLS="$PUBLIC_DIR/skills"

rm -rf "$PUBLIC_SKILLS"
mkdir -p "$PUBLIC_SKILLS"

# Sync the 4 skill dirs (excluding __pycache__ / install.sh which is repo-dev only)
for name in glk-add glk-read glk-search glk-source; do
  src="$REPO_ROOT/skills/$name"
  [[ -d "$src" ]] || continue
  rsync -a --exclude '__pycache__' --exclude '*.pyc' "$src/" "$PUBLIC_SKILLS/$name/"
done

# The remote installer itself → /install.sh
cp "$REPO_ROOT/skills/install-remote.sh" "$PUBLIC_DIR/install.sh"
chmod +x "$PUBLIC_DIR/install.sh"

echo "synced skills → $PUBLIC_SKILLS"
echo "synced installer → $PUBLIC_DIR/install.sh"
