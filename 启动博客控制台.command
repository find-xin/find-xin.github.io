#!/bin/bash
# ========================================================
# 双击此文件即可直接启动博客可视化管理控制台
# ========================================================
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "正在启动 ✦ find-xin 博客可视化控制台..."

if command -v python3 >/dev/null 2>&1; then
    python3 scripts/dashboard.py
elif command -v python >/dev/null 2>&1; then
    python scripts/dashboard.py
else
    echo "❌ 错误：未检测到 Python 3 环境，请先安装 Python 3。"
    read -n 1 -s -r -p "按任意键退出..."
fi
