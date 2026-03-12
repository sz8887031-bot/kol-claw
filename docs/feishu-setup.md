# 飞书配置独立化说明

## 问题背景

之前飞书配置依赖 ccswitch 全局环境变量，当 ccswitch 切换配置时会导致飞书功能报 502 错误。

## 解决方案

将飞书配置独立为项目级配置，不受 ccswitch 影响。

## 配置方式

### 1. 项目级配置（推荐）

在项目根目录创建 `.env.feishu` 文件：

```bash
# 复制模板
cp .env.feishu.template .env.feishu

# 编辑配置
vim .env.feishu
```

填入你的飞书应用凭证：
```env
FEISHU_APP_ID=your_app_id
FEISHU_APP_SECRET=your_app_secret
```

### 2. 系统环境变量（备选）

如果没有 `.env.feishu` 文件，会自动读取系统环境变量：

```bash
export FEISHU_APP_ID=your_app_id
export FEISHU_APP_SECRET=your_app_secret
```

## 配置优先级

```
项目级 .env.feishu > 系统环境变量 > 报错
```

## 测试配置

```bash
# 测试配置加载
python3 feishu_config.py

# 测试脚本运行
python3 sync_feishu_auto.py
```

## 已更新的文件

所有飞书相关脚本已更新为使用新的配置模块：

- ✅ sync_feishu_auto.py
- ✅ sync_to_feishu_incremental.py
- ✅ sync_to_feishu_bitable.py
- ✅ check_bitable_info.py
- ✅ fix_feishu_permission.py
- ✅ check_bitable_structure.py
- ✅ manage_feishu_permission.py
- ✅ fix_permission_v2.py
- ✅ create_feishu_doc.py
- ✅ test_feishu_docs.py

## 核心文件

- `feishu_config.py` - 配置加载模块
- `.env.feishu` - 项目级配置文件（已添加到 .gitignore）
- `.env.feishu.template` - 配置模板

## 优势

1. **独立性**：飞书配置不受 ccswitch 切换影响
2. **安全性**：配置文件已加入 .gitignore，不会泄露
3. **灵活性**：支持项目级和系统级两种配置方式
4. **易用性**：统一的配置加载模块，所有脚本自动使用

## 迁移完成

- ✅ 删除了旧的 `~/.feishu_config` 文件
- ✅ 创建了新的项目级配置 `.env.feishu`
- ✅ 更新了所有 10 个飞书脚本
- ✅ 添加了配置模板和说明文档
- ✅ 更新了 .gitignore 防止配置泄露
