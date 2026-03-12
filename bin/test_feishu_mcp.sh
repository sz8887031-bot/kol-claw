#!/bin/bash
# 飞书MCP测试脚本

echo "=========================================="
echo "飞书MCP功能测试"
echo "=========================================="

# 1. 检查环境变量
echo ""
echo "1. 检查飞书配置..."
if [ -f ~/.feishu_config ]; then
    source ~/.feishu_config
    echo "✅ 配置文件存在"
    echo "   APP_ID: ${APP_ID:0:10}..."
else
    echo "❌ 配置文件不存在"
    exit 1
fi

# 2. 测试飞书CLI
echo ""
echo "2. 测试飞书CLI工具..."
if ~/bin/feishu search 张远 > /dev/null 2>&1; then
    echo "✅ 飞书CLI工作正常"
    ~/bin/feishu search 张远 | head -5
else
    echo "❌ 飞书CLI测试失败"
fi

# 3. 测试飞书MCP包
echo ""
echo "3. 测试飞书MCP包..."
if npx -y @larksuiteoapi/lark-mcp --version > /dev/null 2>&1; then
    VERSION=$(npx -y @larksuiteoapi/lark-mcp --version 2>&1)
    echo "✅ 飞书MCP包已安装 (版本: $VERSION)"
else
    echo "❌ 飞书MCP包未安装"
fi

# 4. 测试MCP服务器启动
echo ""
echo "4. 测试MCP服务器启动..."
export APP_ID="$APP_ID"
export APP_SECRET="$APP_SECRET"

# 启动MCP服务器并在后台运行
npx -y @larksuiteoapi/lark-mcp mcp -a "$APP_ID" -s "$APP_SECRET" -t preset.im.default > /tmp/feishu_mcp_test.log 2>&1 &
MCP_PID=$!

sleep 2

if ps -p $MCP_PID > /dev/null; then
    echo "✅ MCP服务器启动成功 (PID: $MCP_PID)"
    kill $MCP_PID 2>/dev/null
else
    echo "❌ MCP服务器启动失败"
    cat /tmp/feishu_mcp_test.log
fi

# 5. 检查Claude配置
echo ""
echo "5. 检查Claude MCP配置..."
if grep -q "feishu" ~/.claude.json 2>/dev/null; then
    echo "✅ Claude配置中包含飞书MCP"
else
    echo "⚠️  Claude配置中未找到飞书MCP"
    echo "   需要添加MCP服务器到当前项目"
fi

echo ""
echo "=========================================="
echo "测试完成"
echo "=========================================="
