# 建联管理系统 v3.0 - 快速指南

## 📋 建联状态体系

```
0. 🔍 待筛选    - 还没看过，待评估
1. 📝 待接触    - 已评估，计划打招呼
2. 📤 已私信    - 已发私信/邮件，等待回复
3. ⏰ 待跟进    - 超过48小时无回复，需二次跟进
4. ✅ 已回复    - 达人已回复，待深入沟通
5. 💰 已报价    - 达人已报价，谈判中
6. 🤝 确定合作  - 已确定合作意向
7. ❌ 无效/拒绝 - 跟进3次以上无回复或明确拒绝
```

## 🚀 每日工作流程

### 1. 早上10:00 - 生成每日任务

```bash
python3 daily_tasks.py
```

这会生成：
- 📤 今日待打招呼清单（优先级排序，默认50个）
- ⏰ 今日待跟进清单（已私信超48小时）
- 💬 待深入沟通清单（已回复待谈价）
- 💰 谈判中清单（已报价待确认）

### 2. 批量打招呼（工作时间）

发完私信/邮件后，批量更新状态：

```bash
python3 update_status.py --contact 达人1 达人2 达人3
```

或者一次更新多个：
```bash
python3 update_status.py --contact \
  美香疯 \
  惠中 \
  不可思议大王 \
  米菲历险记 \
  铜板
```

### 3. 晚上回顾 - 处理回复

#### 达人回复了
```bash
python3 update_status.py --reply 达人名
```

#### 达人报价了
```bash
python3 update_status.py --quote 达人名 3000
```

#### 确定合作
```bash
python3 update_status.py --confirm 达人名
```

#### 需要跟进（超48小时无回复）
```bash
python3 update_status.py --follow 达人名
```

#### 标记无效（跟进3次以上）
```bash
python3 update_status.py --invalid 达人名
```

## 📊 查看数据分析

### 查看所有达人评分排名
```bash
python3 analyze_kol.py
```

### 只看未建联达人排名
```bash
python3 analyze_kol.py | grep -A 13 "^[0-9]" | grep -B 8 "待接触\|待筛选"
```

## 💡 实战案例

### 场景1：早上开始工作

```bash
# 1. 生成今日任务
python3 daily_tasks.py

# 2. 批量打招呼（从优先级清单选前10个）
python3 update_status.py --contact \
  美香疯 惠中 不可思议大王 米菲历险记 铜板 \
  一里菜花蛇 工作主理人 想进开水团 沈清云 胡闹波波
```

### 场景2：处理回复

```bash
# 1. 标记已回复
python3 update_status.py --reply 美香疯 惠中

# 2. 更新报价
python3 update_status.py --quote 美香疯 400
python3 update_status.py --quote 惠中 2800

# 3. 确定合作
python3 update_status.py --confirm 美香疯
```

### 场景3：跟进无回复达人

```bash
# 1. 查看待跟进清单
python3 daily_tasks.py

# 2. 二次跟进
python3 update_status.py --follow 达人1 达人2

# 3. 跟进3次仍无回复，标记无效
python3 update_status.py --invalid 达人3
```

## 🎯 工作目标

- **每天打招呼**：50个达人（系统自动按优先级排序）
- **回复率目标**：30%+
- **建联周期**：48小时内回复 → 确定合作
- **跟进策略**：超48小时跟进，3次无回复标记无效

## 📈 转化漏斗监控

系统会自动统计：
- 已打招呼数量
- 回复率（已回复/已打招呼）
- 报价率（已报价/已回复）
- 成单率（确定合作/已报价）

每天运行 `python3 daily_tasks.py` 即可查看。

## ⚠️ 注意事项

1. **每次操作后都会自动保存CSV**，无需手动保存
2. **跟进次数自动累计**，达到3次会提示标记无效
3. **状态只能往前推进**，不会自动回退
4. **建议每天工作结束时运行一次**，检查转化漏斗

## 🔧 高级用法

### 自定义每日打招呼数量
```bash
python3 daily_tasks.py 100  # 生成100个待打招呼清单
```

### 批量导入新达人
直接在CSV中添加新行，保持格式一致即可。系统会自动识别为"待筛选"状态。
