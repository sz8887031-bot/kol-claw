#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日建联任务生成器 v3.0
功能：
1. 生成今日待打招呼清单（50个优先级最高的）
2. 生成今日待跟进清单（已私信超48小时无回复）
3. 生成待深入沟通清单（已回复但未报价）
4. 自动更新状态和时间
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / 'data'

# 建联状态定义（以当前CSV为准）
STATUS_MAP = {
    '未建联': 0,
    '已建联': 1,
    '未报价': 2,
    '待跟进': 3,
    '确定合作': 4,
    '已拒绝': 5,
    # 兼容旧数据
    '待筛选': 0,
    '待接触': 0,
    '已私信': 1,
    '已回复': 2,
    '已报价': 3,
    '无效': 5,
    '拒绝': 5,
    'nan': 0,
}

def load_data(csv_path=DATA_DIR / '达人跟进表.csv'):
    """加载数据"""
    df = pd.read_csv(csv_path, encoding='utf-8-sig')

    # 添加缺失列
    if '触达次数' not in df.columns:
        df['触达次数'] = 0
    if '确定合作' not in df.columns:
        df['确定合作'] = ''

    # 处理空值
    df['建联状态'] = df['建联状态'].fillna('未建联')
    df['触达次数'] = df['触达次数'].fillna(0)
    df['确定合作'] = df['确定合作'].fillna('')

    # 兼容旧/新状态到当前口径
    df['建联状态'] = df['建联状态'].replace({
        '待筛选': '未建联',
        '待接触': '未建联',
        '已私信': '已建联',
        '待跟进': '已建联',
        '已回复': '未报价',
        '已报价': '已建联',
        '确定合作': '已建联',
        '无回复': '已建联'
    })

    return df

def calculate_priority_score(row):
    """
    计算达人优先级（使用analyze_kol.py的逻辑）
    简化版：播粉比 + 趋势
    """
    try:
        fans = row['粉丝数']
        play_data = []
        for col in ['播放1', '播放2', '播放3', '播放4', '播放5']:
            if pd.notna(row.get(col)):
                play_data.append(float(row[col]))

        if len(play_data) == 0:
            return 0

        # 去除极值
        play_sorted = sorted(play_data)
        while len(play_sorted) >= 3 and play_sorted[-1] > play_sorted[-2] * 3:
            play_sorted = play_sorted[:-1]

        avg_play = np.mean(play_sorted)
        ratio = avg_play / fans if fans > 0 else 0

        # 优先级评分
        score = 0

        # 播粉比加分
        if ratio > 15:
            score += 10
        elif ratio > 5:
            score += 8
        elif ratio > 3:
            score += 6
        elif ratio > 1:
            score += 4

        # 粉丝量加分（小达人议价能力弱，优先）
        if fans < 5000:
            score += 3
        elif fans < 30000:
            score += 2

        return score
    except:
        return 0

def generate_daily_tasks(csv_path=DATA_DIR / '达人跟进表.csv', contact_limit=50):
    """生成每日任务清单"""
    df = load_data(csv_path)
    today = datetime.now().strftime('%Y-%m-%d')

    print("="*80)
    print(f"📋 每日建联任务清单 - {datetime.now().strftime('%Y年%m月%d日 %H:%M')}")
    print("="*80)

    # 统计概览
    print("\n📊 资源库状态概览:\n")
    status_counts = df['建联状态'].value_counts()
    for status, count in status_counts.items():
        emoji = {'未建联': '📝', '已建联': '📤', '未报价': '💬', '确定合作': '🤝', '已拒绝': '❌'}
        print(f"   {emoji.get(status, '📌')} {status}: {count}人")
    print(f"\n   总计: {len(df)}个达人资源")

    # 任务1: 今日待打招呼（从"待接触"中选优先级最高的50个）
    print("\n" + "="*80)
    print(f"📤 任务1: 今日待打招呼清单 (目标{contact_limit}个)")
    print("="*80)
    print()

    # 筛选真正未行动的达人：建联状态为"未建联"且沟通记录为空或只有"未报价"
    def is_not_contacted(row):
        comm_record = str(row.get('沟通记录', '')).strip()
        contact_status = str(row.get('建联状态', '')).strip()
        coop_status = str(row.get('确定合作', '')).strip()

        # 只有未建联才算待打招呼
        if contact_status != '未建联':
            return False
        if coop_status in ['确定合作', '已拒绝']:
            return False

        # 如果沟通记录有实质内容（不是空、不是nan、不只是"未报价"），说明已经行动了
        if comm_record and comm_record not in ['', 'nan', '未报价']:
            return False

        # 如果状态包含明确的行动词（已私信、已发邮件、已加微信等），说明已经行动了
        action_keywords = ['已私信', '已发', '已加', '等待', '跟进', '暂时不', '最近']
        if any(keyword in comm_record for keyword in action_keywords):
            return False

        return True

    to_contact = df[df.apply(is_not_contacted, axis=1)].copy()

    if len(to_contact) > 0:
        # 计算优先级
        to_contact['优先级分数'] = to_contact.apply(calculate_priority_score, axis=1)
        to_contact = to_contact.sort_values('优先级分数', ascending=False).head(contact_limit)

        print(f"今日建议打招呼 {min(len(to_contact), contact_limit)} 个达人：\n")

        for i, (idx, row) in enumerate(to_contact.iterrows(), 1):
            fans = row['粉丝数']
            name = row['达人昵称']
            score = row.get('优先级分数', 0)
            print(f"{i:2d}. {name:<15} | 粉丝: {fans:>7,.0f} | 优先级: {score:.1f}")

        print(f"\n💡 操作提示：")
        print(f"   1. 批量复制达人名单")
        print(f"   2. 使用话术模板发送私信/邮件")
        print(f"   3. 完成后运行：python3 update_status.py --contact <达人名单>")
    else:
        print("✅ 待接触池已空，建议添加新达人资源")

    # 任务2: 今日待跟进（已私信超过48小时未回复）
    print("\n" + "="*80)
    print("⏰ 任务2: 今日待跟进清单 (待跟进/需要二次联系)")
    print("="*80)
    print()

    if '确定合作' in df.columns:
        to_follow = df[df['确定合作'] == '待跟进'].copy()
    else:
        to_follow = df[df['建联状态'] == '已建联'].copy()

    # 检查最后跟进时间
    if '最后跟进时间' in df.columns:
        def should_follow_today(row):
            if pd.isna(row.get('最后跟进时间')):
                return True
            try:
                last_time = pd.to_datetime(row['最后跟进时间'])
                days_ago = (datetime.now() - last_time).days
                return days_ago >= 2  # 2天未跟进
            except:
                return True

        to_follow = to_follow[to_follow.apply(should_follow_today, axis=1)]

    if len(to_follow) > 0:
        print(f"今日需跟进 {len(to_follow)} 个达人：\n")

        for i, (idx, row) in enumerate(to_follow.iterrows(), 1):
            name = row['达人昵称']
            fans = row['粉丝数']
            follow_count = row.get('触达次数', 0)
            last_time = row.get('最后跟进时间', '未知')

            if follow_count >= 3:
                status_note = "❌ 建议标记为无效"
            else:
                status_note = f"第{int(follow_count)+1}次跟进"

            print(f"{i:2d}. {name:<15} | 粉丝: {fans:>7,.0f} | {status_note}")

        print(f"\n💡 操作提示：")
        print(f"   1. 更换话术/时间段再次联系")
        print(f"   2. 跟进3次仍无回复，标记为'无效'")
        print(f"   3. 完成后运行：python3 update_status.py --follow <达人名单>")
    else:
        print("✅ 暂无需跟进的达人")

    # 任务3: 待深入沟通（已回复但未报价）
    print("\n" + "="*80)
    print("💬 任务3: 待深入沟通清单 (已回复待谈价)")
    print("="*80)
    print()

    to_communicate = df[(df['建联状态'] == '未报价') & (df['报价'].isna() | (df['报价'] == ''))].copy()

    if len(to_communicate) > 0:
        print(f"今日需深入沟通 {len(to_communicate)} 个达人：\n")

        for i, (idx, row) in enumerate(to_communicate.iterrows(), 1):
            name = row['达人昵称']
            fans = row['粉丝数']
            reply_time = row.get('最后跟进时间', '未知')
            memo = row.get('沟通记录', '')

            print(f"{i:2d}. {name:<15} | 粉丝: {fans:>7,.0f} | 回复时间: {reply_time}")
            if memo:
                print(f"     备注: {memo[:50]}...")

        print(f"\n💡 操作提示：")
        print(f"   1. 询问报价/合作意向")
        print(f"   2. 获得报价后更新：python3 update_status.py --quote <达人名> <报价>")
    else:
        print("✅ 暂无待沟通的达人")

    # 任务4: 谈判中（已报价）
    print("\n" + "="*80)
    print("💰 任务4: 谈判中清单 (已报价待确认)")
    print("="*80)
    print()

    negotiating = df[
        (df['报价'].notna() & (df['报价'] != '')) &
        (~df['确定合作'].isin(['确定合作', '已拒绝']))
    ].copy()

    if len(negotiating) > 0:
        print(f"正在谈判 {len(negotiating)} 个达人：\n")

        for i, (idx, row) in enumerate(negotiating.iterrows(), 1):
            name = row['达人昵称']
            fans = row['粉丝数']
            quote = row.get('报价', '未知')
            memo = row.get('沟通记录', '')

            print(f"{i:2d}. {name:<15} | 粉丝: {fans:>7,.0f} | 报价: ¥{quote}")
            if memo:
                print(f"     备注: {memo[:50]}...")
    else:
        print("✅ 暂无谈判中的达人")

    # 今日目标总结
    print("\n" + "="*80)
    print("🎯 今日工作目标")
    print("="*80)
    print()
    print(f"✓ 新增打招呼: {min(len(to_contact), contact_limit)}个")
    print(f"✓ 跟进回复: {len(to_follow)}个")
    print(f"✓ 深入沟通: {len(to_communicate)}个")
    print(f"✓ 推进合作: {len(negotiating)}个")
    total_tasks = min(len(to_contact), contact_limit) + len(to_follow) + len(to_communicate) + len(negotiating)
    print(f"\n📊 今日任务总量: {total_tasks}个达人")

    # 转化漏斗统计
    print("\n" + "="*80)
    print("📈 建联转化漏斗")
    print("="*80)
    print()

    total = len(df)
    contacted = len(df[df['建联状态'] != '未建联'])
    replied = len(df[df['建联状态'] == '未报价'])
    quoted = len(df[df['报价'].notna() & (df['报价'] != '')])
    confirmed = len(df[df['确定合作'] == '确定合作'])

    print(f"达人总数:     {total:3d}人")
    print(f"已打招呼:     {contacted:3d}人  ({contacted/total*100:.1f}%)")
    print(f"已回复:       {replied:3d}人  ({replied/contacted*100:.1f}% 回复率)" if contacted > 0 else "已回复:       0人")
    print(f"已报价:       {quoted:3d}人  ({quoted/replied*100:.1f}% 报价率)" if replied > 0 else "已报价:       0人")
    print(f"确定合作:     {confirmed:3d}人  ({confirmed/quoted*100:.1f}% 成单率)" if quoted > 0 else "确定合作:     0人")


if __name__ == '__main__':
    import sys

    contact_limit = 50
    if len(sys.argv) > 1:
        try:
            contact_limit = int(sys.argv[1])
        except:
            pass

    generate_daily_tasks(contact_limit=contact_limit)
