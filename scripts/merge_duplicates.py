#!/usr/bin/env python3
"""
达人重复记录合并脚本
自动检测并合并重复的达人记录，保留最完整的信息
"""

import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / 'data'

def merge_duplicates(df):
    """合并重复的达人记录"""

    # 找出重复的抖音号
    duplicated_names = df[df.duplicated(subset=['达人昵称'], keep=False)]['达人昵称'].unique()

    if len(duplicated_names) == 0:
        print("✓ 没有发现重复记录")
        return df

    print(f"发现 {len(duplicated_names)} 个重复达人，开始合并...\n")

    # 存储要删除的行索引
    rows_to_drop = []

    # 建联状态优先级（按当前CSV列）
    contact_status_priority = {
        '未建联': 1,
        '待接触': 1,
        '待筛选': 1,
        '已建联': 2,
        '已私信': 2,
        '待跟进': 2,
        '未报价': 3,
        '已回复': 3,
        '已报价': 4,
        '确定合作': 5
    }

    # 合作状态优先级（确定合作列）
    coop_status_priority = {
        '已拒绝': 0,
        '待跟进': 1,
        '确定合作': 2,
        '已投放': 3,
        '已发布': 4
    }

    def choose_best_status(records, column, priority_map):
        """选择优先级最高的状态值"""
        if column not in records.columns:
            return np.nan
        values = records[column]
        if values.notna().any():
            priorities = values.apply(lambda x: priority_map.get(str(x).strip(), -1) if pd.notna(x) else -1)
            best_idx = priorities.idxmax()
            return records.loc[best_idx, column]
        return np.nan

    def merge_play_data(records):
        """合并播放数据"""
        plays = []
        for idx, row in records.iterrows():
            for i in range(1, 6):
                col = f'播放{i}'
                if pd.notna(row[col]) and row[col] != '':
                    plays.append(row[col])
        # 返回前5个播放数据
        result = {}
        for i, play in enumerate(plays[:5], 1):
            result[f'播放{i}'] = play
        return result

    def merge_text_field(records, field):
        """合并文本字段（去重）"""
        texts = []
        for idx, row in records.iterrows():
            if pd.notna(row[field]) and str(row[field]).strip() != '':
                text = str(row[field]).strip()
                if text not in texts:
                    texts.append(text)
        return '；'.join(texts) if texts else np.nan

    def choose_best_value(records, field, prefer='latest'):
        """选择最佳值"""
        values = records[field].dropna()
        if len(values) == 0:
            return np.nan

        if prefer == 'latest':
            # 选择最新的记录的值
            return records.sort_values('添加日期', ascending=False).iloc[0][field]
        elif prefer == 'max':
            # 选择最大值
            return values.max()
        elif prefer == 'first':
            # 选择第一个有值的
            return values.iloc[0]
        else:
            return values.iloc[-1]

    # 对每个重复的达人进行合并
    for name in duplicated_names:
        records = df[df['达人昵称'] == name].copy()

        print(f"【{name}】合并 {len(records)} 条记录:")
        for idx, row in records.iterrows():
            date = row['添加日期']
            contact_status = row['建联状态'] if '建联状态' in records.columns and pd.notna(row.get('建联状态')) else ''
            coop_status = row['确定合作'] if '确定合作' in records.columns and pd.notna(row.get('确定合作')) else ''
            status = f"{contact_status}/{coop_status}".strip('/')
            price = f"{int(row['报价'])}元" if pd.notna(row['报价']) else '无'
            print(f"  ID{row['达人ID']} | {date} | {status} | {price}")

        # 创建合并后的记录
        merged = {}

        # 基础信息
        merged['达人ID'] = records.iloc[0]['达人ID']  # 保留第一个ID
        merged['达人昵称'] = name

        # 日期：最早添加，最晚跟进
        merged['添加日期'] = records['添加日期'].min()
        if records['最后跟进时间'].notna().any():
            merged['最后跟进时间'] = records['最后跟进时间'].max()
        else:
            merged['最后跟进时间'] = np.nan

        if records['建联时间'].notna().any():
            merged['建联时间'] = records['建联时间'].min()
        else:
            merged['建联时间'] = np.nan

        # 数值字段：选择有值的，优先最新的
        merged['粉丝数'] = choose_best_value(records, '粉丝数', 'max')  # 粉丝数选最大的
        merged['报价'] = choose_best_value(records, '报价', 'latest')  # 报价选最新的
        merged['触达次数'] = records['触达次数'].sum() if records['触达次数'].notna().any() else np.nan

        # 文本字段：选择有值的第一个
        merged['达人级别'] = choose_best_value(records, '达人级别', 'first')
        merged['微信联系方式'] = choose_best_value(records, '微信联系方式', 'first')

        # 状态：选择优先级最高的
        merged['建联状态'] = choose_best_status(records, '建联状态', contact_status_priority)
        merged['确定合作'] = choose_best_status(records, '确定合作', coop_status_priority)

        # 合并播放数据
        play_data = merge_play_data(records)
        for i in range(1, 6):
            col = f'播放{i}'
            merged[col] = play_data.get(col, np.nan)

        # 合并文本字段（追加）
        merged['沟通记录'] = merge_text_field(records, '沟通记录')
        merged['备注'] = merge_text_field(records, '备注')
        # 更新第一条记录
        first_idx = records.index[0]
        for key, value in merged.items():
            df.at[first_idx, key] = value

        # 标记其他记录待删除
        rows_to_drop.extend(records.index[1:].tolist())

        status_display = f"{merged.get('建联状态', '')}/{merged.get('确定合作', '')}".strip('/')
        print(f"  → 合并到ID{merged['达人ID']} | {merged['添加日期']} | {status_display}")
        print()

    # 删除重复的记录
    df = df.drop(rows_to_drop)

    # 按达人ID排序（保持原有顺序，新增的永远在最后）
    df = df.sort_values('达人ID', ascending=True)
    df = df.reset_index(drop=True)
    df['达人ID'] = range(1, len(df) + 1)

    print(f"✓ 合并完成，删除了 {len(rows_to_drop)} 条重复记录")
    print(f"✓ 当前总数: {len(df)} 个达人")

    return df


def main():
    """主函数"""
    print("=== 达人记录合并工具 ===\n")

    # 备份原文件
    backup_file = DATA_DIR / f'达人跟进表_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    import shutil
    shutil.copy(DATA_DIR / '达人跟进表.csv', backup_file)
    print(f"✓ 已备份到: {backup_file}\n")

    # 读取数据
    df = pd.read_csv(DATA_DIR / '达人跟进表.csv')
    print(f"原始数据: {len(df)} 条记录\n")

    # 合并重复记录
    df = merge_duplicates(df)

    # 保存
    df.to_csv(DATA_DIR / '达人跟进表.csv', index=False, encoding='utf-8-sig')
    print(f"\n✓ 已保存到: {DATA_DIR / '达人跟进表.csv'}")

    # 统计
    print(f"\n=== 最终统计 ===")
    print(f"总达人数: {len(df)}")
    print(f"有报价: {df['报价'].notna().sum()}")
    if '确定合作' in df.columns:
        confirmed = df['确定合作'].astype(str).str.contains('确定合作|已投放|已发布', na=False).sum()
        print(f"确定合作: {confirmed}")


if __name__ == '__main__':
    main()
