#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
建联状态更新工具 v3.0
快速批量更新达人建联状态和时间

使用方法：
1. 批量更新为"已建联"：
   python3 update_status.py --contact 达人1 达人2 达人3

2. 跟进操作（自动+1次数）：
   python3 update_status.py --follow 达人1 达人2

3. 标记为已回复（未报价）：
   python3 update_status.py --reply 达人1 达人2

4. 更新报价：
   python3 update_status.py --quote 达人名 3000

5. 确定合作：
   python3 update_status.py --confirm 达人名

6. 标记无效（已拒绝）：
   python3 update_status.py --invalid 达人名
"""

import pandas as pd
import sys
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / 'data'

def update_status(csv_path=DATA_DIR / '达人跟进表.csv'):
    """更新建联状态"""
    if len(sys.argv) < 3:
        print(__doc__)
        return

    df = pd.read_csv(csv_path, encoding='utf-8-sig')

    action = sys.argv[1]
    names = sys.argv[2:]
    today = datetime.now().strftime('%Y-%m-%d')

    # 确保必要列存在
    if '触达次数' not in df.columns:
        df['触达次数'] = 0
    if '确定合作' not in df.columns:
        df['确定合作'] = ''

    updated_count = 0

    if action == '--contact':
        # 批量打招呼
        for name in names:
            mask = df['达人昵称'] == name
            if mask.any():
                df.loc[mask, '建联状态'] = '已建联'
                df.loc[mask, '建联时间'] = df.loc[mask, '建联时间'].replace('', today).fillna(today)
                df.loc[mask, '最后跟进时间'] = today
                df.loc[mask, '触达次数'] = df.loc[mask, '触达次数'].fillna(0) + 1
                print(f"✓ {name} → 已建联")
                updated_count += 1
            else:
                print(f"✗ 未找到: {name}")

    elif action == '--follow':
        # 跟进操作
        for name in names:
            mask = df['达人昵称'] == name
            if mask.any():
                current_count = df.loc[mask, '触达次数'].fillna(0).iloc[0]
                new_count = current_count + 1

                if new_count >= 3:
                    df.loc[mask, '确定合作'] = '待跟进'
                    print(f"⚠️  {name} → 待跟进 (第{int(new_count)}次，建议标记已拒绝)")
                else:
                    df.loc[mask, '确定合作'] = '待跟进'
                    print(f"✓ {name} → 待跟进 (第{int(new_count)}次)")

                if (df.loc[mask, '建联状态'] == '未建联').any():
                    df.loc[mask, '建联状态'] = '已建联'
                df.loc[mask, '最后跟进时间'] = today
                df.loc[mask, '触达次数'] = new_count
                updated_count += 1
            else:
                print(f"✗ 未找到: {name}")

    elif action == '--reply':
        # 标记已回复
        for name in names:
            mask = df['达人昵称'] == name
            if mask.any():
                df.loc[mask, '建联状态'] = '未报价'
                df.loc[mask, '最后跟进时间'] = today
                print(f"✓ {name} → 已回复(未报价)")
                updated_count += 1
            else:
                print(f"✗ 未找到: {name}")

    elif action == '--quote':
        # 更新报价
        if len(names) < 2:
            print("错误：需要提供达人名和报价金额")
            print("用法：python3 update_status.py --quote 达人名 3000")
            return

        name = names[0]
        try:
            price = float(names[1])
        except:
            print(f"错误：报价金额无效: {names[1]}")
            return

        mask = df['达人昵称'] == name
        if mask.any():
            if (df.loc[mask, '建联状态'] == '未建联').any():
                df.loc[mask, '建联状态'] = '已建联'
            df.loc[mask, '报价'] = price
            df.loc[mask, '最后跟进时间'] = today
            if '确定合作' in df.columns and (df.loc[mask, '确定合作'].isna() | (df.loc[mask, '确定合作'] == '')).any():
                df.loc[mask, '确定合作'] = '待跟进'
            print(f"✓ {name} → 已记录报价 ¥{price:.0f}")
            updated_count += 1
        else:
            print(f"✗ 未找到: {name}")

    elif action == '--confirm':
        # 确定合作
        for name in names:
            mask = df['达人昵称'] == name
            if mask.any():
                df.loc[mask, '确定合作'] = '确定合作'
                if (df.loc[mask, '建联状态'] == '未建联').any():
                    df.loc[mask, '建联状态'] = '已建联'
                df.loc[mask, '最后跟进时间'] = today
                print(f"🎉 {name} → 确定合作")
                updated_count += 1
            else:
                print(f"✗ 未找到: {name}")

    elif action == '--invalid':
        # 标记无效
        for name in names:
            mask = df['达人昵称'] == name
            if mask.any():
                df.loc[mask, '确定合作'] = '已拒绝'
                df.loc[mask, '最后跟进时间'] = today
                print(f"✓ {name} → 已拒绝")
                updated_count += 1
            else:
                print(f"✗ 未找到: {name}")

    else:
        print(f"错误：未知操作 {action}")
        print(__doc__)
        return

    if updated_count > 0:
        # 保存CSV
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        print(f"\n✅ 成功更新 {updated_count} 个达人状态")
        print(f"📁 已保存到: {csv_path}")
    else:
        print("\n❌ 没有更新任何数据")


if __name__ == '__main__':
    update_status()
