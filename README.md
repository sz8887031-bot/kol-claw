# KOL 投放管理系统

> 轻量级达人投放管理工具 - 性价比优先，数据驱动，开箱即用

## 功能模块

1. **达人分析与评级** - 多维度评估（粉赞比、稳定性、样本量），S/A/B/C/D 五级评级
2. **预算追踪管理** - 项目预算执行、投放计划、剩余预算实时追踪
3. **建联跟进** - 进度追踪、话术生成、时间记录
4. **MediaCrawler 集成** - 关键词搜索、批量抓取、自动分类（需配置 MediaCrawler）
5. **飞书自动化** - 每日推送、日历同步、多维表格同步（可选）
6. **数据分析** - 定价策略、性价比分析、投放建议

---

## 目录结构

```
kol-claw/
├── scripts/          # 所有 Python 脚本
│   ├── analyze_kol.py              # 达人分析与定价
│   ├── grade_kol.py                # 达人评级
│   ├── budget_tracker.py           # 预算追踪
│   ├── contact_tracker.py          # 建联进度追踪
│   ├── contact_strategy.py         # 建联策略
│   ├── generate_script.py          # 话术生成
│   ├── daily_tasks.py              # 每日任务
│   ├── update_status.py            # 状态更新
│   ├── process_mediacrawler_data_v2.py  # MediaCrawler 数据处理
│   ├── sync_calendar.py            # 日历同步
│   ├── feishu_config.py            # 飞书配置
│   ├── feishu_sync.py              # 飞书数据同步
│   ├── sync_feishu_auto.py         # 飞书自动同步
│   └── ...                         # 更多脚本
├── docs/             # 文档
│   ├── quick-start.md              # 快速上手指南
│   ├── creator-selection-guide.md  # 达人筛选流程
│   ├── feishu-setup.md             # 飞书配置说明
│   ├── contact-management.md       # 建联管理
│   ├── pricing-rules.md            # 定价规则
│   └── evaluation-rules.md         # 评估规则
├── bin/              # Shell 脚本
│   ├── check_env.sh                # 环境检查
│   └── quick_start.sh              # 快速启动
├── data/
│   └── sample/       # 演示数据（完全虚构）
│       ├── 达人跟进表.csv
│       ├── 优质达人.csv
│       ├── 备选达人.csv
│       ├── 确定合作达人跟进表.csv
│       ├── 项目预算追踪.csv
│       └── 投放计划表.csv
├── .claude/
│   └── CLAUDE.md     # Claude Code 配置
├── .env.example      # 环境变量模板
├── .gitignore
├── LICENSE
├── requirements.txt
└── README.md
```

---

## 快速开始

### 1. 克隆并安装依赖

```bash
git clone https://github.com/your-username/kol-claw.git
cd kol-claw
pip install -r requirements.txt
```

### 2. 准备数据文件

将演示数据复制到 `data/` 目录作为起点：

```bash
cp data/sample/*.csv data/
```

然后编辑 `data/达人跟进表.csv`，填入你的真实达人信息：
- 达人昵称、粉丝数
- 最近 5 个视频的播放量
- 其他字段可后续填写

### 3. 分析达人

```bash
python scripts/analyze_kol.py
```

输出：
- 播放中位数（去除爆款干扰）
- 预期报价（分层定价）
- 性价比评分与优先级排序

### 4. 查看预算

```bash
python scripts/budget_tracker.py
```

### 5. 建联话术

```bash
python scripts/generate_script.py
```

根据达人类型自动生成话术：询价型、预算型、长期合作型。

### 6. 跟进进度

```bash
python scripts/contact_tracker.py
```

---

## 核心规则

### 评级标准（S/A/B/C/D）

| 等级 | 条件 | 建议 |
|------|------|------|
| S | 粉赞比>5% + 平均点赞>1000 + 样本≥5条 + 稳定性>30% | 优先建联 |
| A | 粉赞比>5% + 平均点赞>1000，但样本不足或不稳定 | 高潜力，可测试 |
| B | 粉赞比 2-5% | 良好，可小额测试 |
| C | 粉赞比 1-2% | 一般，谨慎投放 |
| D | 粉赞比<1% | 不推荐 |

### 定价策略

- **低粉达人**（<5K 粉）：固定预算 ¥300-800
- **中大体量**（≥5K 粉）：CPM=15 计算报价

### 优先级

- CPM<10：极致性价比
- CPM 10-12：高性价比
- CPM 12-15：标准性价比
- CPM>15：偏贵

---

## MediaCrawler 集成（可选）

配合 [MediaCrawler](https://github.com/NanmiCoder/MediaCrawler) 可实现全自动达人发现：

```bash
# 环境检查
bash bin/check_env.sh

# 数据处理（在 MediaCrawler 抓取完成后运行）
python scripts/process_mediacrawler_data_v2.py
```

输出：
- `data/优质达人.csv` - S/A 级达人（优先建联）
- `data/备选达人.csv` - B/C/D 级达人（可测试）

详见 [docs/mediacrawler-guide.md](docs/mediacrawler-guide.md)。

---

## 飞书集成（可选）

### 配置

```bash
cp .env.example .env.feishu
# 编辑 .env.feishu，填入你的飞书应用凭证
```

所需凭证：
- `FEISHU_APP_ID` / `FEISHU_APP_SECRET`：从飞书开放平台创建应用获取
- `FEISHU_APP_TOKEN`：多维表格的 Token（可选）
- `FEISHU_WEBHOOK_URL`：群机器人 Webhook（可选，用于每日推送）

详见 [docs/feishu-setup.md](docs/feishu-setup.md)。

### 功能

```bash
# 同步数据到飞书多维表格
python scripts/sync_feishu_auto.py

# 日历同步（macOS）
python scripts/sync_calendar.py
```

---

## 工作流程

```
发现达人 → 填入 CSV → 分析评级 → 生成话术 → 建联 → 跟进更新 → 确认合作 → 追踪预算 → 效果复盘
```

---

## 配置说明

所有敏感配置通过环境变量管理，不写入代码：

```bash
# 复制模板
cp .env.example .env.feishu

# 必填
FEISHU_APP_ID=your_app_id
FEISHU_APP_SECRET=your_app_secret

# 可选
FEISHU_USER_ID=your_user_id
FEISHU_APP_TOKEN=your_bitable_token
FEISHU_WEBHOOK_URL=your_webhook_url
```

---

## 依赖

```
pandas
numpy
python-dotenv
requests
```

```bash
pip install -r requirements.txt
```

---

## License

GPL-3.0 - 详见 [LICENSE](LICENSE)
