#!/bin/bash
# Glynk 开发环境启动脚本
#
# 用法:
#   ./dev.sh          启动后端 + 前端
#   ./dev.sh backend  只启动后端
#   ./dev.sh frontend 只启动前端
#   ./dev.sh stop     停止所有

set -e
cd "$(dirname "$0")"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

stop_all() {
    echo -e "${YELLOW}Stopping services...${NC}"
    pkill -f "uvicorn glynk.main" 2>/dev/null || true
    pkill -f "vite.*glynk-web" 2>/dev/null || true
    echo -e "${GREEN}Stopped.${NC}"
}

start_backend() {
    echo -e "${GREEN}Starting backend on :5000...${NC}"
    cd /Users/sunlit/Code/Glynk
    python3 -m uvicorn glynk.main:app --port 5000 --reload &
    sleep 3
    if curl -s http://127.0.0.1:5000/health > /dev/null 2>&1; then
        echo -e "${GREEN}Backend ready: http://127.0.0.1:5000${NC}"
        echo -e "  API docs: http://127.0.0.1:5000/docs"
    else
        echo -e "${RED}Backend failed to start!${NC}"
        return 1
    fi
}

start_frontend() {
    echo -e "${GREEN}Starting frontend on :3000...${NC}"
    cd /Users/sunlit/Code/Glynk/glynk-web
    npx vite --port 3000 --strictPort &
    sleep 4
    if curl -s http://127.0.0.1:3000/ > /dev/null 2>&1; then
        echo -e "${GREEN}Frontend ready: http://127.0.0.1:3000${NC}"
    else
        echo -e "${RED}Frontend failed to start!${NC}"
        return 1
    fi
}

show_status() {
    echo ""
    echo -e "${GREEN}=== Glynk Dev Environment ===${NC}"

    # Check test data
    CONTENTS=$(curl -s http://127.0.0.1:5000/contents 2>/dev/null | python3 -c "import sys,json;print(len(json.load(sys.stdin)['contents']))" 2>/dev/null || echo "0")
    echo -e "  Contents in DB: ${CONTENTS}"

    echo ""
    echo -e "  Backend:  http://127.0.0.1:5000"
    echo -e "  Frontend: http://127.0.0.1:3000"
    echo -e "  API Docs: http://127.0.0.1:5000/docs"
    echo ""
    echo -e "  Stop: ${YELLOW}./dev.sh stop${NC}"
}

case "${1:-all}" in
    stop)
        stop_all
        ;;
    backend)
        stop_all
        start_backend
        show_status
        ;;
    frontend)
        start_frontend
        ;;
    all|"")
        stop_all
        start_backend
        start_frontend
        show_status
        ;;
    *)
        echo "Usage: ./dev.sh [all|backend|frontend|stop]"
        exit 1
        ;;
esac
