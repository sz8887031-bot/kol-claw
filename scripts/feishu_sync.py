#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书自动化推送工具
功能：
1. 每天早上10点自动推送待跟进清单
2. 同步达人数据到飞书多维表格
3. 智能提醒建联任务
"""

import pandas as pd
from datetime import datetime, timedelta
import json
import os
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / 'data'

CONTACT_STATUS_NOT_CONTACTED = {'未建联', '待接触', '待筛选', '', 'nan'}
CONTACT_STATUS_REPLIED = {'已回复', '未报价', '已报价', '确定合作'}
CONTACT_STATUS_QUOTED = {'已报价', '确定合作'}
COOP_STATUS_CONFIRMED = {'确定合作', '已投放', '已发布'}
COOP_STATUS_FOLLOW = {'待跟进'}

class FeishuKOLManager:
    """飞书KOL管理工具"""

    def __init__(self, csv_path=DATA_DIR / '达人跟进表.csv'):
        self.csv_path = csv_path
        self.df = pd.read_csv(csv_path, encoding='utf-8-sig')
        self.df_valid = self.df[
            self.df['达人昵称'].notna() &
            (self.df['达人昵称'] != '') &
            (self.df['达人昵称'] != '未建联')
        ].copy()

        # 计算播放数据
        play_cols = ['播放1', '播放2', '播放3', '播放4', '播放5']
        self.df_valid['平均播放'] = self.df_valid[play_cols].mean(axis=1)
        self.df_valid['播粉比'] = self.df_valid['平均播放'] / self.df_valid['粉丝数']

    def generate_daily_report(self):
        """生成每日待跟进报告"""
        report = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'stats': self._get_stats(),
            'todo_contact': self._get_todo_contact(),
            'need_followup': self._get_need_followup(),
            'need_quote': self._get_need_quote(),
            'weekly_progress': self._get_weekly_progress()
        }
        return report

    def _get_stats(self):
        """获取统计数据"""
        total = len(self.df_valid)
        if '建联状态' not in self.df_valid.columns:
            return {
                'total': total,
                'contacted': 0,
                'replied': 0,
                'quoted': 0,
                'contact_rate': 0,
                'reply_rate': 0,
                'quote_rate': 0
            }

        contact_status = self.df_valid['建联状态'].fillna('').astype(str).str.strip()
        if '确定合作' in self.df_valid.columns:
            coop_status = self.df_valid['确定合作'].fillna('').astype(str).str.strip()
        else:
            coop_status = pd.Series([''] * total, index=self.df_valid.index)

        contacted = len(self.df_valid[~contact_status.isin(CONTACT_STATUS_NOT_CONTACTED)])
        replied = len(self.df_valid[contact_status.isin(CONTACT_STATUS_REPLIED) | coop_status.isin(COOP_STATUS_CONFIRMED)])
        quoted = len(self.df_valid[
            contact_status.isin(CONTACT_STATUS_QUOTED) |
            (self.df_valid['报价'].notna() & (self.df_valid['报价'] != '')) |
            coop_status.isin(COOP_STATUS_CONFIRMED)
        ])

        return {
            'total': total,
            'contacted': contacted,
            'replied': replied,
            'quoted': quoted,
            'contact_rate': round(contacted / total * 100, 1) if total > 0 else 0,
            'reply_rate': round(replied / contacted * 100, 1) if contacted > 0 else 0,
            'quote_rate': round(quoted / replied * 100, 1) if replied > 0 else 0
        }

    def _get_todo_contact(self):
        """获取待建联清单（按优先级）"""
        contact_status = self.df_valid['建联状态'].fillna('').astype(str).str.strip()
        not_contacted = self.df_valid[contact_status.isin(CONTACT_STATUS_NOT_CONTACTED)].copy()

        if len(not_contacted) == 0:
            return []

        # 计算优先级
        def calc_priority(row):
            score = 0
            fans = row['粉丝数']
            ratio = row['播粉比']

            if 5000 <= fans <= 100000 and ratio > 1:
                score = 3
            elif fans < 5000 and ratio > 5:
                score = 2
            else:
                score = 1
            return score

        not_contacted['priority_score'] = not_contacted.apply(calc_priority, axis=1)
        not_contacted = not_contacted.sort_values('priority_score', ascending=False)

        result = []
        for idx, row in not_contacted.head(5).iterrows():
            priority = "🔥高" if row['priority_score'] >= 3 else "⭐中" if row['priority_score'] >= 2 else "💡低"
            avg_play = row['平均播放']
            price = (avg_play * 15) / 1000

            # 推荐话术
            if row['粉丝数'] >= 50000:
                script = "方案B（正式型）"
            elif row['粉丝数'] < 5000:
                script = "方案C（低粉爆款）"
            else:
                script = "方案A（询价型）"

            result.append({
                'priority': priority,
                'name': row['达人昵称'],
                'fans': int(row['粉丝数']),
                'avg_play': int(avg_play),
                'price': int(price),
                'script': script
            })

        return result

    def _get_need_followup(self):
        """获取需要跟进的达人"""
        contact_status = self.df_valid['建联状态'].fillna('').astype(str).str.strip()
        if '确定合作' in self.df_valid.columns:
            coop_status = self.df_valid['确定合作'].fillna('').astype(str).str.strip()
            need_follow = self.df_valid[coop_status.isin(COOP_STATUS_FOLLOW)].copy()
        else:
            need_follow = self.df_valid[contact_status.isin({'已建联', '已私信', '待跟进'})].copy()

        if len(need_follow) == 0:
            return []

        result = []
        for idx, row in need_follow.iterrows():
            contact_date = row.get('建联时间', '')
            days_passed = 0
            action = "📝 请填写建联时间"

            if pd.notna(contact_date) and contact_date != '':
                try:
                    contact_dt = pd.to_datetime(contact_date)
                    days_passed = (datetime.now() - contact_dt).days

                    if days_passed >= 3:
                        action = "⚠️ 超过3天，标记'无回复'"
                    elif days_passed >= 2:
                        action = "🔔 可以发二次跟进"
                    else:
                        action = "⏳ 继续等待"
                except:
                    action = "📝 请填写正确的建联时间"

            result.append({
                'name': row['达人昵称'],
                'contact_date': contact_date,
                'days': days_passed,
                'action': action
            })

        return result

    def _get_need_quote(self):
        """获取待询价的达人"""
        contact_status = self.df_valid['建联状态'].fillna('').astype(str).str.strip()
        need_quote = self.df_valid[
            contact_status.isin({'已回复', '未报价'}) &
            (self.df_valid['报价'].isna() | (self.df_valid['报价'] == ''))
        ].copy()

        if len(need_quote) == 0:
            return []

        result = []
        for idx, row in need_quote.iterrows():
            wechat = row.get('微信联系方式', row.get('微信号', '未填写'))
            avg_play = row['平均播放']
            price = (avg_play * 15) / 1000

            result.append({
                'name': row['达人昵称'],
                'wechat': wechat,
                'expected_price': int(price)
            })

        return result

    def _get_weekly_progress(self):
        """获取本周进度"""
        # 简单统计（可以扩展为真正的周统计）
        stats = self._get_stats()

        # 计算本周目标
        contact_status = self.df_valid['建联状态'].fillna('').astype(str).str.strip()
        not_contacted = len(self.df_valid[contact_status.isin(CONTACT_STATUS_NOT_CONTACTED)])
        weekly_target = min(3, not_contacted)

        return {
            'total': stats['total'],
            'contacted': stats['contacted'],
            'not_contacted': not_contacted,
            'weekly_target': weekly_target,
            'contact_rate': stats['contact_rate'],
            'reply_rate': stats['reply_rate']
        }

    def format_markdown_message(self, report):
        """格式化为飞书Markdown消息"""
        stats = report['stats']
        todo = report['todo_contact']
        followup = report['need_followup']
        quote = report['need_quote']
        progress = report['weekly_progress']

        message = f"""# 📅 KOL建联日报 - {report['date']}

## 📊 进度统计
- 总达人数：{stats['total']} 人
- 已建联：{stats['contacted']} 人（{stats['contact_rate']}%）
- 已回复：{stats['replied']} 人（回复率 {stats['reply_rate']}%）
- 已报价：{stats['quoted']} 人

---

## 🎯 今日待办

"""

        # 待建联清单
        if len(todo) > 0:
            message += "### 1️⃣ 优先建联（按优先级）\n\n"
            for item in todo[:3]:  # 只显示前3个
                message += f"{item['priority']} **{item['name']}**\n"
                message += f"   - 粉丝：{item['fans']:,} | 播放：{item['avg_play']:,}\n"
                message += f"   - 预估报价：¥{item['price']:,}\n"
                message += f"   - 话术：{item['script']}\n\n"
        else:
            message += "### 1️⃣ 待建联清单\n✅ 暂无待建联达人\n\n"

        # 需要跟进
        if len(followup) > 0:
            message += "### 2️⃣ 需要跟进的达人\n\n"
            for item in followup:
                message += f"**{item['name']}** - 建联 {item['days']} 天\n"
                message += f"   {item['action']}\n\n"
        else:
            message += "### 2️⃣ 需要跟进\n✅ 暂无待跟进\n\n"

        # 待询价
        if len(quote) > 0:
            message += "### 3️⃣ 待询价的达人\n\n"
            for item in quote:
                message += f"**{item['name']}** - 微信：{item['wechat']}\n"
                message += f"   预估报价：¥{item['expected_price']:,}\n\n"
        else:
            message += "### 3️⃣ 待询价\n✅ 暂无待询价\n\n"

        # 本周目标
        message += f"""---

## 📈 本周目标
- 本周建联目标：{progress['weekly_target']} 人
- 当前进度：{progress['contacted']}/{progress['total']}
- 剩余待建联：{progress['not_contacted']} 人

💡 建议今天建联 1-2 个优先级最高的达人
"""

        return message

    def export_to_json(self, report, output_path='daily_report.json'):
        """导出为JSON（供飞书API使用）"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        return output_path


def main():
    """主函数：生成并显示日报"""
    print("="*80)
    print(f"🤖 飞书KOL管理助手 - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("="*80)

    try:
        manager = FeishuKOLManager()
        report = manager.generate_daily_report()

        # 生成Markdown消息
        message = manager.format_markdown_message(report)
        print(message)

        # 导出JSON
        json_path = manager.export_to_json(report)
        print(f"\n✅ 报告已导出到：{json_path}")

        # 保存Markdown
        md_path = f'daily_report_{datetime.now().strftime("%Y%m%d")}.md'
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(message)
        print(f"✅ Markdown已保存到：{md_path}")

        return report

    except Exception as e:
        print(f"❌ 错误：{str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
