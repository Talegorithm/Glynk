#!/usr/bin/env bash
#
# 把 Agent 仓库的 skills/ 同步到 ~/.claude/skills/
#
# 默认用 **symlink**：源头在 repo，edit-in-repo 立即生效，适合本机开发。
# 跨机器部署/发布用 --copy：把文件 rsync 过去，脱离 repo。
#
# 默认行为：
#   - 目标不存在 → 创建
#   - 目标已是指向本 repo 的 symlink → 跳过（no-op）
#   - 目标已存在（其他 symlink / 目录 / 文件）→ **拒绝安装并报错**，让你自己决定如何处理
#     - 用 --force 才会强制覆盖（先 rm 再装）
#
# 不自动备份的原因：skill 已进版本控制，旧内容通常有 git 历史；
# 盲目 backup 会污染 ~/.claude/skills/（Claude Code 会把 .bak.* 当 skill 索引）。
#
# 用法：
#   bash install.sh                  # symlink 模式（默认，冲突即失败）
#   bash install.sh --copy           # copy 模式
#   bash install.sh --force          # 冲突时强制覆盖
#   bash install.sh --target DIR     # 改安装目录（默认 ~/.claude/skills）
#   bash install.sh --dry-run        # 只打印会做什么，不动文件
#   bash install.sh --skills a,b     # 只装指定的（默认全装）
#
set -euo pipefail

REPO_SKILLS_DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET_DIR="${HOME}/.claude/skills"
MODE="symlink"
DRY_RUN=0
FORCE=0
ONLY_SKILLS=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --copy)     MODE="copy"; shift ;;
    --symlink)  MODE="symlink"; shift ;;
    --target)   TARGET_DIR="$2"; shift 2 ;;
    --dry-run)  DRY_RUN=1; shift ;;
    --force)    FORCE=1; shift ;;
    --skills)   ONLY_SKILLS="$2"; shift 2 ;;
    -h|--help)
      grep '^#' "$0" | sed 's/^# \{0,1\}//' | head -30
      exit 0 ;;
    *) echo "unknown arg: $1" >&2; exit 1 ;;
  esac
done

run() {
  if [[ $DRY_RUN -eq 1 ]]; then
    echo "[dry-run] $*"
  else
    eval "$@"
  fi
}

# 收集要安装的 skill 列表
if [[ -n "$ONLY_SKILLS" ]]; then
  IFS=',' read -r -a skills <<< "$ONLY_SKILLS"
else
  skills=()
  for d in "$REPO_SKILLS_DIR"/*/; do
    [[ -d "$d" ]] || continue
    name="$(basename "$d")"
    [[ "$name" == "__pycache__" ]] && continue
    skills+=("$name")
  done
fi

echo "mode   : $MODE"
echo "source : $REPO_SKILLS_DIR"
echo "target : $TARGET_DIR"
echo "force  : $FORCE"
echo "skills : ${skills[*]}"
echo "---"

run "mkdir -p '$TARGET_DIR'"

conflict_count=0
for name in "${skills[@]}"; do
  src="$REPO_SKILLS_DIR/$name"
  dst="$TARGET_DIR/$name"

  if [[ ! -d "$src" ]]; then
    echo "⚠ skip (not found in repo): $name"
    continue
  fi

  # 已经是指向本 repo 的 symlink → 跳过
  if [[ -L "$dst" ]]; then
    current="$(readlink "$dst")"
    if [[ "$current" == "$src" ]]; then
      echo "= $name (already linked, skip)"
      continue
    fi
  fi

  # 目标存在但不是我们想要的状态 → 要么 --force 覆盖，要么报错
  if [[ -e "$dst" || -L "$dst" ]]; then
    if [[ $FORCE -eq 0 ]]; then
      echo "✗ $name: target exists → $dst"
      echo "    (现状: $( [[ -L "$dst" ]] && echo "symlink → $(readlink "$dst")" || echo "directory/file" ))"
      echo "    用 --force 覆盖；或手动处理后重跑。"
      conflict_count=$((conflict_count + 1))
      continue
    fi
    echo "↺ $name (forced: removing existing)"
    run "rm -rf '$dst'"
  fi

  case "$MODE" in
    symlink)
      run "ln -s '$src' '$dst'"
      echo "✓ $name (symlinked)"
      ;;
    copy)
      run "cp -R '$src' '$dst'"
      run "rm -rf '$dst/__pycache__'"
      echo "✓ $name (copied)"
      ;;
  esac
done

echo ""
if [[ $conflict_count -gt 0 ]]; then
  echo "⚠ $conflict_count 个 skill 因冲突未安装。用 --force 覆盖或先手动处理。"
  exit 2
fi

echo "安装完成。"
if [[ "$MODE" == "symlink" ]]; then
  echo "symlink 模式：在 $REPO_SKILLS_DIR 下改文件，$TARGET_DIR 自动跟随。"
else
  echo "copy 模式：repo 改动后需要重跑本脚本才会同步。"
fi
