# KOL投放管理系统 - Claude配置

> **重要**: 本文件会在每次Claude Code启动时自动读取

---

## 🎯 项目目标

**核心目的**：扩充达人库，以更低价格投放更多达人，并跟踪投放效果

**关键指标**：
- 达人数量：100+
- 平均CPM：<12（市场价15）
- 建联成功率：>30%
- ROI可追踪

---

## 🚀 启动检查清单

### 每次启动自动执行

**我会在启动时自动检查以下项目**:

1. **飞书MCP服务** - 验证连接状态 `claude mcp list | grep feishu`
   - 预期: `feishu - ✓ Connected`
   - 如未连接: 自动提示重新配置

2. **飞书CLI工具** - 测试搜索功能 `~/bin/feishu search 张远`
   - 预期: 返回用户信息
   - 如失败: 检查网络和配置

3. **定时任务** - 检查cron任务 `launchctl list | grep kol`
   - 预期: `com.kol.feishu.sync`
   - 如未运行: 提示重新加载

4. **核心数据** - 验证CSV文件 `ls -lh 达人跟进表.csv`
   - 预期: 文件存在且可读
   - 如缺失: 提示恢复备份

**手动检查命令**:
```bash
# 一键检查所有服务
claude mcp list && ~/bin/feishu search 张远 && launchctl list | grep kol
```

---

## 📋 项目结构

### 唯一数据源
- `达人跟进表.csv` - 所有达人信息（基础、报价、建联、投放数据）

### 核心脚本
- `contact_tracker.py` - 建联进度追踪
- `generate_script.py` - 话术生成
- `analyze_kol.py` - 达人分析和定价
- `feishu_webhook_push.py` - 飞书推送（定时任务）
- `sync_calendar.py` - 日历同步（自动生成日程）
- `analyze_creators.py` - 达人自动分析（标准化流程）⭐ 新增
- `check_env.sh` - 环境检查脚本 ⭐ 新增

### 配置
- **环境变量**：由 **CC-Switch** 统一管理（见下方「环境变量」）
- `~/Library/LaunchAgents/com.kol.feishu.sync.plist` - 定时任务（每天10:00）
- `claude.md` - 本文件

---

## ⚙️ 飞书集成

### 配置信息
- **推送方式**:
  - MCP消息（智能推送）
  - Webhook（群机器人）
- **推送时间**: 每天10:00
- **推送内容**: 待建联清单、跟进提醒、进度统计

### 飞书MCP服务

**状态**: ✅ Connected（需在 CC-Switch 中配置 FEISHU_APP_ID、FEISHU_APP_SECRET）

**配置方式**（凭证从 CC-Switch 环境变量读取，勿写死在仓库）:
- 在 CC-Switch 的 env 中添加：`FEISHU_APP_ID`、`FEISHU_APP_SECRET`
- 本地 MCP 命令示例（由 shell 展开环境变量）:
```bash
npx -y @larksuiteoapi/lark-mcp mcp -a $FEISHU_APP_ID -s $FEISHU_APP_SECRET -t preset.im.default
```
- 在 `~/.claude.json` 或 `claude mcp add` 时使用上述命令，确保运行环境已注入上述变量

**可用功能**:
1. **发送消息** - 直接通过MCP给飞书用户发消息
2. **搜索用户** - 通过姓名、邮箱查找用户信息
3. **群聊管理** - 获取群列表、群成员、发送群消息
4. **消息历史** - 获取聊天记录

**使用方式**:
```
你: 搜索张远并给他发消息说XXX
我: [自动调用MCP工具完成]
```

**CLI工具** (备用方案):
- 工具路径: `~/bin/feishu`
- 配置文件: `~/.feishu_config`
- 命令示例: `feishu search 张远`, `feishu send <open_id> "消息"`

**故障排查**:
```bash
# 检查MCP状态
claude mcp list | grep feishu

# 测试CLI工具
~/bin/feishu search 张远

# 重启MCP（凭证从 CC-Switch 环境变量读取，勿写死在命令中）
claude mcp remove feishu
claude mcp add --transport stdio feishu -- npx -y @larksuiteoapi/lark-mcp mcp -a $FEISHU_APP_ID -s $FEISHU_APP_SECRET -t preset.im.default
```

---

## 🔧 Claude工作约束

### ❌ 严格禁止

1. **不要创建文档**
   - 不写README、使用指南、配置指南、总结文档

2. **不要过度设计**
   - 不创建复杂的类和抽象
   - 不引入新框架
   - 不重构已有代码（除非有bug）

3. **不要重复造轮子**
   - 已有脚本不要重写

4. **不要主动扩展**
   - 用户没问的不要做
   - 不要添加数据库、Web界面

### ✅ 应该做的

1. **聚焦核心数据** - 一切围绕 `达人跟进表.csv`
2. **确保飞书推送** - 启动时检查MCP和Webhook
3. **简单实用** - 脚本能跑就行
4. **效果导向** - 帮助用户建联达人、降低CPM、跟踪ROI
5. **多维度评估** - 使用S/A/B/C/D评级体系，考虑稳定性和风险 ⭐ 新增
6. **不跳过新号** - 2-3条视频的达人也要收录并标记 ⭐ 新增
5. **标准化流程** - 达人筛选必须遵循《达人筛选标准化流程》⭐ 新增
6. **优先使用脚本** - 能用脚本就不用 AI，减少 token 消耗 ⭐ 新增

---

## 📊 工作流程

### 达人筛选流程 ⭐ 标准化（新增）

**当用户说"我要筛选达人"时，自动执行以下流程：**

```
环境检查 → 关键词搜索 → 初筛 → 深度抓取 → 自动分析 → 生成报告
```

**详细步骤：**

1. **环境检查**（0 tokens）
   ```bash
   <项目根目录>/check_env.sh
   ```
   - 检查 MediaCrawler 环境
   - 检查登录状态
   - 检查残留进程

2. **询问关键词**
   - 询问用户：想搜索什么类型的达人？
   - 示例：职场、求职、个人成长、副业、理财等

3. **关键词搜索**（5K tokens）⭐ 2026-03-04更新
   - 如需修改关键词，编辑 `discover_creators.py` 第 28 行
   - 运行搜索脚本获取 20-40 个达人
   - **使用 `--type search` 模式**（仅获取达人ID列表，不获取完整数据）

4. **初筛**（0.5K tokens）
   - 使用 Python 脚本快速筛选
   - 标准：粉丝数 5-50万
   - 输出：5-10 个候选达人的ID列表

5. **深度抓取**（15K tokens）⭐ 2026-03-04更新 - 关键修复
   - **必须使用 `--type creator` 模式**（获取完整数据）
   - 输入：步骤4筛选出的达人ID列表
   - 命令格式：`python3 main.py --platform dy --lt qrcode --type creator --creator_id "ID1,ID2,ID3"`
   - 获取数据：粉丝数 + 每个达人最近5条视频数据
   - **数据质量检查**（运行前必��验证）：
     * ✅ 粉丝数字段存在（不是"待查询"）
     * ✅ 每个达人视频数 ≥ 2条（最好5条）
     * ✅ JSON包含 `follower_count` 字段
   - 如数据缺失：不运行分析脚本，返回本步骤重新抓取
   - 使用子 Agent 批量执行

6. **自动分析**（0 tokens）
   ```bash
   cd <项目根目录>/data
   python3 process_mediacrawler_data_v2.py
   ```
   - 多维度评估（粉赞比、稳定性、样本量）
   - S/A/B/C/D 五级评级
   - 风险标签（新号、不稳定、下降趋势）
   - 生成优质达人.csv和备选达人.csv

**评级标准：**
- **S级**：粉赞比>5% + 平均点赞>1000 + 样本≥5条 + 稳定性>30% → 优质且稳定，强烈推荐
- **A级**：粉赞比>5% + 平均点赞>1000，但样本<5条或不稳定 → 高风险高回报
- **B级**：粉赞比2-5% → 良好，可小额测试
- **C级**：粉赞比1-2% → 一般，需谨慎
- **D级**：粉赞比<1% → 不建议投放

**稳定性检查：**
- 最低点赞 / 平均点赞 > 30% = 稳定
- < 30% = 不稳定，投放可能遇到低谷期

**新号处理：**
- 视频数<5条标记为"新号(N条)"
- 不再跳过，放入备选达人供用户手动筛选

**Token 消耗：** 约 25.5K/批次（已优化 54%）

**相关文档：**
- `data/达人筛选标准化流程.md` - 完整流程文档（v2.0多维度评估）
- `data/工具调用前检查清单.md` - 操作前检查清单
- `data/快速使用指南.md` - 5步快速上手
- `data/process_mediacrawler_data_v2.py` - 多维度评估脚本 ⭐ 推荐

### 达人库扩充
```
筛选达人（标准化流程） → 填入CSV → 计算报价 → 优先级排序 → 飞书同步
```

### 建联流程
```
飞书提醒 → 生成话术 → 发送私信 → 更新CSV → 飞书同步 → 跟进提醒
```

### 飞书同步流程 ⭐ 新增（2026-03-10）
```
达人跟进表.csv → 提取确定合作达人 → 同步到飞书
```

**同步时机：**
- 新增确定合作的达人
- 更新达人的建联状态、报价、级别
- 更新达人的投放状态

**同步命令：**
```bash
# 方法1：分步执行
cd <项目根目录>/data
python3 sync_confirmed_creators.py  # 提取确定合作达人
cd ..
python3 sync_to_feishu_incremental.py  # 同步到飞书

# 方法2：一键同步（推荐）
sync-kol  # 需先创建alias
```

**验证同步：**
```bash
# 检查数据一致性
cd <项目根目录>/data
echo "确定合作达人数: $(grep -c '确定合作' 达人跟进表.csv)"
echo "确定合作达人表: $(wc -l < 确定合作达人跟进表.csv)"
```

**详细说明：** 参考 `data/飞书同步规范流程.md`

### 日历同步流程 ⭐ 新增
```
更新CSV（沟通记录/备注中写入日期） → 运行sync_calendar.py → 自动生成日历事件 → 导入系统日历
```

**支持的日期格式**：
- `3月2号通知我联系达人` - 自动识别
- `1月31日跟进` - 自动识别
- `2026-03-02` - 标准格式

**操作步骤**：
1. 在CSV的「沟通记录」或「备注」列写入提醒日期和事项
2. 运行 `python3 sync_calendar.py`
3. 自动打开.ics文件，在日历应用中点击「添加」
4. 事件会添加到你的系统日历并在到期时提醒

### 投放流程（未来）
```
选择达人 → 确认报价 → 发送Brief → 审核视频 → 记录数据 → 计算ROI
```

---

## 🔑 凭证与环境变量

**统一由 CC-Switch 管理**，不在本仓库中写任何 API Key、App Secret 或 Webhook URL。

**重要**：本项目**不设置**任何 Claude/Anthropic 相关环境变量（如 `ANTHROPIC_API_KEY`、`ANTHROPIC_BASE_URL`），全部依赖 CC-Switch 注入。若出现 503 "No available accounts"：
- 不要在本项目下添加 `.env` 或 `CLAUDE_API_CONFIG.md` 来配置 API Key，否则会覆盖 CC-Switch。
- 在 CC-Switch 中确认当前启用的配置有效（如 AiGoCode 性能版/标准版），或切换另一个配置重试。
- 若其他项目正常而仅本项目报错，检查是否有项目级覆盖（如本目录下的 `.claude/`、或 Cursor/IDE 针对本工作区的 API 设置）。

在 CC-Switch 的配置中添加以下环境变量（仅飞书相关）：

| 变量名 | 用途 |
|--------|------|
| `FEISHU_WEBHOOK_URL` | 飞书群机器人 Webhook（日报推送、定时任务） |
| `FEISHU_APP_ID` | 飞书应用 App ID（MCP / CLI） |
| `FEISHU_APP_SECRET` | 飞书应用 App Secret（MCP / CLI） |

- **Claude Code**：由 CC-Switch 注入，无需额外配置。
- **定时任务（launchd）**：需在 plist 的 `EnvironmentVariables` 中配置上述变量，或使用包装脚本从与 CC-Switch 一致的环境来源加载后执行 `feishu_webhook_push.py`。

### 飞书
- App ID / Secret：见上表，仅存储在 CC-Switch，不写入仓库。
- Webhook：`FEISHU_WEBHOOK_URL`
- 用户ID: your_feishu_user_id（可保留，非敏感）

### 定时任务
- 时间: 每天 10:00
- 脚本: feishu_webhook_push.py
- 工作目录: <项目根目录>/data

---

## 📚 常用命令

```bash
# 达人筛选（标准化流程 v2.0）⭐ 新增
<项目根目录>/check_env.sh  # 环境检查
cd <MediaCrawler 安装目录>
uv run python discover_creators.py  # 关键词搜索
cd <项目根目录>/data
python3 process_mediacrawler_data_v2.py  # 多维度评估分析

# MediaCrawler 两步抓取法（2026-03-04更新）⭐ 推荐
cd <MediaCrawler 安装目录>
# 步骤1：搜索达人（获取ID列表）
python3 main.py --platform dy --lt qrcode --type search --keywords "职场干货"
# 步骤2：抓取完整数据（必须！）
python3 main.py --platform dy --lt qrcode --type creator --creator_id "ID1,ID2,ID3"
# 数据质量检查
cat data/douyin/json/creator_*.json | jq '.[].user_info.follower_count' | head -5

# 数据分析
python3 contact_tracker.py
python3 analyze_kol.py
python3 generate_script.py

# 飞书推送
python3 feishu_webhook_push.py

# 日历同步
python3 sync_calendar.py

# 定时任务
launchctl list | grep kol
launchctl start com.kol.feishu.sync
```

---

## ⚠️ 故障排查

```bash
# 未收到飞书推送
# 确认已在 CC-Switch 中配置 FEISHU_WEBHOOK_URL，且定时任务进程能读到该环境变量
python3 feishu_webhook_push.py
tail cron.error.log

# 定时任务未执行
launchctl list | grep kol
tail cron.log

# 达人数据缺失问题（2026-03-04新增）⭐ 常见问题
# 症状：粉丝数="待查询"、每个达人只有1条视频
# 原因：使用了Search模式而非Creator模式
# 检查当前数据状态
cd <MediaCrawler 安装目录>
ls -lh data/douyin/json/  # 查看文件名，应该有creator_*.json
cat data/douyin/json/creator_*.json | jq '.[].user_info.follower_count' | head -5  # 检查粉丝数
# 解决方案：用Creator模式重新抓取
python3 main.py --platform dy --lt qrcode --type creator --creator_id "达人ID列表"
# 清理残留进程
pkill -f "main.py --platform dy"
ps aux | grep "main.py" | grep -v grep  # 确认清理成功
```

---

## 💡 记住

### 核心原则
1. **目标明确** - 低成本投放，高ROI回报
2. **数据唯一** - 一切围绕 `达人跟进表.csv`
3. **飞书优先** - 所有提醒通过飞书
4. **简单有效** - 能用就行，不追求完美
5. **用户驱动** - 用户不问不做

### 工作态度
- ❌ 不过度设计
- ❌ 不写无用文档
- ❌ 不提前优化
- ✅ 聚焦目标
- ✅ 简单实用
- ✅ 效果导向

---

**配置状态**: ✅ 飞书MCP Connected | ✅ 定时任务运行 | ⏳ 请在 CC-Switch 中配置 FEISHU_WEBHOOK_URL

---

## 🔧 MediaCrawler 数据抓取规范（2026-03-04新增）⭐ 重要

### 问题背景
**历史问题**（2026-03-04发现并修复）：
- 子Agent使用 `--type search` 模式导致数据严重缺失
- 症状：粉丝数显示"待查询"、每个达人只有1条视频、无法计算粉赞比
- 根因：Search模式只抓取搜索结果页视频，不进入达人主页获取完整信息

### 正确的两步抓取法 ⭐ 必须遵守

#### 步骤1：搜索阶段（获取达人ID）
```bash
cd <MediaCrawler 安装目录>
python3 main.py --platform dy --lt qrcode --type search --keywords "职场干货"
```
**目的**：发现候选达人
**输出**：搜索结果JSON（包含 `user_id` 或 `sec_uid`）
**数据特点**：
- ✅ 可以获取：达人名称、单条视频点赞数、主页链接
- ❌ 无法获取：粉丝数、多条视频数据、粉赞比

#### 步骤2：抓取阶段（获取完整数据）⭐ 关键
```bash
python3 main.py --platform dy --lt qrcode --type creator --creator_id "用户ID1,用户ID2,用户ID3"
```
**目的**：获取完整达人数据用于多维度评估
**输入**：步骤1提取的达人ID列表
**输出**：Creator数据JSON（包含完整信息）
**数据特点**：
- ✅ 粉丝数（`follower_count`）
- ✅ 最近5条视频的点赞数
- ✅ 可计算粉赞比、评估稳定性、分析趋势

### 数据质量检查清单 ⭐ 运行分析脚本前必检

**检查命令**：
```bash
# 方法1：快速检查粉丝数是否存在
cd <MediaCrawler 安装目录>
cat data/douyin/json/creator_*.json | jq '.[].user_info.follower_count' | head -5

# 方法2：检查视频数量
cat data/douyin/json/creator_*.json | jq '.[].aweme_list | length' | head -5
```

**必须满足的条件**：
1. ✅ 粉丝数字段存在且不为 `null`
2. ✅ 每个达人视频数 ≥ 2条（理想状态5条）
3. ✅ JSON文件名为 `creator_*.json`（不是 `search_*.json`）

**如发现数据缺失**：
- ⚠️ 停止！不要运行 `process_mediacrawler_data_v2.py`
- 🔄 返回步骤2，使用 `--type creator` 重新抓取
- 🧹 清理残留进程：`pkill -f "main.py --platform dy"`

### 常见错误排查

| 错误症状 | 原因 | 解决方案 |
|----------|------|----------|
| 粉丝数="待查询" | 使用了Search模式 | 用Creator模式重新抓取 |
| 每个达人只有1条视频 | 使用了Search模式 | 用Creator模式重新抓取 |
| 无法计算粉赞比 | 缺少粉丝数字段 | 用Creator模式重新抓取 |
| JSON文件名为search_*.json | 执行了Search但没执行Creator | 补充执行Creator抓取 |

### 与历史规则的兼容性
- **补充关系**：本规范补充了「达人筛选流程」中步骤3-5的实现细节
- **不冲突**：所有现有评级标准（S/A/B/C/D）和数据收录标准保持不变
- **强化验证**：新增数据质量检查步骤，确保分析脚本输入数据完整

### 规则管理元信息
- **创建日期**：2026-03-04
- **触发原因**：实际抓取中发现数据缺失问题
- **影响范围**：达人筛选流程的步骤3-5
- **向后兼容**：是（不影响已有数据和脚本）
