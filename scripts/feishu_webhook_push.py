#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书群机器人Webhook推送
最简单的方式 - 无需配置App ID和Secret
"""

import json
import requests
from feishu_sync import FeishuKOLManager
from datetime import datetime


def send_to_feishu_webhook(webhook_url, message_content):
    """
    发送消息到飞书群机器人

    参数：
    - webhook_url: 飞书群机器人的Webhook地址
    - message_content: 消息内容（文本或卡片）
    """
    headers = {'Content-Type': 'application/json'}

    # 构建消息
    data = {
        "msg_type": "text",
        "content": {
            "text": message_content
        }
    }

    try:
        response = requests.post(webhook_url, headers=headers, data=json.dumps(data))
        result = response.json()

        if result.get('code') == 0:
            print("✅ 消息发送成功！")
            return True
        else:
            print(f"❌ 消息发送失败：{result}")
            return False

    except Exception as e:
        print(f"❌ 发送出错：{e}")
        return False


def generate_webhook_message(report):
    """生成Webhook消息内容"""
    stats = report['stats']
    todo = report['todo_contact']
    followup = report['need_followup']

    message = f"""📅 KOL建联日报 - {report['date']}

━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 进度统计

• 总达人：{stats['total']}人
• 已建联：{stats['contacted']}人（{stats['contact_rate']}%）
• 已回复：{stats['replied']}人
• 已报价：{stats['quoted']}人

━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 今日优先建联

"""

    if len(todo) > 0:
        for i, item in enumerate(todo[:3], 1):
            message += f"{i}. {item['priority']} {item['name']}\n"
            message += f"    粉丝：{item['fans']:,} | 播放：{item['avg_play']:,}\n"
            message += f"    预估：¥{item['price']:,} | {item['script']}\n\n"
    else:
        message += "✅ 暂无待建联\n\n"

    if len(followup) > 0:
        message += "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        message += f"🔔 需要跟进（{len(followup)}人）\n\n"
        for item in followup[:5]:
            message += f"• {item['name']} - 已建联{item['days']}天\n"
            message += f"  {item['action']}\n\n"

    progress = report['weekly_progress']
    message += "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    message += f"📈 本周目标\n\n"
    message += f"• 目标建联：{progress['weekly_target']}人\n"
    message += f"• 当前进度：{progress['contacted']}/{progress['total']}\n\n"
    message += f"💡 建议今天建联 1-2 个优先级最高的达人"

    return message


def main():
    """主函数"""
    import os

    print("="*80)
    print(f"📤 飞书Webhook推送 - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("="*80)

    # 检查环境变量中的Webhook URL
    webhook_url = os.getenv('FEISHU_WEBHOOK_URL')

    if not webhook_url:
        print("\n⚠️  未配置Webhook URL")
        print("\n💡 请在 CC-Switch 中配置环境变量：FEISHU_WEBHOOK_URL")
        print("\n配置步骤：")
        print("1. 打开 CC-Switch，在对应配置的 env 中添加 FEISHU_WEBHOOK_URL")
        print("2. 值为飞书群机器人 Webhook 地址（在飞书群聊 → 群机器人 → 自定义机器人 中获取）")
        print("3. 若由定时任务执行，需在 launchd plist 的 EnvironmentVariables 中同样配置该变量")
        print("\n" + "="*80)
        return False

    # 生成报告
    try:
        manager = FeishuKOLManager()
        report = manager.generate_daily_report()

        # 生成消息
        message = generate_webhook_message(report)

        print("\n📝 消息内容：")
        print("-"*80)
        print(message)
        print("-"*80)

        # 发送到飞书
        print("\n📤 发送到飞书...")
        success = send_to_feishu_webhook(webhook_url, message)

        if success:
            print("\n🎉 日报已成功发送到飞书群！")
        else:
            print("\n❌ 发送失败，请检查Webhook URL是否正确")

        return success

    except Exception as e:
        print(f"❌ 错误：{e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    # 环境变量由 CC-Switch 统一管理，此处仅依赖 os.getenv，不再加载 .env
    main()
