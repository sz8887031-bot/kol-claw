#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
建联话术生成器
根据达人信息自动生成个性化建联话术
"""

import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / 'data'

def generate_script(kol_name, csv_path=DATA_DIR / '达人跟进表.csv'):
    """为指定达人生成建联话术"""

    df = pd.read_csv(csv_path, encoding='utf-8-sig')
    kol = df[df['达人昵称'] == kol_name]

    if len(kol) == 0:
        print(f"❌ 未找到达人：{kol_name}")
        return

    kol = kol.iloc[0]
    fans = kol['粉丝数']
    play_cols = ['播放1', '播放2', '播放3', '播放4', '播放5']
    avg_play = kol[play_cols].mean()
    price = (avg_play * 15) / 1000

    print("="*80)
    print(f"📝 【{kol_name}】建联话术生成")
    print("="*80)

    print(f"\n达人信息:")
    print(f"  粉丝数: {fans:,.0f}")
    print(f"  平均播放: {avg_play:,.0f}")
    print(f"  预估报价: ¥{price:.0f}")

    print("\n" + "="*80)

    # 根据粉丝量选择话术
    if fans >= 50000:
        print("推荐话术：方案B（正式型）")
        print("="*80)
        print(f"""
抖音私信话术：

您好，我是某某科技的商务负责人。

我们是一家AI求职简历工具，主要在春招/秋招投放，目前正在储备优质达人资源。

看到您的账号数据稳定，{fans/10000:.1f}万粉丝，平均播放{avg_play/10000:.1f}万，内容质量很不错。

想了解：
1. 您这边的商务合作报价
2. 明年春招时（2-4月）档期是否方便

如果感兴趣，可以加我微信详聊：[你的微信号]
期待合作！
""")

    elif fans < 5000:
        print("推荐话术：方案C（低粉爆款专用）")
        print("="*80)
        max_play = max([kol[col] for col in play_cols if pd.notna(kol[col])])
        print(f"""
抖音私信话术：

您好！看到您有视频播放量破{max_play/10000:.1f}万，数据很不错👍

我们是做AI求职工具的，主要在春招/秋招投放，想和您聊聊合作的可能性。

您这边商务报价大概是多少呢？我们预算在{price:.0f}元左右，主要是看内容适配性和性价比。

方便加个微信详聊吗？微信：[你的微信号]
""")

    else:
        print("推荐话术：方案A（询价型）")
        print("="*80)
        print(f"""
抖音私信话术：

您好，我是小李，负责AI求职工具的达人合作。

看到您的账号数据不错，平均播放{avg_play/10000:.1f}万，内容质量也很好，想了解一下商务合作报价？

我们是做AI求职简历工具的，主要在春招/秋招投放，现在想提前储备一些优质达人。

方便加个微信详聊吗？微信：[你的微信号]
""")

    print("="*80)
    print("加上微信后的话术：")
    print("="*80)
    print(f"""
您好，我是抖音上联系您的小李

简单自我介绍下：
- 我们产品：AI求职简历工具（大学生/求职者用）
- 投放时间：主要春招（2-4月）、秋招（9-11月）
- 现在阶段：提前储备达人资源

看到您的账号：
- 粉丝{fans/10000:.1f}万，平均播放{avg_play/10000:.1f}万
- 数据稳定，内容质量不错

我们的合作模式：
- 内容植入/口播/剧情
- 报价您这边报个价，我们预估{price:.0f}元左右
- 春招时如果合作，会提前1-2周确认

您这边：
1. 商务报价是多少？
2. 春招档期方便吗？
3. 有没有合作过求职类/工具类产品？
""")

    print("="*80)
    print("💡 操作提示")
    print("="*80)
    print(f"""
1. 复制上面的话术，替换[你的微信号]
2. 根据达人特点微调内容（不要完全照搬）
3. 发送后更新表格：
   - 建联状态 → 已建联
   - 建联时间 → {pd.Timestamp.now().strftime('%Y-%m-%d')}
4. 24-48小时后检查回复
""")


def batch_generate(csv_path=DATA_DIR / '达人跟进表.csv', top_n=3):
    """批量生成前N个优先建联的达人话术"""

    df = pd.read_csv(csv_path, encoding='utf-8-sig')
    df_valid = df[df['达人昵称'].notna() & (df['达人昵称'] != '') & (df['达人昵称'] != '未建联')].copy()

    # 只显示未建联的
    not_contacted = df_valid[df_valid['建联状态'] == '未建联'].copy()

    if len(not_contacted) == 0:
        print("✅ 所有达人都已建联！")
        return

    # 计算优先级
    play_cols = ['播放1', '播放2', '播放3', '播放4', '播放5']
    not_contacted['平均播放'] = not_contacted[play_cols].mean(axis=1)
    not_contacted['播粉比'] = not_contacted['平均播放'] / not_contacted['粉丝数']

    def calc_priority(row):
        score = 0
        fans = row['粉丝数']
        ratio = row['播粉比']
        if 5000 <= fans <= 100000 and ratio > 1:
            score += 3
        elif fans < 5000 and ratio > 5:
            score += 2
        else:
            score += 1
        return score

    not_contacted['priority_score'] = not_contacted.apply(calc_priority, axis=1)
    not_contacted = not_contacted.sort_values('priority_score', ascending=False)

    # 生成前N个
    top_kols = not_contacted.head(top_n)

    print("="*80)
    print(f"📝 批量生成建联话术（前{top_n}个优先级）")
    print("="*80)

    for idx, row in top_kols.iterrows():
        print("\n")
        generate_script(row['达人昵称'], csv_path)
        print("\n" + "="*80 + "\n")


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        # 生成单个达人话术
        kol_name = sys.argv[1]
        generate_script(kol_name)
    else:
        # 批量生成前3个
        batch_generate(top_n=3)
