#!/bin/bash
#
# 从服务器同步 Glynk 数据到本地备份
#
# 用法：
#   ./scripts/sync_to_local.sh              # 手动运行
#   crontab: 0 3 * * * /path/to/sync_to_local.sh   # 每天凌晨3点
#
# 同步内容：
#   1. PostgreSQL dump（内容+标注+用户）
#   2. HTML 文件（内容原文）
#

set -e

# ===== 配置 =====
REMOTE_HOST="dell@ijiaodui.com"
REMOTE_PORT=32001
REMOTE_GLYNK="/mnt/tracker/Glynk"

LOCAL_BACKUP_DIR="${HOME}/Backups/glynk"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="${LOCAL_BACKUP_DIR}/${TIMESTAMP}"

# 保留最近几份备份
KEEP_BACKUPS=7

# ===== 执行 =====
echo "=== Glynk Data Sync ==="
echo "  Time: $(date)"
echo "  Target: ${BACKUP_DIR}"

mkdir -p "${BACKUP_DIR}"

# 1. PostgreSQL dump
echo ""
echo "--- PostgreSQL dump ---"
ssh -p ${REMOTE_PORT} ${REMOTE_HOST} \
    "docker exec glynk-postgres-1 pg_dump -U glynk glynk" \
    > "${BACKUP_DIR}/glynk_pg.sql" 2>/dev/null

PG_SIZE=$(wc -c < "${BACKUP_DIR}/glynk_pg.sql" | tr -d ' ')
echo "  Dump: ${PG_SIZE} bytes"

# 2. HTML 文件（增量同步）
echo ""
echo "--- HTML files (rsync) ---"
mkdir -p "${LOCAL_BACKUP_DIR}/html"
rsync -az --delete \
    -e "ssh -p ${REMOTE_PORT}" \
    "${REMOTE_HOST}:${REMOTE_GLYNK}/Glynk-data/html/" \
    "${LOCAL_BACKUP_DIR}/html/"

HTML_COUNT=$(find "${LOCAL_BACKUP_DIR}/html" -name "*.html" 2>/dev/null | wc -l | tr -d ' ')
echo "  HTML files: ${HTML_COUNT}"

# 3. 在 backup 目录里放一个软链到最新的 html
ln -sf "${LOCAL_BACKUP_DIR}/html" "${BACKUP_DIR}/html"

# 4. 清理旧备份（只保留最近 N 份 SQL dump）
echo ""
echo "--- Cleanup ---"
BACKUPS=$(ls -d "${LOCAL_BACKUP_DIR}"/20* 2>/dev/null | sort -r)
COUNT=0
for dir in ${BACKUPS}; do
    COUNT=$((COUNT + 1))
    if [ ${COUNT} -gt ${KEEP_BACKUPS} ]; then
        echo "  Removing old backup: $(basename ${dir})"
        rm -rf "${dir}"
    fi
done

echo ""
echo "=== Sync complete ==="
echo "  SQL:  ${BACKUP_DIR}/glynk_pg.sql"
echo "  HTML: ${LOCAL_BACKUP_DIR}/html/"
