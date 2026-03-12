#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日预算和建联进度推送
整合预算追踪 + 建联清单
"""

import json
import requests
import os
import pandas as pd
from datetime import datetime
from budget_tracker import BudgetTracker
from contact_tracker import ContactTracker


def send_to_feishu(webhook_url, content):
    """发送消息到飞书"""
    data = {
        "msg_type": "text",
        "content": {"text": content}
    }

    try:
        response = requests.post(
            webhook_url,
            headers={'Content-Type': 'application/json'},
            data=json.dumps(data)
        )
        result = response.json()
        if result.get('code') == 0:
            print("✅ 飞书推送成功")
            return True
        else:
            print(f"❌ 推送失败：{result}")
            return False
    except Exception as e:
        print(f"❌ 推送出错：{e}")
        return False


def generate_daily_message():
    """生成每日推送消息"""
    # 获取预算状态
    budget_tracker = BudgetTracker()
    budget_tracker.load_data()
    status = budget_tracker.get_project_status()
    pending = budget_tracker.get_pending_kols()

    # 获取建联状态
    contact_tracker = ContactTracker()
    contact_report = contact_tracker.generate_report()

    today = datetime.now().strftime('%Y-%m-%d')

    message = f"""📊 KOL投放日报 - {today}

━━━━━━━━━━━━━━━━━━━━━
💰 预算执行情况
━━━━━━━━━━━━━━━━━━━━━
项目：{status['project_name']}
截止：{status['deadline']} (剩余{status['days_left']}天)

总预算：¥{status['total_budget']:,}
已花费：¥{status['actual_spent']:,} ({status['actual_spent']/status['total_budget']*100:.1f}%)
已确定：¥{status['estimated_total']:,} ({status['estimated_total']/status['total_budget']*100:.1f}%)
剩余：¥{status['remaining_budget']:,}

投放达人：{status['confirmed_kols']}人
预估播放：{status['estimated_play']:,}

━━━━━━━━━━━━━━━━━━━━━
🎯 今日待办
━━━━━━━━━━━━━━━━━━━━━
"""

    # 添加已确定合作的待办
    confirmed = budget_tracker.plan[budget_tracker.plan['合作状态'] == '已确定合作']
    if not confirmed.empty:
        message += "\n✅ 已确定合作（待投放）：\n"
        for _, row in confirmed.iterrows():
            kol = budget_tracker.kols[budget_tracker.kols['达人ID'] == row['达人ID']]
            if not kol.empty:
                median_play = budget_tracker.calculate_median_play(kol.iloc[0])
                estimated_cost = budget_tracker.estimate_cost(median_play, row['谈定CPM'])
                message += f"• {row['达人名称']} - CPM¥{row['谈定CPM']} | 预估播放{median_play:,} | 预估¥{estimated_cost:,}\n"
                if pd.notna(row['备注']):
                    message += f"  📌 {row['备注']}\n"

    # 添加待跟进的优先达人（前3个）
    stats = contact_report['stats']
    if stats['待建联'] > 0:
        message += f"\n🎯 待跟进达人（按性价比排序，显示前3）：\n"
        for i, kol in enumerate(pending[:3], 1):
            message += f"{i}. {kol['priority']} {kol['name']} - CPM¥{kol['estimated_cpm']} | 预估播放{kol['median_play']:,} | 预估¥{kol['estimated_cost']:,}\n"

    # 添加建联统计
    message += f"""
━━━━━━━━━━━━━━━━━━━━━
📈 建���进度
━━━━━━━━━━━━━━━━━━━━━
总达人数：{stats['总数']}
已建联：{stats['已建联']}人 ({stats['已建联']/stats['总数']*100 if stats['总数']>0 else 0:.1f}%)
待建联：{stats['待建联']}人

━━━━━━━━━━━━━━━━━━━━━
💡 行动建议
━━━━━━━━━━━━━━━━━━━━━
• 日均预算目标：¥{status['remaining_budget']/status['days_left'] if status['days_left']>0 else 0:,.0f}/天
• 预估还需达人：约{int(status['remaining_budget']/5000)}人
• 优先级：性价比优先（CPM从低到高）

加油！💪
"""

    return message


def main():
    """主函数"""
    print("=" * 60)
    print(f"📤 每日预算和建联进度推送 - {datetime.now().strftime('%H:%M')}")
    print("=" * 60)
    print()

    # 从环境变量读取Webhook URL
    webhook_url = os.getenv('FEISHU_WEBHOOK_URL')

    if not webhook_url:
        print("⚠️  未设置FEISHU_WEBHOOK_URL环境变量")
        print("💡 请在 CC-Switch 中配置 FEISHU_WEBHOOK_URL（飞书群机器人 Webhook 地址）")
        return

    # 生成并发送消息
    try:
        message = generate_daily_message()
        print("生成的消息：")
        print(message)
        print()
        send_to_feishu(webhook_url, message)
    except Exception as e:
        print(f"❌ 生成消息失败：{e}")
        import traceback
        traceback.print_exc()

    print()
    print("=" * 60)
    print("✨ 完成")
    print("=" * 60)


if __name__ == '__main__':
    main()
