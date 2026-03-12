#!/bin/bash
# KOL投放管理系统 - 快速启动脚本

cd "$(dirname "$0")"

# 检查 Python 环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到 Python3，请先安装 Python"
    exit 1
fi

# 检查依赖
if ! python3 -c "import pandas, numpy, requests, icalendar" &> /dev/null; then
    echo "📦 正在安装依赖..."
    pip3 install -r requirements.txt
fi

# 运行命令
if [ $# -eq 0 ]; then
    python3 data/daily_tasks.py
else
    python3 "$@"
fi
