#!/usr/bin/env python3
"""处理MediaCrawler抓取的数据并生成CSV - 多维度评估版本"""

import json
import csv
from collections import defaultdict
from pathlib import Path
from datetime import datetime

# 文件路径（支持自动查找今日文件）
today = datetime.now().strftime("%Y-%m-%d")
CREATOR_FILE = f"<MEDIACRAWLER_DIR>/data/douyin/json/creator_contents_{today}.json"
CREATOR_INFO_FILE = f"<MEDIACRAWLER_DIR>/data/douyin/json/creator_creators_{today}.json"
SEARCH_FILE = f"<MEDIACRAWLER_DIR>/data/douyin/json/search_contents_{today}.json"
OUTPUT_PREMIUM = "<PROJECT_DIR>/data/优质达人.csv"
OUTPUT_BACKUP = "<PROJECT_DIR>/data/备选达人.csv"
TRACKING_FILE = "<PROJECT_DIR>/data/达人跟进表.csv"

# 优先读取creator_contents，如果不存在则使用search_contents
from pathlib import Path
if Path(CREATOR_FILE).exists():
    print(f"📂 读取数据文件: {CREATOR_FILE}")
    with open(CREATOR_FILE, 'r', encoding='utf-8') as f:
        all_videos = json.load(f)
else:
    print(f"📂 读取数据文件: {SEARCH_FILE}")
    with open(SEARCH_FILE, 'r', encoding='utf-8') as f:
        all_videos = json.load(f)

print(f"✅ 共读取 {len(all_videos)} 条视频数据")

# 读取达人信息文件（包含粉丝数）
creator_fans_map = {}
if Path(CREATOR_INFO_FILE).exists():
    print(f"📂 读取达人信息文件: {CREATOR_INFO_FILE}")
    with open(CREATOR_INFO_FILE, 'r', encoding='utf-8') as f:
        creator_infos = json.load(f)
        for creator in creator_infos:
            # creator_creators文件中user_id字段实际存储的是sec_uid
            sec_uid = creator.get('user_id')
            fans = creator.get('fans', 0)
            if sec_uid and fans:
                creator_fans_map[sec_uid] = fans
    print(f"✅ 共读取 {len(creator_fans_map)} 个达人的粉丝数据")
else:
    print("⚠️  未找到达人信息文件，将使用估算粉丝数")

# 按达人聚合视频（使用sec_uid）
creator_videos = defaultdict(list)
creator_info = {}

for video in all_videos:
    sec_uid = video.get('sec_uid')
    if not sec_uid:
        continue

    creator_videos[sec_uid].append(video)

    # 保存达人基本信息（取最新的）
    if sec_uid not in creator_info:
        creator_info[sec_uid] = {
            'user_id': video.get('user_id'),
            'nickname': video.get('nickname', '未知'),
            'avatar': video.get('avatar'),
        }

print(f"👤 共发现 {len(creator_info)} 个达人")

# 读取已有的达人库（去重用）
existing_creators = set()

# 1. 读取达人跟进表
try:
    with open(TRACKING_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get('达人名称', '').strip()
            if name:
                existing_creators.add(name)
except FileNotFoundError:
    print("⚠️  达人跟进表不存在，跳过去重")

# 2. 读取优质达人表
try:
    with open(OUTPUT_PREMIUM, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get('达人名称', '').strip()
            if name:
                existing_creators.add(name)
except FileNotFoundError:
    print("ℹ️  优质达人表不存在，将创建新文件")

# 3. 读取备选达人表
try:
    with open(OUTPUT_BACKUP, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get('达人名称', '').strip()
            if name:
                existing_creators.add(name)
except FileNotFoundError:
    print("ℹ️  备选达人表不存在，将创建新文件")

print(f"🗂️  已有达人库: {len(existing_creators)} 个（去重）")

# 分析每个达人
results = []
skipped_duplicate = 0

for sec_uid, info in creator_info.items():
    nickname = info.get('nickname', '未知')
    user_id = info.get('user_id', '')
    videos = creator_videos.get(sec_uid, [])

    # 去重检查
    if nickname in existing_creators:
        skipped_duplicate += 1
        continue

    # 修改：不再跳过视频数不足5条的达人
    if len(videos) < 2:
        print(f"⚠️  {nickname}: 视频数不足2条（{len(videos)}条），跳过")
        continue

    # 取所有可用视频（最多5条）
    videos_sorted = sorted(videos, key=lambda x: x.get('create_time', 0), reverse=True)[:5]
    video_count = len(videos_sorted)

    # 提取点赞数并转换为预估播放量
    likes = []  # 原始点赞数
    plays = []  # 预估播放量（点赞数 ÷ 3%）
    for v in videos_sorted:
        like_count = v.get('liked_count', '0')
        if isinstance(like_count, str):
            like_count = int(like_count.replace(',', ''))
        likes.append(like_count)
        # 点赞率3%，播放量 = 点赞数 / 0.03
        estimated_play = int(like_count / 0.03)
        plays.append(estimated_play)

    # 规则（2026-03-11）：稳定性过滤——成熟账号（≥5条）中有≥2条播放<1w，说明不稳定，直接pass
    # 新号（<5条）豁免，仍可进入观察列表
    if video_count >= 5:
        below_10k = sum(1 for p in plays[:video_count] if p < 10000)
        if below_10k >= 2:
            print(f"⏭️  {nickname}: {video_count}条中{below_10k}条播放<1w，稳定性不足，pass")
            continue

    # 计算指标
    avg_likes = sum(likes) / len(likes)
    min_likes = min(likes)
    max_likes = max(likes)

    # 获取真实粉丝数或使用估算
    real_fans = creator_fans_map.get(sec_uid, 0)
    if real_fans > 0:
        fans = real_fans
    else:
        # search模式无粉丝数，使用平均点赞×20作为估算（粉赞比约5%）
        fans = int(avg_likes * 20)

    fan_like_ratio = (avg_likes / fans * 100) if fans > 0 else 0
    stability_ratio = min_likes / avg_likes if avg_likes > 0 else 0

    # 判断趋势
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

    # 多维度评估
    # 1. 评级（S/A/B/C/D）
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

    # 2. 风险标签
    risk_tags = []
    if video_count < 5:
        risk_tags.append(f"新号({video_count}条)")
    if stability_ratio < 0.3 and avg_likes > 1000:
        risk_tags.append(f"不稳定(最低{min_likes})")
    if trend == "下降":
        risk_tags.append("下降趋势")

    risk_label = ",".join(risk_tags) if risk_tags else "无"

    # 主页链接
    homepage = f"https://www.douyin.com/user/{user_id}"

    # 内容定位（从视频标题/描述推断）
    all_text = ' '.join([v.get('desc', '') + v.get('title', '') for v in videos_sorted])
    if '求职' in all_text or '校招' in all_text or '面试' in all_text:
        content_type = "求职/校招"
    elif '职场' in all_text:
        content_type = "职场"
    elif '成长' in all_text or '提升' in all_text:
        content_type = "个人成长"
    else:
        content_type = "职场/成长"

    # 补齐播放数据（不足5条用0填充）
    while len(plays) < 5:
        plays.append(0)

    results.append({
        '达人名称': nickname,
        '粉丝数': f"~{fans}" if real_fans == 0 else fans,  # 估算值标记~，真实值不标记
        '播放1(最新)': plays[0],
        '播放2': plays[1],
        '播放3': plays[2],
        '播放4': plays[3],
        '播放5(最早)': plays[4],
        '平均播放': int(sum(plays[:video_count]) / video_count),
        '粉赞比(%)': round(fan_like_ratio, 2),
        '评级': grade,
        '趋势': trend,
        '风险标签': risk_label,
        '样本量': video_count,
        '内容定位': content_type,
        '主页链接': homepage,
        '投放评估': evaluation,
        '稳定性': stability_ratio  # 用于排序
    })

# 按评级和粉赞比排序
def sort_key(r):
    grade_order = {'S级': 0, 'A级': 1, 'B级': 2, 'C级': 3, 'D级': 4}
    return (grade_order.get(r['评级'], 5), -r['粉赞比(%)'])

results.sort(key=sort_key)

# 分类：S级和A级进优质达人，其余进备选
premium = [r for r in results if r['评级'] in ['S级', 'A级']]
backup = [r for r in results if r['评级'] not in ['S级', 'A级']]

# 移除稳定性字段（不输出到CSV）
for r in results:
    r.pop('稳定性', None)

# 写入CSV
def write_csv(filename, data):
    if not data:
        print(f"⚠️  {filename}: 无数据")
        return

    fieldnames = ['达人名称', '粉丝数', '播放1(最新)', '播放2', '播放3', '播放4', '播放5(最早)',
                 '平均播放', '粉赞比(%)', '评级', '趋势', '风险标签', '样本量',
                 '内容定位', '主页链接', '投放评估']

    # 追加模式：读取已有数据，合并后写入
    existing_data = []
    existing_names = set()
    if Path(filename).exists():
        with open(filename, 'r', encoding='utf-8-sig', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing_data.append(row)
                existing_names.add(row.get('达人名称', '').strip())

    # 只追加不重复的新达人
    new_data = [d for d in data if d['达人名称'] not in existing_names]

    all_data = existing_data + new_data
    with open(filename, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_data)

    print(f"✓ {filename}: {len(all_data)} 个达人（新增 {len(new_data)} 个）")

# 输出结果
print("\n" + "="*80)
print("达人分析完成 - 多维度评估")
print("="*80)
print(f"\n原始数据: {len(all_videos)} 条视频")
print(f"发现达人: {len(creator_info)} 个")
print(f"跳过重复: {skipped_duplicate} 个")
print(f"最终分析: {len(results)} 个新达人")
print(f"\n评级分布:")
for grade in ['S级', 'A级', 'B级', 'C级', 'D级']:
    count = len([r for r in results if r['评级'] == grade])
    if count > 0:
        print(f"  {grade}: {count} 个")

print(f"\n优质达人（S/A级）: {len(premium)} 个")
print(f"备选达人（B/C/D级）: {len(backup)} 个\n")

write_csv(OUTPUT_PREMIUM, premium)
write_csv(OUTPUT_BACKUP, backup)

print("\n⭐ 优质达人详情（前10个）:\n")
for i, r in enumerate(premium[:10], 1):
    risk_info = f" | ⚠️ {r['风险标签']}" if r['风险标签'] != "无" else ""
    print(f"{i}. [{r['评级']}] {r['达人名称']}")
    print(f"   粉丝: {r['粉丝数']} | 平均播放: {r['平均播放']:,} | 粉赞比: {r['粉赞比(%)']}%")
    print(f"   样本: {r['样本量']}条 | 趋势: {r['趋势']}{risk_info}")
    print(f"   💡 {r['投放评估']}")
    print(f"   🔗 {r['主页链接']}\n")

print("="*80)
print(f"✅ 数据已保存到:")
print(f"   - 优质达人: {OUTPUT_PREMIUM}")
print(f"   - 备选达人: {OUTPUT_BACKUP}")
print("="*80)

