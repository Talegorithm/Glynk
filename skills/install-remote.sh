#!/usr/bin/env bash
#
# Glynk agent skills —— 一键安装
#
# 把 4 个 skill（glk-add / glk-read / glk-search / glk-source）及其辅助脚本
# 下载到本地 skill 目录。默认装到 ~/.claude/skills（Claude Code 的位置），
# 其他 Agent 自己用 --target 指。
#
# 用法:
#   curl -sL https://brainow.link/install.sh | bash
#   curl -sL https://brainow.link/install.sh | bash -s -- --target ~/.cursor/skills
#   curl -sL https://brainow.link/install.sh | bash -s -- --force        # 覆盖已存在目录
#
set -euo pipefail

BASE_URL="${GLYNK_SKILL_BASE:-https://brainow.link/skills}"
TARGET_DIR="${HOME}/.claude/skills"
FORCE=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target) TARGET_DIR="$2"; shift 2 ;;
    --force)  FORCE=1; shift ;;
    --base)   BASE_URL="$2"; shift 2 ;;   # 改下载源（开发 / 自建镜像用）
    -h|--help)
      sed -n '2,14p' "$0" | sed 's/^# \{0,1\}//'
      exit 0 ;;
    *) echo "unknown arg: $1" >&2; exit 1 ;;
  esac
done

# 每个 skill 的文件清单 —— 硬编码比从 server 拉 manifest 稳
declare_skill() {
  # $1=name, $2...=files
  SKILL_NAMES+=("$1")
  shift
  eval "SKILL_FILES_$1=\"\$*\""
  # 上面这行在 set -u 下会坏，改用关联数组：
}

SKILL_NAMES=(glk-add glk-read glk-search glk-source)
# file list per skill
SKILL_FILES_glk_add="SKILL.md upload_md.py upload_media.py"
SKILL_FILES_glk_read="SKILL.md"
SKILL_FILES_glk_search="SKILL.md"
SKILL_FILES_glk_source="SKILL.md"

mkdir -p "$TARGET_DIR"

installed=0
skipped=0
for name in "${SKILL_NAMES[@]}"; do
  dst="$TARGET_DIR/$name"
  if [[ -e "$dst" && $FORCE -eq 0 ]]; then
    echo "= $name already exists at $dst (use --force to overwrite), skip"
    skipped=$((skipped + 1))
    continue
  fi
  rm -rf "$dst"
  mkdir -p "$dst"

  # files list is stored as an env-ish variable; look it up via indirection
  var="SKILL_FILES_${name//-/_}"
  files="${!var}"
  for f in $files; do
    url="$BASE_URL/$name/$f"
    if ! curl -sSfL --retry 2 --max-time 30 "$url" -o "$dst/$f"; then
      echo "✗ $name/$f: download failed ($url)" >&2
      exit 2
    fi
  done
  echo "✓ $name  ($(echo $files | wc -w | tr -d ' ') files)"
  installed=$((installed + 1))
done

echo ""
echo "Installed $installed skill(s) to $TARGET_DIR  (skipped $skipped)"
echo "Next: set these env vars so the skills can reach your Glynk account:"
echo "  export GLYNK_API_URL=https://brainow.link"
echo "  export GLYNK_TOKEN=<your token>"
