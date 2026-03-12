#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
建联进度追踪工具
用于管理达人建联任务和进度
"""

import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / 'data'

CONTACT_STATUS_NOT_CONTACTED = {'未建联', '待接触', '待筛选', '', 'nan'}
CONTACT_STATUS_CONTACTED = {'已建联', '已私信', '待跟进', '已回复', '未报价', '已报价', '确定合作'}
CONTACT_STATUS_REPLIED = {'已回复', '未报价', '已报价', '确定合作'}
CONTACT_STATUS_NEED_FOLLOW = {'待跟进', '无回复'}
COOP_STATUS_CONFIRMED = {'确定合作', '已投放', '已发布'}
COOP_STATUS_REJECTED = {'已拒绝', '无效', '拒绝'}

def show_contact_plan(csv_path=DATA_DIR / '达人跟进表.csv'):
    """显示建联计划和进度"""

    df = pd.read_csv(csv_path, encoding='utf-8-sig')
    df_valid = df[df['达人昵称'].notna() & (df['达人昵称'] != '') & (df['达人昵称'] != '未建联')].copy()

    print("="*90)
    print(f"📞 达人建联执行清单 - {datetime.now().strftime('%Y-%m-%d')}")
    print("="*90)

    # 统计建联状态
    print("\n📊 建联进度统计:\n")
    if '建联状态' in df_valid.columns:
        status_counts = df_valid['建联状态'].value_counts()
        total = len(df_valid)

        status_icons = {
            '未建联': '⏳',
            '待接触': '📝',
            '待筛选': '🔍',
            '已建联': '📤',
            '已私信': '📤',
            '待跟进': '⏰',
            '已回复': '✅',
            '未报价': '💬',
            '已报价': '💰',
            '确定合作': '🤝',
            '无回复': '❌',
            '已拒绝': '❌'
        }

        for status, count in status_counts.items():
            percentage = (count / total) * 100
            icon = status_icons.get(status, '📌')
            print(f"   {icon} {status}: {count}人 ({percentage:.1f}%)")

        contacted = len(df_valid[~df_valid['建联状态'].isin(CONTACT_STATUS_NOT_CONTACTED)])
        contact_rate = (contacted / total) * 100 if total > 0 else 0
        print(f"\n   建联率: {contacted}/{total} ({contact_rate:.1f}%)")

    # 未建联清单（按优先级排序）
    not_contacted = df_valid[df_valid['建联状态'].isin(CONTACT_STATUS_NOT_CONTACTED)].copy()

    if len(not_contacted) > 0:
        print("\n" + "="*90)
        print("🎯 待建联清单（按优先级）")
        print("="*90)

        # 计算优先级分数
        play_cols = ['播放1', '播放2', '播放3', '播放4', '播放5']
        not_contacted['平均播放'] = not_contacted[play_cols].mean(axis=1)
        not_contacted['播粉比'] = not_contacted['平均播放'] / not_contacted['粉丝数']

        # 简单优先级评分
        def calc_priority(row):
            score = 0
            fans = row['粉丝数']
            ratio = row['播粉比']

            # 中等体量+稳定 = 高优先级
            if 5000 <= fans <= 100000 and ratio > 1:
                score += 3
            # 低粉爆款 = 中优先级
            elif fans < 5000 and ratio > 5:
                score += 2
            # 其他
            else:
                score += 1

            return score

        not_contacted['priority_score'] = not_contacted.apply(calc_priority, axis=1)
        not_contacted = not_contacted.sort_values('priority_score', ascending=False)

        print("\n优先级 | 达人 | 粉丝数 | 平均播放 | 预估报价 | 建议话术")
        print("-" * 90)

        for idx, row in not_contacted.iterrows():
            priority = "🔥高" if row['priority_score'] >= 3 else "⭐中" if row['priority_score'] >= 2 else "💡低"
            fans = row['粉丝数']
            avg_play = row['平均播放']
            price = (avg_play * 15) / 1000

            # 推荐话术方案
            if fans >= 50000:
                script = "方案B（正式型）"
            elif fans < 5000:
                script = "方案C（低粉爆款）"
            else:
                script = "方案A（询价型）"

            print(f"{priority:4} | {row['达人昵称']:<8} | {fans:>7,.0f} | {avg_play:>9,.0f} | ¥{price:>6.0f} | {script}")

        print("\n💡 操作指南:")
        print("1. 按优先级从上到下建联")
        print("2. 参考建议话术方案（详见 建联方案.md）")
        print("3. 发送私信后，记得更新表格：建联状态改为'已建联'，填写建联时间")

    # 已建联但未加微信的（需要跟进）
    if '确定合作' in df_valid.columns:
        need_follow = df_valid[df_valid['确定合作'].isin(CONTACT_STATUS_NEED_FOLLOW)].copy()
    else:
        need_follow = df_valid[df_valid['建联状态'].isin({'已建联', '已私信', '待跟进'})].copy()
    if len(need_follow) > 0:
        print("\n" + "="*90)
        print("📤 已建联待回复（需要跟进）")
        print("="*90)

        for idx, row in need_follow.iterrows():
            contact_date = row.get('建联时间', '')
            days_passed = "未知"

            if pd.notna(contact_date) and contact_date != '':
                try:
                    contact_dt = pd.to_datetime(contact_date)
                    days = (datetime.now() - contact_dt).days
                    days_passed = f"{days}天"

                    if days >= 3:
                        action = "⚠️ 超过3天，标记'无回复'"
                    elif days >= 2:
                        action = "🔔 可以发二次跟进"
                    else:
                        action = "⏳ 继续等待"
                except:
                    action = "📝 请填写正确的建联时间"
            else:
                action = "📝 请填写建联时间"

            print(f"  {row['达人昵称']:<12} | 建联时间: {contact_date} ({days_passed}) | {action}")

    # 已加微信的（资源池）
    if '确定合作' in df_valid.columns:
        wechat_added = df_valid[
            df_valid['建联状态'].isin(CONTACT_STATUS_REPLIED) |
            df_valid['确定合作'].isin(COOP_STATUS_CONFIRMED)
        ].copy()
    else:
        wechat_added = df_valid[df_valid['建联状态'].isin(CONTACT_STATUS_REPLIED)].copy()
    if len(wechat_added) > 0:
        print("\n" + "="*90)
        print("✅ 已建立联系（微信资源池）")
        print("="*90)

        for idx, row in wechat_added.iterrows():
            wechat = row.get('微信联系方式', row.get('微信号', '未填写'))
            price = row.get('报价', '未报价')
            status = row.get('确定合作', row.get('状态', '未知'))

            print(f"  {row['达人昵称']:<12} | 微信: {wechat:<15} | 报价: {price} | 状态: {status}")

        print(f"\n💼 已建联资源：{len(wechat_added)}人")
        print("春招时（2月中旬）提前1-2周联系确认档期")

    # 无回复的（需要决策）
    if '确定合作' in df_valid.columns:
        no_response = df_valid[df_valid['确定合作'].isin(COOP_STATUS_REJECTED) | df_valid['建联状态'].isin({'无回复'})].copy()
    else:
        no_response = df_valid[df_valid['建联状态'] == '无回复'].copy()
    if len(no_response) > 0:
        print("\n" + "="*90)
        print("❌ 无回复达人（暂时放弃）")
        print("="*90)

        for idx, row in no_response.iterrows():
            print(f"  {row['达人昵称']:<12} - 暂时放弃，可在春招前再次尝试")

    # 本周目标
    print("\n" + "="*90)
    print("🎯 本周建联目标")
    print("="*90)

    total = len(df_valid)
    contacted = len(df_valid[~df_valid['建联状态'].isin(CONTACT_STATUS_NOT_CONTACTED)])
    not_contact = total - contacted

    # 建议本周建联数量
    weekly_target = min(3, not_contact)

    print(f"""
当前进度: {contacted}/{total} 已建联
待建联: {not_contact} 人

本周目标: 建联 {weekly_target} 人
推荐建联: {', '.join(not_contacted.head(weekly_target)['达人昵称'].tolist()) if len(not_contacted) > 0 else '无'}

操作步骤:
1. 打开 建联方案.md 查看话术模板
2. 按优先级发送抖音私信
3. 更新达人跟进表.csv:
   - 建联状态 → 已建联
   - 建联时间 → {datetime.now().strftime('%Y-%m-%d')}
4. 明天检查回复情况
""")


if __name__ == '__main__':
    show_contact_plan()
