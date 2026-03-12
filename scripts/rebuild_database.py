#!/usr/bin/env python3
"""从所有历史JSON重建达人库，然后改为追加模式"""

import json
import csv
from collections import defaultdict
from pathlib import Path
from datetime import datetime

# 路径
JSON_DIR = "<MEDIACRAWLER_DIR>/data/douyin/json"
KOL_DIR = "<PROJECT_DIR>/data"
OUTPUT_PREMIUM = f"{KOL_DIR}/优质达人.csv"
OUTPUT_BACKUP = f"{KOL_DIR}/备选达人.csv"
TRACKING_FILE = f"{KOL_DIR}/达人跟进表.csv"

# 读取达人跟进表中的达人（排除）
tracking_creators = set()
try:
    with open(TRACKING_FILE, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get('达人名称', '').strip()
            if name:
                tracking_creators.add(name)
except FileNotFoundError:
    pass

print(f"📋 达人跟进表中有 {len(tracking_creators)} 个达人（不重复分析）")

# 合并所有历史creator JSON
all_videos = []
all_creators_info = {}

for json_file in sorted(Path(JSON_DIR).glob("creator_contents_*.json")):
    # 跳过备份文件
    if "_group" in json_file.name or "_old" in json_file.name:
        continue
    with open(json_file, 'r') as f:
        data = json.load(f)
    all_videos.extend(data)
    print(f"  📂 {json_file.name}: {len(data)} 条视频")

# 合并所有creator_creators文件（粉丝数）
creator_fans_map = {}
for json_file in sorted(Path(JSON_DIR).glob("creator_creators_*.json")):
    if "_group" in json_file.name or "_old" in json_file.name:
        continue
    with open(json_file, 'r') as f:
        data = json.load(f)
    for creator in data:
        sec_uid = creator.get('user_id')
        fans = creator.get('fans', 0)
        if sec_uid and fans:
            creator_fans_map[sec_uid] = fans
    print(f"  📂 {json_file.name}: {len(data)} 个达人信息")

print(f"\n✅ 总计: {len(all_videos)} 条视频数据")
print(f"✅ 粉丝数据: {len(creator_fans_map)} 个达人")

# 按达人聚合视频（使用sec_uid去重）
creator_videos = defaultdict(list)
creator_info = {}

for video in all_videos:
    sec_uid = video.get('sec_uid')
    if not sec_uid:
        continue
    creator_videos[sec_uid].append(video)
    if sec_uid not in creator_info:
        creator_info[sec_uid] = {
            'user_id': video.get('user_id'),
            'nickname': video.get('nickname', '未知'),
        }

print(f"👤 共发现 {len(creator_info)} 个唯一达人")

# 分析每个达人
results = []
skipped = 0

for sec_uid, info in creator_info.items():
    nickname = info.get('nickname', '未知')
    user_id = info.get('user_id', '')
    videos = creator_videos.get(sec_uid, [])

    # 跳过跟进表中的达人
    if nickname in tracking_creators:
        skipped += 1
        continue

    if len(videos) < 2:
        continue

    # 取最新5条
    videos_sorted = sorted(videos, key=lambda x: str(x.get('create_time', '0')), reverse=True)[:5]
    video_count = len(videos_sorted)

    # 提取点赞数
    likes = []
    plays = []
    for v in videos_sorted:
        like_count = v.get('liked_count', '0')
        if isinstance(like_count, str):
            like_count = int(like_count.replace(',', ''))
        likes.append(like_count)
        plays.append(int(like_count / 0.03))

    avg_likes = sum(likes) / len(likes)
    min_likes = min(likes)

    # 粉丝数
    real_fans = creator_fans_map.get(sec_uid, 0)
    fans = real_fans if real_fans > 0 else int(avg_likes * 20)

    fan_like_ratio = (avg_likes / fans * 100) if fans > 0 else 0
    stability_ratio = min_likes / avg_likes if avg_likes > 0 else 0

    # 趋势
    if len(likes) >= 3:
        recent_avg = sum(likes[:2]) / 2
        old_avg = sum(likes[-2:]) / 2
        if recent_avg > old_avg * 1.2:
            trend = "上升"
        elif recent_avg < old_avg * 0.8:
            trend = "下降"
        else:
            trend = "波动"
    else:
        trend = "样本不足"

    # 评级
    if fan_like_ratio > 5 and avg_likes > 1000:
        if video_count >= 5 and stability_ratio > 0.3:
            grade = "S级"
            evaluation = "优质且稳定，强烈推荐"
        elif video_count < 5:
            grade = "A级"
            evaluation = f"数据优质但样本少（仅{video_count}条），建议观察"
        elif stability_ratio <= 0.3:
            grade = "A级"
            evaluation = f"粉赞比高但不稳定（最低{min_likes}赞），高风险高回报"
        else:
            grade = "A级"
            evaluation = "优质，推荐"
    elif fan_like_ratio > 2:
        grade = "B级"
        evaluation = "良好，可小额测试"
    elif fan_like_ratio > 1:
        grade = "C级"
        evaluation = "一般，需谨慎"
    else:
        grade = "D级"
        evaluation = "差，不建议投放"

    # 风险标签
    risk_tags = []
    if video_count < 5:
        risk_tags.append(f"新号({video_count}条)")
    if stability_ratio < 0.3 and avg_likes > 1000:
        risk_tags.append(f"不稳定(最低{min_likes})")
    if trend == "下降":
        risk_tags.append("下降趋势")

    while len(plays) < 5:
        plays.append(0)

    # 内容定位
    all_text = ' '.join([v.get('desc', '') + v.get('title', '') for v in videos_sorted])
    if '求职' in all_text or '校招' in all_text or '面试' in all_text:
        content_type = "求职/校招"
    elif '职场' in all_text:
        content_type = "职场"
    elif '成长' in all_text or '提升' in all_text:
        content_type = "个人成长"
    else:
        content_type = "职场/成长"

    results.append({
        '达人名称': nickname,
        '粉丝数': f"~{fans}" if real_fans == 0 else fans,
        '播放1(最新)': plays[0],
        '播放2': plays[1],
        '播放3': plays[2],
        '播放4': plays[3],
        '播放5(最早)': plays[4],
        '平均播放': int(sum(plays[:video_count]) / video_count),
        '粉赞比(%)': round(fan_like_ratio, 2),
        '评级': grade,
        '趋势': trend,
        '风险标签': ",".join(risk_tags) if risk_tags else "无",
        '样本量': video_count,
        '内容定位': content_type,
        '主页链接': f"https://www.douyin.com/user/{user_id}",
        '投放评估': evaluation,
    })

# 排序
def sort_key(r):
    grade_order = {'S级': 0, 'A级': 1, 'B级': 2, 'C级': 3, 'D级': 4}
    return (grade_order.get(r['评级'], 5), -r['粉赞比(%)'])

results.sort(key=sort_key)

premium = [r for r in results if r['评级'] in ['S级', 'A级']]
backup = [r for r in results if r['评级'] not in ['S级', 'A级']]

# 写入CSV
fieldnames = ['达人名称', '粉丝数', '播放1(最新)', '播放2', '播放3', '播放4', '播放5(最早)',
             '平均播放', '粉赞比(%)', '评级', '趋势', '风险标签', '样本量',
             '内容定位', '主页链接', '投放评估']

def write_csv(filename, data):
    with open(filename, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    print(f"✓ {filename}: {len(data)} 个达人")

write_csv(OUTPUT_PREMIUM, premium)
write_csv(OUTPUT_BACKUP, backup)

print(f"\n{'='*60}")
print(f"重建完成！")
print(f"  跳过跟进表达人: {skipped}")
print(f"  优质达人: {len(premium)} 个")
print(f"  备选达人: {len(backup)} 个")
print(f"  总计: {len(results)} 个")
print(f"{'='*60}")

for grade in ['S级', 'A级', 'B级', 'C级', 'D级']:
    count = len([r for r in results if r['评级'] == grade])
    if count > 0:
        print(f"  {grade}: {count}")
