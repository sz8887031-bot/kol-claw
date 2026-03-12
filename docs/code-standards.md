# 代码编写规范

> **目的**：防止更新代码时移除原有功能或改崩溃系统

---

## 🚨 核心原则

### 1. 只新增，不删除
- **禁止删除**已有功能代码（除非明确废弃）
- **禁止删除**已有配置项
- **禁止删除**CSV字段（可新增，不可删）
- **禁止删除**环境变量（可新增，不可删）

### 2. 向后兼容
- 新增功能必须兼容旧数据
- 修改字段必须保留旧字段或提供迁移脚本
- 修改API必须保持旧接口可用或提供过渡期

### 3. 修改前必读
- 阅读 `data/claude.md` 了解系统架构
- 阅读 `MEMORY.md` 了解历史决策
- 检查相关脚本是否依赖要修改的部分

---

## 📋 修改前检查清单

### 修改CSV文件结构
- [ ] 检查所有Python脚本是否依赖该字段
- [ ] 检查飞书推送是否使用该字段
- [ ] 如删除字段，提供数据迁移方案
- [ ] 更新 `data/claude.md` 中的字段说明

### 修改Python脚本
- [ ] 检查是否被其他脚本调用
- [ ] 检查是否被定时任务使用
- [ ] 检查是否依赖特定环境变量
- [ ] 运行测试确保不影响现有功能

### 修改环境变量
- [ ] 检查所有脚本中的环境变量引用
- [ ] 更新 `CC_SWITCH_配置说明.md`
- [ ] 更新 `data/claude.md` 中的环境变量表
- [ ] 通知用户更新CC-Switch配置

### 修改工作流程
- [ ] 更新 `data/claude.md` 中的流程图
- [ ] 更新 `MEMORY.md` 中的规则
- [ ] 标注修改日期（如：2026-03-05更新）
- [ ] 说明修改原因和影响范围

---

## 🔧 安全修改模式

### 模式1：扩展式新增
**适用场景**：添加新功能、新字段、新脚本

```python
# ✅ 正确：新增字段，保留旧字段
df['新字段'] = df['旧字段'].apply(lambda x: process(x))
# 旧字段继续可用

# ❌ 错误：直接替换
df['旧字段'] = df['旧字段'].apply(lambda x: process(x))
# 可能破坏依赖旧数据格式的代码
```

### 模式2：渐进式迁移
**适用场景**：重构现有功能

```python
# ✅ 正确：提供新旧两种方式
def get_data_v2():  # 新版本
    return new_logic()

def get_data():  # 旧版本，标记为deprecated
    warnings.warn("请使用get_data_v2", DeprecationWarning)
    return old_logic()

# ❌ 错误：直接修改原函数
def get_data():
    return new_logic()  # 可能破坏调用方
```

### 模式3：配置化切换
**适用场景**：实验性功能

```python
# ✅ 正确：通过配置控制
USE_NEW_FEATURE = os.getenv('USE_NEW_FEATURE', 'false') == 'true'

if USE_NEW_FEATURE:
    result = new_method()
else:
    result = old_method()

# ❌ 错误：直接替换
result = new_method()  # 无法回退
```

---

## 📊 数据文件管理规范

### CSV文件修改规则
1. **新增字段**：追加到末尾，不插入中间
2. **删除字段**：先标记为deprecated，至少保留一个版本周期
3. **重命名字段**：保留旧字段，新增新字段，提供映射
4. **修改数据格式**：提供转换脚本，支持新旧格式共存

### 备份策略
```bash
# 修改CSV前必须备份
cp data/达人跟进表.csv "data/达人跟进表_备份_$(date +%Y%m%d).csv"

# 修改后验证
python3 -c "import pandas as pd; df = pd.read_csv('data/达人跟进表.csv'); print(df.shape)"
```

---

## 🧪 测试规范

### 修改后必须测试
```bash
# 1. 数据完整性测试
python3 -c "
import pandas as pd
df = pd.read_csv('data/达人跟进表.csv')
assert '达人ID' in df.columns, '缺少达人ID字段'
assert len(df) > 0, '数据为空'
print('✅ 数据完整性检查通过')
"

# 2. 脚本功能测试
python3 contact_tracker.py --dry-run
python3 analyze_kol.py --test
python3 feishu_webhook_push.py --test

# 3. 环境变量测试
echo $FEISHU_WEBHOOK_URL
echo $FEISHU_APP_ID
```

---

## 📝 文档更新规范

### 必须同步更新的文档
1. **data/claude.md** - 系统架构和工作流程
2. **MEMORY.md** - 规则和决策记录
3. **README.md** - 项目说明
4. **相关规范文档** - 如本文件

### 文档更新模板
```markdown
## 功能名称 ⭐ 新增/更新（日期）

**变更内容**：
- 新增：XXX功能
- 修改：XXX逻辑
- 废弃：XXX功能（保留至YYYY-MM-DD）

**影响范围**：
- 影响文件：xxx.py, yyy.csv
- 影响流程：达人筛选流程步骤3
- 向后兼容：是/否

**使用方式**：
```bash
# 示例命令
```

**注意事项**：
- 注意点1
- 注意点2
```

---

## 🚫 禁止操作清单

### 绝对禁止
- ❌ 删除 `data/达人跟进表.csv` 中的任何字段
- ❌ 修改CSV文件编码（必须保持UTF-8）
- ❌ 硬编码API密钥、Webhook URL等敏感信息
- ❌ 删除正在使用的环境变量
- ❌ 修改已有函数的返回值类型
- ❌ 删除正在使用的Python脚本

### 谨慎操作
- ⚠️ 修改CSV字段顺序（可能影响脚本）
- ⚠️ 重命名Python函数（检查所有调用）
- ⚠️ 修改数据格式（提供转换脚本）
- ⚠️ 更改工作流程（更新所有文档）

---

## 🔄 版本管理规范

### Git提交规范
```bash
# 提交前检查
git status
git diff

# 提交信息格式
git commit -m "类型: 简短描述

详细说明：
- 变更1
- 变更2

影响范围：
- 文件A
- 文件B

向后兼容：是/否
"
```

### 提交类型
- `feat`: 新功能
- `fix`: 修复bug
- `refactor`: 重构（不改变功能）
- `docs`: 文档更新
- `style`: 代码格式（不影响功能）
- `test`: 测试相关
- `chore`: 构建/工具相关

---

## 🆘 出问题时的恢复流程

### 1. 立即回滚
```bash
# 查看最近提交
git log --oneline -5

# 回滚到上一个版本
git reset --hard HEAD~1

# 或回滚到指定版本
git reset --hard <commit-hash>
```

### 2. 恢复数据文件
```bash
# 从备份恢复
cp "data/达人跟进表_备份_YYYYMMDD.csv" data/达人跟进表.csv

# 或从git历史恢复
git checkout HEAD~1 -- data/达人跟进表.csv
```

### 3. 检查系统状态
```bash
# 运行健康检查
<PROJECT_DIR>/check_env.sh

# 测试核心功能
python3 contact_tracker.py
python3 feishu_webhook_push.py --test
```

---

## 📚 参考文档

- `data/claude.md` - 系统架构和工作约束
- `MEMORY.md` - 规则管理和历史决策
- `data/达人筛选标准化流程.md` - 达人筛选流程
- `data/工具调用前检查清单.md` - 操作前检查
- `CC_SWITCH_配置说明.md` - 环境变量管理

---

**最后更新**: 2026-03-05
**维护者**: Claude Code
**版本**: 1.0
