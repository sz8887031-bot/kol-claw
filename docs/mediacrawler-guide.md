# MediaCrawler 集成说明

## 简介

MediaCrawler 是一个功能强大的多平台自媒体数据采集工具，已集成到本项目中用于 KOL 达人数据采集。

**✨ 特别说明：本项目已包含自定义的 `discover_creators.py` 脚本，专门用于抖音达人发现和数据分析。**

## 支持平台

- 小红书 (xhs)
- 抖音 (dy)
- 快手 (ks)
- B站 (bili)
- 微博 (wb)
- 贴吧 (tieba)
- 知乎 (zhihu)

## 核心功能

✅ 关键词搜索达人/内容
✅ 指定帖子ID爬取详情
✅ 爬取评论（一级/二级）
✅ 指定创作者主页数据
✅ 登录态缓存
✅ IP代理池支持
✅ 生成评论词云图

## 安装路径

```
<MEDIACRAWLER_DIR>
```

## 快速使用

### 方式1: 使用自定义的抖音达人发现脚本（推荐⭐）

```python
from mediacrawler_config import MediaCrawlerClient

# 初始化客户端
client = MediaCrawlerClient()

# 运行自定义的抖音达人发现脚本
# 自动搜索 "求职"、"个人成长"、"职场" 等关键词
result = client.run_discover_creators()

if result['success']:
    # 加载发现的达人数据
    creators_data = client.load_discovered_creators()
    print(f"发现 {creators_data['total_creators']} 个达人")

    # 筛选优质达人（粉丝数 >= 50000）
    top_creators = client.get_top_creators(min_followers=50000, limit=10)
    for creator in top_creators:
        print(f"{creator['creator_name']} - 粉丝: {creator['follower_count']:,}")
```

### 方式2: 使用封装的 Python 模块（通用）

```python
from mediacrawler_config import MediaCrawlerClient

# 初始化客户端
client = MediaCrawlerClient()

# 搜索小红书达人
result = client.search_creators(
    platform="xhs",
    keywords="美妆博主,护肤达人",
    max_count=20,
    login_type="qrcode"
)

# 获取创作者详情
result = client.get_creator_detail(
    platform="xhs",
    creator_id="5c9e3e3e0000000007009d3e"
)

# 获取帖子详情和评论
result = client.get_post_detail(
    platform="xhs",
    post_ids="65f3e3e3e3e3e3e3e3e3e3e3",
    get_comments=True,
    max_comments=100
)

# 加载最新爬取的数据
data = client.load_latest_data(platform="xhs", data_type="search")
```

### 方式3: 直接使用命令行

```bash
cd <MEDIACRAWLER_DIR>

# 运行自定义的抖音达人发现脚本
uv run python discover_creators.py

# 搜索小红书内容
uv run python main.py --platform xhs --type search --keywords "美妆博主" --lt qrcode

# 获取指定创作者主页
uv run python main.py --platform xhs --type creator --creator_id "用户ID" --lt qrcode

# 获取指定帖子详情
uv run python main.py --platform xhs --type detail --specified_id "帖子ID" --lt qrcode
```

## 配置说明

### 登录方式
- `qrcode`: 二维码扫码登录（推荐）
- `phone`: 手机号登录
- `cookie`: Cookie 登录

### 数据保存格式
- `json`: JSON 文件（默认）
- `csv`: CSV 文件
- `excel`: Excel 文件
- `sqlite`: SQLite 数据库
- `db`: MySQL 数据库
- `postgres`: PostgreSQL 数据库

### 爬取类型
- `search`: 关键词搜索
- `detail`: 帖子详情
- `creator`: 创作者主页

## 数据存储位置

爬取的数据默认保存在：
```
<MEDIACRAWLER_DIR>/data/
```

文件命名格式：
- `{platform}_{timestamp}_search_*.json` - 搜索结果
- `{platform}_{timestamp}_creator_*.json` - 创作者数据
- `{platform}_{timestamp}_detail_*.json` - 帖子详情

## 使用场景

### 1. 抖音达人批量发现（使用自定义脚本）⭐
使用 `discover_creators.py` 自动搜索多个关键词，批量发现达人并获取详细数据。

**特点：**
- 自动搜索多个关键词（求职、个人成长、职场）
- 自动获取达人的粉丝数、作品数、点赞数
- 自动抓取每个达人的最近5个视频
- 计算平均点赞数等关键指标
- 按粉丝数自动排序

```python
# 运行达人发现
result = client.run_discover_creators()

# 筛选优质达人
top_creators = client.get_top_creators(min_followers=100000, limit=20)
```

**数据输出位置：**
```
<MEDIACRAWLER_DIR>/discovered_creators.json
```

### 2. 达人发现与筛选（通用方法）
搜索特定领域的达人，获取基础数据用于初步筛选。

```python
client.search_creators(
    platform="xhs",
    keywords="美妆,护肤,彩妆",
    max_count=50
)
```

### 3. 达人深度分析
获取达人的详细主页数据，包括粉丝数、作品数、互动数据等。

```python
client.get_creator_detail(
    platform="xhs",
    creator_id="达人ID"
)
```

### 4. 内容效果分析
分析达人的具体作品表现，包括点赞、评论、转发等数据。

```python
client.get_post_detail(
    platform="xhs",
    post_ids="帖子ID1,帖子ID2",
    get_comments=True,
    max_comments=200
)
```

### 5. 评论情感分析
爬取评论数据，分析用户反馈和情感倾向。

## 注意事项

⚠️ **重要提醒**

1. **合法合规使用**：仅用于学习和研究目的，不得用于商业用途
2. **频率控制**：合理控制爬取频率，避免对平台造成负担
3. **登录状态**：首次使用需要扫码登录，登录状态会被缓存
4. **数据隐私**：妥善保管爬取的数据，不得泄露用户隐私
5. **平台规则**：遵守各平台的 robots.txt 和使用条款

## 常见问题

### Q: 扫码登录失败？
A: 设置 `headless=False` 打开浏览器，手动通过滑动验证码。

### Q: 爬取速度慢？
A: 可以调整 `max_concurrency_num` 参数增加并发数，但要注意频率限制。

### Q: 数据保存在哪里？
A: 默认保存在 MediaCrawler 的 `data/` 目录，可通过 `save_data_path` 自定义。

### Q: 如何启用 IP 代理？
A: 设置 `enable_ip_proxy=True` 并配置代理提供商。

## 技术原理

- **核心技术**：基于 Playwright 浏览器自动化框架
- **登录保持**：保存登录态的浏览器上下文环境
- **签名获取**：通过 JS 表达式获取签名参数，无需逆向
- **CDP 模式**：支持使用用户现有的 Chrome/Edge 浏览器

## 相关资源

- [MediaCrawler GitHub](https://github.com/NanmiCoder/MediaCrawler)
- [完整文档](https://nanmicoder.github.io/MediaCrawler/)
- [数据存储指南](https://github.com/NanmiCoder/MediaCrawler/blob/main/docs/data_storage_guide.md)

## 更新日志

- 2026-03-02: 集成 MediaCrawler 到 KOL 投放管理系统
