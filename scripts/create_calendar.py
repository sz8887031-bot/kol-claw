#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建Mac日历日程
功能：从CSV中提取需要跟进的达人，生成.ics日历文件
"""

import pandas as pd
import re
from datetime import datetime, timedelta
from icalendar import Calendar, Event, Alarm
from icalendar import vCalAddress, vText
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / 'data'

def extract_date_from_text(text):
    """从文本中提取日期信息"""
    if not text or pd.isna(text):
        return []

    text = str(text)
    results = []

    # 匹配 "X月X号" 或 "X月X日" 格式
    pattern1 = r'(\d{1,2})\s*月\s*(\d{1,2})\s*[号日]'
    matches = re.findall(pattern1, text)

    for month, day in matches:
        try:
            year = 2026  # 默认2026年
            date_obj = datetime(year, int(month), int(day))

            # 提取该日期相关的行动描述
            action_pattern = rf"{month}\s*月\s*{day}\s*[号日]([^；。，,]+)"
            action_match = re.search(action_pattern, text)
            action = action_match.group(1).strip() if action_match else "联系达人跟进"

            results.append({
                'date': date_obj,
                'action': action
            })
        except ValueError:
            continue

    return results

def create_calendar_events(csv_path=DATA_DIR / '达人跟进表.csv', output_path=DATA_DIR / '达人跟进日程.ics'):
    """创建日历事件"""

    # 读取CSV
    df = pd.read_csv(csv_path, encoding='utf-8-sig')

    # 创建日历对象
    cal = Calendar()
    cal.add('prodid', '-//KOL投放管理系统//达人跟进日程//')
    cal.add('version', '2.0')
    cal.add('X-WR-CALNAME', 'KOL达人跟进')
    cal.add('X-WR-TIMEZONE', 'Asia/Shanghai')

    events_created = []

    print("="*80)
    print("📅 创建Mac日历日程")
    print("="*80)
    print()

    # 遍历每个达人
    for idx, row in df.iterrows():
        kol_name = row['达人昵称']
        fans = int(row['粉丝数']) if pd.notna(row['粉丝数']) else 0

        # 从备注和沟通记录中提取日期
        memo = str(row.get('备注', ''))
        comm = str(row.get('沟通记录', ''))

        dates_in_memo = extract_date_from_text(memo)
        dates_in_comm = extract_date_from_text(comm)

        all_dates = dates_in_memo + dates_in_comm

        # 为每个日期创建事件
        for date_info in all_dates:
            event = Event()

            # 事件标题
            summary = f"📱 联系达人：{kol_name}"
            event.add('summary', summary)

            # 事件描述
            description = f"""达人信息：
• 抖音号：{kol_name}
• 粉丝数：{fans:,}
• 行动：{date_info['action']}

沟通记录：{comm if comm != 'nan' else ''}
备注：{memo if memo != 'nan' else ''}

---
来自：KOL投放管理系统
"""
            event.add('description', description)

            # 事件时间（上午10点，1小时）
            start_time = date_info['date'].replace(hour=10, minute=0)
            end_time = date_info['date'].replace(hour=11, minute=0)

            event.add('dtstart', start_time)
            event.add('dtend', end_time)

            # 提醒：事件开始前1天
            alarm = Alarm()
            alarm.add('action', 'DISPLAY')
            alarm.add('trigger', timedelta(days=-1))  # 提前1天
            alarm.add('description', f'明天记得联系 {kol_name}')
            event.add_component(alarm)

            # 添加位置
            event.add('location', '线上沟通')

            # 添加到日历
            cal.add_component(event)

            events_created.append({
                'kol': kol_name,
                'date': date_info['date'].strftime('%Y-%m-%d'),
                'action': date_info['action']
            })

            print(f"✅ {date_info['date'].strftime('%m月%d日')}: {kol_name} - {date_info['action']}")

    # 保存为.ics文件
    with open(output_path, 'wb') as f:
        f.write(cal.to_ical())

    print()
    print("="*80)
    print(f"📁 日历文件已生成：{output_path}")
    print("="*80)
    print()
    print(f"📊 统计信息：")
    print(f"  • 创建事件数：{len(events_created)}")
    print(f"  • 涉及达人：{len(set(e['kol'] for e in events_created))}")
    print()
    print("💡 导入方法：")
    print("  1. 双击 达人跟进日程.ics 文件")
    print("  2. 系统会自动打开日历应用")
    print("  3. 选择要添加到的日历（建议新建一个\"达人跟进\"日历）")
    print("  4. 点击「添加」按钮")
    print()
    print("⏰ 提醒设置：")
    print("  • 每个事件会在前1天提醒你")
    print("  • 时间默认设置为上午10:00-11:00")
    print()

    # 显示详细事件列表
    if events_created:
        print("="*80)
        print("📋 日程明细")
        print("="*80)

        # 按日期排序
        events_created.sort(key=lambda x: x['date'])

        current_date = None
        for event in events_created:
            if event['date'] != current_date:
                current_date = event['date']
                print(f"\n📅 {current_date}:")
            print(f"  • {event['kol']}: {event['action']}")

    return len(events_created)

if __name__ == '__main__':
    try:
        count = create_calendar_events()

        if count == 0:
            print("⚠️  未找到任何需要跟进的日期信息")
            print("💡 请在CSV的「备注」或「沟通记录」字段中添加日期，例如：")
            print("   • 2月26号联系推进报价")
            print("   • 3月5号春招跟进")
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
