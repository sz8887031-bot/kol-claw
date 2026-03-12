#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
导出达人跟进表为Excel格式
可以直接导入到飞书多维表格
"""

import pandas as pd
from datetime import datetime
import os


def export_to_excel():
    """导出CSV为Excel格式"""
    print("=" * 80)
    print("导出达人跟进表为Excel")
    print("=" * 80)

    # 读取CSV
    csv_path = "data/达人跟进表.csv"
    print(f"\n📖 读取CSV文件: {csv_path}")
    df = pd.read_csv(csv_path, encoding='utf-8-sig')
    print(f"✅ 读取成功，共 {len(df)} 条数据")

    # 统计信息
    total = len(df)
    contacted = len(df[df['建联状态'].notna() & (df['建联状态'] != '未建联')])
    confirmed = len(df[df['确定合作'].notna() & (df['确定合作'] == '确定合作')])
    print(f"   📊 总达人: {total} | 已建联: {contacted} | 确定合作: {confirmed}")

    # 导出为Excel
    output_file = f"达人跟进表_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    output_path = os.path.join("data", output_file)

    print(f"\n📝 导出为Excel: {output_file}")

    # 使用openpyxl引擎，支持更好的格式化
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='达人跟进表', index=False)

        # 获取工作表
        worksheet = writer.sheets['达人跟进表']

        # 自动调整列宽
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width

    print(f"✅ 导出成功: {output_path}")

    print("\n" + "=" * 80)
    print("✅ 完成！")
    print("=" * 80)
    print(f"\n📄 文件位置: {output_path}")
    print("\n💡 使用方法:")
    print("   1. 在飞书中创建新的多维表格")
    print("   2. 点击右上角「...」→「导入」")
    print("   3. 选择刚才导出的Excel文件")
    print("   4. 这样创建的表格所有者就是你自己")

    return output_path


if __name__ == '__main__':
    export_to_excel()
