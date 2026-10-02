#!/bin/bash
# ==============================================================================
# 有珠之夜 · 博客本地服务管理脚本 (start.sh)
# 
# 用法:
#   ./start.sh          启动管理控制台与 Hugo 实时预览（推荐，全套服务）
#   ./start.sh hugo     仅启动 Hugo 本地预览服务 (端口 1314)
#   ./start.sh dash     仅启动博客可视化管理控制台 (端口 2026)
#   ./start.sh stop     停止所有正在运行的博客与控制台服务
#   ./start.sh restart  重启所有服务
#   ./start.sh status   查看当前服务运行状态
# ==============================================================================

set -e

# 定位博客根目录
ROOT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$ROOT_DIR"

# 注入 macOS 常用命令路径 (Homebrew Apple Silicon / Intel)
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

# 终端色彩定义
BOLD='\033[1m'
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 查找 Hugo 二进制路径
find_hugo() {
    if command -v hugo >/dev/null 2>&1; then
        echo "$(command -v hugo)"
    elif [ -x "/opt/homebrew/bin/hugo" ]; then
        echo "/opt/homebrew/bin/hugo"
    elif [ -x "/usr/local/bin/hugo" ]; then
        echo "/usr/local/bin/hugo"
    else
        echo ""
    fi
}

# 查找 Python 3 二进制路径
find_python() {
    if [ -x "/usr/bin/python3" ]; then
        echo "/usr/bin/python3"
    elif command -v python3 >/dev/null 2>&1; then
        echo "$(command -v python3)"
    elif command -v python >/dev/null 2>&1; then
        echo "$(command -v python)"
    else
        echo ""
    fi
}

HUGO_BIN="$(find_hugo)"
PY_BIN="$(find_python)"

# 获取进程 PID
get_hugo_pid() {
    lsof -ti:1314 2>/dev/null | head -n 1 || pgrep -f "hugo server" 2>/dev/null | head -n 1 || true
}

get_dash_pid() {
    lsof -ti:2026 2>/dev/null | head -n 1 || pgrep -f "dashboard.py" 2>/dev/null | head -n 1 || true
}

# 停止服务
stop_services() {
    echo -e "${YELLOW}🛑 正在安全停止博客相关服务...${NC}"
    
    local h_pid=$(get_hugo_pid)
    if [ -n "$h_pid" ]; then
        echo -e "   正在终止 Hugo 服务 (PID: $h_pid)..."
        lsof -ti:1314 | xargs kill -9 2>/dev/null || true
        pkill -9 -f "hugo server" 2>/dev/null || true
    fi

    local d_pid=$(get_dash_pid)
    if [ -n "$d_pid" ]; then
        echo -e "   正在终止管理控制台 (PID: $d_pid)..."
        lsof -ti:2026 | xargs kill -9 2>/dev/null || true
        pkill -9 -f "dashboard.py" 2>/dev/null || true
    fi

    sleep 0.5
    echo -e "${GREEN}✨ 所有相关服务已全部安全停止。${NC}"
}

# 查看状态
show_status() {
    echo -e "\n${BOLD}${CYAN}✦ 有珠之夜 · 博客服务运行状态${NC}"
    echo "======================================================="
    
    local h_pid=$(get_hugo_pid)
    if [ -n "$h_pid" ]; then
        echo -e "📖 Hugo 本地预览服务 : ${GREEN}● 运行中${NC} (PID: $h_pid, 端口: 1314)"
        echo -e "   🌐 预览链接        : ${BLUE}http://localhost:1314/${NC}"
    else
        echo -e "📖 Hugo 本地预览服务 : ${RED}○ 未运行${NC}"
    fi

    local d_pid=$(get_dash_pid)
    if [ -n "$d_pid" ]; then
        echo -e "🎛️ 博客管理控制台   : ${GREEN}● 运行中${NC} (PID: $d_pid, 端口: 2026)"
        echo -e "   🌐 控制台链接      : ${BLUE}http://localhost:2026/${NC}"
    else
        echo -e "🎛️ 博客管理控制台   : ${RED}○ 未运行${NC}"
    fi
    echo "=======================================================\n"
}

# 仅启动 Hugo
start_hugo() {
    if [ -z "$HUGO_BIN" ]; then
        echo -e "${RED}❌ 错误：未找到 Hugo 程序，请先安装 Hugo (brew install hugo)${NC}"
        exit 1
    fi

    local h_pid=$(get_hugo_pid)
    if [ -n "$h_pid" ]; then
        echo -e "${YELLOW}ℹ️ Hugo 服务已在运行中 (PID: $h_pid, http://localhost:1314/)${NC}"
        return
    fi

    echo -e "${CYAN}⚡ 正在启动 Hugo 本地预览服务 (端口 1314)...${NC}"
    "$HUGO_BIN" server -D --port 1314 --bind 0.0.0.0 -b http://localhost:1314/ --disableFastRender >/dev/null 2>&1 &
    
    # 等待端口就绪
    for i in {1..20}; do
        sleep 0.1
        if [ -n "$(get_hugo_pid)" ]; then
            break
        fi
    done

    echo -e "${GREEN}✅ Hugo 本地预览服务已就绪！${NC}"
    echo -e "   👉 本地预览直达: ${BOLD}${BLUE}http://localhost:1314/${NC}"
}

# 仅启动控制台
start_dashboard() {
    if [ -z "$PY_BIN" ]; then
        echo -e "${RED}❌ 错误：未找到 Python 3 环境，请先安装 Python 3${NC}"
        exit 1
    fi

    local d_pid=$(get_dash_pid)
    if [ -n "$d_pid" ]; then
        echo -e "${YELLOW}ℹ️ 控制台已在运行中 (PID: $d_pid, http://localhost:2026/)${NC}"
        return
    fi

    echo -e "${CYAN}⚡ 正在启动可视化博客管理控制台 (端口 2026)...${NC}"
    "$PY_BIN" scripts/dashboard.py
}

# 启动全套（默认）
start_all() {
    echo -e "\n${BOLD}${PURPLE}=======================================================${NC}"
    echo -e "${BOLD}${PURPLE}✨ 有珠之夜 · 博客全套本地服务启动程序${NC}"
    echo -e "${BOLD}${PURPLE}=======================================================${NC}"

    # 先清理此前意外残存的死锁进程
    local h_pid=$(get_hugo_pid)
    local d_pid=$(get_dash_pid)
    if [ -n "$h_pid" ] || [ -n "$d_pid" ]; then
        echo -e "${YELLOW}🔄 正在清理此前残留的后台进程，确保全新启动...${NC}"
        stop_services >/dev/null 2>&1 || true
        sleep 0.5
    fi

    # 1. 启动 Hugo 预览服务
    start_hugo

    # 2. 启动控制台 (Python)
    if [ -z "$PY_BIN" ]; then
        echo -e "${RED}❌ 错误：未检测到 Python 3 环境！${NC}"
        exit 1
    fi

    echo -e "${CYAN}🎛️ 正在启动博客可视化管理控制台...${NC}"
    echo -e "${GREEN}🎉 本地服务正在运行！控制台界面将自动在浏览器中打开。${NC}"
    echo -e "   💡 按 ${BOLD}Ctrl + C${NC} 可随时退出所有服务。\n"

    # 运行控制台前台监听
    exec "$PY_BIN" scripts/dashboard.py
}

# 命令路由
case "${1:-}" in
    stop)
        stop_services
        ;;
    status)
        show_status
        ;;
    restart)
        stop_services
        sleep 0.5
        start_all
        ;;
    hugo|server)
        start_hugo
        ;;
    dash|dashboard)
        start_dashboard
        ;;
    help|--help|-h)
        echo -e "${BOLD}有珠之夜 博客服务管理脚本帮助:${NC}"
        echo "  ./start.sh          启动全套服务（Hugo 1314 + 控制台 2026，默认）"
        echo "  ./start.sh hugo     仅启动 Hugo 预览服务"
        echo "  ./start.sh dash     仅启动管理控制台"
        echo "  ./start.sh stop     停止所有博客服务"
        echo "  ./start.sh restart  重启所有服务"
        echo "  ./start.sh status   查看运行状态"
        ;;
    *)
        start_all
        ;;
esac
