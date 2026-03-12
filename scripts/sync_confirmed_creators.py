#!/usr/bin/env python3
"""
同步已确定合作达人数据
从达人跟进表.csv提取确定合作的达人，更新到确定合作达人跟进表.csv

版本：v2.0
更新：2026-03-10
- 修复：统一使用CSV格式，避免Excel列名不一致问题
- 优化：简化逻辑，直接覆盖CSV文件
- 新增：自动备份旧文件
"""

import pandas as pd
from datetime import datetime
import os
import shutil
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / 'data'

def backup_file(file_path):
    """备份文件"""
    if os.path.exists(file_path):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f"{file_path}.backup_{timestamp}"
        shutil.copy2(file_path, backup_path)
        print(f"📦 已备份旧文件: {backup_path}")
        return True
    return False

def sync_confirmed_creators():
    """同步确定合作达人"""

    # 文件路径
    source_file = DATA_DIR / '达人跟进表.csv'
    target_file = DATA_DIR / '确定合作达人跟进表.csv'

    print("=" * 60)
    print("同步确定合作达人数据")
    print("=" * 60)

    # 1. 读取达人跟进表
    print(f"\n📖 读取源文件: {source_file}")
    try:
        df = pd.read_csv(source_file, encoding='utf-8-sig')
        print(f"✅ 读取成功，共 {len(df)} 条数据")
    except FileNotFoundError:
        print(f"❌ 错误：找不到文件 {source_file}")
        return False
    except Exception as e:
        print(f"❌ 读取失败: {e}")
        return False

    # 2. 筛选确定合作的达人
    print("\n🔍 筛选确定合作的达人...")
    confirmed = df[df['确定合作'] == '确定合作'].copy()
    print(f"✅ 找到 {len(confirmed)} 个确定合作的达人")

    if len(confirmed) == 0:
        print("⚠️  没有确定合作的达人，无需同步")
        return True

    # 3. 备份旧文件
    if os.path.exists(target_file):
        backup_file(target_file)

    # 4. 保存到CSV
    print(f"\n💾 保存到: {target_file}")
    try:
        confirmed.to_csv(target_file, index=False, encoding='utf-8-sig')
        print(f"✅ 保存成功")
    except Exception as e:
        print(f"❌ 保存失败: {e}")
        return False

    # 5. 显示统计信息
    print("\n" + "=" * 60)
    print("📊 同步统计")
    print("=" * 60)
    print(f"总数: {len(confirmed)} 个达人")

    # 按达人级别统计
    if '达人级别' in confirmed.columns:
        level_counts = confirmed['达人级别'].value_counts()
        print("\n按级别分布:")
        for level, count in level_counts.items():
            print(f"  {level}: {count} 个")

    # 按投放状态统计
    if '投放状态' in confirmed.columns:
        status_counts = confirmed['投放状态'].value_counts()
        print("\n按投放状态分布:")
        for status, count in status_counts.items():
            print(f"  {status}: {count} 个")

    # 显示最新5个达人
    print("\n最新5个确定合作的达人:")
    for idx, row in confirmed.tail(5).iterrows():
        name = row.get('达人昵称', '未知')
        price = row.get('报价', '未报价')
        level = row.get('达人级别', '未评级')
        print(f"  - {name} (报价: {price}, 级别: {level})")

    print("\n" + "=" * 60)
    print("✅ 同步完成！")
    print("=" * 60)

    return True

if __name__ == '__main__':
    success = sync_confirmed_creators()
    exit(0 if success else 1)
