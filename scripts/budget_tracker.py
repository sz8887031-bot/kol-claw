#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KOL投放预算追踪系统
功能：
1. 追踪项目预算完成进度
2. 生成每日预算报告
3. 预估播放量和花费
"""

import pandas as pd
from datetime import datetime, timedelta
import json
from pathlib import Path


class BudgetTracker:
    """预算追踪管理器"""

    def __init__(self):
        self.base_path = Path(__file__).parent.parent / 'data'
        self.kol_csv = self.base_path / '达人跟进表.csv'
        self.budget_csv = self.base_path / '项目预算追踪.csv'
        self.plan_csv = self.base_path / '投放计划表.csv'

    def load_data(self):
        """加载所有数据"""
        self.kols = pd.read_csv(self.kol_csv, encoding='utf-8-sig')
        self.budget = pd.read_csv(self.budget_csv, encoding='utf-8-sig')
        self.plan = pd.read_csv(self.plan_csv, encoding='utf-8-sig')

    def calculate_median_play(self, row):
        """计算达人播放量中位数（去除极端值）"""
        plays = []
        for i in range(1, 6):
            col = f'播放{i}'
            if col in row and pd.notna(row[col]) and row[col] != '':
                try:
                    plays.append(float(row[col]))
                except:
                    pass

        if not plays:
            return 0

        # 排序后取中位数
        plays.sort()
        n = len(plays)
        if n % 2 == 0:
            # 偶数个，取中间两个的平均
            median = int((plays[n//2-1] + plays[n//2]) / 2)
        else:
            # 奇数个，取中间的
            median = int(plays[n//2])

        return median

    def estimate_cost(self, median_play, cpm, price_type='cpm'):
        """
        根据播放量和CPM估算费用，或使用一口价

        参数：
        - median_play: 中位数播放量
        - cpm: CPM价格或一口价
        - price_type: 'cpm' 或 'fixed'（一口价）
        """
        if pd.isna(cpm):
            return 0

        if price_type == 'fixed':
            # 一口价直接返回
            return int(cpm)
        else:
            # CPM计算
            if median_play == 0:
                return 0
            return int((median_play / 1000) * cpm)

    def get_project_status(self):
        """获取项目状态"""
        project = self.budget.iloc[0]

        # 计算已确定合作的达人情况
        confirmed = self.plan[self.plan['合作状态'].isin(['已确定合作', '已投放'])]

        total_estimated_cost = 0
        total_estimated_play = 0
        confirmed_count = 0

        for _, row in confirmed.iterrows():
            # 从达人跟进表获取播放数据
            kol = self.kols[self.kols['达人ID'] == row['达人ID']]
            if not kol.empty:
                median_play = self.calculate_median_play(kol.iloc[0])
                cpm = row['谈定CPM']
                estimated_cost = self.estimate_cost(median_play, cpm)

                total_estimated_play += median_play
                total_estimated_cost += estimated_cost
                confirmed_count += 1

        # 计算实际已花费（已投放的达人）
        launched = self.plan[self.plan['合作状态'] == '已投放']
        actual_spent = launched['实际费用'].sum() if not launched.empty else 0

        # 修正：剩余预算 = 总预算 - 已花费 - 已确定预估
        remaining = int(project['总预算'] - actual_spent - total_estimated_cost)

        return {
            'project_name': project['项目名称'],
            'deadline': project['截止日期'],
            'total_budget': int(project['总预算']),
            'actual_spent': int(actual_spent),
            'estimated_total': total_estimated_cost,
            'remaining_budget': remaining,
            'confirmed_kols': confirmed_count,
            'estimated_play': total_estimated_play,
            'days_left': self.calculate_days_left(project['截止日期'])
        }

    def calculate_days_left(self, deadline_str):
        """计算剩余天数"""
        deadline = datetime.strptime(deadline_str, '%Y-%m-%d')
        today = datetime.now()
        delta = deadline - today
        return max(0, delta.days)

    def get_pending_kols(self):
        """获取待建联达人列表（按性价比排序）"""
        pending = []

        for _, row in self.kols.iterrows():
            # 跳过已在投放计划中的达人
            if row['达人ID'] in self.plan['达人ID'].values:
                continue

            # 只统计有数据的达人
            if pd.notna(row['达人昵称']) and row['达人昵称'] != '':
                median_play = self.calculate_median_play(row)
                if median_play > 0:
                    # 预估CPM为10-12之间
                    estimated_cpm = 11
                    estimated_cost = self.estimate_cost(median_play, estimated_cpm)

                    # 确定优先级标识
                    if estimated_cpm < 10:
                        priority = '🌟🌟🌟'
                        priority_text = '极致性价比'
                    elif estimated_cpm <= 12:
                        priority = '🌟🌟'
                        priority_text = '高性价比'
                    elif estimated_cpm <= 15:
                        priority = '🌟'
                        priority_text = '标准性价比'
                    else:
                        priority = '⏸️'
                        priority_text = '偏贵'

                    pending.append({
                        'name': row['达人昵称'],
                        'fans': int(row['粉丝数']) if pd.notna(row['粉丝数']) else 0,
                        'median_play': median_play,
                        'estimated_cpm': estimated_cpm,
                        'estimated_cost': estimated_cost,
                        'priority': priority,
                        'priority_text': priority_text,
                        'status': row['备注'] if pd.notna(row['备注']) else ''
                    })

        # 按实际CPM排序（性价比优先），CPM相同时按预估费用从高到低
        pending.sort(key=lambda x: (x['estimated_cpm'], -x['estimated_cost']))
        return pending

    def generate_daily_report(self):
        """生成每日预算报告"""
        status = self.get_project_status()
        pending = self.get_pending_kols()

        # 生成Markdown报告
        report = f"""# 📊 KOL投放预算日报 - {datetime.now().strftime('%Y-%m-%d')}

## 🎯 项目概况

**项目名称**：{status['project_name']}
**截止日期**：{status['deadline']} （剩余 {status['days_left']} 天）
**总预算**：¥{status['total_budget']:,}

---

## 💰 预算执行情况

| 项目 | 金额 | 占比 |
|------|------|------|
| 已花费 | ¥{status['actual_spent']:,} | {status['actual_spent']/status['total_budget']*100:.1f}% |
| 已确定（预估）| ¥{status['estimated_total']:,} | {status['estimated_total']/status['total_budget']*100:.1f}% |
| 剩余预算 | ¥{status['remaining_budget']:,} | {status['remaining_budget']/status['total_budget']*100:.1f}% |

**进度条**：{'█' * int(status['actual_spent']/status['total_budget']*20)}{'░' * (20-int(status['actual_spent']/status['total_budget']*20))} {status['actual_spent']/status['total_budget']*100:.1f}%

---

## 📈 投放数据

- **已确定投放达人数**：{status['confirmed_kols']} 人
- **预估总播放量**：{status['estimated_play']:,}
- **预估平均CPM**：¥{status['estimated_total']/status['estimated_play']*1000 if status['estimated_play'] > 0 else 0:.2f}

---

## 📋 今日待办

### ✅ 已确定合作达人
"""

        # 添加已确定合作的达人
        confirmed = self.plan[self.plan['合作状态'] == '已确定合作']
        if confirmed.empty:
            report += "\n暂无已确定合作的达人\n"
        else:
            for _, row in confirmed.iterrows():
                kol = self.kols[self.kols['达人ID'] == row['达人ID']]
                if not kol.empty:
                    median_play = self.calculate_median_play(kol.iloc[0])
                    estimated_cost = self.estimate_cost(median_play, row['谈定CPM'])
                    report += f"""
**{row['达人名称']}**
- 谈定CPM：¥{row['谈定CPM']}
- 预估播放（中位数）：{median_play:,}
- 预估费用：¥{estimated_cost:,}
- 待办：{row['备注']}
"""

        report += "\n### 🎯 待跟进达人（按性价比排序）\n"

        # 只显示前5个待建联达人
        for i, kol in enumerate(pending[:5], 1):
            report += f"""
{i}. {kol['priority']} **{kol['name']}**
   - 粉丝：{kol['fans']:,} | 播放中位数：{kol['median_play']:,}
   - CPM：¥{kol['estimated_cpm']} ({kol['priority_text']}) | 预估费用：¥{kol['estimated_cost']:,}
   - 状态：{kol['status'] if kol['status'] else '待建联'}
"""

        # 计算完成目标还需多少达人
        remaining = status['remaining_budget']
        avg_cost = 5000  # 假设平均每个达人5000元
        need_kols = max(0, int(remaining / avg_cost))

        report += f"""
---

## 💡 预算建议

- 剩余预算：¥{remaining:,}
- 预估还需达人数：约 {need_kols} 人（按均价¥{avg_cost:,}/人计算）
- 日均预算目标：¥{remaining/status['days_left'] if status['days_left'] > 0 else 0:,.0f}/天
- 建议行动：
  - 优先跟进待回复达人（少吃点、易灵儿、eating张陛下）
  - 3月5号跟进胡闹波波（春招）
  - 持续开发新达人以达成预算目标

---

**生成时间**：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

        return report

    def save_report(self, report):
        """保存报告"""
        date_str = datetime.now().strftime('%Y%m%d')
        filename = self.base_path / f'budget_report_{date_str}.md'

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"✅ 预算报告已生成：{filename}")
        return filename


def main():
    """主函数"""
    print("=" * 80)
    print(f"📊 KOL投放预算追踪 - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 80)
    print()

    tracker = BudgetTracker()
    tracker.load_data()

    # 生成报告
    report = tracker.generate_daily_report()
    filename = tracker.save_report(report)

    # 打印到控制台
    print(report)

    print()
    print("=" * 80)
    print("✨ 完成！")
    print("=" * 80)


if __name__ == '__main__':
    main()
