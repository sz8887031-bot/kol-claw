#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
美妆护肤达人分析脚本
从MediaCrawler搜索结果中分析达人数据，去重并分类到优质/备选达人表
"""

import json
import csv
import os
from typing import Dict, List, Set
from datetime import datetime

# 文件路径
SEARCH_RESULT = "<MEDIACRAWLER_DIR>/discovered_creators.json"
TRACKING_TABLE = "<PROJECT_DIR>/data/达人跟进表.csv"
QUALITY_TABLE = "<PROJECT_DIR>/data/优质达人.csv"
BACKUP_TABLE = "<PROJECT_DIR>/data/备选达人.csv"

def load_existing_creators() -> Set[str]:
    """加载已存在的达人名称（用于去重）"""
    existing = set()

    for file_path in [TRACKING_TABLE, QUALITY_TABLE, BACKUP_TABLE]:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        # 从跟进表获取"达人昵称"，从优质/备选表获取"达人名称"
                        name = row.get('达人昵称') or row.get('达人名称', '')
                        if name:
                            existing.add(name.strip())
            except Exception as e:
                print(f"读取 {file_path} 时出错: {e}")

    print(f"已加载 {len(existing)} 个已存在的达人")
    return existing

def analyze_creator(creator: Dict) -> Dict:
    """分析单个达人数据"""
    name = creator.get('creator_name', '未知')
    fans = creator.get('follower_count', 0)

    # 获取视频点赞数据
    videos = creator.get('recent_videos', [])
    if not videos or len(videos) < 5:
        return None

    # 提取最近5条视频的点赞数（从最新到最早）
    likes = []
    for video in videos[:5]:
        like_count = video.get('like_count', 0)
        likes.append(like_count)

    if len(likes) < 5:
        return None

    # 计算平均点赞和粉赞比
    avg_likes = sum(likes) / len(likes)
    fan_like_ratio = (avg_likes / fans * 100) if fans > 0 else 0

    # 判断趋势
    if likes[0] > likes[-1] * 1.2:
        trend = "上升"
    elif likes[0] < likes[-1] * 0.8:
        trend = "下降"
    else:
        trend = "波动"

    # 投放评估
    if fan_like_ratio > 5 and avg_likes > 1000:
        evaluation = f"优质-粉赞比{fan_like_ratio:.1f}%-推荐投放"
    elif fan_like_ratio > 2:
        evaluation = f"良好-粉赞比{fan_like_ratio:.1f}%-可考虑"
    elif fan_like_ratio > 1:
        evaluation = f"一般-粉赞比{fan_like_ratio:.1f}%-需谨慎"
    else:
        evaluation = f"差-粉赞比{fan_like_ratio:.1f}%-不建议投放"

    # 内容定位
    content_type = "美妆护肤"

    # 主页链接
    homepage = creator.get('profile_url', '')

    return {
        '达人名称': name,
        '粉丝数': fans,
        '点赞1(最新)': likes[0],
        '点赞2': likes[1],
        '点赞3': likes[2],
        '点赞4': likes[3],
        '点赞5(最早)': likes[4],
        '平均点赞': int(avg_likes),
        '粉赞比(%)': round(fan_like_ratio, 2),
        '趋势': trend,
        '内容定位': content_type,
        '主页链接': homepage,
        '投放评估': evaluation
    }

def classify_creators(creators: List[Dict]) -> tuple:
    """将达人分类为优质和备选"""
    quality = []
    backup = []

    for creator in creators:
        fan_like_ratio = creator['粉赞比(%)']
        avg_likes = creator['平均点赞']

        # 优质达人标准：粉赞比 > 5% 且 平均点赞 > 1000
        if fan_like_ratio > 5 and avg_likes > 1000:
            quality.append(creator)
        else:
            backup.append(creator)

    return quality, backup

def append_to_csv(file_path: str, creators: List[Dict]):
    """追加达人数据到CSV文件"""
    if not creators:
        return

    # 检查文件是否存在
    file_exists = os.path.exists(file_path)

    # CSV字段
    fieldnames = ['达人名称', '粉丝数', '点赞1(最新)', '点赞2', '点赞3', '点赞4', '点赞5(最早)',
                  '平均点赞', '粉赞比(%)', '趋势', '内容定位', '主页链接', '投放评估']

    with open(file_path, 'a', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        # 如果文件不存在，写入表头
        if not file_exists:
            writer.writeheader()

        # 写入数据
        for creator in creators:
            writer.writerow(creator)

def main():
    print("=" * 80)
    print("美妆护肤达人分析")
    print("=" * 80)

    # 1. 加载搜索结果
    print(f"\n1. 加载搜索结果: {SEARCH_RESULT}")
    with open(SEARCH_RESULT, 'r', encoding='utf-8') as f:
        data = json.load(f)

    creators_data = data.get('creators', [])
    print(f"   共搜索到 {len(creators_data)} 个达人")

    # 2. 加载已存在的达人（去重）
    print(f"\n2. 加载已存在的达人")
    existing_creators = load_existing_creators()

    # 3. 分析达人数据
    print(f"\n3. 分析达人数据")
    analyzed_creators = []
    skipped_count = 0

    for creator in creators_data:
        name = creator.get('nickname', '未知')

        # 去重检查
        if name in existing_creators:
            skipped_count += 1
            continue

        # 分析达人
        result = analyze_creator(creator)
        if result:
            analyzed_creators.append(result)

    print(f"   分析完成: {len(analyzed_creators)} 个新达人")
    print(f"   跳过重复: {skipped_count} 个")

    # 4. 分类达人
    print(f"\n4. 分类达人")
    quality_creators, backup_creators = classify_creators(analyzed_creators)
    print(f"   优质达人: {len(quality_creators)} 个")
    print(f"   备选达人: {len(backup_creators)} 个")

    # 5. 追加到CSV文件
    print(f"\n5. 追加到CSV文件")
    append_to_csv(QUALITY_TABLE, quality_creators)
    print(f"   已追加 {len(quality_creators)} 个优质达人到: {QUALITY_TABLE}")

    append_to_csv(BACKUP_TABLE, backup_creators)
    print(f"   已追加 {len(backup_creators)} 个备选达人到: {BACKUP_TABLE}")

    # 6. 输出摘要
    print("\n" + "=" * 80)
    print("分析摘要")
    print("=" * 80)
    print(f"搜索到达人: {len(creators_data)} 个")
    print(f"去重后新达人: {len(analyzed_creators)} 个")
    print(f"优质达人: {len(quality_creators)} 个（粉赞比>5% 且 平均点赞>1000）")
    print(f"备选达人: {len(backup_creators)} 个")

    # 显示优质达人列表
    if quality_creators:
        print(f"\n优质达人列表（前10个）:")
        for i, creator in enumerate(quality_creators[:10], 1):
            print(f"  {i}. {creator['达人名称']} - 粉丝{creator['粉丝数']:,} - "
                  f"粉赞比{creator['粉赞比(%)']}% - 平均点赞{creator['平均点赞']:,}")

    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
