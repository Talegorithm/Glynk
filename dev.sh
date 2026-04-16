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

# 检测端口占用，询问 kill 或换端口
# 用法: resolve_port <port> → 设置全局变量 RESOLVED_PORT
resolve_port() {
    local port=$1
    local pid
    pid=$(lsof -ti tcp:"$port" 2>/dev/null | head -1)
    if [ -z "$pid" ]; then
        RESOLVED_PORT=$port
        return
    fi
    local proc
    proc=$(ps -p "$pid" -o comm= 2>/dev/null || echo "unknown")
    echo -e "${YELLOW}端口 $port 已被占用 (PID $pid, $proc)${NC}"
    read -p "是否 kill 该进程? [y/N] " -r ans
    if [[ "$ans" =~ ^[Yy]$ ]]; then
        kill -9 "$pid" 2>/dev/null || true
        sleep 1
        RESOLVED_PORT=$port
        echo -e "${GREEN}已终止 PID $pid，使用端口 $port${NC}"
    else
        local new_port=$((port + 1))
        while lsof -ti tcp:"$new_port" >/dev/null 2>&1; do
            new_port=$((new_port + 1))
        done
        RESOLVED_PORT=$new_port
        echo -e "${GREEN}改用端口 $new_port${NC}"
    fi
}

start_backend() {
    resolve_port 5000
    local port=$RESOLVED_PORT
    echo -e "${GREEN}Starting backend on :$port...${NC}"
    cd /Users/sunlit/Code/Glynk
    python3 -m uvicorn glynk.main:app --port "$port" --reload &
    sleep 3
    if curl -s "http://127.0.0.1:$port/health" > /dev/null 2>&1; then
        echo -e "${GREEN}Backend ready: http://127.0.0.1:$port${NC}"
        echo -e "  API docs: http://127.0.0.1:$port/docs"
        BACKEND_PORT=$port
    else
        echo -e "${RED}Backend failed to start!${NC}"
        return 1
    fi
}

start_frontend() {
    resolve_port 3000
    local port=$RESOLVED_PORT
    echo -e "${GREEN}Starting frontend on :$port...${NC}"
    cd /Users/sunlit/Code/Glynk/glynk-web
    npx vite --port "$port" --strictPort &
    sleep 4
    if curl -s "http://127.0.0.1:$port/" > /dev/null 2>&1; then
        echo -e "${GREEN}Frontend ready: http://127.0.0.1:$port${NC}"
        FRONTEND_PORT=$port
    else
        echo -e "${RED}Frontend failed to start!${NC}"
        return 1
    fi
}

show_status() {
    local be=${BACKEND_PORT:-5000}
    local fe=${FRONTEND_PORT:-3000}
    echo ""
    echo -e "${GREEN}=== Glynk Dev Environment ===${NC}"

    # Check test data
    CONTENTS=$(curl -s "http://127.0.0.1:$be/contents" 2>/dev/null | python3 -c "import sys,json;print(len(json.load(sys.stdin)['contents']))" 2>/dev/null || echo "0")
    echo -e "  Contents in DB: ${CONTENTS}"

    echo ""
    echo -e "  Backend:  http://127.0.0.1:$be"
    echo -e "  Frontend: http://127.0.0.1:$fe"
    echo -e "  API Docs: http://127.0.0.1:$be/docs"
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
