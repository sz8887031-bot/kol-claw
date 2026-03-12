#!/bin/bash
# 为当前项目配置飞书MCP服务器

echo "=========================================="
echo "配置飞书MCP服务器"
echo "=========================================="

# 读取飞书配置
if [ -f ~/.feishu_config ]; then
    source ~/.feishu_config
    echo "✅ 读取飞书配置成功"
else
    echo "❌ 未找到飞书配置文件"
    exit 1
fi

# 使用jq更新Claude配置
echo ""
echo "正在更新Claude配置..."

# 备份原配置
cp ~/.claude.json ~/.claude.json.backup.$(date +%Y%m%d_%H%M%S)
echo "✅ 已备份原配置"

# 更新配置（添加飞书MCP到当前项目）
cat ~/.claude.json | jq \
  --arg app_id "$APP_ID" \
  --arg app_secret "$APP_SECRET" \
  '.projects["<PROJECT_DIR>"].mcpServers.feishu = {
    "type": "stdio",
    "command": "npx",
    "args": ["-y", "@larksuiteoapi/lark-mcp", "mcp", "-a", $app_id, "-s", $app_secret, "-t", "preset.im.default"],
    "env": {}
  }' > ~/.claude.json.tmp

if [ $? -eq 0 ]; then
    mv ~/.claude.json.tmp ~/.claude.json
    echo "✅ 配置更新成功"
else
    echo "❌ 配置更新失败"
    rm ~/.claude.json.tmp
    exit 1
fi

echo ""
echo "=========================================="
echo "配置完成！"
echo "=========================================="
echo ""
echo "请重启Claude Code以使配置生效"
echo ""
