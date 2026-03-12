#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KOL投放分析工具 - 资源库管理版 v2.1
适用于季节性投放的达人资源库建设（春招/秋招）

v2.1 更新（2026-01-28）：
- 递归去除所有极值（避免多爆款误判）
- 增加"多爆款"识别和加分（爆款潜力价值）
- 修正趋势计算（排除极值避免误判）
- 定价保守，但评分体现爆款价值

v2.0 更新：
- 修正低粉爆款定价逻辑（考虑达人议价能力）
- 低粉达人不按CPM计算，而是按固定预算估算
"""

import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / 'data'

CONTACT_STATUS_NOT_CONTACTED = {'未建联', '待接触', '待筛选', '', 'nan'}
CONTACT_STATUS_NEED_FOLLOW = {'无回复', '待跟进'}
CONTACT_STATUS_REPLIED = {'已回复', '未报价', '已报价', '确定合作'}
COOP_STATUS_CONFIRMED = {'确定合作', '已投放', '已发布'}

def calculate_play_trend(row, play_cols=['播放1', '播放2', '播放3', '播放4', '播放5']):
    """
    计算播放量趋势（从旧到新）

    规则：
    - 播放1 = 最新视频
    - 播放5 = 最旧视频
    - 趋势方向：最新3个 vs 最旧2个
    - v2.1：排除极值避免误判趋势

    返回：
    - trend: 'rising'(上升), 'stable'(稳定), 'declining'(下降)
    - trend_score: 趋势评分 (+2/0/-1)
    - trend_ratio: 趋势比率（新/旧）
    """
    play_data = []
    for col in play_cols:
        if col in row and pd.notna(row[col]) and row[col] != '':
            try:
                play_data.append(float(row[col]))
            except:
                pass

    # 数据不足，无法判断趋势
    if len(play_data) < 3:
        return 'unknown', 0, 1.0, '数据不足'

    # 检测并排除极值（最大值是第二大值的3倍以上）
    sorted_data = sorted(play_data)
    if len(sorted_data) >= 3 and sorted_data[-1] > sorted_data[-2] * 3:
        # 去掉极值
        play_data_clean = [x for x in play_data if x != sorted_data[-1]]
    else:
        play_data_clean = play_data

    # 播放1-3为最新，播放4-5为较旧（如果有的话）
    if len(play_data_clean) >= 4:
        recent = play_data_clean[:3]  # 最新3个
        older = play_data_clean[3:]   # 较旧的
    elif len(play_data_clean) >= 3:
        recent = play_data_clean[:2]  # 最新2个
        older = [play_data_clean[2]]  # 最旧1个
    else:
        # 去掉极值后数据不足
        return 'unknown', 0, 1.0, '数据不足(极值)'

    recent_avg = np.mean(recent)
    older_avg = np.mean(older)

    # 计算趋势比率
    if older_avg > 0:
        trend_ratio = recent_avg / older_avg
    else:
        trend_ratio = 1.0

    # 判断趋势
    if trend_ratio >= 1.3:
        # 上升30%以上 = 强上升趋势
        trend = 'rising'
        trend_score = 2
        trend_desc = f'↗️强势上升({trend_ratio:.1f}x)'
    elif trend_ratio >= 1.15:
        # 上升15-30% = 温和上升
        trend = 'rising'
        trend_score = 1
        trend_desc = f'↗️温和上升({trend_ratio:.1f}x)'
    elif trend_ratio >= 0.85:
        # 变化<15% = 稳定
        trend = 'stable'
        trend_score = 0
        trend_desc = '→稳定'
    elif trend_ratio >= 0.7:
        # 下降15-30% = 温和下降
        trend = 'declining'
        trend_score = -1
        trend_desc = f'↘️温和下降({trend_ratio:.1f}x)'
    else:
        # 下降30%以上 = 强下降趋势
        trend = 'declining'
        trend_score = -2
        trend_desc = f'↘️强势下降({trend_ratio:.1f}x)'

    return trend, trend_score, trend_ratio, trend_desc


def calculate_expected_price(fans, avg_play_stable, target_cpm=15):
    """
    计算预期报价（考虑达人议价能力）

    规则：
    1. 低粉达人（<5千粉）：按固定预算估算
       - <3千粉：¥300-500
       - 3-5千粉：¥500-800
       原因：小达人议价能力弱，即使播放高也不敢要高价

    2. 中大体量（>5千粉）：按CPM=15计算
       原因：有粉丝基础，有议价能力
    """
    if fans < 3000:
        # 超小达人，预期报价300-500
        price_low = 300
        price_mid = 400
        price_high = 500
        note = "超小达人，议价能力极弱"
    elif fans < 5000:
        # 小达人，预期报价500-800
        price_low = 500
        price_mid = 650
        price_high = 800
        note = "小达人，议价能力弱"
    else:
        # 中大体量，按CPM计算
        price_mid = (avg_play_stable * target_cpm) / 1000
        price_low = (avg_play_stable * 10) / 1000
        price_high = (avg_play_stable * 20) / 1000
        note = f"中大体量，按CPM={target_cpm}计算"

    return price_low, price_mid, price_high, note


def analyze_kol_data(csv_path=DATA_DIR / '达人跟进表.csv', target_cpm=15, mode='resource'):
    """
    分析KOL数据并生成投放建议

    Args:
        csv_path: CSV文件路径
        target_cpm: 目标CPM值（仅用于中大体量达人）
        mode: 分析模式 - 'resource'(资源库建设) 或 'campaign'(投放执行)
    """
    # 读取CSV文件
    df = pd.read_csv(csv_path, encoding='utf-8-sig')

    # 过滤掉空行
    df = df[df['达人昵称'].notna() & (df['达人昵称'] != '') & (df['达人昵称'] != '未建联')].copy()

    # 计算播放量指标（包含去除极值的逻辑）
    play_cols = ['播放1', '播放2', '播放3', '播放4', '播放5']

    def calculate_stable_metrics(row):
        """计算去除极值后的稳定播放量（v2.1：递归去除所有极值，统计爆款数量）"""
        play_data = [row[col] for col in play_cols if pd.notna(row[col])]
        if len(play_data) == 0:
            return None, None, None, False, 0

        # 原始平均值
        avg_all = np.mean(play_data)

        # 中位数
        median_play = np.median(play_data)

        # 递归去除所有极值（如果数据>=3个）
        has_outlier = False
        outlier_count = 0  # 统计爆款数量
        if len(play_data) >= 3:
            play_stable = sorted(play_data)
            # 持续检测并去除极值
            while len(play_stable) >= 3:
                if play_stable[-1] > play_stable[-2] * 3:
                    # 发现极值，去除
                    play_stable = play_stable[:-1]
                    has_outlier = True
                    outlier_count += 1
                else:
                    break

            # 使用去除极值后的平均值
            avg_stable = np.mean(play_stable)
        else:
            avg_stable = avg_all
            has_outlier = False

        return avg_all, avg_stable, median_play, has_outlier, outlier_count

    df['平均播放_含极值'] = df.apply(lambda row: calculate_stable_metrics(row)[0], axis=1)
    df['平均播放_稳定'] = df.apply(lambda row: calculate_stable_metrics(row)[1], axis=1)
    df['中位数播放'] = df.apply(lambda row: calculate_stable_metrics(row)[2], axis=1)
    df['有极值爆款'] = df.apply(lambda row: calculate_stable_metrics(row)[3], axis=1)
    df['爆款数量'] = df.apply(lambda row: calculate_stable_metrics(row)[4], axis=1)

    # 使用稳定播放量计算指标
    df['播粉比'] = df['平均播放_稳定'] / df['粉丝数']

    print("="*90)
    if mode == 'resource':
        print(f"🗂️  KOL 资源库管理 v2.1 - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print("    适用场景：春招/秋招投放准备")
        print("    v2.1：多爆款识别，递归去极值，定价保守评分准确")
    else:
        print(f"🎯 KOL 投放执行分析 v2.1 - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("="*90)

    # 统计建联状态
    print("\n📊 资源库状态统计:\n")
    if '建联状态' in df.columns:
        status_counts = df['建联状态'].value_counts()
        for status, count in status_counts.items():
            print(f"   {status}: {count}人")
    print(f"\n   总计: {len(df)}个达人资源")

    print("\n" + "="*90)
    if mode == 'resource':
        print("📋 达人资源评估（按性价比排序）")
    else:
        print("🎯 投放推荐列表")
    print("="*90)

    recommendations = []

    for idx, row in df.iterrows():
        avg_play_all = row['平均播放_含极值']
        avg_play_stable = row['平均播放_稳定']
        has_outlier = row['有极值爆款']
        outlier_count = row['爆款数量']  # 新增：爆款数量
        fans = row['粉丝数']
        ratio = row['播粉比']

        # 计算播放量趋势
        trend, trend_score, trend_ratio, trend_desc = calculate_play_trend(row)

        # 使用新的定价逻辑
        price_low, price_mid, price_high, price_note = calculate_expected_price(fans, avg_play_stable, target_cpm)

        # 计算实际CPM（用于评估性价比）
        actual_cpm = (price_mid / avg_play_stable) * 1000 if avg_play_stable > 0 else 0

        # 评分系统（资源库模式更注重性价比）
        score = 0
        tags = []
        category = ""
        priority = ""

        # 1. 低粉爆款（粉丝<5000 且 播粉比>5）
        if fans < 5000 and ratio > 5:
            score += 5  # 提高低粉爆款权重（因为性价比高）
            tags.append("🚀低粉爆款")
            category = "低粉爆款"
            priority = "🔥高"

        # 2. 中粉爆款（粉丝5千-3万 且 播粉比>15）- 新增
        elif 5000 <= fans <= 30000 and ratio > 15:
            score += 6  # 最高体量分（超高播粉比+有议价能力）
            tags.append("🚀中粉爆款")
            category = "中粉爆款"
            priority = "🔥高"

        # 3. 稳定中体量（粉丝5千-10万 且 播粉比>1 但<15）
        elif 5000 <= fans <= 100000 and ratio > 1:
            score += 4
            tags.append("⭐稳定账号")
            category = "稳定中体量"
            priority = "⭐高"

        # 4. 大体量（粉丝>10万）
        elif fans > 100000:
            score += 3
            tags.append("📊大体量")
            category = "大体量"
            priority = "⭐中"
        else:
            priority = "💡一般"
            category = "普通账号"

        # 播粉比额外加分
        if ratio >= 3.0:
            score += 1
            if "低粉爆款" not in [t for t in tags]:
                tags.append("数据优质")
        elif ratio >= 1.5:
            score += 1
            tags.append("数据良好")

        # 数据稳定性（修正：使用全部数据避免误判）
        play_data = [row['播放1'], row['播放2'], row['播放3']]
        play_data = [x for x in play_data if pd.notna(x)]
        cv = None
        if len(play_data) >= 2:
            # 使用全部数据计算真实波动性
            std = np.std(play_data)
            mean = np.mean(play_data)
            cv = (std / mean) * 100 if mean > 0 else 0

            if cv < 30:
                score += 2
                tags.append("✓数据稳定")
            elif cv < 50:
                score += 1
                tags.append("○波动适中")
            elif cv >= 80:
                # 高波动标记，但不扣分（爆款型账号）
                tags.append("⚠️波动较大")

        # 极值处理标记和爆款潜力加分（v2.1新增）
        if has_outlier:
            tags.append("⚡有爆款")
            # 多爆款账号额外加分（爆款潜力价值）
            if outlier_count >= 2:
                score += 2
                tags.append("🔥多爆款")

        # 性价比加分（CPM<8为超值）
        if actual_cpm < 8:
            score += 2
            tags.append("💰超值")

        # 趋势评分（新增）
        score += trend_score
        if trend == 'rising':
            if trend_score >= 2:
                tags.append("📈强势上升")
            else:
                tags.append("📈上升")
        elif trend == 'declining':
            if trend_score <= -2:
                tags.append("📉强势下降")
            else:
                tags.append("📉下降")
        # stable不添加标签

        recommendations.append({
            'name': row['达人昵称'],
            'fans': fans,
            'avg_play_all': avg_play_all,
            'avg_play_stable': avg_play_stable,
            'has_outlier': has_outlier,
            'ratio': ratio,
            'trend': trend,
            'trend_score': trend_score,
            'trend_ratio': trend_ratio,
            'trend_desc': trend_desc,
            'price_low': price_low,
            'price_mid': price_mid,
            'price_high': price_high,
            'price_note': price_note,
            'actual_cpm': actual_cpm,
            'score': score,
            'tags': tags,
            'category': category,
            'priority': priority,
            'contact_status': row.get('建联状态', '未知'),
            'cooperation_status': row.get('确定合作', row.get('状态', '')),
            'current_price': row.get('报价', None),
            'cv': cv
        })

    # 按评分排序
    recommendations.sort(key=lambda x: x['score'], reverse=True)

    # 输出推荐列表
    print()
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. 【{rec['name']}】 {rec['priority']} | {' '.join(rec['tags'])} (评分: {rec['score']}/14)")
        print(f"   类型: {rec['category']}")
        print(f"   粉丝: {rec['fans']:,.0f} | 稳定播放: {rec['avg_play_stable']:,.0f} | 播粉比: {rec['ratio']:.2f}")

        # 显示播放趋势
        print(f"   📊 播放趋势: {rec['trend_desc']}")

        # 如果有极值，显示对比
        if rec['has_outlier']:
            print(f"   ⚠️  检测到爆款视频，含爆款平均: {rec['avg_play_all']:,.0f} (已排除计算)")

        # 显示预期报价（区分低粉和中大体量）
        if rec['fans'] < 5000:
            print(f"   💰 预期报价: ¥{rec['price_mid']:.0f} | 合理区间: ¥{rec['price_low']:.0f}-{rec['price_high']:.0f}")
            print(f"       ({rec['price_note']}，实际CPM≈{rec['actual_cpm']:.1f})")
        else:
            print(f"   💰 CPM={target_cpm} 预期报价: ¥{rec['price_mid']:.0f} | 合理区间: ¥{rec['price_low']:.0f}-{rec['price_high']:.0f}")
            print(f"       (基于稳定播放量定价，爆款为额外收益)")

        # 显示当前报价
        if pd.notna(rec['current_price']):
            current_cpm = (rec['current_price'] / rec['avg_play_stable']) * 1000
            print(f"   📝 当前报价: ¥{rec['current_price']:.0f} (CPM={current_cpm:.1f})", end="")
            if current_cpm <= target_cpm:
                print(" ✅ 合理")
            elif current_cpm <= target_cpm * 1.3:
                print(" ⚠️ 略高")
            else:
                print(" ❌ 偏贵")

        # 显示建联状态
        contact_icon = {
            '未建联': '⏳',
            '待接触': '⏳',
            '待筛选': '🔍',
            '已建联': '📤',
            '已私信': '📤',
            '待跟进': '⏰',
            '已回复': '✅',
            '未报价': '💬',
            '已报价': '💰',
            '确定合作': '🤝',
            '无回复': '❌'
        }
        icon = contact_icon.get(rec['contact_status'], '❓')
        coop_status = rec['cooperation_status'] if rec['cooperation_status'] else '未标记'
        print(f"   {icon} 建联状态: {rec['contact_status']} | 合作状态: {coop_status}")

        # 资源库建议
        if mode == 'resource':
            if rec['score'] >= 7:
                print(f"   📌 资源价值: 极高 - 超高性价比且趋势向好，立即建联")
            elif rec['score'] >= 5:
                print(f"   📌 资源价值: 高 - 优先建联并保持联系")
            elif rec['score'] >= 3:
                print(f"   📌 资源价值: 中 - 可以建联备用")
            else:
                print(f"   📌 资源价值: 低 - 观察后再定")
        else:
            # 投放执行建议
            if rec['score'] >= 6:
                print(f"   ✅ 强烈推荐投放（超高性价比）", end="")
            elif rec['score'] >= 5:
                print(f"   ✅ 强烈推荐投放", end="")
            elif rec['score'] >= 3:
                print(f"   ⭐ 推荐投放", end="")
            else:
                print(f"   💡 可尝试投放", end="")

            # 根据建联状态给出行动建议
            if rec['contact_status'] in CONTACT_STATUS_NOT_CONTACTED:
                print(" - 🔔 需要立即建联")
            elif rec['contact_status'] in {'已建联', '已私信'}:
                print(" - 📌 等待回复中")
            elif rec['contact_status'] in CONTACT_STATUS_NEED_FOLLOW or rec['cooperation_status'] in CONTACT_STATUS_NEED_FOLLOW:
                print(" - 🔄 需要二次跟进")
            else:
                print()

        print()

    # 生成待办事项
    print("="*90)
    if mode == 'resource':
        print("📋 资源库建设任务")
    else:
        print("📋 投放执行清单")
    print("="*90)
    print()

    # 需要建联的高优先级达人
    need_contact = [r for r in recommendations if r['contact_status'] in CONTACT_STATUS_NOT_CONTACTED and r['score'] >= 5]
    if need_contact:
        print("🔔 优先建联的达人:")
        for rec in need_contact:
            cpm_note = f"(实际CPM≈{rec['actual_cpm']:.1f})" if rec['fans'] < 5000 else ""
            print(f"   • {rec['name']} ({rec['category']}) - 预估¥{rec['price_mid']:.0f} {cpm_note}")

    # 需要二次跟进的达人
    need_follow = [
        r for r in recommendations
        if r['contact_status'] in CONTACT_STATUS_NEED_FOLLOW or r['cooperation_status'] in CONTACT_STATUS_NEED_FOLLOW
    ]
    if need_follow:
        print("\n🔄 需要二次跟进的达人:")
        for rec in need_follow:
            print(f"   • {rec['name']} - 换个时间或话术再次联系")

    # 已建联待激活的达人（资源库模式）
    if mode == 'resource':
        contacted = [r for r in recommendations if r['contact_status'] not in CONTACT_STATUS_NOT_CONTACTED]
        if contacted:
            print(f"\n✅ 已建联资源: {len(contacted)}人")
            print("   春招/秋招时可快速激活投放")

    # 快速报价表
    print("\n" + "="*90)
    print(f"💰 快速报价表 (中大体量按CPM={target_cpm}, 低粉按固定预算)")
    print("="*90)
    print()
    print(f"{'达人':<12} {'类型':<12} {'粉丝':<10} {'稳定播放':<12} {'预期报价':<12} {'建联状态':<10}")
    print("-" * 90)

    for rec in recommendations:
        contact_icon = {'未建联': '⏳', '已建联': '📤', '已回复': '✅', '无回复': '❌'}
        icon = contact_icon.get(rec['contact_status'], '❓')
        outlier_mark = " ⚡" if rec['has_outlier'] else "  "
        value_mark = " 💰" if rec['actual_cpm'] < 8 else "  "
        print(f"{rec['name']:<12} {rec['category'] if rec['category'] else '普通':<12} "
              f"{rec['fans']:>8,.0f}  {rec['avg_play_stable']:>10,.0f}{outlier_mark} "
              f"¥{rec['price_mid']:>8.0f}{value_mark} {icon}{rec['contact_status']:<10}")

    print("\n说明:")
    print("• 定价原则：按稳定播放（递归去除所有极值）* CPM计算")
    print("• 中大体量（>5千粉）: 报价按CPM=15计算")
    print("• 低粉爆款（<5千粉）: 报价按固定预算估算（小达人议价能力弱）")
    print("• ⚡标记: 有爆款视频（视为额外收益，不计入定价）")
    print("• 🔥标记: 多爆款账号（2个以上极值，爆款潜力高，可接受溢价）")
    print("• 💰标记: 超值资源（实际CPM<8）")
    print("• 📈/📉标记: 播放趋势（上升=平台推流红利，下降=需谨慎）")
    print("• 评分系统: 最高14分（体量6分+稳定2分+性价比2分+趋势±2分+多爆款2分）")
    print("• 适用于春招/秋招季节性投放")


if __name__ == '__main__':
    import sys

    # 支持命令行参数
    target_cpm = 15
    mode = 'resource'  # 默认资源库模式

    if len(sys.argv) > 1:
        try:
            target_cpm = float(sys.argv[1])
        except:
            if sys.argv[1] in ['resource', 'campaign']:
                mode = sys.argv[1]

    if len(sys.argv) > 2:
        if sys.argv[2] in ['resource', 'campaign']:
            mode = sys.argv[2]

    print(f"\n💡 当前模式: {'资源库建设' if mode == 'resource' else '投放执行'}")
    print(f"💡 目标CPM: {target_cpm} (仅用于中大体量达人)\n")

    analyze_kol_data(target_cpm=target_cpm, mode=mode)
