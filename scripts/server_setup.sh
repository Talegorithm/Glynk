#!/bin/bash
#
# Glynk 服务器首次部署脚本
#
# 在服务器上运行：
#   ssh -p 32001 dell@ijiaodui.com
#   cd /mnt/tracker
#   git clone <glynk-repo-url> Glynk
#   cd Glynk
#   bash scripts/server_setup.sh
#

set -e

echo "=== Glynk Server Setup ==="
echo ""

# 1. 创建数据目录
echo "--- Creating data directories ---"
mkdir -p Glynk-data/{html,uploads,postgres}
echo "  Done"

# 2. 添加 flask 到 requirements（CD webhook 需要）
echo "--- Checking flask dependency ---"
if ! grep -q "flask" requirements.txt; then
    echo "flask" >> requirements.txt
    echo "  Added flask to requirements.txt"
fi

# 3. 创建 .env（如果不存在）
if [ ! -f .env ]; then
    echo "--- Creating .env ---"
    cp .env.example .env
    echo "  Created .env from .env.example"
    echo "  NOTE: Edit .env to set AZURE_OPENAI_API_KEY if needed"
fi

# 4. 启动服务
echo ""
echo "--- Starting services ---"
docker compose up -d postgres
echo "  Waiting for PostgreSQL..."
sleep 5

docker compose up -d api
echo "  Waiting for API..."
sleep 3

# 5. 验证
echo ""
echo "--- Health check ---"
HEALTH=$(curl -s http://localhost:22500/health 2>/dev/null || echo '{"error":"failed"}')
echo "  API: ${HEALTH}"

# 6. 启动 nginx 和 CD
docker compose up -d nginx dev
echo "  Nginx + CD started"

echo ""
echo "=== Setup Complete ==="
echo ""
echo "端口映射："
echo "  API:     localhost:22500"
echo "  Nginx:   localhost:22533"
echo "  CD:      localhost:22538"
echo "  PG:      localhost:22433"
echo ""
echo "下一步："
echo "  1. 运行迁移: python3 scripts/migrate_from_resonote.py"
echo "  2. 配置 GitHub webhook: http://ijiaodui.com:22538/webhook"
echo "  3. 验证: curl http://localhost:22500/contents"
