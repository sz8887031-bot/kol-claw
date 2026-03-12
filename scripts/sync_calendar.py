#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KOL投放管理系统 - 日历同步脚本
自动检测达人跟进表的状态变化，生成macOS日历事件
"""

import pandas as pd
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / 'data'


class CalendarSync:
    """日历同步管理"""

    def __init__(self, csv_path=DATA_DIR / '达人跟进表.csv'):
        self.csv_path = csv_path
        self.ics_dir = '/tmp'

    def parse_reminder_date(self, text):
        """
        从文本中提取提醒日期
        支持格式：
        - 3月2号通知我联系达人
        - 1月31日跟进
        - 2026-03-02
        """
        if pd.isna(text) or not text:
            return None

        # 格式1: X月X号/日 (支持空格)
        match = re.search(r'(\d{1,2})\s*月\s*(\d{1,2})\s*[号日]', text)
        if match:
            month = int(match.group(1))
            day = int(match.group(2))
            year = datetime.now().year
            # 如果日期已过，则设为明年
            date = datetime(year, month, day)
            if date < datetime.now():
                date = datetime(year + 1, month, day)
            return date

        # 格式2: YYYY-MM-DD
        match = re.search(r'(\d{4})-(\d{1,2})-(\d{1,2})', text)
        if match:
            year = int(match.group(1))
            month = int(match.group(2))
            day = int(match.group(3))
            return datetime(year, month, day)

        return None

    def create_ics_file(self, event_date, summary, description, location='抖音'):
        """创建ICS日历文件"""
        # 生成唯一ID
        event_id = f"kol-{event_date.strftime('%Y%m%d')}-{abs(hash(summary)) % 10000}"

        # UTC时间（北京时间-8小时）
        start_utc = event_date.strftime('%Y%m%dT%H%M%SZ')
        end_time = event_date.replace(hour=event_date.hour+1)
        end_utc = end_time.strftime('%Y%m%dT%H%M%SZ')
        now_utc = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')

        ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//KOL投放管理系统//CN
CALSCALE:GREGORIAN
METHOD:PUBLISH
BEGIN:VEVENT
UID:{event_id}
DTSTAMP:{now_utc}
DTSTART:{start_utc}
DTEND:{end_utc}
SUMMARY:{summary}
DESCRIPTION:{description.replace(chr(10), '\\n')}
LOCATION:{location}
BEGIN:VALARM
TRIGGER:-PT0M
ACTION:DISPLAY
DESCRIPTION:提醒：{summary}
END:VALARM
END:VEVENT
END:VCALENDAR"""

        # 保存文件
        filename = f"kol_schedule_{event_date.strftime('%Y%m%d')}_{abs(hash(summary)) % 1000}.ics"
        filepath = os.path.join(self.ics_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(ics_content)

        return filepath

    def scan_pending_reminders(self):
        """扫描待跟进的达人，生成日历提醒（跳过已创建的）"""
        if not os.path.exists(self.csv_path):
            print(f"❌ 文件不存在: {self.csv_path}")
            return []

        df = pd.read_csv(self.csv_path, encoding='utf-8-sig')

        # 确保有"已创建日历"字段
        if '已创建日历' not in df.columns:
            df['已创建日历'] = ''

        events = []
        skipped_count = 0

        print("="*80)
        print(f"📅 KOL日历同步 - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print("="*80)

        for idx, row in df.iterrows():
            # 跳过空行
            if pd.isna(row['达人昵称']) or not row['达人昵称']:
                continue

            # 检查是否已创建日历
            if pd.notna(row['已创建日历']) and str(row['已创建日历']).strip() != '':
                skipped_count += 1
                continue

            # 检查沟通记录、备注和触达次数中的日期提醒
            reminder_date = None
            reminder_text = None

            # 优先检查备注
            if not pd.isna(row['备注']):
                reminder_date = self.parse_reminder_date(str(row['备注']))
                reminder_text = str(row['备注'])

            # 如果备注没有，检查触达次数
            if not reminder_date and not pd.isna(row['触达次数']):
                reminder_date = self.parse_reminder_date(str(row['触达次数']))
                reminder_text = str(row['触达次数'])

            # 如果还没有，检查沟通记录
            if not reminder_date and not pd.isna(row['沟通记录']):
                reminder_date = self.parse_reminder_date(str(row['沟通记录']))
                reminder_text = str(row['沟通记录'])

            if reminder_date:
                # 构建日历事件
                kol_name = row['达人昵称']
                status = row['建联状态'] if not pd.isna(row['建联状态']) else '未知'
                fans = row['粉丝数'] if not pd.isna(row['粉丝数']) else '未知'
                coop_status = row['确定合作'] if not pd.isna(row['确定合作']) else ''

                summary = f"【KOL投放】跟进达人 - {kol_name}"
                description = f"达人：{kol_name}\n"
                description += f"粉丝：{fans}\n"
                description += f"建联状态：{status}\n"
                if coop_status:
                    description += f"合作状态：{coop_status}\n"
                description += f"提醒内容：{reminder_text}\n\n"
                description += "操作：更新达人跟进表.csv"

                event_info = {
                    'idx': idx,  # 保存索引用于后续标记
                    'date': reminder_date,
                    'kol_name': kol_name,
                    'summary': summary,
                    'description': description
                }
                events.append(event_info)

                print(f"\n📌 发现提醒：{kol_name}")
                print(f"   日期：{reminder_date.strftime('%Y-%m-%d %H:%M')}")
                print(f"   内容：{reminder_text[:50]}...")

        if skipped_count > 0:
            print(f"\n⏭️  跳过 {skipped_count} 个已创建日历的达人")

        return events, df

    def sync_all(self):
        """同步所有待办日历事件"""
        result = self.scan_pending_reminders()

        if not result or len(result) != 2:
            print("\n✅ 未发现需要同步的日历提醒")
            return

        events, df = result

        if not events:
            print("\n✅ 未发现需要同步的日历提醒")
            return

        print("\n" + "="*80)
        print(f"📅 准备创建 {len(events)} 个日历事件")
        print("="*80)

        created_files = []
        for event in events:
            filepath = self.create_ics_file(
                event['date'],
                event['summary'],
                event['description']
            )
            created_files.append(filepath)
            print(f"\n✅ 已创建：{event['summary']}")
            print(f"   文件：{filepath}")
            print(f"   日期：{event['date'].strftime('%Y-%m-%d %H:%M')}")

        # 自动打开日历文件
        print("\n" + "="*80)
        print("📂 正在打开日历文件...")
        print("="*80)

        for filepath in created_files:
            self.open_calendar_file(filepath)

        print(f"\n✅ 已打开 {len(created_files)} 个日历文件")
        print("💡 请在日历应用中选择正确的账户并点击「添加」")

        # 标记已创建日历的达人
        print("\n" + "="*80)
        print("💾 正在标记已创建日历的达人...")
        print("="*80)

        for event in events:
            df.at[event['idx'], '已创建日历'] = datetime.now().strftime('%Y-%m-%d %H:%M')

        # 保存更新后的CSV
        df.to_csv(self.csv_path, index=False, encoding='utf-8-sig')
        print(f"✅ 已标记 {len(events)} 个达人为已创建日历")
        print(f"📁 已更新文件：{self.csv_path}")

        return created_files

    def open_calendar_file(self, filepath):
        """跨平台打开日历文件"""
        try:
            if sys.platform == 'darwin':
                subprocess.run(['open', filepath], check=False)
            elif sys.platform.startswith('linux'):
                opener = shutil.which('xdg-open')
                if opener:
                    subprocess.run([opener, filepath], check=False)
                else:
                    print(f"⚠️  未找到可用的打开命令，请手动打开：{filepath}")
            elif sys.platform.startswith('win'):
                os.startfile(filepath)  # type: ignore[attr-defined]
            else:
                print(f"⚠️  未识别的平台，请手动打开：{filepath}")
        except Exception as e:
            print(f"⚠️  无法自动打开 {filepath}: {e}")


def main():
    """主函数"""
    syncer = CalendarSync()
    syncer.sync_all()


if __name__ == '__main__':
    main()
