#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
达人分级和触达策略推荐系统
功能：
1. 自动给达人分级（S/A/B/C）
2. 推荐下一步触达渠道
3. 生成每日触达清单
4. 更新触达记录
"""

import pandas as pd
from datetime import datetime, timedelta
import sys
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / 'data'

# 触达渠道配置
CONTACT_CHANNELS = {
    'S': [  # S级达人：7轮触达
        {'round': 1, 'channel': '抖音私信(账号A)', 'interval_days': 3, 'script': '标准话术'},
        {'round': 2, 'channel': '抖音私信(账号A)', 'interval_days': 3, 'script': '价值话术'},
        {'round': 3, 'channel': '抖音私信(账号B)', 'interval_days': 3, 'script': '个性化话术'},
        {'round': 4, 'channel': '星图派单', 'interval_days': 3, 'script': '低价试探'},
        {'round': 5, 'channel': '微信添加', 'interval_days': 3, 'script': '主动添加'},
        {'round': 6, 'channel': '邮件联系', 'interval_days': 3, 'script': '邮件话术'},
        {'round': 7, 'channel': '其他平台', 'interval_days': 0, 'script': '多平台搜索'},
    ],
    'A': [  # A级达人：5轮触达
        {'round': 1, 'channel': '抖音私信(账号A)', 'interval_days': 3, 'script': '标准话术'},
        {'round': 2, 'channel': '抖音私信(账号A)', 'interval_days': 3, 'script': '价值话术'},
        {'round': 3, 'channel': '抖音私信(账号B)', 'interval_days': 3, 'script': '个性化话术'},
        {'round': 4, 'channel': '星图派单', 'interval_days': 3, 'script': '低价试探'},
        {'round': 5, 'channel': '微信添加', 'interval_days': 0, 'script': '主动添加'},
    ],
    'B': [  # B级达人：3轮触达
        {'round': 1, 'channel': '抖音私信(账号A)', 'interval_days': 2, 'script': '标准话术'},
        {'round': 2, 'channel': '抖音私信(账号A)', 'interval_days': 2, 'script': '价值话术'},
        {'round': 3, 'channel': '抖音私信(账号B)', 'interval_days': 0, 'script': '个性化话术'},
    ],
    'C': [  # C级达人：1轮触达
        {'round': 1, 'channel': '抖音私信(账号A)', 'interval_days': 0, 'script': '标准话术'},
    ],
}

def calculate_kol_score(row):
    """计算达人评分（简化版，使用analyze_kol.py的逻辑）"""
    try:
        fans = row['粉丝数']
        play_data = []
        for col in ['播放1', '播放2', '播放3', '播放4', '播放5']:
            if pd.notna(row.get(col)):
                play_data.append(float(row[col]))

        if len(play_data) == 0:
            return 0

        # 简化评分
        import numpy as np
        avg_play = np.mean(play_data)
        ratio = avg_play / fans if fans > 0 else 0

        score = 0
        if ratio > 15:
            score = 10
        elif ratio > 5:
            score = 8
        elif ratio > 3:
            score = 6
        elif ratio > 1:
            score = 4

        return score
    except:
        return 0

def classify_kol(row):
    """达人分级"""
    score = calculate_kol_score(row)

    if score >= 9:
        return 'S'
    elif score >= 7:
        return 'A'
    elif score >= 5:
        return 'B'
    else:
        return 'C'

def parse_contact_record(record):
    """解析触达记录"""
    if not record or pd.isna(record) or record == '':
        return []

    # 格式：抖音A(1/28-无回复);抖音B(1/31-无回复)
    parts = str(record).split(';')
    contacts = []

    for part in parts:
        if '(' in part and ')' in part:
            channel = part.split('(')[0].strip()
            info = part.split('(')[1].split(')')[0]
            if '-' in info:
                date_str, result = info.split('-', 1)
                contacts.append({
                    'channel': channel,
                    'date': date_str,
                    'result': result
                })

    return contacts

def get_next_contact_strategy(row):
    """获取下一步触达策略"""
    level = row.get('达人级别', classify_kol(row))
    contact_record = parse_contact_record(row.get('触达记录', ''))

    current_round = len(contact_record) + 1
    channels_config = CONTACT_CHANNELS.get(level, CONTACT_CHANNELS['C'])

    if current_round > len(channels_config):
        return {
            'status': 'completed',
            'message': f'已完成{len(channels_config)}轮触达，建议放弃',
            'action': '标记为无效'
        }

    next_config = channels_config[current_round - 1]

    # 计算下次触达时间
    if contact_record:
        last_contact_date = contact_record[-1]['date']
        try:
            last_date = datetime.strptime(f"2026-{last_contact_date}", '%Y-%m/%d')
            next_date = last_date + timedelta(days=next_config['interval_days'])
        except:
            next_date = datetime.now()
    else:
        next_date = datetime.now()

    return {
        'status': 'pending',
        'level': level,
        'round': current_round,
        'channel': next_config['channel'],
        'script': next_config['script'],
        'next_date': next_date.strftime('%Y-%m-%d'),
        'total_rounds': len(channels_config),
        'message': f"第{current_round}/{len(channels_config)}轮触达"
    }

def generate_daily_contact_plan(csv_path=DATA_DIR / '达人跟进表.csv'):
    """生成每日触达清单"""

    df = pd.read_csv(csv_path, encoding='utf-8-sig')

    # 添加达人级别（如果没有）
    if '达人级别' not in df.columns:
        df['达人级别'] = df.apply(classify_kol, axis=1)

    # 添加触达记录（如果没有）
    if '触达记录' not in df.columns:
        df['触达记录'] = ''

    # 添加触达次数（如果没有）
    if '触达次数' not in df.columns:
        df['触达次数'] = 0

    print("="*80)
    print("📋 达人分级和触达策略推荐")
    print("="*80)
    print()

    # 统计分级
    level_counts = df['达人级别'].value_counts()
    print("📊 达人分级统计:")
    print(f"  S级（重点攻坚）: {level_counts.get('S', 0)}人")
    print(f"  A级（积极跟进）: {level_counts.get('A', 0)}人")
    print(f"  B级（常规跟进）: {level_counts.get('B', 0)}人")
    print(f"  C级（观察备用）: {level_counts.get('C', 0)}人")
    print()

    # 筛选未建联的达人
    pending_df = df[df['建联状态'] == '未建联'].copy()

    # 筛选需要触达的达人（已经有沟通记录但未成功建联的）
    need_contact = []

    for idx, row in pending_df.iterrows():
        strategy = get_next_contact_strategy(row)

        if strategy['status'] == 'pending':
            need_contact.append({
                'index': idx,
                'name': row['达人昵称'],
                'level': strategy['level'],
                'round': strategy['round'],
                'total_rounds': strategy['total_rounds'],
                'channel': strategy['channel'],
                'script': strategy['script'],
                'next_date': strategy['next_date'],
                'fans': int(row['粉丝数']) if pd.notna(row['粉丝数']) else 0,
                'comm': row.get('沟通记录', ''),
            })

    # 按级别和日期排序
    level_priority = {'S': 1, 'A': 2, 'B': 3, 'C': 4}
    need_contact.sort(key=lambda x: (level_priority[x['level']], x['next_date']))

    # 显示今日待触达清单
    print("="*80)
    print("📅 今日触达建议")
    print("="*80)
    print()

    today = datetime.now().strftime('%Y-%m-%d')

    # S级达人
    s_level = [k for k in need_contact if k['level'] == 'S' and k['next_date'] <= today]
    if s_level:
        print("🔥 S级达人（优先）:")
        for i, kol in enumerate(s_level, 1):
            print(f"\n{i}. {kol['name']} (粉丝: {kol['fans']:,})")
            print(f"   进度: 第{kol['round']}/{kol['total_rounds']}轮")
            print(f"   渠道: {kol['channel']}")
            print(f"   话术: {kol['script']}")
            if kol['comm']:
                print(f"   记录: {kol['comm'][:40]}...")
        print()

    # A级达人
    a_level = [k for k in need_contact if k['level'] == 'A' and k['next_date'] <= today]
    if a_level:
        print("⭐ A级达人:")
        for i, kol in enumerate(a_level, 1):
            print(f"\n{i}. {kol['name']} (粉丝: {kol['fans']:,})")
            print(f"   进度: 第{kol['round']}/{kol['total_rounds']}轮")
            print(f"   渠道: {kol['channel']}")
            print(f"   话术: {kol['script']}")
        print()

    # B级达人
    b_level = [k for k in need_contact if k['level'] == 'B' and k['next_date'] <= today]
    if b_level:
        print("💼 B级达人:")
        for i, kol in enumerate(b_level, 1):
            print(f"{i}. {kol['name']} - 第{kol['round']}/{kol['total_rounds']}轮 - {kol['channel']}")

    # 未触达清单（新达人）
    never_contact = [k for k in need_contact if k['round'] == 1 and not k['comm']]
    if never_contact:
        print()
        print("="*80)
        print("📨 首次触达清单")
        print("="*80)
        print()

        for level in ['S', 'A', 'B', 'C']:
            level_kols = [k for k in never_contact if k['level'] == level]
            if level_kols:
                emoji = {'S': '🔥', 'A': '⭐', 'B': '💼', 'C': '📌'}
                print(f"\n{emoji[level]} {level}级达人 ({len(level_kols)}人):")
                for kol in level_kols:
                    print(f"  • {kol['name']} (粉丝: {kol['fans']:,})")

    # 保存分级结果
    if '达人级别' not in pd.read_csv(csv_path, encoding='utf-8-sig').columns:
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        print()
        print("✅ 达人级别已更新到CSV")

    print()
    print("="*80)
    print("💡 操作建议")
    print("="*80)
    print()
    print("1. 优先处理S级达人（性价比最高）")
    print("2. 按推荐渠道和话术进行触达")
    print("3. 完成后记录触达结果：")
    print("   python3 contact_strategy.py --update 达人名 渠道 结果")
    print()

    return need_contact

def update_contact_record(kol_name, channel, result, csv_path=DATA_DIR / '达人跟进表.csv'):
    """更新触达记录"""

    df = pd.read_csv(csv_path, encoding='utf-8-sig')

    # 找到达人
    idx = df[df['达人昵称'] == kol_name].index

    if len(idx) == 0:
        print(f"❌ 未找到达人：{kol_name}")
        return

    idx = idx[0]
    today = datetime.now().strftime('%m/%d')

    # 更新触达记录
    current_record = str(df.at[idx, '触达记录']) if pd.notna(df.at[idx, '触达记录']) else ''
    new_entry = f"{channel}({today}-{result})"

    if current_record and current_record != 'nan':
        updated_record = f"{current_record};{new_entry}"
    else:
        updated_record = new_entry

    df.at[idx, '触达记录'] = updated_record

    # 更新触达次数
    df.at[idx, '触达次数'] = len(parse_contact_record(updated_record))

    # 保存
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')

    print(f"✅ 已更新 {kol_name} 的触达记录")
    print(f"   渠道: {channel}")
    print(f"   结果: {result}")
    print(f"   累计触达: {df.at[idx, '触达次数']}次")

    # 推荐下一步
    row = df.loc[idx]
    strategy = get_next_contact_strategy(row)

    if strategy['status'] == 'pending':
        print()
        print(f"💡 下一步建议:")
        print(f"   {strategy['message']}")
        print(f"   渠道: {strategy['channel']}")
        print(f"   话术: {strategy['script']}")
        print(f"   建议时间: {strategy['next_date']}")
    else:
        print()
        print(f"⚠️  {strategy['message']}")

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--update':
        # 更新触达记录
        if len(sys.argv) < 5:
            print("用法: python3 contact_strategy.py --update 达人名 渠道 结果")
            print("示例: python3 contact_strategy.py --update 美香疯 抖音B 无回复")
            sys.exit(1)

        kol_name = sys.argv[2]
        channel = sys.argv[3]
        result = sys.argv[4]

        update_contact_record(kol_name, channel, result)

    else:
        # 生成每日触达清单
        generate_daily_contact_plan()
