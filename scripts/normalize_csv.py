#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSV规范化工具
功能：
1. 统一日期格式为 YYYY-MM-DD
2. 分离沟通记录和备注中的混合信息
3. 补全缺失的字段
4. 修复格式错乱的行
"""

import pandas as pd
import re
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / 'data'

def normalize_csv(input_file=DATA_DIR / '达人跟进表.csv', output_file=DATA_DIR / '达人跟进表_规范化.csv'):
    """规范化CSV文件"""

    # 读取CSV
    df = pd.read_csv(input_file, encoding='utf-8-sig')

    print(f"📊 原始数据: {len(df)}行")
    print(f"📋 列名: {list(df.columns)}\n")

    # 1. 处理达人ID - 自动生成连续ID
    df['达人ID'] = range(1, len(df) + 1)

    # 2. 统一添加日期格式
    today = datetime.now().strftime('%Y-%m-%d')
    df['添加日期'] = df['添加日期'].fillna(today)

    # 确保新字段存在（以当前CSV为准）
    for col in ['确定合作', '微信联系方式', '已创建日历', '达人级别']:
        if col not in df.columns:
            df[col] = ''
    if '触达次数' not in df.columns:
        df['触达次数'] = 0

    # 3. 补全空字段
    df['粉丝数'] = df['粉丝数'].fillna(0).astype(int)
    df['报价'] = df['报价'].fillna('')
    df['建联状态'] = df['建联状态'].fillna('未建联')
    df['确定合作'] = df['确定合作'].fillna('')
    df['最后跟进时间'] = df['最后跟进时间'].fillna('')
    df['建联时间'] = df['建联时间'].fillna('')
    df['微信联系方式'] = df['微信联系方式'].fillna('')
    df['触达次数'] = df['触达次数'].fillna(0)
    df['已创建日历'] = df['已创建日历'].fillna('')

    # 4. 规范化沟通记录和备注
    for idx, row in df.iterrows():
        comm = str(row.get('沟通记录', '')).strip()
        memo = str(row.get('备注', '')).strip()

        # 提取日期信息到备注
        date_pattern = r'(\d{1,2}\s*月\s*\d{1,2}\s*[号日].*?(?:联系|跟进|谈判|制作))'
        dates = re.findall(date_pattern, comm)
        if dates:
            # 将日期信息移到备注
            for date_str in dates:
                if date_str not in memo:
                    memo = f"{date_str}；{memo}" if memo and memo != 'nan' else date_str
                comm = comm.replace(date_str, '').strip()

        # 提取报价信息
        price_pattern = r'报价\s*(\d+)'
        price_match = re.search(price_pattern, comm)
        if price_match and not row['报价']:
            df.at[idx, '报价'] = price_match.group(1)
            comm = comm.replace(price_match.group(0), '').strip()

        # 清理多余分号
        comm = re.sub(r'；+', '；', comm).strip('；').strip()
        memo = re.sub(r'；+', '；', memo).strip('；').strip()

        # 更新
        df.at[idx, '沟通记录'] = comm if comm and comm != 'nan' else ''
        df.at[idx, '备注'] = memo if memo and memo != 'nan' else ''

    # 5. 确保所有列都存在且有序
    expected_columns = [
        '达人ID', '添加日期', '达人昵称', '粉丝数',
        '播放1', '播放2', '播放3', '播放4', '播放5',
        '报价', '建联状态', '确定合作',
        '最后跟进时间', '建联时间',
        '沟通记录', '备注', '达人级别',
        '微信联系方式', '触达次数', '已创建日历'
    ]

    # 添加缺失的列
    for col in expected_columns:
        if col not in df.columns:
            df[col] = ''

    # 按预期顺序排列
    df = df[expected_columns]

    # 6. 保存规范化后的CSV
    df.to_csv(output_file, index=False, encoding='utf-8-sig')

    print(f"✅ 规范化完成！")
    print(f"📁 输出文件: {output_file}")
    print(f"📊 规范化后: {len(df)}行 × {len(df.columns)}列\n")

    # 显示统计
    print("=" * 80)
    print("📊 数据统计")
    print("=" * 80)
    print(f"总达人数: {len(df)}")
    print(f"已建联: {len(df[df['建联状态'] != '未建联'])}")
    print(f"未建联: {len(df[df['建联状态'] == '未建联'])}")
    print(f"有报价: {len(df[df['报价'] != ''])}")
    print(f"有备注: {len(df[df['备注'] != ''])}")

    # 显示前几行预览
    print("\n" + "=" * 80)
    print("📋 前3行预览")
    print("=" * 80)
    for idx, row in df.head(3).iterrows():
        print(f"\n{idx+1}. {row['达人昵称']} | 粉丝:{row['粉丝数']:,}")
        print(f"   建联状态: {row['建联状态']}")
        if row['沟通记录']:
            print(f"   沟通: {row['沟通记录'][:50]}")
        if row['备注']:
            print(f"   备注: {row['备注'][:50]}")

    return df

if __name__ == '__main__':
    import sys

    # 支持命令行参数
    input_file = sys.argv[1] if len(sys.argv) > 1 else '达人跟进表.csv'
    output_file = sys.argv[2] if len(sys.argv) > 2 else '达人跟进表_规范化.csv'

    print("=" * 80)
    print("🔧 CSV规范化工具")
    print("=" * 80)
    print()

    try:
        df = normalize_csv(input_file, output_file)

        print("\n" + "=" * 80)
        print("💡 下一步操作")
        print("=" * 80)
        print("1. 检查规范化后的文件: 达人跟进表_规范化.csv")
        print("2. 确认无误后，替换原文件:")
        print("   mv 达人跟进表_规范化.csv 达人跟进表.csv")
        print("3. 或者直接使用规范化文件进行后续工作")

    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
