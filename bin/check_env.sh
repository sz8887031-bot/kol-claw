#!/bin/bash
# MediaCrawler 环境检查脚本
# 用于在调用工具前快速检查环境状态

echo "================================================================================"
echo "MediaCrawler 环境检查"
echo "================================================================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 检查计数
PASS=0
WARN=0
FAIL=0

# 项目根目录（相对于 bin/ 脚本所在位置）
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DATA_DIR="$PROJECT_ROOT/data"

# 1. 检查 MediaCrawler 目录
echo "1. 检查 MediaCrawler 目录..."
if [ -d "<MEDIACRAWLER_DIR>" ]; then
    echo -e "   ${GREEN}✅ MediaCrawler 目录存在${NC}"
    ((PASS++))
else
    echo -e "   ${RED}❌ MediaCrawler 目录不存在${NC}"
    ((FAIL++))
fi
echo ""

# 2. 检查残留进程
echo "2. 检查残留进程..."
if ps aux | grep -E "(main.py|chrome.*9222)" | grep -v grep > /dev/null; then
    echo -e "   ${YELLOW}⚠️  发现残留进程${NC}"
    ps aux | grep -E "(main.py|chrome.*9222)" | grep -v grep | awk '{print "      PID: "$2" - "$11" "$12" "$13}'
    echo "      建议运行: pkill -f 'main.py' && pkill -f 'chrome.*9222'"
    ((WARN++))
else
    echo -e "   ${GREEN}✅ 没有残留进程${NC}"
    ((PASS++))
fi
echo ""

# 3. 检查登录缓存
echo "3. 检查登录缓存..."
if [ -d "<MEDIACRAWLER_DIR>/browser_data/cdp_dy_user_data_dir" ]; then
    echo -e "   ${GREEN}✅ 登录缓存存在${NC}"
    ((PASS++))
else
    echo -e "   ${YELLOW}⚠️  登录缓存不存在，需要重新登录${NC}"
    echo "      运行: cd <MEDIACRAWLER_DIR> && uv run python main.py --platform dy --type search --keywords '测试' --lt qrcode"
    ((WARN++))
fi
echo ""

# 4. 检查搜索结果文件
echo "4. 检查搜索结果文件..."
if [ -f "<MEDIACRAWLER_DIR>/discovered_creators.json" ]; then
    FILE_SIZE=$(ls -lh <MEDIACRAWLER_DIR>/discovered_creators.json | awk '{print $5}')
    FILE_TIME=$(ls -l <MEDIACRAWLER_DIR>/discovered_creators.json | awk '{print $6" "$7" "$8}')
    echo -e "   ${GREEN}✅ 搜索结果文件存在${NC}"
    echo "      大小: $FILE_SIZE"
    echo "      修改时间: $FILE_TIME"
    ((PASS++))
else
    echo -e "   ${YELLOW}⚠️  搜索结果文件不存在${NC}"
    echo "      运行: cd <MEDIACRAWLER_DIR> && uv run python discover_creators.py"
    ((WARN++))
fi
echo ""

# 5. 检查输出目录
echo "5. 检查输出目录..."
if [ -d "$DATA_DIR" ]; then
    echo -e "   ${GREEN}✅ 输出目录存在${NC}"
    # 检查写入权限
    if touch "$DATA_DIR/.test" 2>/dev/null; then
        rm "$DATA_DIR/.test"
        echo -e "   ${GREEN}✅ 输出目录可写${NC}"
        ((PASS++))
    else
        echo -e "   ${RED}❌ 输出目录不可写${NC}"
        ((FAIL++))
    fi
else
    echo -e "   ${RED}❌ 输出目录不存在${NC}"
    ((FAIL++))
fi
echo ""

# 6. 检查分析脚本
echo "6. 检查分析脚本..."
if [ -f "$SCRIPT_DIR/../scripts/analyze_beauty_creators.py" ]; then
    echo -e "   ${GREEN}✅ 分析脚本存在${NC}"
    ((PASS++))
else
    echo -e "   ${YELLOW}⚠️  分析脚本不存在${NC}"
    ((WARN++))
fi
echo ""

# 7. 检查详细数据文件
echo "7. 检查详细数据文件..."
if [ -f "$DATA_DIR/creator_detail_analysis.json" ]; then
    FILE_SIZE=$(ls -lh "$DATA_DIR/creator_detail_analysis.json" | awk '{print $5}')
    FILE_TIME=$(ls -l "$DATA_DIR/creator_detail_analysis.json" | awk '{print $6" "$7" "$8}')
    echo -e "   ${GREEN}✅ 详细数据文件存在${NC}"
    echo "      大小: $FILE_SIZE"
    echo "      修改时间: $FILE_TIME"
    ((PASS++))
else
    echo -e "   ${YELLOW}⚠️  详细数据文件不存在（需要先运行深度抓取）${NC}"
    ((WARN++))
fi
echo ""

# 总结
echo "================================================================================"
echo "检查总结"
echo "================================================================================"
echo -e "${GREEN}通过: $PASS${NC} | ${YELLOW}警告: $WARN${NC} | ${RED}失败: $FAIL${NC}"
echo ""

if [ $FAIL -gt 0 ]; then
    echo -e "${RED}❌ 环境检查失败，请修复上述问题后再继续${NC}"
    exit 1
elif [ $WARN -gt 0 ]; then
    echo -e "${YELLOW}⚠️  环境检查通过，但有警告项需要注意${NC}"
    exit 0
else
    echo -e "${GREEN}✅ 环境检查全部通过，可以开始工作${NC}"
    exit 0
fi
