# KOL Claw

**你在抖音投过多少冤枉钱？**

达人报 ¥5000，你不知道贵不贵，砍到 ¥3500 觉得赚了，实际 CPM 已经超过 30。
粉丝 50 万的账号，播放量只有 2000，你还以为买到了大号。
手动一个个刷主页找达人，一天过去只找到三个，没一个满意的。
建联发出去石沉大海，不知道说什么才能让达人回消息。

**这些问题，KOL Claw 全部解决。**

---

## 这套系统改变了什么

在 KOL Claw 之前，达人投放是一门玄学：靠感觉定价，靠运气找人，靠经验判断好坏。

**KOL Claw 把这门玄学变成了一套可复制的标准。**

一句话触发，系统自动完成从找人到建联的全流程：

```
你：帮我找 15 个职场干货类达人，粉丝 10-30 万，CPM 控制在 12 以内

系统：
  → 自动搜索抖音平台候选达人
  → 抓取每个达人的粉丝数、最近 5 条视频播放量
  → 计算粉赞比、稳定性、趋势
  → S/A/B/C/D 评级 + 建议报价
  → 生成针对每个达人的建联话术
  → 同步到飞书，团队实时可见
```

从需求到结果，**不需要手动刷一个主页**。

---

## 完整工作链路

```
一句话需求
    ↓
① 抓达人 — 自动搜索 + 批量抓取（MediaCrawler）
    ↓
② 分析推荐 — 粉赞比 × 稳定性 × 样本量 × 趋势，S/A/B/C/D 评级
    ↓
③ 建联 — 个性化话术（大/中/小达人三套策略），一键生成
    ↓
④ 报价评估 — CPM 定价框架，10 秒判断值不值
    ↓
⑤ 谈判策略 — 用数据说话，锚定 CPM 基准，逐步压价
    ↓
⑥ 跟进同步 — 飞书每日推送：待建联清单 + 跟进提醒 + 进度统计
               状态全程追踪：未建联 → 已建联 → 已回复 → 确定合作
```

---

## ① 抓达人：一句话搜索，全自动抓取

配合 [MediaCrawler](https://github.com/NanmiCoder/MediaCrawler) 实现全自动抓取：

```bash
bash bin/check_env.sh   # 环境检查

# 步骤 1：关键词搜索，获取候选达人 ID 列表
python main.py --platform dy --lt qrcode --type search --keywords "职场干货"

# 步骤 2：抓取完整数据（粉丝数 + 最近 5 条视频）⭐ 必须执行
python main.py --platform dy --lt qrcode --type creator --creator_id "ID1,ID2,ID3"
```

> 必须使用 `--type creator` 才能获取粉丝数和多条视频数据，`--type search` 数据不完整，无法评级。

---

## ② 分析推荐：五级评分，不靠感觉

光看粉丝数是最大的坑。10 万粉丝、平均播放 500，不如 2 万粉丝、平均播放 8000 的账号。

**真正决定投放效果的是粉赞比和稳定性：**

| 等级 | 标准 | 投放建议 |
|------|------|----------|
| **S级** | 粉赞比>5% + 均赞>1000 + ≥5条视频 + 稳定性>30% | 优先建联，主动谈价，这种账号不多 |
| **A级** | 粉赞比>5% + 均赞>1000，但视频少或波动大 | 高潜力，先小额测试再追加 |
| **B级** | 粉赞比 2-5% | 中等质量，性价比合适就投 |
| **C级** | 粉赞比 1-2% | 除非极低价，否则不建议 |
| **D级** | 粉赞比<1% | 粉丝质量存疑，跳过 |

**稳定性额外检查**：最低点赞 ÷ 平均点赞 > 30% = 稳定账号。低于这个值代表数据忽高忽低，你的视频可能恰好落在低谷期。

```bash
# 多维度分析，生成优质达人 / 备选达人列表
python scripts/process_mediacrawler_data_v2.py
```

---

## ③ 建联：系统自动生成话术，不再石沉大海

系统根据达人数据（账号体量、粉赞比、垂直领域）自动生成三套策略：

- **大达人（50万+）**：突出品牌背书 + 长期合作
- **中达人（10-50万）**：强调 CPM 数据 + 数据对标
- **小达人（10万以下）**：聚焦成长机会 + 优先排期

```bash
python scripts/generate_script.py   # 一键生成建联话术
```

---

## ④ 报价评估：CPM 框架，10 秒判断值不值

这是整个行业长期缺失的东西：**一套所有人都能用的 KOL 定价框架**。

```
CPM = 报价 ÷ (预期播放量 ÷ 1000)

行业基准：CPM 15 = 市场价
           CPM 12 = 低于市场价，值得谈
           CPM 8  = 极致性价比，优先锁定
           CPM 20+ = 明显虚高，直接砍价或放弃
```

**实操示例：**

> 达人 A：粉丝 30 万，报价 ¥3000，预估播放 1.5 万
>
> CPM = 3000 ÷ 15 = **200** → 严重虚高，建议报价 ¥225（CPM=15）
>
> 你的话术：「参考同类达人数据，这个体量建议在 ¥200-250 区间，您能接受吗？」

不是砍价，是拿数据说话。达人也没法反驳。

```bash
python scripts/analyze_kol.py   # 分析达人评级和 CPM 定价
```

---

## ⑤ 谈判策略：用数据锚定，逐步压价

**三步谈判法：**

1. **抛锚**：先报 CPM 8 的价格，用行业数据背书
2. **对标**：「同体量账号我们合作价在 X 区间」，不说绝对价格
3. **退让**：从 CPM 8 → CPM 10 → CPM 12，每次退让换取额外资源（专属链接、优先排期）

**话术模板：**

```
「我们参考了最近 30 个同类达人的数据，您的账号数据质量不错，
 但按当前播放体量，建议报价在 [CPM=10 价格] 附近。
 如果能确定本月档期，我们可以安排优先对接。」
```

---

## ⑥ 跟进同步：飞书实时推送，团队共享进度

```bash
cp .env.example .env.feishu
# 填入 FEISHU_APP_ID / FEISHU_APP_SECRET / FEISHU_WEBHOOK_URL

python scripts/sync_feishu_auto.py   # 同步数据到飞书
```

每天 10:00 自动推送：

- 待建联清单（按优先级排序）
- 跟进提醒（回复超 3 天未处理）
- 进度统计（本周建联数、回复率、确定合作数）

---

## 快速开始

### 1. 安装

```bash
git clone https://github.com/sz8887031-bot/kol-claw.git
cd kol-claw
pip install -r requirements.txt
```

### 2. 准备数据

```bash
cp data/sample/*.csv data/
```

### 3. 接入 Claude Code（解锁一句话操控）

```bash
npm install -g @anthropic-ai/claude-code
cd kol-claw
claude
```

Claude Code 自动读取项目配置，直接输入你的需求即可。

### 4. 手动使用脚本

```bash
python scripts/analyze_kol.py          # 分析达人评级和定价
python scripts/generate_script.py      # 生成建联话术
python scripts/daily_tasks.py          # 今日跟进任务
python scripts/budget_tracker.py       # 预算执行情况
```

---

## MCP 服务（供 AI 工具调用）

`mcp_server.py` 将核心功能暴露为标准 MCP 工具，Claude Code 或任何支持 MCP 协议的 AI 可直接调用，详见 [kol-claw-mcp](https://github.com/sz8887031-bot/kol-claw-mcp)。

---

## 项目结构

```
kol-claw/
├── mcp_server.py                       # MCP 服务
├── scripts/
│   ├── analyze_kol.py                  # 达人分析与定价
│   ├── generate_script.py              # 建联话术生成
│   ├── contact_tracker.py              # 建联进度追踪
│   ├── daily_tasks.py                  # 每日任务清单
│   ├── budget_tracker.py               # 预算追踪
│   ├── process_mediacrawler_data_v2.py # 多维度分析
│   └── sync_feishu_auto.py             # 飞书同步
├── data/sample/                        # 演示数据
├── docs/                               # 详细文档
└── .claude/CLAUDE.md                   # Claude Code 配置
```

---

## License

GPL-3.0

---

## 关于我们

> 不只是一套工具，更是一套经过实战验证的投放方法论。

我们已累计建联达人 **500+**，其中大部分为**低粉爆款达人**（粉丝 5-30 万、CPM 控制在 12 以内），平均 ROI 显著高于行业均值。这套系统正是在真实投放过程中一步步打磨出来的。

**如果你有 KOL 投放或品牌 PR 需求**，欢迎联系我们的专业团队，提供从达人筛选、建联谈判到效果追踪的全链路交付服务。

扫码加微信，备注来意：

![微信二维码](./assets/wechat_qr.jpg)
